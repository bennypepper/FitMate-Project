"""
WhatsApp webhook router (Twilio Sandbox).

Intent routing:
  ingredient_safety_inquiry  → DB verdict (rule-based) + LLM empathetic reply
  ingredient_info_inquiry    → DB context + LLM informational reply
  general_tcm_chat           → LLM helpful conversational reply

Multi-ingredient support:
  If parse_intent() returns a comma-separated ingredient_name (e.g. from
  reading a label), all items are looked up in the DB and a combined
  safety card is returned. Multi-ingredient detection happens AFTER intent
  classification — NOT on raw message text — to avoid false positives.

First-time users:
  A welcome message is sent once per phone number (tracked in _welcomed_set).
  Uses asyncio-safe check-and-set (no await between check and set) to prevent
  duplicate welcomes from rapid-fire rapid messages.

Conversation memory:
  - Per-phone history in TTLCache (expires 2h after last message)
  - Max 15 user bubbles kept in context

Security:
  - Twilio webhook signature validation (drops fake requests silently)
  - Per-phone rate limiting: 20 messages per 10 minutes
"""
import re
import asyncio
import traceback
from fastapi import APIRouter, Request, BackgroundTasks, Form
from services.whatsapp_service import whatsapp_client
from cachetools import TTLCache
from core.config import settings

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

# ── Rate limiting ─────────────────────────────────────────────────────────────
_rate_limit_cache: TTLCache = TTLCache(maxsize=1000, ttl=600)
RATE_LIMIT_MAX = 20

# ── Conversation history ──────────────────────────────────────────────────────
# Expires after 2h of inactivity. Each value: list[{"role", "content"}]
_conversation_store: TTLCache = TTLCache(maxsize=1000, ttl=7200)
MAX_HISTORY_USER_BUBBLES = 15

# ── Welcome tracking ──────────────────────────────────────────────────────────
# Simple set — checked and written without any await in between (asyncio-safe).
# Resets on server restart (acceptable; welcome message is low-stakes).
_welcomed_set: set[str] = set()

# ── Constants ─────────────────────────────────────────────────────────────────
DISCLAIMER = "⚕️ *Disclaimer:* Informasi ini bukan pengganti saran medis profesional.\n\n"

WELCOME_MESSAGE = (
    "Halo! Saya *FitMate* 🌿 — teman cek keamanan produk herbal & TCM kamu.\n\n"
    "Langsung aja ketik:\n"
    "• Nama bahan/produk → saya cek keamanannya\n"
    "• _\"Apakah [bahan] aman untuk [kondisi]?\"_ → saya jawab sesuai kondisimu\n"
    "• _\"Apa itu [bahan]?\"_ → saya jelaskan info & manfaatnya\n\n"
    "Semua jawaban berbasis database TCM tervalidasi ya, bukan saran medis. "
    "Kalau ada yang urgent, tetap konsultasi dokter dulu! 💊"
)


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
    return list(_conversation_store.get(phone, []))


def _append_history(phone: str, role: str, content: str) -> None:
    history = _get_history(phone)
    history.append({"role": role, "content": content})
    user_indices = [i for i, m in enumerate(history) if m["role"] == "user"]
    if len(user_indices) > MAX_HISTORY_USER_BUBBLES:
        cutoff = user_indices[-MAX_HISTORY_USER_BUBBLES]
        history = history[cutoff:]
    _conversation_store[phone] = history


def _is_multi_ingredient(ingredient_name: str) -> bool:
    """
    Checks if the LLM-extracted ingredient_name is a comma/newline-separated list.
    We check the EXTRACTED name (not raw user message) to avoid false positives
    from natural sentences with commas like "saya ingin beli X, apa aman?".
    """
    if not ingredient_name:
        return False
    parts = re.split(r"[,\n]+", ingredient_name.strip())
    parts = [p.strip() for p in parts if p.strip() and len(p.strip()) > 1]
    return len(parts) >= 2


def _split_ingredient_list(ingredient_name: str) -> list[str]:
    """Splits a comma/newline-separated ingredient_name into individual names."""
    parts = re.split(r"[,\n]+", ingredient_name.strip())
    return [p.strip() for p in parts if p.strip() and len(p.strip()) > 1]


def _build_safety_verdict(best_match: dict | None, highest_score: int) -> str:
    """
    Rule-based safety verdict. LLM never determines this.
    Returns: "safe" | "toxic" | "not_found"
    """
    if not best_match or highest_score < 68:
        return "not_found"
    if best_match.get("is_toxic", False):
        return "toxic"
    return "safe"


@router.post("/webhook")
async def receive_message(
    request: Request,
    background_tasks: BackgroundTasks,
    Body: str = Form(default=""),
    From: str = Form(default=""),
    To: str = Form(default=""),
    MessageSid: str = Form(default=""),
):
    # ── Twilio signature validation ───────────────────────────────────────────
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
    Fuzzy match ingredient_name against all name variants in tcm_ingredients.
    Returns (best_match_doc, score) or (None, 0).
    """
    from thefuzz import fuzz

    ingredients = await db["tcm_ingredients"].find({}).to_list(length=2000)
    print(f"[Bot] DB has {len(ingredients)} ingredients")

    if not ingredients:
        print("[Bot] ⚠️  tcm_ingredients is EMPTY — run seed_100_tcm.py first!")
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
    print(f"[Bot] Best match for '{ingredient_name}': {matched_name} (score={highest_score})")
    return best_match, highest_score


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

        history = _get_history(sender)
        print(f"[Bot] History length: {len(history)} messages")

        # ── Welcome message — asyncio-safe check-and-set ──────────────────────
        # No await between the `if` check and `add()` — so this is atomic in asyncio.
        # Prevents duplicate welcomes even when multiple messages arrive simultaneously.
        if sender not in _welcomed_set:
            _welcomed_set.add(sender)
            _append_history(sender, "assistant", WELCOME_MESSAGE)
            await whatsapp_client.send_text_message(to_phone=sender, text=WELCOME_MESSAGE)
            await asyncio.sleep(0.8)  # small pause so welcome arrives before the actual reply

        db = get_db()
        reply = ""

        # ── Intent classification — ALWAYS first ──────────────────────────────
        # We run parse_intent() on the raw text before any other routing.
        # Multi-ingredient detection happens on the EXTRACTED ingredient_name,
        # not on the raw message — this prevents false positives from natural
        # sentences that happen to contain commas.
        intent = await parse_intent(text, history=history)
        intent_type = intent.get("intent", "general_tcm_chat")
        ingredient_name = (intent.get("ingredient_name") or "").strip()
        print(f"[Bot] Intent: {intent_type}, ingredient: '{ingredient_name}'")

        # Record user message in history
        _append_history(sender, "user", text)

        # ────────────────────────────────────────────────────────────────────
        # ROUTE 1: general_tcm_chat
        # ────────────────────────────────────────────────────────────────────
        if intent_type == "general_tcm_chat" or not ingredient_name:
            reply = await generate_chat_reply(text, history=history)
            print(f"[Bot] General chat reply (len={len(reply)})")

        # ────────────────────────────────────────────────────────────────────
        # ROUTE 2: ingredient_info_inquiry
        # ────────────────────────────────────────────────────────────────────
        elif intent_type == "ingredient_info_inquiry":
            best_match, score = await _fuzzy_lookup(ingredient_name.lower(), db)
            db_match = best_match if (best_match and score >= 65) else None
            reply = await generate_ingredient_info_reply(ingredient_name, db_match, history=history)

        # ────────────────────────────────────────────────────────────────────
        # ROUTE 3: ingredient_safety_inquiry
        # Check if it's a multi-ingredient list (comma-separated ingredient_name)
        # THEN do single or batch lookup.
        # ────────────────────────────────────────────────────────────────────
        else:
            if _is_multi_ingredient(ingredient_name):
                # ── Multi-ingredient batch lookup ─────────────────────────
                ingredient_list = _split_ingredient_list(ingredient_name)
                print(f"[Bot] Multi-ingredient list: {ingredient_list}")
                reply = await _handle_multi_ingredient(ingredient_list, db)
            else:
                # ── Single ingredient safety lookup ───────────────────────
                best_match, highest_score = await _fuzzy_lookup(ingredient_name.lower(), db)
                safety_verdict = _build_safety_verdict(best_match, highest_score)
                print(f"[Bot] Safety verdict: {safety_verdict} (score={highest_score})")

                llm_reply = await generate_safety_reply(
                    ingredient_name=ingredient_name,
                    db_match=best_match if safety_verdict != "not_found" else None,
                    safety_verdict=safety_verdict,
                    user_message=text,
                    history=history,
                )
                reply = DISCLAIMER + llm_reply

        # ── Send reply and record in history ──────────────────────────────────
        if reply:
            _append_history(sender, "assistant", reply)
            await whatsapp_client.send_text_message(to_phone=sender, text=reply)

    except Exception as e:
        print(f"[Bot ERROR] {e}")
        traceback.print_exc()
        error_reply = (
            "Aduh, ada error nih dari sisi saya. Coba kirim lagi ya! 🙏\n"
            "Kalau masih error, tunggu sebentar dan coba lagi."
        )
        _append_history(sender, "assistant", error_reply)
        try:
            await whatsapp_client.send_text_message(to_phone=sender, text=error_reply)
        except Exception as send_err:
            print(f"[Bot ERROR] Cannot send error message: {send_err}")


async def _handle_multi_ingredient(ingredient_list: list[str], db) -> str:
    """
    Batch DB lookup for a list of ingredient names.
    Returns a combined safety card.
    """
    results = []
    has_toxic = False
    has_unknown = False

    for name in ingredient_list[:6]:  # cap at 6 to avoid timeout
        best_match, score = await _fuzzy_lookup(name.lower(), db)
        safety_verdict = _build_safety_verdict(best_match, score)

        display_name = (
            best_match.get("indonesian_name", name)
            if best_match and score >= 68
            else name
        )

        if safety_verdict == "toxic":
            emoji = "⚠️"
            verdict_text = "Berbahaya/Toksik"
            has_toxic = True
        elif safety_verdict == "safe":
            emoji = "✅"
            verdict_text = "Aman"
        else:
            emoji = "❓"
            verdict_text = "Tidak ada di database kami"
            has_unknown = True

        results.append(f"{emoji} *{display_name}* — {verdict_text}")

    if not results:
        return (
            f"{DISCLAIMER}"
            "Hmm, tidak ada bahan yang ketemu di database kami. "
            "Coba ketik satu per satu ya, dengan nama Indonesia, Mandarin, atau Pinyin. 🌿"
        )

    lines = "\n".join(results)
    reply = f"{DISCLAIMER}🔍 *Hasil cek {len(results)} bahan:*\n\n{lines}\n\n"

    if has_toxic:
        reply += "⚠️ *Ada bahan berbahaya di daftar ini.* Sebaiknya konsultasi dengan apoteker atau dokter sebelum dikonsumsi.\n\n"

    if has_unknown:
        reply += "Beberapa bahan tidak ada di database kami — coba tanya satu per satu untuk hasil lebih detail.\n\n"

    reply += "Ada yang ingin kamu tahu lebih lanjut tentang salah satunya? 🌿"
    return reply
