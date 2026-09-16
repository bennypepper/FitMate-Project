"""
bridge.py — Session pairing bridge between desktop and mobile.

Allows a desktop user to scan a QR code with their mobile phone,
take a photo of TCM medicine packaging, and have the analysis
results automatically appear on their desktop browser.
"""

import uuid
import time
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from cachetools import TTLCache
from database.mongo import get_db
from services.vision import extract_and_translate_text
from services.safety import match_ingredients
from core.limiter import limiter

logger = logging.getLogger("fitmate.bridge")

router = APIRouter(prefix="/api/v1/bridge", tags=["bridge"])

# Store up to 1000 active sessions with a 5-minute TTL (300 seconds)
_sessions: TTLCache = TTLCache(maxsize=1000, ttl=300)

@router.post("/session")
@limiter.limit("30/minute")
async def create_session(request: Request, custom_id: str = None):
    """Creates or registers a temporary session ID for mobile-to-desktop bridging."""
    session_id = custom_id or f"fm_{uuid.uuid4().hex[:8]}"
    _sessions[session_id] = {
        "status": "waiting",  # "waiting" | "processing" | "completed" | "error"
        "created_at": time.time(),
        "results": None,
        "error": None,
    }
    return {
        "session_id": session_id,
        "status": "waiting",
        "expires_in_seconds": 300,
    }

@router.get("/{session_id}/status")
async def get_session_status(session_id: str):
    """Checks the current status of a bridge session (polled by desktop)."""
    session = _sessions.get(session_id)
    if not session:
        # Auto-provision if desktop generated the ID client-side
        session = {
            "status": "waiting",
            "created_at": time.time(),
            "results": None,
            "error": None,
        }
        _sessions[session_id] = session

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
    db = Depends(get_db)
):
    """Receives a photo upload from mobile and analyzes it for the desktop session."""
    session = _sessions.get(session_id)
    if not session:
        session = {
            "status": "waiting",
            "created_at": time.time(),
            "results": None,
            "error": None,
        }
        _sessions[session_id] = session

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File harus berupa gambar")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Ukuran gambar terlalu besar. Maksimum ukuran adalah 10MB.")

    session["status"] = "processing"

    try:
        ocr_blocks = await extract_and_translate_text(content)
        detected_texts = [block["text"] for block in ocr_blocks]
        safety_results = await match_ingredients(detected_texts, db)

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
