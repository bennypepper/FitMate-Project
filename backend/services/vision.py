import os
import base64
import json
import httpx
from core.config import settings

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"


async def extract_and_translate_text(image_bytes: bytes) -> list[dict]:
    """
    Extracts TCM ingredient names from an image using a multimodal LLM via OpenRouter.

    Returns a list of dicts: [{"text": <ingredient_name>, "bounding_box": [...]}, ...]
    Returns an empty list (not an exception) when no ingredients are found.
    """
    if os.environ.get("MOCK_VISION_API", "false").lower() == "true":
        return [
            {"text": "人参", "bounding_box": [{"x": 10, "y": 10}, {"x": 50, "y": 10}, {"x": 50, "y": 30}, {"x": 10, "y": 30}]},
            {"text": "当归", "bounding_box": [{"x": 10, "y": 40}, {"x": 50, "y": 40}, {"x": 50, "y": 60}, {"x": 10, "y": 60}]},
        ]

    # Convert image to base64
    b64_img = base64.b64encode(image_bytes).decode("utf-8")

    # Detect media type from magic bytes
    media_type = "image/jpeg"
    if image_bytes[:4] == b"\x89PNG":
        media_type = "image/png"
    elif image_bytes[:6] in (b"GIF87a", b"GIF89a"):
        media_type = "image/gif"
    elif image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
        media_type = "image/webp"

    prompt = (
        "You are a TCM (Traditional Chinese Medicine) ingredient extractor. "
        "Look at this product label image and extract ALL ingredient names listed in the composition section. "
        "Include Chinese (Hanzi), Pinyin, Latin, Indonesian, and English names if visible. "
        "Return ONLY a JSON array of strings — one ingredient per string. "
        "Example: [\"Ginseng\", \"当归\", \"Radix Astragali\", \"Lo Han Guo\"] "
        "If you cannot find any ingredients, return an empty array: [] "
        "Do NOT include markdown code fences, do NOT include any explanation."
    )

    payload = {
        "model": settings.OPENROUTER_OCR_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{b64_img}"}},
                ],
            }
        ],
        "temperature": 0.1,
    }

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_OCR_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://fitmate-tcm.vercel.app",
        "X-Title": "FitMate TCM Safety Scanner",
    }

    async with httpx.AsyncClient(timeout=45.0) as client:
        response = await client.post(OPENROUTER_BASE_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    # OpenRouter sometimes returns HTTP 200 with {"error": {...}} on upstream failures
    if "error" in data:
        error_msg = data["error"].get("message", "Unknown upstream error")
        print(f"[Vision] OpenRouter upstream error: {error_msg}")
        raise RuntimeError(f"Vision API upstream error: {error_msg}")

    # Guard: choices array might be missing if model returns empty
    choices = data.get("choices")
    if not choices:
        print("[Vision] No choices in OpenRouter response:", str(data)[:200])
        return []

    content = choices[0]["message"]["content"]
    if not content:
        print("[Vision] Empty content from model")
        return []

    # Strip any accidental markdown fences the model might add
    content = content.strip()
    for fence in ("```json", "```"):
        if content.startswith(fence):
            content = content[len(fence):]
        if content.endswith("```"):
            content = content[:-3]
    content = content.strip()

    try:
        ingredients_list = json.loads(content)
        if not isinstance(ingredients_list, list):
            print(f"[Vision] Expected list, got {type(ingredients_list).__name__}: {content[:100]}")
            ingredients_list = []
    except json.JSONDecodeError:
        print(f"[Vision] Failed to decode JSON from model response: {content[:200]}")
        ingredients_list = []

    # Map into the dict format expected by the routers
    results = []
    for ing in ingredients_list:
        if isinstance(ing, str) and ing.strip():
            results.append({
                "text": ing.strip(),
                "bounding_box": [
                    {"x": 0, "y": 0}, {"x": 100, "y": 0},
                    {"x": 100, "y": 100}, {"x": 0, "y": 100},
                ],
            })

    print(f"[Vision] Extracted {len(results)} ingredients from image")
    return results
