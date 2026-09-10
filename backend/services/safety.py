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

        # 2. Strict word boundary check (Requires full word match, not loose partial letters)
        matched_item = None
        matched_score = 0
        for name_key, item in lookup_keys.items():
            if len(name_key) >= 3 or re.search(r'[\u4e00-\u9fff]', name_key):
                p1 = r'(?:\b|^)' + re.escape(name_key) + r'(?:\b|$)'
                p2 = r'(?:\b|^)' + re.escape(lower_text) + r'(?:\b|$)'
                if re.search(p1, lower_text) or (len(lower_text) >= 4 and re.search(p2, name_key)):
                    matched_item = item
                    matched_score = 95
                    break

        if matched_item:
            _categorize_item(matched_item, raw_text, results, matched_score)
            matched_texts.add(raw_text)
            continue

        # 3. Fuzzy token ratio matching (only for shorter text snippets)
        if len(lower_text) <= 35:
            best_match = process.extractOne(lower_text, list(lookup_keys.keys()), scorer=fuzz.token_sort_ratio)
            if best_match and best_match[1] >= 88:
                matched_item = lookup_keys[best_match[0]]
                _categorize_item(matched_item, raw_text, results, best_match[1])
                matched_texts.add(raw_text)
                continue

        results["unknown"].append({
            "detected_text": raw_text,
            "match_score": 0,
            "is_toxic": False,
            "is_herbal": False,
            "status_label": "Bukan Komposisi Herbal / Teks Kemasan Umum"
        })

    total_toxic = len(results["toxic"]) + len(results["contraindicated"])
    total_safe = len(results["safe"])
    total_unknown = len(results["unknown"])
    is_herbal = (total_toxic + total_safe) > 0

    results["meta"] = {
        "total_detected": len(detected_texts),
        "total_toxic": total_toxic,
        "total_safe": total_safe,
        "total_unknown": total_unknown,
        "is_herbal_product": is_herbal,
        "classification": "toxic" if total_toxic > 0 else ("safe" if total_safe > 0 else "non_herbal")
    }

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
