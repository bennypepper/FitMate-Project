"""
sync_mongodb.py — Idempotent CLI to validate and sync the 1,500-entry TCM/herbal
dataset into MongoDB via bulk_write upserts.

Usage (from backend/):
    python -m database.sync_mongodb --dry-run
    python -m database.sync_mongodb [--file path/to/tcm_1500_ingredients.json]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from database.schemas import TCMIngredient
from pydantic import ValidationError
from pymongo import MongoClient, UpdateOne
from pymongo.errors import PyMongoError

DEFAULT_DATA_FILE = Path(__file__).resolve().parent / "data" / "tcm_1500_ingredients.json"


def build_natural_key_filter(doc: dict) -> dict:
    """Return the compound natural key used for idempotent upserts."""
    mandarin = (doc.get("mandarin_name") or "").strip()
    if mandarin:
        return {"mandarin_name": mandarin}
    return {
        "indonesian_name": (doc.get("indonesian_name") or "").strip(),
        "latin_name": (doc.get("latin_name") or "").strip(),
    }


def load_and_validate_records(file_path: Path) -> list[dict]:
    """Load JSON records and validate every entry against TCMIngredient."""
    if not file_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {file_path}")

    raw_records = json.loads(file_path.read_text(encoding="utf-8"))
    if not isinstance(raw_records, list):
        raise TypeError(f"Expected a JSON array in {file_path}, got {type(raw_records).__name__}")

    validated: list[dict] = []
    errors: list[tuple[int, str, str]] = []

    for idx, record in enumerate(raw_records):
        try:
            model = TCMIngredient(**record)
            doc = model.model_dump()
            doc.pop("_id", None)
            validated.append(doc)
        except ValidationError as exc:
            errors.append((idx, str(record.get("indonesian_name", "<unknown>")), str(exc)))

    if errors:
        preview = "\n".join(f"  row {i} ({name}): {err}" for i, name, err in errors[:5])
        raise ValueError(
            f"Schema validation failed for {len(errors)}/{len(raw_records)} records:\n{preview}"
        )

    return validated


def sync_to_mongodb(file_path: Path, dry_run: bool = False) -> dict:
    """Validate dataset and optionally upsert all records into MongoDB."""
    validated_docs = load_and_validate_records(file_path)

    mandarin_keyed = sum(1 for d in validated_docs if (d.get("mandarin_name") or "").strip())
    compound_keyed = len(validated_docs) - mandarin_keyed

    print(
        f"[SYNC] Validated {len(validated_docs)}/{len(validated_docs)} records "
        f"({mandarin_keyed} mandarin-keyed, {compound_keyed} indonesian+latin-keyed) "
        f"from {file_path.name}."
    )

    if dry_run:
        print(
            f"[DRY-RUN] Plan: ensure indexes (mandarin_name, indonesian_name, latin_name) "
            f"and bulk-upsert {len(validated_docs)} records into tcm_ingredients. No DB writes performed."
        )
        return {
            "dry_run": True,
            "validated": len(validated_docs),
            "mandarin_keyed": mandarin_keyed,
            "compound_keyed": compound_keyed,
        }

    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    db_name = os.getenv("MONGODB_DB_NAME", "fitmate_db")

    client = MongoClient(
        mongodb_url,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
    )
    try:
        db = client[db_name]
        collection = db["tcm_ingredients"]

        collection.create_index("mandarin_name")
        collection.create_index("indonesian_name")
        collection.create_index("latin_name")

        operations = [
            UpdateOne(build_natural_key_filter(doc), {"$set": doc}, upsert=True)
            for doc in validated_docs
        ]
        result = collection.bulk_write(operations, ordered=False)
        total_in_collection = collection.count_documents({})

        print(
            f"[SYNC] MongoDB sync complete (db='{db_name}', collection='tcm_ingredients'): "
            f"matched={result.matched_count}, modified={result.modified_count}, "
            f"upserted={result.upserted_count}, total={total_in_collection}."
        )
        return {
            "dry_run": False,
            "validated": len(validated_docs),
            "matched": result.matched_count,
            "modified": result.modified_count,
            "upserted": result.upserted_count,
            "total": total_in_collection,
        }
    finally:
        client.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Idempotently validate and sync the FitMate 1,500-entry TCM dataset to MongoDB."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate all records and print the sync plan without connecting to MongoDB.",
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=DEFAULT_DATA_FILE,
        help=f"Path to dataset JSON file (default: {DEFAULT_DATA_FILE})",
    )
    args = parser.parse_args(argv)

    try:
        sync_to_mongodb(file_path=args.file, dry_run=args.dry_run)
        return 0
    except (OSError, ValueError, TypeError, PyMongoError) as exc:
        print(f"[SYNC ERROR] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
