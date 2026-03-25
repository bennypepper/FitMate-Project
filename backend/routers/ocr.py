from fastapi import APIRouter, File, UploadFile, HTTPException
from services.vision import extract_and_translate_text
import traceback

router = APIRouter(prefix="/api/v1/ocr", tags=["ocr"])

@router.post("/upload")
async def process_image_ocr(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        content = await file.read()
        results = extract_and_translate_text(content)
        return {
            "status": "success",
            "results": results
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
