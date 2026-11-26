import re

from database.ingredient_repository import ingredient_repository
from thefuzz import fuzz, process

# Everyday culinary staple words may appear on non-herbal food packaging
# (e.g., "Krekers Beras Rasa Asin"); require exact or Latin/Mandarin match rather than substring hit.
_FOOD_STAPLE_EXACT_ONLY_KEYS = frozenset({
    "beras",
    "rice",
    "gula",
    "sugar",
    "garam",
    "salt",
    "air",
    "water",
    "tepung",
    "flour",
    "minyak",
    "oil",
    "susu",
    "milk",
    "telur",
    "egg",
    "madu",
    "honey",
    "teh",
    "tea",
    "kopi",
    "coffee",
    "jagung",
    "corn",
    "kedelai",
    "soy",
})


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

    lookup_keys = await ingredient_repository.get_lookup_keys(db)

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

        # 2. Substring (CJK) / strict word-boundary (Latin/ID/EN) scan — collect ALL distinct matched items
        matched_items: list[dict] = []
        seen_item_keys: set[tuple[str, str, str]] = set()
        for name_key, item in lookup_keys.items():
            if name_key in _FOOD_STAPLE_EXACT_ONLY_KEYS:
                continue
            is_cjk = bool(re.search(r"[\u4e00-\u9fff]", name_key))
            is_match = False
            if is_cjk:
                if name_key in lower_text or (len(lower_text) >= 4 and lower_text in name_key):
                    is_match = True
            elif len(name_key) >= 3:
                p1 = r"(?:\b|^)" + re.escape(name_key) + r"(?:\b|$)"
                p2 = r"(?:\b|^)" + re.escape(lower_text) + r"(?:\b|$)"
                if re.search(p1, lower_text) or (len(lower_text) >= 4 and re.search(p2, name_key)):
                    is_match = True

            if is_match:
                canonical_key = (
                    str(item.get("mandarin_name") or ""),
                    str(item.get("indonesian_name") or ""),
                    str(item.get("latin_name") or ""),
                )
                if canonical_key not in seen_item_keys:
                    seen_item_keys.add(canonical_key)
                    matched_items.append(item)

        if matched_items:
            for matched_item in matched_items:
                _categorize_item(matched_item, raw_text, results, 95)
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

    if item.get("target_organ"):
        payload["target_organ"] = item["target_organ"]

    if is_toxic or severity in ("toxic", "highly_toxic", "high", "moderate"):
        results["toxic"].append(payload)
    elif severity == "contraindicated":
        results["contraindicated"].append(payload)
    else:
        results["safe"].append(payload)
