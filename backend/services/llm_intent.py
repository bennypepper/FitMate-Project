"""
LLM Intent Parser & Chat Reply Generator via OpenRouter API.
Uses google/gemini-2.5-flash-lite for fast response and medical inference.

Intent classes
--------------
  ingredient_safety_inquiry  — user asking if ingredient/brand is safe/toxic/contraindicated
                              → DB verdict is ALWAYS rule-based; LLM only writes the reply language
  ingredient_info_inquiry    — user asking what an ingredient is, benefits, uses
                              → LLM answers using DB context if available
  general_tcm_chat           — greetings, general health/TCM questions, off-topic
                              → LLM answers, explains bot capabilities if first interaction

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
        "   Also classify here if user types JUST an ingredient name (like 'lo han guo') with no question.\n"
        "   Example: 'apakah ginseng berbahaya?', 'lo han guo aman tidak?', 'bahan tadi aman?', 'lo han guo'\n\n"
        "2. ingredient_info_inquiry — asking what an ingredient is, its benefits, uses, history "
        "(NOT specifically about safety/toxicity).\n"
        "   Example: 'apa itu ginseng?', 'lo han guo untuk apa?', 'apa manfaat jahe merah?'\n\n"
        "3. general_tcm_chat — greetings, general health questions, statements, off-topic, "
        "or messages that do NOT mention a specific ingredient name.\n"
        "   Example: 'halo!', 'buah apa yang sehat?', 'okay', 'terima kasih'\n\n"
        "IMPORTANT: If the user refers to 'bahan itu', 'yang tadi', or similar vague references, "
        "extract the actual ingredient name from the context above.\n\n"
        "IMPORTANT: A message with a COMMA-SEPARATED LIST of ingredients (e.g. 'lo han guo, akar manis, jahe') "
        "should be classified as ingredient_safety_inquiry. Set ingredient_name to the full list as one string.\n\n"
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


async def generate_safety_reply(
    ingredient_name: str,
    db_match: dict | None,
    safety_verdict: str,
    user_message: str,
    history: list[dict] | None = None,
) -> str:
    """
    Generates a human, empathetic safety reply grounded in the DB verdict.

    CRITICAL: safety_verdict is determined purely by rule-based code (never LLM).
    The LLM only writes the surrounding language — it CANNOT change the verdict.

    Parameters:
        ingredient_name  — ingredient queried
        db_match         — full DB document (may be None)
        safety_verdict   — "safe" | "toxic" | "not_found"  (set by caller, not LLM)
        user_message     — raw user text (may contain health conditions)
        history          — conversation history for multi-turn context
    """
    # Build DB context block
    if db_match:
        db_context = (
            f"Indonesian name: {db_match.get('indonesian_name', ingredient_name)}\n"
            f"Mandarin: {db_match.get('mandarin_name', '-')}\n"
            f"Latin: {db_match.get('latin_name', '-')}\n"
            f"Description: {db_match.get('description', 'Tidak tersedia')}\n"
        )
        if db_match.get("is_toxic"):
            db_context += (
                f"Toxicity level: {db_match.get('toxicity_level', 'tidak diketahui')}\n"
                f"Target organ: {db_match.get('target_organ', 'tidak diketahui')}\n"
                f"Contraindications: {db_match.get('contraindications', 'tidak ada data')}\n"
            )
        else:
            db_context += f"Contraindications: {db_match.get('contraindications', 'tidak ada data khusus')}\n"
    else:
        db_context = "Bahan ini tidak ditemukan dalam database kami."

    # Verdict instruction — the LLM MUST reproduce this verdict faithfully
    verdict_instructions = {
        "safe": (
            "Verdict dari database: AMAN (safe). "
            "Sampaikan bahwa bahan ini tergolong aman berdasarkan database kami. "
            "Jika user menyebut kondisi kesehatan (diabetes, hamil, hipertensi, dll.), "
            "akui kondisi tersebut dan jelaskan bahwa meskipun aman secara umum, "
            "tetap perlu berkonsultasi dengan dokter/apoteker mengingat kondisi spesifik mereka."
        ),
        "toxic": (
            "Verdict dari database: BERBAHAYA / TOKSIK. "
            "Sampaikan dengan tegas bahwa bahan ini dikategorikan berbahaya atau toksik "
            "berdasarkan database kami. Jika user menyebut kondisi kesehatan, "
            "tekankan bahwa risikonya lebih besar untuk kondisi tersebut."
        ),
        "not_found": (
            "Verdict dari database: TIDAK DITEMUKAN. "
            "Sampaikan bahwa bahan ini tidak ada dalam database kami sehingga kami tidak bisa "
            "memberikan penilaian keamanan yang terverifikasi. "
            "Sarankan untuk mencoba nama lain (Indonesia, Mandarin, atau Latin)."
        ),
    }.get(safety_verdict, "Verdict tidak diketahui.")

    system = (
        "Kamu adalah FitMate, asisten keamanan produk TCM yang ramah dan empatik.\n\n"
        f"=== DATA DARI DATABASE ===\n{db_context}\n"
        f"=== INSTRUKSI VERDICT ===\n{verdict_instructions}\n\n"
        "=== INSTRUKSI PENULISAN REPLY ===\n"
        "- Balas dalam bahasa Indonesia yang hangat dan empatik\n"
        "- WAJIB sebutkan kondisi kesehatan yang disebutkan user (diabetes, hamil, hipertensi, dll.) "
        "jika ada — jangan abaikan kondisi ini\n"
        "- Sampaikan verdict keamanan dengan jelas berdasarkan data DB di atas\n"
        "- Jika bahan AMAN tapi user punya kondisi khusus: tetap sarankan konsultasi dokter\n"
        "- Jika bahan TOKSIK: tegas namun tetap sopan, dorong konsultasi segera\n"
        "- Jangan fabrikasi klaim keamanan di luar data DB yang diberikan\n"
        "- Panjang reply: 4–6 kalimat, tidak lebih\n"
        "- JANGAN tulis ulang disclaimer — itu akan ditambahkan secara terpisah\n"
        "- Akhiri dengan: 'Ada bahan TCM lain yang ingin dicek? Ketik saja namanya! 🌿'\n"
        f"\nPesan user: {user_message}"
    )

    messages: list[dict] = [{"role": "system", "content": system}]
    if history:
        # Only last 6 messages for context, not to bloat the prompt
        messages.extend(history[-6:])
    messages.append({"role": "user", "content": user_message})

    try:
        return (await _chat(messages, temperature=0.4, timeout=15.0)).strip()
    except Exception as e:
        print(f"[OpenRouter] generate_safety_reply error: {e}")
        # Fallback to simple template if LLM fails
        if safety_verdict == "toxic":
            name = db_match.get("indonesian_name", ingredient_name) if db_match else ingredient_name
            return (
                f"⚠️ *{name}* dikategorikan berbahaya/toksik berdasarkan database kami.\n"
                "Segera konsultasikan dengan dokter atau apoteker. 🏥"
            )
        elif safety_verdict == "safe":
            name = db_match.get("indonesian_name", ingredient_name) if db_match else ingredient_name
            return (
                f"✅ *{name}* tergolong aman berdasarkan database kami.\n"
                "Tetap konsultasikan dengan dokter untuk kondisi spesifikmu. "
                "Ada bahan lain yang ingin dicek? 🌿"
            )
        else:
            return (
                f"❓ Bahan *{ingredient_name}* tidak ditemukan dalam database kami.\n"
                "Coba ketik nama dalam bahasa Indonesia, Mandarin, atau Pinyin. "
                "Ada bahan lain yang ingin dicek? 🌿"
            )


async def generate_chat_reply(message_text: str, history: list[dict] | None = None) -> str:
    """
    Generates a conversational reply for general/health questions.
    Passes full conversation history for multi-turn coherence.

    For first-time users (empty history), can explain bot capabilities.
    Always steers the user toward TCM ingredient questions.
    """
    is_first_message = not history

    system = (
        "Kamu adalah FitMate, asisten keamanan produk TCM yang ramah dan membantu. "
        "FitMate bisa digunakan langsung via WhatsApp — user tidak perlu membuka aplikasi web.\n\n"
        "Kemampuan FitMate:\n"
        "• Cek keamanan bahan herbal/TCM\n"
        "• Menjawab apakah suatu bahan aman untuk kondisi kesehatan tertentu\n"
        "• Memberikan info/manfaat umum bahan TCM\n\n"
        "Aturan:\n"
        "- Balas dalam bahasa yang sama dengan user (Indonesia atau Inggris)\n"
        "- Jika user menyebut kondisi kesehatan (diabetes, hamil, dll.), AKUI kondisi itu dalam balasanmu\n"
        "- Kamu BOLEH menjawab pertanyaan kesehatan/nutrisi umum secara singkat\n"
        "- Kamu TIDAK BISA mendiagnosis penyakit atau meresepkan obat\n"
        "- Panjang reply: 3–5 kalimat (lebih panjang jika user punya pertanyaan kompleks atau kondisi kesehatan)\n"
    )
    if is_first_message:
        system += (
            "- Ini adalah pesan PERTAMA user — perkenalkan dirimu singkat dan jelaskan apa yang bisa kamu bantu\n"
        )
    system += (
        "- Di akhir reply, tanyakan apakah ada bahan TCM yang ingin dicek:\n"
        "  Indonesia: 'Ada bahan TCM atau produk herbal yang ingin kamu cek keamanannya? 🌿'\n"
        "  Inggris: 'Is there a TCM ingredient or herbal product you\\'d like me to check? 🌿'\n"
        "  (gunakan bahasa yang sama dengan balasanmu)"
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
            "Halo! Saya FitMate 😊 Saya bisa membantu mengecek keamanan bahan-bahan TCM.\n"
            "Ada bahan TCM atau produk herbal yang ingin kamu cek keamanannya? 🌿"
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
        "Kamu adalah FitMate, asisten TCM yang berpengetahuan. "
        "Gunakan konteks database untuk menjawab. Jangan fabrikasi klaim keamanan/toksisitas.\n\n"
        f"Bahan: {ingredient_name}\n"
        f"{db_context}\n\n"
        "Instruksi:\n"
        "- Balas dalam bahasa Indonesia\n"
        "- Jelaskan apa bahan ini, kegunaannya, dan manfaat umum dalam 3–4 kalimat\n"
        "- Jika ada data keamanan dari DB, sebutkan secara singkat\n"
        "- Akhiri dengan: 'Ingin tahu apakah bahan ini aman untuk kondisimu? "
        "Ketik saja: \"apakah [nama bahan] aman untuk [kondisimu]?\" 🌿'\n"
        "- Maksimal 180 kata"
    )

    messages: list[dict] = [{"role": "system", "content": system}]
    if history:
        messages.extend(history[-6:])
    messages.append({"role": "user", "content": f"Ceritakan tentang {ingredient_name}"})

    try:
        return (await _chat(messages, temperature=0.4, timeout=15.0)).strip()
    except Exception as e:
        print(f"[OpenRouter] generate_ingredient_info_reply error: {e}")
        name = db_match.get("indonesian_name", ingredient_name) if db_match else ingredient_name
        return (
            f"Maaf, saya tidak dapat memuat info lengkap tentang *{name}* saat ini.\n"
            "Ingin cek keamanannya? Ketik: \"apakah [nama bahan] aman?\" 🌿"
        )
