"""
seed.py — Seed MongoDB from validated pharmacist Excel

Reads validated/tcm_validated.xlsx and inserts records into MongoDB.
All records are validated via Pydantic schemas before insertion.
Records failing validation are logged to output/seed_errors.json — NOT inserted.

Usage: python -m backend.database.seed
Requires: MONGODB_URL env var or default localhost connection
"""

import pandas as pd
import json
import os
from pathlib import Path
from datetime import datetime
from pydantic import ValidationError
from backend.database.mongodb import get_db, create_indexes
from backend.database.schemas import TCMIngredient

VALIDATED_EXCEL = Path(__file__).parent.parent.parent / "data" / "scraper" / "validated" / "tcm_validated.xlsx"
ERRORS_LOG = Path(__file__).parent.parent.parent / "data" / "scraper" / "output" / "seed_errors.json"

# Column mapping from Excel headers to schema fields
COLUMN_MAP = {
    "Mandarin Name (锁定)": "mandarin_name",
    "Pinyin Name": "pinyin_name",
    "Latin/Scientific Name": "latin_name",
    "Indonesian Name ← VERIFY": "indonesian_name",
    "Is Toxic? (TRUE/FALSE) ← DECIDE": "is_toxic",
    "Target Organ ← SELECT": "target_organ",
    "Toxicity Level ← SELECT": "toxicity_level",
    "Warning Message (Indonesian) ← WRITE": "medical_advice_preview",
    "Source (SymMap ID / BPOM ref)": "source_reference",
    "Validated? (TRUE when done) ← CHECK": "validated",
}


def load_validated_excel() -> pd.DataFrame:
    if not VALIDATED_EXCEL.exists():
        raise FileNotFoundError(
            f"Validated Excel not found at {VALIDATED_EXCEL}\n"
            "Please run data/scraper/export_excel.py and have pharmacy team complete validation."
        )
    df = pd.read_excel(VALIDATED_EXCEL, engine="openpyxl")
    print(f"[load] Read {len(df)} rows from {VALIDATED_EXCEL.name}")
    return df


def seed_ingredients(df: pd.DataFrame) -> dict:
    """Seed tcm_ingredients collection from validated DataFrame."""
    db = get_db()
    collection = db["tcm_ingredients"]

    inserted = 0
    skipped_validation = 0
    skipped_unvalidated = 0
    errors = []

    for idx, row in df.iterrows():
        # Skip rows not marked as validated
        validated_flag = row.get("Validated? (TRUE when done) ← CHECK", False)
        if str(validated_flag).upper() not in ("TRUE", "1", "YES"):
            skipped_unvalidated += 1
            continue

        # Build ingredient dict
        record = {
            "mandarin_name": str(row.get("Mandarin Name (锁定)", "")).strip(),
            "pinyin_name": str(row.get("Pinyin Name", "")).strip() or None,
            "latin_name": str(row.get("Latin/Scientific Name", "")).strip() or None,
            "indonesian_name": str(row.get("Indonesian Name ← VERIFY", "")).strip(),
            "is_toxic": str(row.get("Is Toxic? (TRUE/FALSE) ← DECIDE", "FALSE")).upper() == "TRUE",
            "target_organ": str(row.get("Target Organ ← SELECT", "")).strip() or None,
            "toxicity_level": str(row.get("Toxicity Level ← SELECT", "unknown")).strip().lower(),
            "source_reference": str(row.get("Source (SymMap ID / BPOM ref)", "")).strip(),
        }

        # Validate via Pydantic schema
        try:
            ingredient = TCMIngredient(**record)
            # Upsert by mandarin_name to avoid duplicates
            collection.update_one(
                {"mandarin_name": ingredient.mandarin_name},
                {"$set": ingredient.model_dump()},
                upsert=True,
            )
            inserted += 1
        except ValidationError as e:
            skipped_validation += 1
            errors.append({"row": idx + 2, "data": record, "error": str(e)})

    # Log errors for pharmacy team review
    if errors:
        with open(ERRORS_LOG, "w", encoding="utf-8") as f:
            json.dump(errors, f, ensure_ascii=False, indent=2)
        print(f"[warn] {skipped_validation} records failed validation → {ERRORS_LOG.name}")

    return {
        "inserted": inserted,
        "skipped_unvalidated": skipped_unvalidated,
        "skipped_validation_errors": skipped_validation,
        "total": len(df),
    }


def main():
    print("=== FitMate MongoDB Seeder ===\n")
    print("[init] Creating indexes...")
    create_indexes()

    print("[load] Loading validated Excel...")
    df = load_validated_excel()

    print("[seed] Inserting ingredients...")
    result = seed_ingredients(df)

    print(f"\n=== Seed Complete ===")
    print(f"  Inserted/updated: {result['inserted']}")
    print(f"  Skipped (not validated): {result['skipped_unvalidated']}")
    print(f"  Skipped (validation errors): {result['skipped_validation_errors']}")
    print(f"  Total rows in Excel: {result['total']}")

    if result["inserted"] < 50:
        print(f"\n[warn] Only {result['inserted']} records seeded. Target is 50+.")
        print("  → Check that pharmacy team marked 'Validated? = TRUE' for reviewed rows")
        print("  → Check seed_errors.json for validation failures")
    else:
        print(f"\n[ok] Database ready with {result['inserted']} TCM ingredients")


if __name__ == "__main__":
    main()
