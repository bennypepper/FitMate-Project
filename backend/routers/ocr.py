import logging
from fastapi import APIRouter, File, UploadFile, HTTPException, Request
from services.vision import extract_and_translate_text
from core.limiter import limiter

logger = logging.getLogger("fitmate.ocr")

router = APIRouter(prefix="/api/v1/ocr", tags=["ocr"])

@router.post("/upload")
@limiter.limit("10/minute")
async def process_image_ocr(
    request: Request,
    file: UploadFile = File(...),
):
    """
    Raw OCR endpoint — returns extracted text blocks only.
    Rate limited: max 10 requests per minute per IP.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    try:
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Image too large. Maximum size is 10MB.")

        results = await extract_and_translate_text(content)
        return {
            "status": "success",
            "results": results
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[OCR] OCR processing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Gagal mengekstraksi teks gambar. Terjadi kendala teknis pada sistem OCR."
        )
