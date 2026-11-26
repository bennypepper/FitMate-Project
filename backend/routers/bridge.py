"""
bridge.py — Session pairing bridge between desktop and mobile.

Allows a desktop user to scan a QR code with their mobile phone,
take a photo of TCM medicine packaging, and have the analysis
results automatically appear on their desktop browser.
"""

import hmac
import secrets
import time
import logging
from fastapi import APIRouter, UploadFile, File, Form, Header, HTTPException, Depends, Query, Request
from cachetools import TTLCache
from database.mongo import get_db
from services.vision import extract_and_translate_text
from services.safety import match_ingredients
from services.safety_interceptor import merge_bko_findings
from core.limiter import limiter
from utils.upload_validation import detect_image_mime, read_upload_limited

logger = logging.getLogger("fitmate.bridge")

router = APIRouter(prefix="/api/v1/bridge", tags=["bridge"])

# Store up to 1000 active sessions with a 5-minute TTL (300 seconds)
_sessions: TTLCache = TTLCache(maxsize=1000, ttl=300)


@router.post("/session")
@limiter.limit("30/minute")
async def create_session(request: Request, custom_id: str | None = None):
    """Creates a temporary session ID and upload token for mobile-to-desktop bridging."""
    if custom_id:
        if custom_id in _sessions:
            raise HTTPException(status_code=409, detail="Session ID already exists")
        session_id = custom_id
    else:
        session_id = f"fm_{secrets.token_urlsafe(16)}"

    upload_token = secrets.token_urlsafe(24)
    _sessions[session_id] = {
        "status": "waiting",  # "waiting" | "processing" | "completed" | "error"
        "created_at": time.time(),
        "upload_token": upload_token,
        "results": None,
        "error": None,
    }
    return {
        "session_id": session_id,
        "upload_token": upload_token,
        "status": "waiting",
        "expires_in_seconds": 300,
    }


@router.get("/{session_id}/status")
@limiter.limit("60/minute")
async def get_session_status(request: Request, session_id: str):
    """Checks the current status of a bridge session (polled by desktop)."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    return {
        "session_id": session_id,
        "status": session["status"],
        "results": session.get("results"),
        "error": session.get("error"),
    }


@router.post("/{session_id}/upload")
@limiter.limit("5/minute")
async def upload_for_session(
    request: Request,
    session_id: str,
    file: UploadFile = File(...),
    x_bridge_token: str | None = Header(default=None, alias="X-Bridge-Token"),
    upload_token: str | None = Query(default=None),
    upload_token_form: str | None = Form(default=None, alias="upload_token"),
    db = Depends(get_db),
):
    """Receives a photo upload from mobile and analyzes it for the desktop session."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    provided_token = (x_bridge_token or upload_token or upload_token_form or "").strip()
    expected_token = session.get("upload_token", "")
    if not provided_token or not expected_token or not hmac.compare_digest(provided_token, expected_token):
        raise HTTPException(status_code=403, detail="Invalid or missing bridge upload token")

    if session["status"] == "processing":
        raise HTTPException(status_code=409, detail="Session is already processing an upload")

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File harus berupa gambar")

    content = await read_upload_limited(
        file,
        max_bytes=10 * 1024 * 1024,
        detail="Ukuran gambar terlalu besar. Maksimum ukuran adalah 10MB.",
    )
    if not detect_image_mime(content):
        raise HTTPException(
            status_code=400,
            detail="Konten gambar tidak valid. Format yang didukung: JPEG, PNG, GIF, WEBP.",
        )

    session["status"] = "processing"

    try:
        ocr_blocks = await extract_and_translate_text(content)
        detected_texts = [block["text"] for block in ocr_blocks]
        safety_results = await match_ingredients(detected_texts, db)
        safety_results = merge_bko_findings(safety_results, detected_texts)

        payload = {
            "status": "success",
            "ocr_blocks": ocr_blocks,
            "safety_analysis": safety_results,
            "disclaimer": (
                "MEDICAL DISCLAIMER: FitMate provides rule-based information only and does not "
                "substitute professional medical advice. Always consult a certified healthcare "
                "professional before consuming any TCM product."
            )
        }

        session["status"] = "completed"
        session["results"] = payload
        return {
            "status": "success",
            "message": "Hasil analisis berhasil diproses",
            **payload
        }
    except HTTPException:
        session["status"] = "error"
        raise
    except Exception as e:
        logger.error(f"[Bridge] Failed processing image for session {session_id}: {e}", exc_info=True)
        session["status"] = "error"
        session["error"] = "Gagal memproses gambar pada server"
        raise HTTPException(status_code=500, detail="Gagal memproses gambar. Terjadi kendala teknis pada sistem pemrosesan.")
