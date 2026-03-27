from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings


class MongoDB:
    client: AsyncIOMotorClient = None


db = MongoDB()


async def connect_to_mongo():
    db.client = AsyncIOMotorClient(settings.MONGODB_URL)
    
    # Verify connection and warn if tcm_ingredients is empty (seed not run)
    try:
        database = db.client[settings.MONGODB_DB_NAME]
        count = await database["tcm_ingredients"].count_documents({})
        if count == 0:
            print(
                "⚠️  [DB] WARNING: tcm_ingredients collection is EMPTY!\n"
                "   The WhatsApp bot and safety scanner won't find any ingredients.\n"
                "   Run: python database/seed_100_tcm.py  to populate the database."
            )
        else:
            print(f"✅ [DB] Connected to MongoDB — {count} ingredients in tcm_ingredients")
    except Exception as e:
        print(f"⚠️  [DB] Could not verify collection count: {e}")


async def close_mongo_connection():
    if db.client:
        db.client.close()


def get_db():
    return db.client[settings.MONGODB_DB_NAME]
