"""
LLM Intent Parser & Chat Reply Generator via OpenRouter API.
Uses google/gemini-2.5-flash-lite for fast response and medical inference.
OpenRouter is OpenAI-compatible — calls /chat/completions with httpx.

Intent classes
--------------
  ingredient_safety_inquiry  — user asking if an ingredient/brand is safe/toxic/contraindicated
                              → ALWAYS DB-grounded; LLM never fabricates a safety verdict
  ingredient_info_inquiry    — user asking what an ingredient is, its benefits, history, uses
                              → LLM answers using DB context if available
  general_tcm_chat           — greetings, general health/TCM questions, off-topic
                              → LLM answers shortly, then redirects to TCM context
"""
import json
import asyncio
import httpx
from core.config import settings

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

if not settings.OPENROUTER_API_KEY:
    raise RuntimeError(
        "OPENROUTER_API_KEY is not set in .env. "
        "Add it to backend/.env and restart the server."
    )

_HEADERS = {
    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://fitmate-tcm.vercel.app",
    "X-Title": "FitMate TCM Safety Scanner",
}

# Reduced from 3 retries × 5s base (35s max) → 2 retries × 2s base (≤8s max)
# This keeps total latency well within Twilio's webhook window
_MAX_RETRIES = 2
_RETRY_BASE_DELAY = 2  # seconds


async def _chat(user_content: str, temperature: float = 0.3, timeout: float = 15.0) -> str:
    """
    Calls OpenRouter /chat/completions with a single user message.
    Retries on 429 / 5xx with exponential backoff.
    timeout: per-request HTTP timeout in seconds (default 15s for chat, use 30s for vision)
    """
    payload = {
        "model": settings.OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": user_content}],
        "temperature": temperature,
    }

    last_err = None
    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(_MAX_RETRIES):
            try:
                resp = await client.post(
                    OPENROUTER_BASE_URL,
                    headers=_HEADERS,
                    json=payload,
                )
                if resp.status_code in (429, 502, 503, 504):
                    wait = _RETRY_BASE_DELAY * (2 ** attempt)
                    print(
                        f"[OpenRouter] HTTP {resp.status_code} on attempt "
                        f"{attempt + 1}/{_MAX_RETRIES}. Retrying in {wait}s..."
                    )
                    await asyncio.sleep(wait)
                    last_err = Exception(f"HTTP {resp.status_code}: {resp.text[:200]}")
                    continue

                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]

            except httpx.TimeoutException as e:
                wait = _RETRY_BASE_DELAY * (2 ** attempt)
                print(
                    f"[OpenRouter] Timeout on attempt {attempt + 1}/{_MAX_RETRIES}. "
                    f"Retrying in {wait}s..."
                )
                await asyncio.sleep(wait)
                last_err = e

    raise last_err or Exception("OpenRouter: all retries exhausted")


async def parse_intent(message_text: str) -> dict:
    """
    Parses a raw WhatsApp message into structured intent.

    Returns one of:
      {"intent": "ingredient_safety_inquiry", "ingredient_name": "Lo Han Guo"}
      {"intent": "ingredient_info_inquiry",   "ingredient_name": "Ginseng"}
      {"intent": "general_tcm_chat",          "ingredient_name": null}

    Safety intents are always DB-grounded.
    Info intents use LLM with DB context.
    General chat uses LLM with short answer + TCM redirect.
    """
    prompt = (
        "You are an AI classifier for a Traditional Chinese Medicine (TCM) safety app.\n"
        "Classify the user's message into EXACTLY one of three intents:\n\n"
        "1. ingredient_safety_inquiry — asking whether an ingredient/brand/product is safe, toxic, dangerous, "
        "has side effects, is contraindicated, or suitable for a health condition.\n"
        "   Example: 'apakah ginseng berbahaya?', 'lo han guo aman tidak?', 'pien tze huang untuk ibu hamil?'\n\n"
        "2. ingredient_info_inquiry — asking what an ingredient is, its benefits, uses, history, or how it works "
        "(but NOT specifically about its safety/toxicity).\n"
        "   Example: 'apa itu ginseng?', 'lo han guo untuk apa?', 'apa manfaat jahe merah?'\n\n"
        "3. general_tcm_chat — greetings, general health questions, off-topic, or anything not covered above.\n"
        "   Example: 'halo!', 'buah apa yang sehat?', 'okay', 'terima kasih'\n\n"
        "Respond ONLY with valid JSON, no markdown, no explanation:\n"
        '  {"intent": "ingredient_safety_inquiry", "ingredient_name": "NAME"}\n'
        '  {"intent": "ingredient_info_inquiry",   "ingredient_name": "NAME"}\n'
        '  {"intent": "general_tcm_chat",          "ingredient_name": null}\n\n'
        f"User message: {message_text}"
    )

    try:
        text = await _chat(prompt, temperature=0.0, timeout=12.0)
        # Strip markdown fences if model wraps JSON
        text = text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        result = json.loads(text)
        # Validate structure
        if "intent" not in result:
            raise ValueError("Missing 'intent' key")
        return result
    except (json.JSONDecodeError, ValueError) as e:
        print(f"[OpenRouter] parse_intent: bad reply ({e}): {locals().get('text', '')!r:.200}")
        return {"intent": "general_tcm_chat", "ingredient_name": None}
    except Exception as e:
        print(f"[OpenRouter] parse_intent error: {e}")
        return {"intent": "general_tcm_chat", "ingredient_name": None}


async def generate_chat_reply(message_text: str) -> str:
    """
    Generates a short conversational reply for general/health questions.

    Strategy:
    - Answer general health/lifestyle questions BRIEFLY (2-3 sentences max)
    - Always end by steering the user toward TCM product/ingredient questions
    - Never diagnose or prescribe for specific medical conditions
    """
    prompt = (
        "You are FitMate, a friendly assistant for a Traditional Chinese Medicine (TCM) safety app.\n"
        "The user sent a general message or general health question.\n\n"
        "Rules:\n"
        "- Reply in the SAME language the user used (Indonesian or English)\n"
        "- Keep your answer SHORT — max 2-3 sentences\n"
        "- You CAN answer general health/nutrition/lifestyle questions briefly\n"
        "- You CANNOT diagnose diseases or prescribe treatments for specific conditions\n"
        "- At the end of EVERY reply, add ONE short question to guide the user toward TCM:\n"
        "  Indonesian: 'Ada produk TCM atau herbal yang ingin kamu cek keamanannya? 🌿'\n"
        "  English: 'Is there a TCM product or herb you'd like me to check for you? 🌿'\n"
        "  (Match language to user's language)\n\n"
        f"User: {message_text}\n"
        "FitMate:"
    )

    try:
        return (await _chat(prompt, temperature=0.5, timeout=15.0)).strip()
    except Exception as e:
        print(f"[OpenRouter] generate_chat_reply error: {e}")
        return (
            "Halo! Saya FitMate, asisten keamanan produk TCM Anda. 😊\n"
            "Ada produk TCM atau herbal yang ingin kamu cek keamanannya? 🌿"
        )


async def generate_ingredient_info_reply(ingredient_name: str, db_match: dict | None) -> str:
    """
    Generates an informational reply about a TCM ingredient.
    Uses DB data as grounding context if available.
    LLM can explain benefits/uses/history; safety verdict comes from DB only.
    """
    if db_match:
        db_context = (
            f"Database entry found:\n"
            f"- Indonesian name: {db_match.get('indonesian_name', '-')}\n"
            f"- Mandarin: {db_match.get('mandarin_name', '-')}\n"
            f"- Latin: {db_match.get('latin_name', '-')}\n"
            f"- Description: {db_match.get('description', 'Not available')}\n"
            f"- Safety status: {'⚠️ Flagged — see safety notes' if db_match.get('is_toxic') else '✅ Generally safe per our database'}\n"
        )
    else:
        db_context = "This ingredient was not found in our database — provide general TCM knowledge only."

    prompt = (
        "You are FitMate, a knowledgeable TCM assistant. The user asked about a TCM ingredient.\n"
        "Use the database context below to ground your answer. Do NOT fabricate safety/toxicity claims.\n\n"
        f"Ingredient: {ingredient_name}\n"
        f"{db_context}\n\n"
        "Instructions:\n"
        "- Reply in Indonesian\n"
        "- Explain what this ingredient is, its traditional uses, and general benefits in 3-4 sentences\n"
        "- If safety data is available in the database, mention it briefly\n"
        "- End with: 'Ingin tahu apakah bahan ini aman untuk kondisi kesehatanmu? Kirimkan nama produk TCM-nya! 🌿'\n"
        "- Keep total reply under 150 words\n"
    )

    try:
        return (await _chat(prompt, temperature=0.4, timeout=15.0)).strip()
    except Exception as e:
        print(f"[OpenRouter] generate_ingredient_info_reply error: {e}")
        name = db_match.get("indonesian_name", ingredient_name) if db_match else ingredient_name
        return (
            f"Maaf, saya tidak dapat memuat informasi lengkap tentang *{name}* saat ini.\n"
            "Ingin tahu apakah bahan ini aman? Kirimkan nama produk TCM-nya! 🌿"
        )
