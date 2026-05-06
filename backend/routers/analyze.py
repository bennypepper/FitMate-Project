from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Request
from services.vision import extract_and_translate_text
from services.safety import match_ingredients
from database.mongo import get_db
from main import limiter
import traceback

router = APIRouter(prefix="/api/v1/analyze", tags=["analyze"])

@router.post("/")
@limiter.limit("5/minute")
async def analyze_tcm_label(
    request: Request,
    file: UploadFile = File(...),
    db = Depends(get_db)
):
    """
    Analyzes a TCM label image.
    Rate limited: max 5 requests per minute per IP.
    LLM-powered OCR is expensive — this prevents abuse.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image too large. Maximum size is 10MB.")

    try:

        ocr_blocks = await extract_and_translate_text(content)

        detected_texts = [block["text"] for block in ocr_blocks]

        safety_results = await match_ingredients(detected_texts, db)

        return {
            "status": "success",
            "ocr_blocks": ocr_blocks,
            "safety_analysis": safety_results,
            "disclaimer": (
                "MEDICAL DISCLAIMER: FitMate provides rule-based information only and does not "
                "substitute professional medical advice. Always consult a certified healthcare "
                "professional before consuming any TCM product."
            )
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
