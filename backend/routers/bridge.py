"""
bridge.py — Session pairing bridge between desktop and mobile.

Allows a desktop user to scan a QR code with their mobile phone,
take a photo of TCM medicine packaging, and have the analysis
results automatically appear on their desktop browser.
"""

import uuid
import time
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from cachetools import TTLCache
from database.mongo import get_db
from services.vision import extract_and_translate_text
from services.safety import match_ingredients

router = APIRouter(prefix="/api/v1/bridge", tags=["bridge"])

# Store up to 1000 active sessions with a 5-minute TTL (300 seconds)
_sessions: TTLCache = TTLCache(maxsize=1000, ttl=300)

@router.post("/session")
async def create_session(custom_id: str = None):
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
async def upload_for_session(
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

    session["status"] = "processing"

    try:
        content = await file.read()
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
        return {"status": "success", "message": "Hasil analisis berhasil dikirim ke desktop"}
    except Exception as e:
        session["status"] = "error"
        session["error"] = str(e)
        raise HTTPException(status_code=500, detail=f"Gagal memproses gambar: {str(e)}")
