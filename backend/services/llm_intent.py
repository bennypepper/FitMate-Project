"""
LLM Intent Parser & Chat Reply Generator via OpenRouter API.
Uses google/gemini-2.5-flash-lite for fast, natural responses.

Intent classes
--------------
  ingredient_safety_inquiry  — user asking if ingredient/brand is safe/toxic/contraindicated
                              → DB verdict is ALWAYS rule-based; LLM writes the reply language only
  ingredient_info_inquiry    — user asking what an ingredient is, benefits, uses
                              → LLM answers using DB context if available
  general_tcm_chat           — greetings, general health/TCM questions, off-topic
                              → LLM answers helpfully and naturally; steers to TCM when relevant

Conversation history is passed to all chat functions so the LLM can resolve
references like "bahan itu", "yang tadi", "apakah aman?", etc.
"""
import json
import asyncio
import httpx
from core.config import settings

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

if not settings.OPENROUTER_CHATBOT_API_KEY:
    raise RuntimeError(
        "OPENROUTER_CHATBOT_API_KEY is not set in .env. "
        "Add it to backend/.env and restart the server."
    )

_HEADERS = {
    "Authorization": f"Bearer {settings.OPENROUTER_CHATBOT_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://fitmate-tcm.vercel.app",
    "X-Title": "FitMate TCM Safety Scanner",
}

# 2 retries × 2s/4s delays = ≤8s max — fits within Twilio webhook window
_MAX_RETRIES = 2
_RETRY_BASE_DELAY = 2  # seconds


async def _chat(
    messages: list[dict],
    temperature: float = 0.4,
    timeout: float = 15.0,
    model: str | None = None,
) -> str:
    """
    Calls OpenRouter /chat/completions with a messages array (supports multi-turn).
    Each message: {"role": "user"|"assistant"|"system", "content": "..."}
    Retries on 429 / 5xx with exponential backoff.
    """
    payload = {
        "model": model or settings.OPENROUTER_CHATBOT_MODEL,
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


async def parse_intent(message_text: str, history: list[dict] | None = None, model: str | None = None) -> dict:
    """
    Parses a raw WhatsApp message into structured intent.
    The LLM also normalizes/translates foreign ingredient names to Indonesian/English/Pinyin.

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
        "You are an AI classifier for a TCM (Traditional Chinese Medicine) safety app.\n"
        "Classify the user's message into EXACTLY one of three intents.\n"
        "Use the conversation context below to resolve vague references.\n\n"

        "1. ingredient_safety_inquiry — user wants to know if an ingredient/product is safe, dangerous,\n"
        "   has side effects, is contraindicated, OK for a health condition, or OK to drink/consume.\n"
        "   Also classify here if user just types a bare ingredient name with no question.\n"
        "   Examples: 'apakah ginseng berbahaya?', 'lo han guo aman?', 'bahan tadi aman?', "
        "'lo han guo', 'saya ingin beli X apa aman'\n\n"

        "2. ingredient_info_inquiry — user wants to know WHAT an ingredient is, its benefits,\n"
        "   uses, or history (not primarily about safety).\n"
        "   Examples: 'apa itu ginseng?', 'lo han guo untuk apa?', 'manfaat jahe merah?'\n\n"

        "3. general_tcm_chat — greetings, general health questions, off-topic, statements,\n"
        "   or messages that cannot be mapped to a specific ingredient.\n"
        "   Examples: 'halo', 'buah apa yang sehat?', 'makasih', 'oke'\n\n"

        "INGREDIENT NAME RULES:\n"
        "- Extract the ingredient name from the user's message\n"
        "- If the name is in a foreign language (German, Dutch, Japanese, Latin, etc.), "
        "TRANSLATE or NORMALIZE it to its most common Indonesian, English, or Pinyin name\n"
        "  Example: 'Sibirischer Ginseng' → 'Siberian Ginseng' or 'Jahe Siber'\n"
        "  Example: 'Kamille' (German) → 'Chamomile' or 'Kamomil'\n"
        "- If the user references a previous ingredient vaguely ('bahan itu', 'tadi'), "
        "extract the actual name from context\n"
        "- If the user sends a comma-separated LIST of ingredient names "
        "(e.g. 'lo han guo, akar manis, jahe'), set ingredient_name to the full list as-is\n\n"

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
            model=model,
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
    model: str | None = None,
) -> str:
    """
    Generates a warm, empathetic safety reply grounded in the DB verdict.

    CRITICAL: safety_verdict is determined purely by rule-based code (never LLM).
    The LLM writes the surrounding language — it CANNOT change the verdict.

    Parameters:
        ingredient_name  — ingredient queried (already normalized)
        db_match         — full DB document (may be None)
        safety_verdict   — "safe" | "toxic" | "not_found"  (set by caller, not LLM)
        user_message     — raw user text (may contain health conditions)
        history          — conversation history for multi-turn context
    """
    # Build DB context block
    if db_match:
        db_context = (
            f"Nama Indonesia: {db_match.get('indonesian_name', ingredient_name)}\n"
            f"Nama Mandarin: {db_match.get('mandarin_name', '-')}\n"
            f"Nama Latin: {db_match.get('latin_name', '-')}\n"
            f"Deskripsi: {db_match.get('description', 'Tidak tersedia')}\n"
            f"Kontraindikasi: {db_match.get('contraindications', 'Tidak ada data khusus')}\n"
        )
        if db_match.get("is_toxic"):
            db_context += (
                f"Level toksisitas: {db_match.get('toxicity_level', 'tidak diketahui')}\n"
                f"Organ target: {db_match.get('target_organ', 'tidak diketahui')}\n"
            )
    else:
        db_context = "Bahan tidak ditemukan dalam database kami."

    # Verdict instruction — LLM MUST deliver this verdict faithfully
    verdict_instructions = {
        "safe": (
            "VERDICT: AMAN. Bahan ini tergolong aman berdasarkan database kami. "
            "Sampaikan ini dengan jelas. "
            "Jika user menyebut kondisi kesehatan spesifik (diabetes, hamil, hipertensi, "
            "gagal ginjal, dll.) — WAJIB sebutkan kondisi itu dan sarankan tetap konsultasi dokter "
            "karena kondisi spesifik memerlukan penilaian personal."
        ),
        "toxic": (
            "VERDICT: BERBAHAYA/TOKSIK. Sampaikan dengan tegas tapi sopan. "
            "Jika user menyebut kondisi kesehatan, tekankan risikonya lebih besar untuk kondisi itu. "
            "Sarankan konsultasi dokter/apoteker segera."
        ),
        "not_found": (
            "VERDICT: TIDAK ADA DI DATABASE. Kamu DILARANG berspekulasi tentang keamanan atau "
            "bahaya bahan ini karena tidak ada data terverifikasi. "
            "Jangan membuat klaim keamanan berdasarkan pengetahuan umum — ini aplikasi medis. "
            "Sampaikan bahwa kita tidak bisa memberi penilaian, dan sarankan user konsultasi apoteker "
            "atau dokter, serta coba ketik nama bahan dengan ejaan berbeda (Indonesia/Mandarin/Pinyin)."
        ),
    }.get(safety_verdict, "Verdict tidak diketahui.")

    # Hard rule: block LLM from normalizing pharmaceutical drugs in herbal context.
    # This is a backstop — the interceptor should catch most BKO cases first,
    # but this rule prevents the LLM from softening a verdict on its own.
    BKO_HARD_RULE = (
        "=== ATURAN MUTLAK — BKO (BAHAN KIMIA OBAT) ===\n"
        "Jika nama bahan mengandung obat farmasi keras (steroid, PDE5 inhibitor, NSAID, "
        "antidiabetik, sedatif, diuretik, anabolik steroid, atau obat penurun berat badan), "
        "dan konteksnya adalah produk herbal/TCM:\n"
        "- JANGAN menyebutkan khasiat medisnya seolah itu wajar\n"
        "- JANGAN menyatakan 'aman dengan resep dokter' dalam konteks herbal\n"
        "- WAJIB: nyatakan ini sebagai BKO ilegal dalam produk herbal, berbahaya, dan minta user berhenti konsumsi\n"
        "- Aturan ini tidak bisa di-override oleh verdict database manapun.\n\n"
    )

    system = (
        "Kamu adalah FitMate, asisten TCM yang ramah, hangat, dan berpengetahuan. "
        "Kamu berbicara seperti teman yang paham kesehatan — bukan robot kaku.\n\n"
        f"=== DATA DATABASE ===\n{db_context}\n\n"
        + BKO_HARD_RULE
        + f"=== INSTRUKSI VERDICT (JANGAN UBAH INI) ===\n{verdict_instructions}\n\n"
        "=== CARA MEMBALAS ===\n"
        "- Balas dalam bahasa Indonesia yang natural dan hangat, gunakan 'kamu'\n"
        "- WAJIB akui kondisi kesehatan yang user sebutkan, jangan abaikan\n"
        "- Sampaikan verdict dengan jelas tapi tidak kaku\n"
        "- Boleh tambah info berguna dari DB seperti kontraindikasi, tapi jangan berlebihan\n"
        "- Panjang: 3–5 kalimat, cukup informatif tapi tidak overwhelming\n"
        "- Tutup dengan pertanyaan natural, tidak harus selalu sama — variasikan\n"
        "- JANGAN tulis disclaimer — itu sudah ditambahkan secara terpisah\n"
        f"\nPesan user: {user_message}"
    )

    messages: list[dict] = [{"role": "system", "content": system}]
    if history:
        messages.extend(history[-6:])
    messages.append({"role": "user", "content": user_message})

    try:
        return (await _chat(messages, temperature=0.5, timeout=15.0, model=model)).strip()
    except Exception as e:
        print(f"[OpenRouter] generate_safety_reply error: {e}")
        # Simple fallback
        if safety_verdict == "toxic":
            name = db_match.get("indonesian_name", ingredient_name) if db_match else ingredient_name
            return (
                f"⚠️ *{name}* dikategorikan berbahaya berdasarkan database kami. "
                "Tolong konsultasikan dengan dokter atau apoteker sebelum mengonsumsi ya. 🏥"
            )
        elif safety_verdict == "safe":
            name = db_match.get("indonesian_name", ingredient_name) if db_match else ingredient_name
            return (
                f"✅ *{name}* tergolong aman berdasarkan database kami. "
                "Tetap konsultasi dengan dokter untuk kondisi kesehatanmu ya. "
                "Ada bahan lain yang ingin dicek? 🌿"
            )
        else:
            return (
                f"Hmm, bahan *{ingredient_name}* belum ada di database kami. "
                "Coba ketik dengan nama Indonesia, Mandarin, atau Pinyin-nya — "
                "mungkin ada di sana. 🌿"
            )


async def generate_chat_reply(message_text: str, history: list[dict] | None = None, model: str | None = None) -> str:
    """
    Generates a warm, helpful conversational reply.
    Acknowledges health conditions. Steers toward TCM naturally, not robotically.
    """
    system = (
        "Kamu adalah FitMate, asisten TCM yang ramah dan helpful — bukan bot kaku. "
        "Kamu bisa diakses langsung via WhatsApp tanpa perlu buka aplikasi apapun.\n\n"
        "Kemampuan kamu:\n"
        "• Cek keamanan bahan herbal/TCM dari database tervalidasi\n"
        "• Menjawab apakah suatu bahan aman untuk kondisi kesehatan tertentu\n"
        "• Memberikan info/manfaat umum tentang bahan TCM\n\n"
        "Cara bicara:\n"
        "- Gunakan bahasa Indonesia yang natural dan hangat, pakai 'kamu'\n"
        "- Jika user menyebut kondisi kesehatan (diabetes, hamil, hipertensi, dll.), "
        "AKUI kondisi itu dengan empati sebelum menjawab\n"
        "- Untuk pertanyaan kesehatan/nutrisi umum: boleh jawab SINGKAT (1-2 kalimat), "
        "lalu arahkan ke topik TCM/herbal yang relevan\n"
        "- Tidak bisa mendiagnosis atau meresepkan obat\n"
        "- Panjang: 2–3 kalimat, natural dan tidak berlebihan\n"
        "- Kalau relevan, tawarkan untuk cek bahan TCM spesifik — tapi jangan paksa kalau tidak relevan\n"
        "- Jangan akhiri setiap pesan dengan CTA yang persis sama — buat natural\n\n"
        "BATAS TOPIK KETAT:\n"
        "Jika pesan sama sekali tidak berhubungan dengan kesehatan, herbal, TCM, obat, "
        "nutrisi, atau kondisi medis (contoh: investasi, teknologi, olahraga non-kesehatan, "
        "hiburan, berita, dll.) — TOLAK dengan sopan dan kembalikan ke topik TCM. "
        "JANGAN jawab pertanyaan di luar cakupan, bahkan sebagian kecil sekalipun."
    )

    messages: list[dict] = [{"role": "system", "content": system}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": message_text})

    try:
        return (await _chat(messages, temperature=0.6, timeout=15.0, model=model)).strip()
    except Exception as e:
        print(f"[OpenRouter] generate_chat_reply error: {e}")
        return (
            "Hai! Saya FitMate 😊 Bisa bantu cek keamanan bahan herbal atau TCM yang ingin kamu ketahui. "
            "Ketik saja nama bahannya! 🌿"
        )


async def generate_ingredient_info_reply(
    ingredient_name: str,
    db_match: dict | None,
    history: list[dict] | None = None,
    model: str | None = None,
) -> str:
    """
    Generates an informational reply about a TCM ingredient.
    Uses DB data as grounding context if available.
    """
    if db_match:
        db_context = (
            f"Nama Indonesia: {db_match.get('indonesian_name', '-')}\n"
            f"Nama Mandarin: {db_match.get('mandarin_name', '-')}\n"
            f"Nama Latin: {db_match.get('latin_name', '-')}\n"
            f"Deskripsi: {db_match.get('description', 'Tidak tersedia')}\n"
            f"Status keamanan: {'⚠️ Terindikasi berbahaya' if db_match.get('is_toxic') else '✅ Umumnya aman'}\n"
            f"Kontraindikasi: {db_match.get('contraindications', 'Tidak ada data khusus')}\n"
        )
    else:
        db_context = "Bahan ini tidak ada di database kami — gunakan pengetahuan umum TCM, tapi jangan fabrikasi klaim keamanan/toksisitas."

    system = (
        "Kamu adalah FitMate, teman yang paham tentang bahan-bahan TCM. "
        "Berikan informasi yang berguna dan mudah dipahami.\n\n"
        f"Bahan: {ingredient_name}\n"
        f"{db_context}\n\n"
        "Cara menjawab:\n"
        "- Pakai bahasa Indonesia yang natural, gunakan 'kamu'\n"
        "- Jelaskan apa bahan ini, kegunaannya, dan manfaat umum\n"
        "- Kalau ada data keamanan dari DB, sebutkan\n"
        "- Kalau tidak ada di DB, boleh kasih info umum tapi jangan klaim soal keamanan/bahaya\n"
        "- Panjang: 3–4 kalimat, informatif tapi ringkas\n"
        "- Tutup dengan tawarkan untuk cek keamanannya kalau mereka mau"
    )

    messages: list[dict] = [{"role": "system", "content": system}]
    if history:
        messages.extend(history[-6:])
    messages.append({"role": "user", "content": f"Ceritakan tentang {ingredient_name}"})

    try:
        return (await _chat(messages, temperature=0.5, timeout=15.0, model=model)).strip()
    except Exception as e:
        print(f"[OpenRouter] generate_ingredient_info_reply error: {e}")
        name = db_match.get("indonesian_name", ingredient_name) if db_match else ingredient_name
        return (
            f"Maaf, saya tidak bisa memuat info tentang *{name}* saat ini. "
            "Coba tanya lagi ya! 🌿"
        )
