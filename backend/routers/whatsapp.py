from fastapi import APIRouter, HTTPException, Request, Depends
from core.config import settings
from services.whatsapp_service import whatsapp_client
from main import limiter

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

# A simple in-memory rate limit for whatsapp sender phone numbers to prevent abuse 
# until proper database rate limiting is applied if needed.
# Since we only get a single IP from webhooks, we use the sender_phone.
# We will do this manually or via a custom dependency.
from cachetools import TTLCache
# cache up to 1000 numbers, max 10 requests per 60 seconds.
rate_limit_cache = TTLCache(maxsize=1000, ttl=60)

@router.get("/webhook")
async def verify_webhook(
    request: Request
):
    """
    Required by Meta to verify the webhook URL.
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
            return int(challenge)
        else:
            raise HTTPException(status_code=403, detail="Verification token mismatch")
    
    raise HTTPException(status_code=400, detail="Missing hub.mode or hub.verify_token")


from fastapi import BackgroundTasks

@router.post("/webhook")
async def receive_message(request: Request, background_tasks: BackgroundTasks):
    """
    Receives incoming WhatsApp messages.
    """
    try:
        body = await request.json()
        
        # Parse Meta's nested payload safely
        entry = body.get("entry", [])
        if not entry:
            return {"status": "ok"}
            
        changes = entry[0].get("changes", [])
        if not changes:
            return {"status": "ok"}
            
        value = changes[0].get("value", {})
        messages = value.get("messages", [])
        
        # If it's a status update (delivered, read) and not an actual message, ignore it
        if not messages:
            return {"status": "ok"}
            
        message = messages[0]
        sender_phone = message.get("from")
        
        if message.get("type") == "text":
            message_text = message.get("text", {}).get("body", "")
            
            # --- Rate Limit Check ---
            count = rate_limit_cache.get(sender_phone, 0)
            if count >= 10:
                # Silently ignore to prevent Meta webhook retries and abuse loops
                return {"status": "rate_limited"}
            rate_limit_cache[sender_phone] = count + 1
            
            # BackgroundTask runs the LLM -> MongoDB -> WhatsApp send pipeline gracefully
            async def process_whatsapp_message(sender: str, text: str):
                from services.llm_intent import parse_intent
                from database.mongo import get_db
                from thefuzz import fuzz
                
                intent = await parse_intent(text)
                
                if intent.get("intent") != "ingredient_inquiry" or not intent.get("ingredient_name"):
                    reply = "Sorry, I can only help check the safety of Traditional Chinese Medicine ingredients. What ingredient would you like to verify?"
                    await whatsapp_client.send_text_message(to_phone=sender, text=reply)
                    return
                
                # Intent matches ingredient
                ingredient_name = intent.get("ingredient_name")
                
                # Connect DB and query via simple fuzzy logic
                db_client = get_db()
                cursor = db_client["ingredients"].find({})
                ingredients = await cursor.to_list(length=1000)
                
                best_match = None
                highest_score = 0
                
                for ing in ingredients:
                    # Check against both mandarin and indonesian name fields assuming Phase 2 logic
                    score_indo = fuzz.token_sort_ratio(ingredient_name.lower(), ing.get("indonesian_name", "").lower())
                    score_mandarin = fuzz.token_sort_ratio(ingredient_name.lower(), ing.get("mandarin_name", "").lower())
                    max_item_score = max(score_indo, score_mandarin)
                    
                    if max_item_score > highest_score:
                        highest_score = max_item_score
                        best_match = ing
                
                if not best_match or highest_score < 75:
                    reply = f"Sorry, {ingredient_name} is not in my safety database. I cannot provide medical advice on it. Please consult a healthcare professional."
                else:
                    if best_match.get("is_toxic", False):
                        reply = f"[MEDICAL DISCLAIMER: Always consult a professional] \n\n⚠️ Warning: {best_match.get('indonesian_name', ingredient_name)} is classified as Toxic/Contraindicated.\nTarget Organ: {best_match.get('target_organ', 'Unknown')}\nDetails: {best_match.get('notes', 'No details available')}"
                    else:
                        reply = f"[MEDICAL DISCLAIMER: Always consult a professional] \n\n✅ {best_match.get('indonesian_name', ingredient_name)} appears safe based on our database."
                        
                await whatsapp_client.send_text_message(to_phone=sender, text=reply)

            # Trigger background logic
            background_tasks.add_task(process_whatsapp_message, sender_phone, message_text)
            
        return {"status": "ok"}
        
    except Exception as e:
        print(f"Error processing webhook: {e}")
        # Always return 200 OK so Meta doesn't retry the webhook endlessly
        return {"status": "ok"}
