import os
import base64
import json
import httpx
from core.config import settings

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

async def extract_and_translate_text(image_bytes: bytes) -> list[dict]:
    """
    Extracts text using OpenRouter + Google Gemini-2.5-flash-lite natively.
    Replaces the legacy Google Cloud Vision OCR.
    """
    if os.environ.get("MOCK_VISION_API", "false").lower() == "true":
        return [
            {"text": "人参", "bounding_box": [{"x": 10, "y": 10}, {"x": 50, "y": 10}, {"x": 50, "y": 30}, {"x": 10, "y": 30}]},
            {"text": "当归", "bounding_box": [{"x": 10, "y": 40}, {"x": 50, "y": 40}, {"x": 50, "y": 60}, {"x": 10, "y": 60}]}
        ]

    # Convert image to base64
    b64_img = base64.b64encode(image_bytes).decode("utf-8")
    
    prompt = (
        "Extract the medicinal ingredients from this image (likely a TCM label). "
        "Return ONLY a JSON list of strings representing the unique ingredient names. "
        "Do NOT include the word JSON or triple backticks. Example: [\"Ginseng\", \"Radix Astragali\", \"Lo Han Guo\"]"
    )

    payload = {
        "model": settings.OPENROUTER_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
                ]
            }
        ],
        "temperature": 0.1
    }

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://fitmate-tcm.vercel.app",
        "X-Title": "FitMate TCM Safety Scanner",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(OPENROUTER_BASE_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
    content = data["choices"][0]["message"]["content"]
    content = content.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
    
    try:
        ingredients_list = json.loads(content)
        if not isinstance(ingredients_list, list):
            ingredients_list = []
    except json.JSONDecodeError:
        print("[Vision] Failed to decode JSON:", content[:100])
        ingredients_list = []

    # Map directly into the identical bounding box dictionary expected by existing routers
    results = []
    for ing in ingredients_list:
        results.append({
            "text": str(ing),
            "bounding_box": [
                {"x": 0, "y": 0}, {"x": 100, "y": 0}, {"x": 100, "y": 100}, {"x": 0, "y": 100}
            ]
        })
        
    return results
