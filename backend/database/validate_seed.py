"""
validate_seed.py — Verify MongoDB seed is correctly populated for the 1,500-entry schema.

Confirms:
- At least 1,500 validated TCM & Indonesian herbal ingredients exist
- Zero records missing BOTH mandarin_name and latin_name
- Zero records missing indonesian_name or source_reference
"""

try:
    from database.mongodb import get_db
except ImportError:
    from backend.database.mongodb import get_db


def validate_seed() -> dict:
    db = get_db()
    col = db["tcm_ingredients"]

    total = col.count_documents({})
    toxic = col.count_documents({"is_toxic": True})
    safe = col.count_documents({"is_toxic": False})

    missing_both_identity = col.count_documents(
        {
            "$and": [
                {"mandarin_name": {"$in": [None, ""]}},
                {"latin_name": {"$in": [None, ""]}},
            ]
        }
    )
    missing_indonesian = col.count_documents({"indonesian_name": {"$in": [None, ""]}})
    missing_source = col.count_documents({"source_reference": {"$in": [None, ""]}})

    rules_count = db["safety_rules"].count_documents({})

    results = {
        "total_ingredients": total,
        "toxic_ingredients": toxic,
        "safe_ingredients": safe,
        "missing_both_mandarin_and_latin": missing_both_identity,
        "missing_indonesian_name": missing_indonesian,
        "missing_source_reference": missing_source,
        "safety_rules_count": rules_count,
    }

    print("=== FitMate 1,500-Entry Seed Validation ===\n")
    print(f"Total TCM & herbal ingredients: {total}")
    print(f"  Toxic: {toxic} | Safe: {safe}")
    print(f"  Missing BOTH mandarin_name & latin_name: {missing_both_identity}")
    print(f"  Missing indonesian_name: {missing_indonesian}")
    print(f"  Missing source_reference: {missing_source}")
    print(f"Safety rules: {rules_count}")

    passed = True
    if total < 1500:
        print(f"\n[FAIL] Need at least 1500 ingredients, got {total}")
        passed = False
    if missing_both_identity > 0:
        print(f"[FAIL] {missing_both_identity} records missing both mandarin_name and latin_name")
        passed = False
    if missing_indonesian > 0:
        print(f"[FAIL] {missing_indonesian} records missing indonesian_name")
        passed = False
    if missing_source > 0:
        print(f"[FAIL] {missing_source} records missing source_reference (traceability broken)")
        passed = False

    if passed:
        print("\n[PASS] All 1,500-entry validation checks passed.")
    results["passed"] = passed
    return results


if __name__ == "__main__":
    validate_seed()
