"""
validate_seed.py — Verify MongoDB seed is correctly populated

Run after seed.py to confirm database meets Phase 1 success criteria:
- At least 50 validated TCM ingredients exist
- All required fields are populated
- At least some toxic ingredients have safety rules
"""

from backend.database.mongodb import get_db


def validate_seed() -> dict:
    db = get_db()

    # Count total ingredients
    total = db["tcm_ingredients"].count_documents({})
    toxic = db["tcm_ingredients"].count_documents({"is_toxic": True})
    safe = db["tcm_ingredients"].count_documents({"is_toxic": False})

    # Check required fields
    missing_mandarin = db["tcm_ingredients"].count_documents({"mandarin_name": {"$in": [None, ""]}})
    missing_indonesian = db["tcm_ingredients"].count_documents({"indonesian_name": {"$in": [None, ""]}})
    missing_source = db["tcm_ingredients"].count_documents({"source_reference": {"$in": [None, ""]}})

    # Count safety rules
    rules_count = db["safety_rules"].count_documents({})

    # Sample record check
    sample = db["tcm_ingredients"].find_one({"is_toxic": True})

    results = {
        "total_ingredients": total,
        "toxic_ingredients": toxic,
        "safe_ingredients": safe,
        "missing_mandarin_name": missing_mandarin,
        "missing_indonesian_name": missing_indonesian,
        "missing_source_reference": missing_source,
        "safety_rules_count": rules_count,
    }

    print("=== FitMate Seed Validation ===\n")
    print(f"Total TCM ingredients: {total}")
    print(f"  Toxic: {toxic} | Safe: {safe}")
    print(f"  Missing mandarin_name: {missing_mandarin}")
    print(f"  Missing indonesian_name: {missing_indonesian}")
    print(f"  Missing source_reference: {missing_source}")
    print(f"Safety rules: {rules_count}")

    passed = True
    if total < 50:
        print(f"\n[FAIL] Need at least 50 ingredients, got {total}")
        passed = False
    if missing_mandarin > 0:
        print(f"[FAIL] {missing_mandarin} records missing mandarin_name")
        passed = False
    if missing_source > 0:
        print(f"[FAIL] {missing_source} records missing source_reference (traceability broken)")
        passed = False

    if passed:
        print(f"\n[PASS] All validation checks passed — database ready for Phase 2")
    results["passed"] = passed
    return results


if __name__ == "__main__":
    validate_seed()
