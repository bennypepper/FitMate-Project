import os
from motor.motor_asyncio import AsyncIOMotorClient

# Load .env explicitly so os.environ picks it up (pydantic-settings does this
# automatically, but bare os.environ.get() calls do not).
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed; rely on env vars set in the shell

class MongoDB:
    client: AsyncIOMotorClient = None

db = MongoDB()

async def connect_to_mongo():
    # Safe no-auth fallback matches the local dev .env default
    uri = os.environ.get("MONGODB_URL", "mongodb://localhost:27017")
    db.client = AsyncIOMotorClient(uri)

async def close_mongo_connection():
    if db.client:
        db.client.close()

def get_db():
    db_name = os.environ.get("MONGODB_DB_NAME", "fitmate_db")
    return db.client[db_name]
