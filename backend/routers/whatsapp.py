from fastapi import APIRouter, Request, BackgroundTasks, Form
from services.whatsapp_service import whatsapp_client
from cachetools import TTLCache

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

# Rate limit: max 10 messages per phone number per 60 seconds
rate_limit_cache = TTLCache(maxsize=1000, ttl=60)


@router.post("/webhook")
async def receive_message(
    background_tasks: BackgroundTasks,
    # Twilio sends form-encoded fields (NOT JSON)
    Body: str = Form(default=""),
    From: str = Form(default=""),   # e.g. "whatsapp:+6281234567890"
    To: str = Form(default=""),
    MessageSid: str = Form(default=""),
):
    """
    Receives incoming WhatsApp messages from the Twilio Sandbox.
    Twilio posts application/x-www-form-urlencoded to this endpoint.
    Configure in Twilio Console → Messaging → Sandbox → When a message comes in.
    """
    # Strip the 'whatsapp:' prefix Twilio adds
    sender_phone = From.replace("whatsapp:", "").strip()
    message_text = Body.strip()

    if not sender_phone or not message_text:
        # Status updates or empty payloads — ignore silently
        return _twiml_ok()

    # --- Rate limit ---
    count = rate_limit_cache.get(sender_phone, 0)
    if count >= 10:
        return _twiml_ok()
    rate_limit_cache[sender_phone] = count + 1

    # Kick off processing in background so Twilio gets 200 OK immediately
    background_tasks.add_task(_process_message, sender_phone, message_text)
    return _twiml_ok()


async def _process_message(sender: str, text: str):
    """
    Core rule-based TCM consultation pipeline.
    1. Parse intent (ingredient lookup vs general chat)
    2. Fuzzy-match against MongoDB ingredient database
    3. Reply with safety info + disclaimer
    """
    from services.llm_intent import parse_intent, generate_chat_reply
    from database.mongo import get_db
    from thefuzz import fuzz

    try:
        intent = await parse_intent(text)

        # General conversation — no specific ingredient asked
        if intent.get("intent") == "general_chat" or not intent.get("ingredient_name"):
            reply = await generate_chat_reply(text)
            await whatsapp_client.send_text_message(to_phone=sender, text=reply)
            return

        ingredient_name = intent.get("ingredient_name", "")

        # Fuzzy-match ingredient in MongoDB
        db_client = get_db()
        cursor = db_client["ingredients"].find({})
        ingredients = await cursor.to_list(length=1000)

        best_match = None
        highest_score = 0

        for ing in ingredients:
            score_indo = fuzz.token_sort_ratio(
                ingredient_name.lower(), ing.get("indonesian_name", "").lower()
            )
            score_mandarin = fuzz.token_sort_ratio(
                ingredient_name.lower(), ing.get("mandarin_name", "").lower()
            )
            score = max(score_indo, score_mandarin)
            if score > highest_score:
                highest_score = score
                best_match = ing

        DISCLAIMER = "⚕️ *Disclaimer:* Informasi ini bukan pengganti saran medis profesional.\n\n"

        if not best_match or highest_score < 75:
            reply = (
                f"{DISCLAIMER}"
                f"❓ Bahan *{ingredient_name}* tidak ditemukan dalam database kami.\n"
                "Hubungi apoteker atau dokter untuk informasi lebih lanjut."
            )
        elif best_match.get("is_toxic", False):
            reply = (
                f"{DISCLAIMER}"
                f"⚠️ *Peringatan Toksisitas*\n"
                f"Bahan: *{best_match.get('indonesian_name', ingredient_name)}*\n"
                f"Organ Target: {best_match.get('target_organ', 'Tidak diketahui')}\n"
                f"Catatan: {best_match.get('notes', 'Tidak ada detail.')}"
            )
        else:
            reply = (
                f"{DISCLAIMER}"
                f"✅ *{best_match.get('indonesian_name', ingredient_name)}* "
                "terlihat aman berdasarkan database kami.\n"
                f"Catatan: {best_match.get('notes', 'Tidak ada catatan tambahan.')}"
            )

        await whatsapp_client.send_text_message(to_phone=sender, text=reply)

    except Exception as e:
        print(f"[WhatsApp Bot Error] {e}")
        await whatsapp_client.send_text_message(
            to_phone=sender,
            text="Maaf, terjadi kesalahan dalam memproses pesan Anda. Silakan coba lagi.",
        )


def _twiml_ok():
    """
    Return empty TwiML response. Twilio expects 200 OK.
    Returning plain JSON also works fine for Sandbox.
    """
    return {"status": "ok"}
