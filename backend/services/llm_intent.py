import json
import google.generativeai as genai
from core.config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)

# Use instruction-tuned flash model
model = genai.GenerativeModel("gemini-1.5-flash")

async def parse_intent(message_text: str) -> dict:
    """
    Parses a raw WhatsApp message into structured intent using Gemini Flash.
    Returns:
        {"intent": "ingredient_inquiry", "ingredient_name": "Radix Ginseng"}
        OR
        {"intent": "unknown", "ingredient_name": None}
    """
    
    prompt = f"""
    You are an AI assistant for a Traditional Chinese Medicine safety app. 
    The user will ask about a TCM ingredient. Extract the main ingredient they are asking about. 
    Respond ONLY in valid JSON matching this schema: {{"intent": "ingredient_inquiry", "ingredient_name": "NAME"}}. 
    If the message is a greeting, small talk, or unrelated to TCM ingredients, set 'intent' to 'unknown' and 'ingredient_name' to null.
    
    User message: "{message_text}"
    """
    
    try:
        response = await model.generate_content_async(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.0,
            ),
        )
        
        return json.loads(response.text)
    except Exception as e:
        print(f"Error parsing intent: {e}")
        return {"intent": "unknown", "ingredient_name": None}
