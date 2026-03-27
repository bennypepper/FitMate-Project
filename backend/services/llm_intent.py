"""
LLM Intent Parser & Chat Reply Generator via OpenRouter API.
Uses google/gemini-2.5-flash-lite for fast response and medical inference.

Intent classes
--------------
  ingredient_safety_inquiry  — user asking if ingredient/brand is safe/toxic/contraindicated
                              → ALWAYS DB-grounded; LLM never fabricates a safety verdict
  ingredient_info_inquiry    — user asking what an ingredient is, benefits, uses
                              → LLM answers using DB context if available
  general_tcm_chat           — greetings, general health/TCM questions, off-topic
                              → LLM answers shortly, then redirects to TCM context

Conversation history is passed to all chat functions so the LLM can resolve
references like "bahan itu", "yang tadi", "apakah aman?", etc.
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

# 2 retries × 2s/4s delays = ≤8s max — fits within Twilio webhook window
_MAX_RETRIES = 2
_RETRY_BASE_DELAY = 2  # seconds


async def _chat(
    messages: list[dict],
    temperature: float = 0.3,
    timeout: float = 15.0,
) -> str:
    """
    Calls OpenRouter /chat/completions with a messages array (supports multi-turn).
    Each message: {"role": "user"|"assistant"|"system", "content": "..."}
    Retries on 429 / 5xx with exponential backoff.
    """
    payload = {
        "model": settings.OPENROUTER_MODEL,
        "messages": messages,
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


def _build_context_snippet(history: list[dict], n_user_bubbles: int = 5) -> str:
    """
    Returns the last N user messages from history as a plain-text context snippet.
    Used to help intent parsing understand references like 'bahan itu', 'tadi', etc.
    """
    if not history:
        return ""
    user_msgs = [m["content"] for m in history if m["role"] == "user"]
    recent = user_msgs[-n_user_bubbles:]
    if not recent:
        return ""
    return "\n".join(f"- {m}" for m in recent)


async def parse_intent(message_text: str, history: list[dict] | None = None) -> dict:
    """
    Parses a raw WhatsApp message into structured intent.
    Passes recent conversation context so references ('bahan itu', 'yang tadi') are resolved.

    Returns one of:
      {"intent": "ingredient_safety_inquiry", "ingredient_name": "Lo Han Guo"}
      {"intent": "ingredient_info_inquiry",   "ingredient_name": "Ginseng"}
      {"intent": "general_tcm_chat",          "ingredient_name": null}
    """
    context_block = ""
    if history:
        snippet = _build_context_snippet(history, n_user_bubbles=5)
        if snippet:
            context_block = (
                "\n\nRecent conversation context (use this to resolve references like "
                "'bahan itu', 'tadi', 'yang disebutkan'):\n"
                + snippet
                + "\n"
            )

    prompt = (
        "You are an AI classifier for a Traditional Chinese Medicine (TCM) safety app.\n"
        "Classify the user's message into EXACTLY one of three intents.\n"
        "Use the conversation context below to resolve vague references like 'bahan itu', "
        "'yang tadi', 'itu', etc.\n\n"
        "1. ingredient_safety_inquiry — asking whether an ingredient/brand/product is safe, toxic, "
        "dangerous, has side effects, is contraindicated, or suitable for a health condition.\n"
        "   Example: 'apakah ginseng berbahaya?', 'lo han guo aman tidak?', 'bahan tadi aman?'\n\n"
        "2. ingredient_info_inquiry — asking what an ingredient is, its benefits, uses, history "
        "(NOT specifically about safety/toxicity).\n"
        "   Example: 'apa itu ginseng?', 'lo han guo untuk apa?', 'apa manfaat jahe merah?'\n\n"
        "3. general_tcm_chat — greetings, general health questions, statements, off-topic.\n"
        "   Example: 'halo!', 'buah apa yang sehat?', 'okay', 'terima kasih'\n\n"
        "IMPORTANT: If the user refers to 'bahan itu', 'yang tadi', or similar vague references, "
        "extract the actual ingredient name from the context above.\n\n"
        "Respond ONLY with valid JSON, no markdown, no explanation:\n"
        '  {"intent": "ingredient_safety_inquiry", "ingredient_name": "NAME"}\n'
        '  {"intent": "ingredient_info_inquiry",   "ingredient_name": "NAME"}\n'
        '  {"intent": "general_tcm_chat",          "ingredient_name": null}\n'
        + context_block
        + f"\nUser message: {message_text}"
    )

    try:
        result_text = await _chat(
            [{"role": "user", "content": prompt}],
            temperature=0.0,
            timeout=12.0,
        )
        result_text = result_text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        result = json.loads(result_text)
        if "intent" not in result:
            raise ValueError("Missing 'intent' key")
        return result
    except (json.JSONDecodeError, ValueError) as e:
        print(f"[OpenRouter] parse_intent: bad reply ({e})")
        return {"intent": "general_tcm_chat", "ingredient_name": None}
    except Exception as e:
        print(f"[OpenRouter] parse_intent error: {e}")
        return {"intent": "general_tcm_chat", "ingredient_name": None}


async def generate_chat_reply(message_text: str, history: list[dict] | None = None) -> str:
    """
    Generates a short conversational reply for general/health questions.
    Passes full conversation history for multi-turn coherence.
    Always ends by steering the user toward TCM product/ingredient questions.
    """
    system = (
        "You are FitMate, a friendly assistant for a Traditional Chinese Medicine (TCM) safety app. "
        "Rules:\n"
        "- Reply in the SAME language the user used (Indonesian or English)\n"
        "- Keep your answer SHORT — max 2-3 sentences\n"
        "- You CAN answer general health/nutrition/lifestyle questions briefly\n"
        "- You CANNOT diagnose diseases or prescribe treatments for specific conditions\n"
        "- At the end of EVERY reply, ask ONE question to guide the user toward TCM:\n"
        "  Indonesian: 'Ada produk TCM atau herbal yang ingin kamu cek keamanannya? 🌿'\n"
        "  English: 'Is there a TCM product or herb you'd like me to check? 🌿'\n"
        "  (use the same language as the rest of your reply)"
    )

    messages: list[dict] = [{"role": "system", "content": system}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": message_text})

    try:
        return (await _chat(messages, temperature=0.5, timeout=15.0)).strip()
    except Exception as e:
        print(f"[OpenRouter] generate_chat_reply error: {e}")
        return (
            "Halo! Saya FitMate 😊 Ada produk TCM atau herbal yang ingin kamu cek keamanannya? 🌿"
        )


async def generate_ingredient_info_reply(
    ingredient_name: str,
    db_match: dict | None,
    history: list[dict] | None = None,
) -> str:
    """
    Generates an informational reply about a TCM ingredient.
    Uses DB data as grounding context if available.
    Passes conversation history for continuity.
    """
    if db_match:
        db_context = (
            f"Database entry found:\n"
            f"- Indonesian name: {db_match.get('indonesian_name', '-')}\n"
            f"- Mandarin: {db_match.get('mandarin_name', '-')}\n"
            f"- Latin: {db_match.get('latin_name', '-')}\n"
            f"- Description: {db_match.get('description', 'Not available')}\n"
            f"- Safety: {'⚠️ Flagged in our database' if db_match.get('is_toxic') else '✅ Generally safe per our database'}\n"
        )
    else:
        db_context = "This ingredient was not found in our database — provide general TCM knowledge only."

    system = (
        "You are FitMate, a knowledgeable TCM assistant. "
        "Use the database context to ground your answer. Do NOT fabricate safety/toxicity claims.\n\n"
        f"Ingredient: {ingredient_name}\n"
        f"{db_context}\n\n"
        "Instructions:\n"
        "- Reply in Indonesian\n"
        "- Explain what this ingredient is, uses, and general benefits in 3-4 sentences\n"
        "- If safety data exists in the DB, mention it briefly\n"
        "- End with: 'Ingin tahu apakah bahan ini aman untuk kondisimu? Kirimkan nama produk TCM-nya! 🌿'\n"
        "- Keep total reply under 150 words"
    )

    messages: list[dict] = [{"role": "system", "content": system}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": f"Ceritakan tentang {ingredient_name}"})

    try:
        return (await _chat(messages, temperature=0.4, timeout=15.0)).strip()
    except Exception as e:
        print(f"[OpenRouter] generate_ingredient_info_reply error: {e}")
        name = db_match.get("indonesian_name", ingredient_name) if db_match else ingredient_name
        return (
            f"Maaf, saya tidak dapat memuat info lengkap tentang *{name}* saat ini.\n"
            "Ingin cek keamanannya? Kirimkan nama produk TCM-nya! 🌿"
        )
