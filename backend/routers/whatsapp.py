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
from fastapi import APIRouter, Request, BackgroundTasks, Form, Depends
from pydantic import BaseModel
from services.whatsapp_service import whatsapp_client
from cachetools import TTLCache
from core.config import settings
from database.mongo import get_db

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

_rate_limit_cache: TTLCache = TTLCache(maxsize=1000, ttl=600)
RATE_LIMIT_MAX = 20

_conversation_store: TTLCache = TTLCache(maxsize=1000, ttl=7200)
MAX_HISTORY_USER_BUBBLES = 15

_welcomed_set: set[str] = set()

DISCLAIMER = "⚕️ *Disclaimer:* Informasi ini bukan pengganti saran medis profesional.\n\n"

_offtopic_counter: TTLCache = TTLCache(maxsize=1000, ttl=7200)

_offtopic_cooldown: TTLCache = TTLCache(maxsize=1000, ttl=300)

OFFTOPIC_SHORT_LIMIT = 2  
OFFTOPIC_TERSE_LIMIT = 3  
OFFTOPIC_COOLDOWN_LIMIT = 5

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

def _get_offtopic_count(phone: str) -> int:
    return _offtopic_counter.get(phone, 0)

def _increment_offtopic(phone: str) -> int:
    """Increments off-topic counter and returns new count. Sets cooldown at limit."""
    count = _offtopic_counter.get(phone, 0) + 1
    _offtopic_counter[phone] = count
    if count >= OFFTOPIC_COOLDOWN_LIMIT:
        _offtopic_cooldown[phone] = True
        print(f"[Bot] Off-topic cooldown triggered for {phone} (count={count})")
    return count

def _is_on_cooldown(phone: str) -> bool:
    return bool(_offtopic_cooldown.get(phone, False))

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

    sender_phone = From.replace("whatsapp:", "").strip()
    message_text = Body.strip()

    if not sender_phone or not message_text:
        return {"status": "ok"}

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
    from services.safety_interceptor import (
        check_emergency,
        check_bko,
        is_health_related,
        OUT_OF_SCOPE_STATIC,
        OUT_OF_SCOPE_TERSE,
        OUT_OF_SCOPE_COOLDOWN,
    )
    from database.mongo import get_db

    try:
        print(f"[Bot] Processing from {sender}: '{text}'")

        history = _get_history(sender)
        print(f"[Bot] History length: {len(history)} messages")

        if sender not in _welcomed_set:
            _welcomed_set.add(sender)
            _append_history(sender, "assistant", WELCOME_MESSAGE)
            await whatsapp_client.send_text_message(to_phone=sender, text=WELCOME_MESSAGE)
            await asyncio.sleep(0.8)

        emergency_reply = check_emergency(text)
        if emergency_reply:
            _append_history(sender, "assistant", emergency_reply)
            await whatsapp_client.send_text_message(to_phone=sender, text=emergency_reply)
            return

        bko_result = await check_bko(text)
        bko_action = bko_result["action"]

        if bko_action in ("block", "clarify"):
            bko_reply = bko_result["response"]
            _append_history(sender, "assistant", bko_reply)
            await whatsapp_client.send_text_message(to_phone=sender, text=bko_reply)
            return

        bko_soft_warning = bko_result.get("soft_warning", "")

        if _is_on_cooldown(sender):
            cooldown_reply = OUT_OF_SCOPE_COOLDOWN
            _append_history(sender, "assistant", cooldown_reply)
            await whatsapp_client.send_text_message(to_phone=sender, text=cooldown_reply)
            return

        db = get_db()
        reply = ""

        intent = await parse_intent(text, history=history)
        intent_type = intent.get("intent", "general_tcm_chat")
        ingredient_name = (intent.get("ingredient_name") or "").strip()
        print(f"[Bot] Intent: {intent_type}, ingredient: '{ingredient_name}'")

        _append_history(sender, "user", text)

        if intent_type == "general_tcm_chat" or not ingredient_name:

            if not is_health_related(text):
                count = _increment_offtopic(sender)
                print(f"[Bot] Off-topic detected for {sender}, count={count}")
                if count >= OFFTOPIC_TERSE_LIMIT:
                    reply = OUT_OF_SCOPE_TERSE
                else:

                    reply = await generate_chat_reply(text, history=history)
            else:
                reply = await generate_chat_reply(text, history=history)
            print(f"[Bot] General chat reply (len={len(reply)})")

        elif intent_type == "ingredient_info_inquiry":
            best_match, score = await _fuzzy_lookup(ingredient_name.lower(), db)
            db_match = best_match if (best_match and score >= 65) else None
            reply = await generate_ingredient_info_reply(ingredient_name, db_match, history=history)

        else:
            if _is_multi_ingredient(ingredient_name):

                ingredient_list = _split_ingredient_list(ingredient_name)
                print(f"[Bot] Multi-ingredient list: {ingredient_list}")
                reply = await _handle_multi_ingredient(ingredient_list, db)
            else:

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

                llm_reply = re.sub(r"(?i)(?:⚕️\s*)?(?:\*?Disclaimer\*?:?)\s*.*?(?:\n+|$)", "", llm_reply).strip()
                reply = DISCLAIMER + llm_reply

        if bko_soft_warning and reply:
            reply = reply.rstrip() + bko_soft_warning

        if reply:
            clean_reply_for_history = reply.replace(DISCLAIMER, "").strip()
            _append_history(sender, "assistant", clean_reply_for_history)
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

    for name in ingredient_list[:6]:
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

class TestChatRequest(BaseModel):
    sender: str = "test_user"
    message: str
    model: str | None = None

@router.post("/test-chat")
async def test_chat(req: TestChatRequest, db=Depends(get_db)):
    """
    Test endpoint to bypass Twilio sandbox limits.
    Acts like the real webhook but returns JSON instead of relying on Twilio API.
    All safety interceptor layers are active here so batch testing reflects real behavior.
    """
    from services.llm_intent import (
        parse_intent,
        generate_chat_reply,
        generate_ingredient_info_reply,
        generate_safety_reply,
    )
    from services.safety_interceptor import (
        check_emergency,
        check_bko,
        is_health_related,
        OUT_OF_SCOPE_STATIC,
        OUT_OF_SCOPE_TERSE,
        OUT_OF_SCOPE_COOLDOWN,
    )

    sender = req.sender
    text = req.message
    model_override = req.model

    history = _get_history(sender)

    welcome_sent = False
    if sender not in _welcomed_set:
        _welcomed_set.add(sender)
        _append_history(sender, "assistant", WELCOME_MESSAGE)
        welcome_sent = True

    reply = ""
    intercepted_by = None

    emergency_reply = check_emergency(text)
    if emergency_reply:
        _append_history(sender, "assistant", emergency_reply)
        return {
            "status": "success",
            "intent": "EMERGENCY",
            "ingredient_extracted": None,
            "welcome_sent": welcome_sent,
            "welcome_message": WELCOME_MESSAGE if welcome_sent else None,
            "intercepted_by": "emergency",
            "reply": emergency_reply,
        }

    bko_result = await check_bko(text)
    bko_action = bko_result["action"]

    if bko_action in ("block", "clarify"):
        bko_reply = bko_result["response"]
        _append_history(sender, "assistant", bko_reply)
        return {
            "status": "success",
            "intent": "BKO_INTERCEPTED",
            "ingredient_extracted": None,
            "welcome_sent": welcome_sent,
            "welcome_message": WELCOME_MESSAGE if welcome_sent else None,
            "intercepted_by": bko_action,
            "reply": bko_reply,
        }

    bko_soft_warning = bko_result.get("soft_warning", "")

    if _is_on_cooldown(sender):
        cooldown_reply = OUT_OF_SCOPE_COOLDOWN
        _append_history(sender, "assistant", cooldown_reply)
        return {
            "status": "success",
            "intent": "OFFTOPIC_COOLDOWN",
            "ingredient_extracted": None,
            "welcome_sent": welcome_sent,
            "welcome_message": WELCOME_MESSAGE if welcome_sent else None,
            "intercepted_by": "offtopic_cooldown",
            "reply": cooldown_reply,
        }

    intent = await parse_intent(text, history=history, model=model_override)
    intent_type = intent.get("intent", "general_tcm_chat")
    ingredient_name = (intent.get("ingredient_name") or "").strip()

    _append_history(sender, "user", text)

    if intent_type == "general_tcm_chat" or not ingredient_name:
        if not is_health_related(text):
            count = _increment_offtopic(sender)
            if count >= OFFTOPIC_TERSE_LIMIT:
                reply = OUT_OF_SCOPE_TERSE
                intercepted_by = f"offtopic_terse_count_{count}"
            else:
                reply = await generate_chat_reply(text, history=history, model=model_override)
                intercepted_by = f"offtopic_warned_count_{count}"
        else:
            reply = await generate_chat_reply(text, history=history, model=model_override)
    elif intent_type == "ingredient_info_inquiry":
        best_match, score = await _fuzzy_lookup(ingredient_name.lower(), db)
        db_match = best_match if (best_match and score >= 65) else None
        reply = await generate_ingredient_info_reply(ingredient_name, db_match, history=history, model=model_override)
    else:
        if _is_multi_ingredient(ingredient_name):
            ingredient_list = _split_ingredient_list(ingredient_name)
            reply = await _handle_multi_ingredient(ingredient_list, db)
        else:
            best_match, highest_score = await _fuzzy_lookup(ingredient_name.lower(), db)
            safety_verdict = _build_safety_verdict(best_match, highest_score)

            llm_reply = await generate_safety_reply(
                ingredient_name=ingredient_name,
                db_match=best_match if safety_verdict != "not_found" else None,
                safety_verdict=safety_verdict,
                user_message=text,
                history=history,
                model=model_override,
            )
            llm_reply = re.sub(r"(?i)(?:⚕️\s*)?(?:\*?Disclaimer\*?:?)\s*.*?(?:\n+|$)", "", llm_reply).strip()
            reply = DISCLAIMER + llm_reply

    if bko_soft_warning and reply:
        reply = reply.rstrip() + bko_soft_warning

    if reply:
        clean_reply_for_history = reply.replace(DISCLAIMER, "").strip()
        _append_history(sender, "assistant", clean_reply_for_history)

    return {
        "status": "success",
        "intent": intent_type,
        "ingredient_extracted": ingredient_name,
        "welcome_sent": welcome_sent,
        "welcome_message": WELCOME_MESSAGE if welcome_sent else None,
        "intercepted_by": intercepted_by,
        "reply": reply,
    }
