"""
WhatsApp webhook router (Twilio Sandbox).

Intent routing:
  ingredient_safety_inquiry  → strict DB lookup, no LLM for the verdict
  ingredient_info_inquiry    → DB lookup + LLM informational reply
  general_tcm_chat           → LLM short answer + redirect to TCM context

Security:
  - Twilio webhook signature validation (X-Twilio-Signature header)
  - Per-phone rate limiting via TTLCache (20 messages per 10 minutes)
"""
import traceback
from fastapi import APIRouter, Request, BackgroundTasks, Form, HTTPException
from services.whatsapp_service import whatsapp_client
from cachetools import TTLCache
from core.config import settings

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

# Rate limit: max 20 messages per phone number per 10 minutes
rate_limit_cache = TTLCache(maxsize=1000, ttl=600)
RATE_LIMIT_MAX = 20

DISCLAIMER = "⚕️ *Disclaimer:* Informasi ini bukan pengganti saran medis profesional.\n\n"


def _validate_twilio_signature(request_url: str, params: dict, signature: str) -> bool:
    """
    Validates the X-Twilio-Signature header to ensure the request is from Twilio.
    Prevents spoofed webhook calls.
    """
    try:
        from twilio.request_validator import RequestValidator
        validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
        return validator.validate(request_url, params, signature)
    except Exception as e:
        print(f"[Twilio] Signature validation error: {e}")
        return False


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
    # Reconstruct the full URL that Twilio used (including ngrok/production host)
    twilio_signature = request.headers.get("X-Twilio-Signature", "")
    
    # Build form params dict for validation (all Twilio POST fields)
    form_data = await request.form()
    params = dict(form_data)
    
    # Get the URL Twilio hit — use X-Forwarded-* headers if behind ngrok/proxy
    scheme = request.headers.get("X-Forwarded-Proto", request.url.scheme)
    host = request.headers.get("X-Forwarded-Host", request.headers.get("host", ""))
    webhook_url = f"{scheme}://{host}{request.url.path}"
    
    if twilio_signature and settings.TWILIO_AUTH_TOKEN:
        if not _validate_twilio_signature(webhook_url, params, twilio_signature):
            print(f"[Twilio] ⚠️  Invalid signature from {request.client.host} — rejected")
            # Return 200 to prevent Twilio from retrying, but don't process
            return {"status": "ok"}

    # ── Extract fields ────────────────────────────────────────────────────────
    sender_phone = From.replace("whatsapp:", "").strip()
    message_text = Body.strip()

    if not sender_phone or not message_text:
        return {"status": "ok"}

    # ── Rate limiting ─────────────────────────────────────────────────────────
    count = rate_limit_cache.get(sender_phone, 0)
    if count >= RATE_LIMIT_MAX:
        print(f"[Bot] Rate limit hit for {sender_phone}")
        return {"status": "ok"}
    rate_limit_cache[sender_phone] = count + 1

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
        intent = await parse_intent(text)
        intent_type = intent.get("intent", "general_tcm_chat")
        ingredient_name = (intent.get("ingredient_name") or "").strip()
        print(f"[Bot] Intent: {intent_type}, ingredient: '{ingredient_name}'")

        db = get_db()

        # ────────────────────────────────────────────────────────────────────
        # ROUTE 1: general_tcm_chat — LLM short answer + TCM redirect
        # ────────────────────────────────────────────────────────────────────
        if intent_type == "general_tcm_chat" or not ingredient_name:
            reply = await generate_chat_reply(text)
            print(f"[Bot] General chat reply: {reply[:80]}")
            await whatsapp_client.send_text_message(to_phone=sender, text=reply)
            return

        # ────────────────────────────────────────────────────────────────────
        # ROUTE 2: ingredient_info_inquiry — DB context + LLM informational
        # ────────────────────────────────────────────────────────────────────
        if intent_type == "ingredient_info_inquiry":
            best_match, score = await _fuzzy_lookup(ingredient_name.lower(), db)
            db_match = best_match if (best_match and score >= 65) else None
            reply = await generate_ingredient_info_reply(ingredient_name, db_match)
            await whatsapp_client.send_text_message(to_phone=sender, text=reply)
            return

        # ────────────────────────────────────────────────────────────────────
        # ROUTE 3: ingredient_safety_inquiry — STRICT DB lookup, no LLM verdict
        # ────────────────────────────────────────────────────────────────────
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
            reply += (
                "\n\n🏥 Segera konsultasikan dengan apoteker atau dokter sebelum mengonsumsi produk ini."
            )
        else:
            desc = best_match.get("description") or "Tidak ada catatan tambahan."
            indonesian_name = best_match.get("indonesian_name", ingredient_name)
            reply = (
                f"{DISCLAIMER}"
                f"✅ *{indonesian_name}* tergolong aman berdasarkan database kami.\n"
                f"Catatan: {desc}\n\n"
                "Ingin memeriksa bahan lain? Ketik nama bahanya atau scan label produk di aplikasi! 🌿"
            )

        await whatsapp_client.send_text_message(to_phone=sender, text=reply)

    except Exception as e:
        print(f"[Bot ERROR] {e}")
        traceback.print_exc()
        try:
            await whatsapp_client.send_text_message(
                to_phone=sender,
                text=(
                    "Maaf, saya mengalami kendala teknis. Silakan coba lagi dalam beberapa saat. 🙏\n"
                    "Atau scan label produk TCM Anda langsung di aplikasi FitMate! 📱"
                ),
            )
        except Exception as send_err:
            print(f"[Bot ERROR] Cannot send error message: {send_err}")
