import logging
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Query, Request
from services.vision import extract_and_translate_text
from services.safety import match_ingredients
from services.safety_interceptor import merge_bko_findings
from database.mongo import get_db
from core.limiter import limiter
from utils.upload_validation import detect_image_mime, read_upload_limited

logger = logging.getLogger("fitmate.analyze")

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

    content = await read_upload_limited(
        file,
        max_bytes=10 * 1024 * 1024,
        detail="Image too large. Maximum size is 10MB.",
    )
    if not detect_image_mime(content):
        raise HTTPException(
            status_code=400,
            detail="Invalid image file content. Supported formats: JPEG, PNG, GIF, WEBP.",
        )

    try:

        ocr_blocks = await extract_and_translate_text(content)

        detected_texts = [block["text"] for block in ocr_blocks]

        safety_results = await match_ingredients(detected_texts, db)
        safety_results = merge_bko_findings(safety_results, detected_texts)

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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Analyze] Analysis pipeline failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Gagal menganalisis gambar. Terjadi kendala teknis pada sistem pemrosesan."
        )

@router.get("/search")
@limiter.limit("60/minute")
async def search_ingredients(
    request: Request,
    q: str = "",
    limit: int = Query(default=20, ge=1, le=100),
    db = Depends(get_db),
):
    """
    Public lookup for TCM ingredients without requiring admin login.
    Returns matched ingredients sorted by relevance.
    Rate limited: max 60 requests per minute per IP.
    """
    from database.ingredient_repository import ingredient_repository
    results = await ingredient_repository.search_ingredients(query=q, db=db, limit=limit)
    return {"total": len(results), "items": results}
