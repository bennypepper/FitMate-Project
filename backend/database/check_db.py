import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def check():
    client = AsyncIOMotorClient(os.getenv("MONGODB_URL", "mongodb://localhost:27017"))
    db = client.get_database(os.getenv("MONGODB_DB_NAME", "fitmate_db"))
    c = await db["tcm_ingredients"].count_documents({})
    print(f"Total documents: {c}")

if __name__ == "__main__":
    asyncio.run(check())
