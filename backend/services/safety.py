import re
from thefuzz import process, fuzz

async def match_ingredients(detected_texts: list[str], db) -> dict:
    """
    Cross-references OCR text with TCM toxicity database using fuzzy and substring matching
    across Mandarin, Indonesian, English, Pinyin, and Latin names.
    Groups results by severity level: toxic, contraindicated, safe, unknown.
    """
    results = {
        "toxic": [],
        "contraindicated": [],
        "safe": [],
        "unknown": []
    }

    cursor = db["tcm_ingredients"].find({})
    ingredients = await cursor.to_list(length=1000)

    # Build lookup index across all available names
    lookup_keys = {}
    for item in ingredients:
        for field in ["mandarin_name", "pinyin_name", "indonesian_name", "english_name", "latin_name"]:
            val = item.get(field)
            if val and isinstance(val, str):
                cleaned = val.strip().lower()
                if cleaned and cleaned not in ("-", "unknown", "none"):
                    lookup_keys[cleaned] = item

    matched_texts = set()

    for text in detected_texts:
        if not text or not text.strip():
            continue

        raw_text = text.strip()
        lower_text = raw_text.lower()

        # 1. Exact or direct match
        if lower_text in lookup_keys:
            _categorize_item(lookup_keys[lower_text], raw_text, results, 100)
            matched_texts.add(raw_text)
            continue

        # 2. Substring matching (both directions)
        matched_item = None
        matched_score = 0
        for name_key, item in lookup_keys.items():
            if len(name_key) >= 2 and (name_key in lower_text or (len(lower_text) >= 3 and lower_text in name_key)):
                matched_item = item
                matched_score = 95
                break

        if matched_item:
            _categorize_item(matched_item, raw_text, results, matched_score)
            matched_texts.add(raw_text)
            continue

        # 3. Fuzzy ratio matching against all known names
        best_match = process.extractOne(lower_text, list(lookup_keys.keys()), scorer=fuzz.partial_ratio)
        if best_match and best_match[1] >= 82:
            matched_item = lookup_keys[best_match[0]]
            _categorize_item(matched_item, raw_text, results, best_match[1])
            matched_texts.add(raw_text)
        else:
            results["unknown"].append({"detected_text": raw_text, "match_score": 0})

    return results

def _categorize_item(item, detected_text: str, results: dict, score: int):
    severity = str(item.get("toxicity_class", item.get("toxicity_level", "safe"))).lower()
    is_toxic = bool(item.get("is_toxic", False))

    payload = {
        "detected_text": detected_text,
        "matched_mandarin": item.get("mandarin_name"),
        "indonesian_name": item.get("indonesian_name"),
        "english_name": item.get("english_name"),
        "match_score": score,
        "is_toxic": is_toxic or severity in ("toxic", "highly_toxic", "high", "moderate"),
        "risk_level": item.get("toxicity_level", item.get("risk_level", "low")),
        "description": item.get("description", ""),
        "source_reference": item.get("source_reference", "")
    }

    if "target_organ" in item and item["target_organ"]:
        payload["target_organ"] = item["target_organ"]

    if is_toxic or severity in ("toxic", "highly_toxic", "high"):
        results["toxic"].append(payload)
    elif severity == "contraindicated":
        results["contraindicated"].append(payload)
    else:
        results["safe"].append(payload)
