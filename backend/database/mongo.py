import os
from motor.motor_asyncio import AsyncIOMotorClient

class MongoDB:
    client: AsyncIOMotorClient = None

db = MongoDB()

async def connect_to_mongo():
    uri = os.environ.get("MONGODB_URL", "mongodb://admin:REDACTED@localhost:27017/fitmate_db?authSource=admin")
    db.client = AsyncIOMotorClient(uri)

async def close_mongo_connection():
    if db.client:
        db.client.close()

def get_db():
    db_name = os.environ.get("MONGODB_DB_NAME", "fitmate_db")
    return db.client[db_name]
