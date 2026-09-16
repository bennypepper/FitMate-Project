import logging
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Request
from services.vision import extract_and_translate_text
from services.safety import match_ingredients
from database.mongo import get_db
from core.limiter import limiter

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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Analyze] Analysis pipeline failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Gagal menganalisis gambar. Terjadi kendala teknis pada sistem pemrosesan."
        )

@router.get("/search")
async def search_ingredients(q: str = "", limit: int = 20, db = Depends(get_db)):
    """
    Public lookup for TCM ingredients without requiring admin login.
    Returns matched ingredients sorted by relevance.
    """
    query = (q or "").strip().lower()
    cursor = db.tcm_ingredients.find({}, {"_id": 0})
    all_ingredients = await cursor.to_list(length=1000)

    if not query:
        return {"total": min(len(all_ingredients), limit), "items": all_ingredients[:limit]}

    matches = []
    for ing in all_ingredients:
        names = [
            str(ing.get("indonesian_name") or "").lower(),
            str(ing.get("mandarin_name") or "").lower(),
            str(ing.get("pinyin_name") or "").lower(),
            str(ing.get("english_name") or "").lower(),
            str(ing.get("latin_name") or "").lower(),
        ]
        score = 0
        for n in names:
            if not n:
                continue
            if query == n:
                score = max(score, 100)
            elif query in n or n in query:
                score = max(score, 80)
        if score > 0:
            matches.append((score, ing))

    matches.sort(key=lambda x: x[0], reverse=True)
    results = [m[1] for m in matches[:limit]]
    return {"total": len(results), "items": results}
