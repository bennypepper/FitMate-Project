"""
mongodb.py — MongoDB connection and collection access for FitMate

Uses pymongo (sync) for seed scripts. Motor (async) will wrap this for FastAPI.
"""

import os
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

# Load .env so os.getenv picks up MONGODB_URL correctly
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "fitmate_db")


def get_db() -> Database:
    """Get synchronous MongoDB database instance."""
    client = MongoClient(MONGODB_URL)
    return client[MONGODB_DB_NAME]


def get_collection(collection_name: str) -> Collection:
    """Get a specific collection from the database."""
    db = get_db()
    return db[collection_name]


def create_indexes():
    """Create MongoDB indexes for performance. Run once during setup."""
    db = get_db()

    # tcm_ingredients indexes
    db["tcm_ingredients"].create_index("mandarin_name")
    db["tcm_ingredients"].create_index("indonesian_name")
    db["tcm_ingredients"].create_index("latin_name")
    db["tcm_ingredients"].create_index([("mandarin_name", "text"), ("indonesian_name", "text")])

    # safety_rules indexes
    db["safety_rules"].create_index("ingredient_id")
    db["safety_rules"].create_index("condition_logic")

    # scan_logs indexes
    db["scan_logs"].create_index("scanned_at")
    db["scan_logs"].create_index("warning_triggered")

    print("[ok] MongoDB indexes created")
