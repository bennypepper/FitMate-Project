import re
from thefuzz import process, fuzz

async def match_ingredients(detected_texts: list[str], db) -> dict:
    """
    Cross-references OCR text with MongoDB toxicity database using fuzzy matching.
    Groups results by severity level.
    """
    
    results = {
        "toxic": [],
        "contraindicated": [],
        "safe": [],
        "unknown": []
    }
    
    # FIX: correct collection name is 'tcm_ingredients', not 'ingredients'
    cursor = db["tcm_ingredients"].find({})
    ingredients = await cursor.to_list(length=1000)
    
    # Create lookup dictionaries
    mandarin_names = {item['mandarin_name']: item for item in ingredients if 'mandarin_name' in item}
    
    # Track which texts have been matched to avoid duplicate unknowns
    matched_texts = set()
    
    # --- Pass 1: substring scan for Mandarin ingredient names in each OCR block ---
    # This catches cases like '草药' appearing inside '60kapsul/粒@草药/500mg'
    for ingredient_name, item in mandarin_names.items():
        if not ingredient_name:
            continue
        for text in detected_texts:
            if ingredient_name in text:
                _categorize_item(item, text, results, 100)
                matched_texts.add(text)
    
    # --- Pass 2: exact + fuzzy match for remaining unmatched texts ---
    for text in detected_texts:
        if not text.strip():
            continue

        # Skip texts already matched in the substring pass
        if text in matched_texts:
            continue

        # 1. Exact Match first
        if text in mandarin_names:
            matched_item = mandarin_names[text]
            _categorize_item(matched_item, text, results, 100)
            matched_texts.add(text)
            continue

        # 2. Fuzzy Match (partial_ratio handles short CJK strings better)
        best_match = process.extractOne(text, list(mandarin_names.keys()), scorer=fuzz.partial_ratio)

        if best_match and best_match[1] > 80:  # Threshold 80
            matched_item = mandarin_names[best_match[0]]
            _categorize_item(matched_item, text, results, best_match[1])
        else:
            results["unknown"].append({"detected_text": text, "match_score": 0})

    return results

def _categorize_item(item, detected_text, results, score):
    severity = item.get("toxicity_class", "safe").lower()
    
    payload = {
        "detected_text": detected_text,
        "matched_mandarin": item.get("mandarin_name"),
        "indonesian_name": item.get("indonesian_name"),
        "match_score": score,
        "risk_level": item.get("risk_level", "low")
    }
    
    if "target_organ" in item:
        payload["target_organ"] = item["target_organ"]
        
    if "effects" in item:
        payload["effects"] = item["effects"]
        
    if severity == "toxic" or severity == "highly_toxic":
        results["toxic"].append(payload)
    elif severity == "contraindicated":
        results["contraindicated"].append(payload)
    else:
        results["safe"].append(payload)
