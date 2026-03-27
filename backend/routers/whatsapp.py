"""
WhatsApp webhook router (Twilio Sandbox).

Intent routing:
  ingredient_safety_inquiry  → DB verdict (rule-based) + LLM empathetic reply
  ingredient_info_inquiry    → DB context + LLM informational reply
  general_tcm_chat           → LLM short answer + redirect to TCM context

Standalone use case:
  Users can consult directly via WhatsApp without ever using the web app.
  First-time users get a welcome/capabilities message.
  Bare ingredient names (no question mark) are treated as safety inquiries.
  Comma-separated ingredient lists get a multi-item safety card.

Conversation memory:
  - Per-phone history stored in TTLCache (expires 2h after last message)
  - Max 15 user bubbles (+ their bot replies) kept in context
  - Enables reference resolution: "bahan itu", "yang tadi", "apakah aman?"

Security:
  - Twilio webhook signature validation (X-Twilio-Signature header)
  - Per-phone rate limiting via TTLCache (20 messages per 10 minutes)
"""
import re
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

WELCOME_MESSAGE = (
    "Halo! Saya *FitMate* 🌿 — asisten keamanan produk TCM kamu.\n\n"
    "Kamu bisa:\n"
    "• Ketik nama bahan herbal untuk cek keamanannya\n"
    "• Tanya _\"apakah [bahan] aman untuk [kondisimu]?\"_\n"
    "• Minta info/manfaat bahan TCM apa saja\n\n"
    "📋 *Catatan:* Jawaban saya berdasarkan database bahan TCM tervalidasi — bukan pengganti saran medis.\n\n"
    "Langsung ketik nama bahan atau produk TCM yang ingin kamu cek! 💊"
)

# Minimum number of comma/newline separated tokens to treat as a multi-ingredient list
_MULTI_INGREDIENT_MIN = 2


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


def _parse_multi_ingredient_list(text: str) -> list[str] | None:
    """
    Detects if the message is a comma/newline-separated list of ingredient names.
    Returns a list of ingredient tokens if detected (≥2 items), else None.
    Only triggers if the message looks like a label list — not a full sentence.
    """
    # Skip full sentences (has question mark, or more than ~8 words before a comma)
    if "?" in text or len(text.split()) > 20:
        return None

    # Split by comma or newline
    parts = re.split(r"[,\n]+", text.strip())
    parts = [p.strip() for p in parts if p.strip() and len(p.strip()) > 1]

    if len(parts) >= _MULTI_INGREDIENT_MIN:
        return parts
    return None


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


def _build_safety_verdict(best_match: dict | None, highest_score: int, ingredient_name: str) -> str:
    """
    Determines safety verdict string based purely on DB data. LLM never touches this.
    Returns: "safe" | "toxic" | "not_found"
    """
    if not best_match or highest_score < 70:
        return "not_found"
    if best_match.get("is_toxic", False):
        return "toxic"
    return "safe"


async def _process_message(sender: str, text: str):
    from services.llm_intent import (
        parse_intent,
        generate_chat_reply,
        generate_ingredient_info_reply,
        generate_safety_reply,
    )
    from database.mongo import get_db

    try:
        print(f"[Bot] Processing from {sender}: '{text}'")

        # Load this user's conversation history for context
        history = _get_history(sender)
        is_first_message = len(history) == 0
        print(f"[Bot] History length: {len(history)} messages, first_message={is_first_message}")

        # ── Welcome message for first-time users ─────────────────────────────
        # Send the welcome card BEFORE processing the first actual message
        # so the user understands the bot's capabilities.
        if is_first_message:
            _append_history(sender, "assistant", WELCOME_MESSAGE)
            await whatsapp_client.send_text_message(to_phone=sender, text=WELCOME_MESSAGE)
            # Small courtesy pause so the two messages don't arrive at exactly the same time
            import asyncio
            await asyncio.sleep(1)

        db = get_db()
        reply = ""

        # ── Multi-ingredient list detection ──────────────────────────────────
        # Check if message is a bare comma-separated label list before running intent classifier
        ingredient_list = _parse_multi_ingredient_list(text)
        if ingredient_list and len(ingredient_list) >= _MULTI_INGREDIENT_MIN:
            print(f"[Bot] Multi-ingredient list detected: {ingredient_list}")
            _append_history(sender, "user", text)
            reply = await _handle_multi_ingredient(ingredient_list, text, history, db, generate_safety_reply)
            if reply:
                _append_history(sender, "assistant", reply)
                await whatsapp_client.send_text_message(to_phone=sender, text=reply)
            return

        # ── Single ingredient / general flow ─────────────────────────────────
        intent = await parse_intent(text, history=history)
        intent_type = intent.get("intent", "general_tcm_chat")
        ingredient_name = (intent.get("ingredient_name") or "").strip()
        print(f"[Bot] Intent: {intent_type}, ingredient: '{ingredient_name}'")

        # Record the user's message in history BEFORE generating reply
        _append_history(sender, "user", text)

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
        # ROUTE 3: ingredient_safety_inquiry
        # DB verdict is RULE-BASED (never LLM). LLM only writes the language.
        # ────────────────────────────────────────────────────────────────────
        else:
            best_match, highest_score = await _fuzzy_lookup(ingredient_name.lower(), db)

            # Determine verdict purely by DB rules — LLM cannot change this
            safety_verdict = _build_safety_verdict(best_match, highest_score, ingredient_name)
            print(f"[Bot] Safety verdict: {safety_verdict} (score={highest_score})")

            # LLM writes an empathetic reply anchored to the verdict
            llm_reply = await generate_safety_reply(
                ingredient_name=ingredient_name,
                db_match=best_match if safety_verdict != "not_found" else None,
                safety_verdict=safety_verdict,
                user_message=text,
                history=history,
            )
            reply = DISCLAIMER + llm_reply

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


async def _handle_multi_ingredient(
    ingredient_list: list[str],
    original_text: str,
    history: list[dict],
    db,
    generate_safety_reply,
) -> str:
    """
    Handles a comma-separated list of ingredients (e.g. from reading a label).
    Runs DB lookup for each item and returns a combined safety card.
    """
    results = []
    found_any = False

    for name in ingredient_list[:6]:  # cap at 6 to avoid timeout
        best_match, score = await _fuzzy_lookup(name.lower(), db)
        safety_verdict = _build_safety_verdict(best_match, score, name)
        display_name = (
            best_match.get("indonesian_name", name) if best_match and score >= 70 else name
        )

        if safety_verdict == "toxic":
            emoji = "⚠️"
            verdict_text = "BERBAHAYA"
            found_any = True
        elif safety_verdict == "safe":
            emoji = "✅"
            verdict_text = "Aman"
            found_any = True
        else:
            emoji = "❓"
            verdict_text = "Tidak ditemukan di database"

        results.append(f"{emoji} *{display_name}* — {verdict_text}")

    if not results:
        return (
            f"{DISCLAIMER}"
            "❓ Tidak ada bahan yang ditemukan dalam database kami.\n"
            "Coba ketik satu nama bahan per pesan dengan nama Indonesia, Mandarin, atau Pinyin."
        )

    lines = "\n".join(results)
    reply = (
        f"{DISCLAIMER}"
        f"🔍 *Hasil cek {len(results)} bahan:*\n\n"
        f"{lines}\n\n"
    )

    if any("⚠️" in r for r in results):
        reply += "⚠️ Ada bahan yang dikategorikan berbahaya. Segera konsultasikan dengan dokter atau apoteker.\n\n"

    if not found_any:
        reply += "Beberapa bahan tidak ditemukan di database kami. Coba ketik satu per satu untuk hasil lebih akurat.\n\n"

    reply += "Ada bahan lain yang ingin dicek, atau ingin tahu lebih detail tentang salah satunya? 🌿"
    return reply
