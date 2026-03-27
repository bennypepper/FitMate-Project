"""
WhatsApp webhook router (Twilio Sandbox).

Intent routing:
  ingredient_safety_inquiry  → strict DB lookup, no LLM for the verdict
  ingredient_info_inquiry    → DB lookup + LLM informational reply
  general_tcm_chat           → LLM short answer + redirect to TCM context

Conversation memory:
  - Per-phone history stored in TTLCache (expires 2h after last message)
  - Max 15 user bubbles (+ their bot replies) kept in context
  - Enables reference resolution: "bahan itu", "yang tadi", "apakah aman?"

Security:
  - Twilio webhook signature validation (X-Twilio-Signature header)
  - Per-phone rate limiting via TTLCache (20 messages per 10 minutes)
"""
import traceback
from fastapi import APIRouter, Request, BackgroundTasks, Form
from services.whatsapp_service import whatsapp_client
from cachetools import TTLCache
from core.config import settings

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

# Rate limit: max 20 messages per phone per 10 minutes (TTL=600s)
_rate_limit_cache: TTLCache = TTLCache(maxsize=1000, ttl=600)
RATE_LIMIT_MAX = 20

# Conversation history: expires after 2 hours of inactivity (TTL=7200s)
# Each value: list of {"role": "user"|"assistant", "content": str}
_conversation_store: TTLCache = TTLCache(maxsize=1000, ttl=7200)

# Max user bubbles kept in context (each "bubble" ≈ 1 paragraph)
MAX_HISTORY_USER_BUBBLES = 15

DISCLAIMER = "⚕️ *Disclaimer:* Informasi ini bukan pengganti saran medis profesional.\n\n"


def _validate_twilio_signature(request_url: str, params: dict, signature: str) -> bool:
    """Validates X-Twilio-Signature to prevent spoofed webhook calls."""
    try:
        from twilio.request_validator import RequestValidator
        validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
        return validator.validate(request_url, params, signature)
    except Exception as e:
        print(f"[Twilio] Signature validation error: {e}")
        return False


def _get_history(phone: str) -> list[dict]:
    """Returns the stored conversation history for a phone number."""
    return list(_conversation_store.get(phone, []))


def _append_history(phone: str, role: str, content: str) -> None:
    """
    Appends a message to conversation history for a phone number.
    Trims to MAX_HISTORY_USER_BUBBLES user bubbles (+ their paired bot replies).
    """
    history = _get_history(phone)
    history.append({"role": role, "content": content})

    # Trim: keep only the last MAX_HISTORY_USER_BUBBLES user messages and their paired replies
    user_indices = [i for i, m in enumerate(history) if m["role"] == "user"]
    if len(user_indices) > MAX_HISTORY_USER_BUBBLES:
        # Drop everything before the oldest bubble we want to keep
        cutoff = user_indices[-MAX_HISTORY_USER_BUBBLES]
        history = history[cutoff:]

    _conversation_store[phone] = history


@router.post("/webhook")
async def receive_message(
    request: Request,
    background_tasks: BackgroundTasks,
    Body: str = Form(default=""),
    From: str = Form(default=""),
    To: str = Form(default=""),
    MessageSid: str = Form(default=""),
):
    # ── Twilio signature validation ──────────────────────────────────────────
    twilio_signature = request.headers.get("X-Twilio-Signature", "")
    form_data = await request.form()
    params = dict(form_data)

    scheme = request.headers.get("X-Forwarded-Proto", request.url.scheme)
    host = request.headers.get("X-Forwarded-Host", request.headers.get("host", ""))
    webhook_url = f"{scheme}://{host}{request.url.path}"

    if twilio_signature and settings.TWILIO_AUTH_TOKEN:
        if not _validate_twilio_signature(webhook_url, params, twilio_signature):
            print(f"[Twilio] ⚠️  Invalid signature from {request.client.host} — rejected")
            return {"status": "ok"}

    # ── Extract fields ────────────────────────────────────────────────────────
    sender_phone = From.replace("whatsapp:", "").strip()
    message_text = Body.strip()

    if not sender_phone or not message_text:
        return {"status": "ok"}

    # ── Rate limiting ─────────────────────────────────────────────────────────
    count = _rate_limit_cache.get(sender_phone, 0)
    if count >= RATE_LIMIT_MAX:
        print(f"[Bot] Rate limit hit for {sender_phone}")
        return {"status": "ok"}
    _rate_limit_cache[sender_phone] = count + 1

    background_tasks.add_task(_process_message, sender_phone, message_text)
    return {"status": "ok"}


async def _fuzzy_lookup(ingredient_name: str, db) -> tuple[dict | None, int]:
    """
    Performs fuzzy matching against all name variants in tcm_ingredients.
    Returns (best_match_doc, score) or (None, 0).
    """
    from thefuzz import fuzz

    ingredients = await db["tcm_ingredients"].find({}).to_list(length=2000)
    print(f"[Bot] DB has {len(ingredients)} ingredients")

    if not ingredients:
        print("[Bot] ⚠️  tcm_ingredients collection is EMPTY — run seed_100_tcm.py first!")
        return None, 0

    best_match = None
    highest_score = 0
    query = ingredient_name.lower()

    for ing in ingredients:
        candidates = [
            ing.get("indonesian_name", ""),
            ing.get("mandarin_name", ""),
            ing.get("pinyin_name", "") or "",
            ing.get("english_name", "") or "",
            ing.get("latin_name", "") or "",
        ]
        score = max(
            fuzz.token_set_ratio(query, str(c).lower())
            for c in candidates if str(c).strip()
        )
        if score > highest_score:
            highest_score = score
            best_match = ing

    matched_name = best_match.get("indonesian_name", "?") if best_match else "None"
    print(f"[Bot] Best match: {matched_name} (score={highest_score})")
    return best_match, highest_score


async def _process_message(sender: str, text: str):
    from services.llm_intent import (
        parse_intent,
        generate_chat_reply,
        generate_ingredient_info_reply,
    )
    from database.mongo import get_db

    try:
        print(f"[Bot] Processing from {sender}: '{text}'")

        # Load this user's conversation history for context
        history = _get_history(sender)
        print(f"[Bot] History length: {len(history)} messages")

        intent = await parse_intent(text, history=history)
        intent_type = intent.get("intent", "general_tcm_chat")
        ingredient_name = (intent.get("ingredient_name") or "").strip()
        print(f"[Bot] Intent: {intent_type}, ingredient: '{ingredient_name}'")

        # Record the user's message in history BEFORE processing
        _append_history(sender, "user", text)

        db = get_db()
        reply = ""

        # ────────────────────────────────────────────────────────────────────
        # ROUTE 1: general_tcm_chat — LLM short answer + TCM redirect
        # ────────────────────────────────────────────────────────────────────
        if intent_type == "general_tcm_chat" or not ingredient_name:
            reply = await generate_chat_reply(text, history=history)
            print(f"[Bot] General chat reply: {reply[:80]}")

        # ────────────────────────────────────────────────────────────────────
        # ROUTE 2: ingredient_info_inquiry — DB context + LLM informational
        # ────────────────────────────────────────────────────────────────────
        elif intent_type == "ingredient_info_inquiry":
            best_match, score = await _fuzzy_lookup(ingredient_name.lower(), db)
            db_match = best_match if (best_match and score >= 65) else None
            reply = await generate_ingredient_info_reply(ingredient_name, db_match, history=history)

        # ────────────────────────────────────────────────────────────────────
        # ROUTE 3: ingredient_safety_inquiry — STRICT DB lookup, no LLM verdict
        # ────────────────────────────────────────────────────────────────────
        else:
            best_match, highest_score = await _fuzzy_lookup(ingredient_name.lower(), db)

            if not best_match or highest_score < 70:
                reply = (
                    f"{DISCLAIMER}"
                    f"❓ Bahan *{ingredient_name}* tidak ditemukan dalam database kami.\n"
                    "Coba ketik nama dalam bahasa Indonesia, Mandarin, atau Pinyin.\n\n"
                    "Kamu juga bisa scan label produk TCM langsung di aplikasi FitMate! 📱"
                )
            elif best_match.get("is_toxic", False):
                level = best_match.get("toxicity_level", "tidak diketahui")
                organ = best_match.get("target_organ") or "Tidak diketahui"
                desc = best_match.get("description") or "Tidak ada detail tambahan."
                contraindications = best_match.get("contraindications", "")
                reply = (
                    f"{DISCLAIMER}"
                    f"⚠️ *Peringatan — {best_match.get('indonesian_name', ingredient_name)}*\n"
                    f"Tingkat toksisitas: *{level}*\n"
                    f"Organ target: {organ}\n"
                    f"Catatan: {desc}"
                )
                if contraindications:
                    reply += f"\nKontraindikasi: {contraindications}"
                reply += "\n\n🏥 Segera konsultasikan dengan apoteker atau dokter."
            else:
                desc = best_match.get("description") or "Tidak ada catatan tambahan."
                indonesian_name = best_match.get("indonesian_name", ingredient_name)
                reply = (
                    f"{DISCLAIMER}"
                    f"✅ *{indonesian_name}* tergolong aman berdasarkan database kami.\n"
                    f"Catatan: {desc}\n\n"
                    "Ingin memeriksa bahan lain? Ketik nama bahanya atau scan label produk di aplikasi! 🌿"
                )

        # Record bot's reply in history
        if reply:
            _append_history(sender, "assistant", reply)
            await whatsapp_client.send_text_message(to_phone=sender, text=reply)

    except Exception as e:
        print(f"[Bot ERROR] {e}")
        traceback.print_exc()
        error_reply = (
            "Maaf, saya mengalami kendala teknis. Silakan coba lagi. 🙏\n"
            "Atau scan label produk TCM Anda di aplikasi FitMate! 📱"
        )
        _append_history(sender, "assistant", error_reply)
        try:
            await whatsapp_client.send_text_message(to_phone=sender, text=error_reply)
        except Exception as send_err:
            print(f"[Bot ERROR] Cannot send error message: {send_err}")
