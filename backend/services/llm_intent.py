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
        {"intent": "general_chat", "ingredient_name": None}
    """
    
    prompt = f"""
    You are an AI assistant for a Traditional Chinese Medicine safety app. 
    The user will ask about a TCM ingredient. Extract the main ingredient they are asking about. 
    Respond ONLY in valid JSON matching this schema: {{"intent": "ingredient_inquiry", "ingredient_name": "NAME"}}. 
    If the message is a greeting, small talk, general question (e.g. "What is TCM?"), or unrelated to specific TCM ingredients, set 'intent' to 'general_chat' and 'ingredient_name' to null.
    
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
        return {"intent": "general_chat", "ingredient_name": None}

async def generate_chat_reply(message_text: str) -> str:
    """
    Generates a conversational reply using Gemini Flash for general inquiries.
    Strictly forbids generating medical advice.
    """
    prompt = f"""
    You are FitMate, an AI assistant for a Traditional Chinese Medicine (TCM) safety app.
    Your main job is to help users understand how to use the app to scan TCM labels and check ingredient safety.
    
    CONSTRAINT: You operate under a ZERO HALLUCINATION MANDATE for medical info. 
    DO NOT provide medical advice, diagnosis, or recommend alternative treatments. 
    If a user asks a medical question, politely decline and advise them to consult a healthcare professional.
    Keep your answers friendly, short, and to the point.
    
    User message: "{message_text}"
    """
    
    try:
        response = await model.generate_content_async(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.3,
            ),
        )
        return response.text.strip()
    except Exception as e:
        print(f"Error generating chat reply: {e}")
        return "Mohon maaf, terjadi kesalahan pada sistem kami. Silakan coba beberapa saat lagi."
