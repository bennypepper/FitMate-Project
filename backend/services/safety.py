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
    
    # In a real app, this should probably cache the DB collection or load chunks.
    # For prototype, we'll fetch all ingredients (assuming reasonably small dataset)
    # or query specifically. Since we need fuzzy match, loading names helps.
    
    cursor = db.ingredients.find({})
    ingredients = await cursor.to_list(length=1000)
    
    # Create lookup dictionaries
    mandarin_names = {item['mandarin_name']: item for item in ingredients if 'mandarin_name' in item}
    
    for text in detected_texts:
        if not text.strip():
            continue
            
        # 1. Exact Match first
        if text in mandarin_names:
            matched_item = mandarin_names[text]
            _categorize_item(matched_item, text, results, 100)
            continue
            
        # 2. Fuzzy Match
        # process.extractOne returns a tuple: (matched_string, score)
        best_match = process.extractOne(text, list(mandarin_names.keys()), scorer=fuzz.token_sort_ratio)
        
        if best_match and best_match[1] > 80: # Threshold 80
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
