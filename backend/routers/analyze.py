from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from services.vision import extract_and_translate_text
from services.safety import match_ingredients
from database.mongo import get_db
import traceback

router = APIRouter(prefix="/api/v1/analyze", tags=["analyze"])

@router.post("/")
async def analyze_tcm_label(file: UploadFile = File(...), db = Depends(get_db)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        content = await file.read()
        
        # 1. OCR Extraction
        ocr_blocks = extract_and_translate_text(content)
        
        # Extract just the continuous texts
        detected_texts = [block["text"] for block in ocr_blocks]
        
        # 2. Safety Match
        safety_results = await match_ingredients(detected_texts, db)
        
        # 3. Formulate Payload (SAFE-04)
        return {
            "status": "success",
            "ocr_blocks": ocr_blocks,
            "safety_analysis": safety_results,
            "disclaimer": "MEDICAL DISCLAIMER: FitMate provides rule-based information only and does not substitute professional medical advice. Always consult a certified healthcare professional before consuming any TCM product."
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
