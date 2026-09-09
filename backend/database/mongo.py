import logging
from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings

logger = logging.getLogger("fitmate.db")

class FallbackCursor:
    """Async cursor simulating Motor / MongoDB cursor for in-memory datasets."""
    def __init__(self, data):
        self._data = list(data)

    def skip(self, n: int):
        self._data = self._data[n:]
        return self

    def limit(self, n: int):
        self._data = self._data[:n]
        return self

    def sort(self, key: str, direction: int = 1):
        self._data = sorted(
            self._data,
            key=lambda x: str(x.get(key, "")),
            reverse=(direction < 0)
        )
        return self

    async def to_list(self, length: int = None):
        if length is not None:
            return self._data[:length]
        return self._data

    def __aiter__(self):
        self._iter = iter(self._data)
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration:
            raise StopAsyncIteration


class FallbackCollection:
    """Async collection simulating Motor collection methods."""
    def __init__(self, name: str, data: list):
        self.name = name
        self.data = list(data)

    async def count_documents(self, filter_query: dict = None) -> int:
        if not filter_query:
            return len(self.data)
        count = 0
        for doc in self.data:
            match = True
            for k, v in filter_query.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                count += 1
        return count

    def find(self, filter_query: dict = None, projection: dict = None):
        filtered = []
        for doc in self.data:
            match = True
            if filter_query:
                for k, v in filter_query.items():
                    if doc.get(k) != v:
                        match = False
                        break
            if match:
                if projection:
                    proj_doc = {}
                    for pk, pv in projection.items():
                        if pv and pk in doc:
                            proj_doc[pk] = doc[pk]
                    filtered.append(proj_doc)
                else:
                    filtered.append(dict(doc))
        return FallbackCursor(filtered)

    async def find_one(self, filter_query: dict = None) -> dict | None:
        for doc in self.data:
            match = True
            if filter_query:
                for k, v in filter_query.items():
                    if doc.get(k) != v:
                        match = False
                        break
            if match:
                return dict(doc)
        return None


class FallbackDatabase:
    """In-memory database preloaded with 100 TCM ingredients."""
    def __init__(self):
        tcm_data = []
        try:
            from database.seed_100_tcm import POPULAR_TCM
            for idx, item in enumerate(POPULAR_TCM, 1):
                mandarin, pinyin, indo, eng, is_toxic, tox_class, organ, desc, source = item
                tcm_data.append({
                    "_id": str(idx),
                    "mandarin_name": mandarin,
                    "pinyin_name": pinyin,
                    "indonesian_name": indo,
                    "english_name": eng,
                    "latin_name": indo if " " in indo else None,
                    "is_toxic": is_toxic,
                    "toxicity_level": tox_class,
                    "toxicity_class": "toxic" if is_toxic else tox_class,
                    "target_organ": organ,
                    "description": desc,
                    "source_reference": source,
                    "validated_by": "fitmate_verified"
                })
        except Exception as e:
            logger.warning(f"Could not load POPULAR_TCM into fallback: {e}")

        self._collections = {
            "tcm_ingredients": FallbackCollection("tcm_ingredients", tcm_data),
            "safety_rules": FallbackCollection("safety_rules", []),
            "scan_logs": FallbackCollection("scan_logs", []),
        }

    def __getitem__(self, name: str) -> FallbackCollection:
        if name not in self._collections:
            self._collections[name] = FallbackCollection(name, [])
        return self._collections[name]

    def __getattr__(self, name: str) -> FallbackCollection:
        return self[name]


class MongoDB:
    client: AsyncIOMotorClient = None
    is_fallback: bool = False
    fallback_db: FallbackDatabase = None

db = MongoDB()
db.fallback_db = FallbackDatabase()

async def connect_to_mongo():
    try:
        # Connect with a strict 3-second server selection timeout
        client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            serverSelectionTimeoutMS=3000,
            connectTimeoutMS=3000
        )
        database = client[settings.MONGODB_DB_NAME]
        count = await database["tcm_ingredients"].count_documents({})
        db.client = client
        db.is_fallback = False
        print(f"[DB] Connected to MongoDB — {count} ingredients in tcm_ingredients")
    except Exception as e:
        db.client = None
        db.is_fallback = True
        total_fallback = await db.fallback_db["tcm_ingredients"].count_documents({})
        print(
            f"[DB] Remote MongoDB unreachable ({e.__class__.__name__}).\n"
            f"   Active: In-Memory Resilient Fallback Store ({total_fallback} validated TCM ingredients loaded)."
        )

async def close_mongo_connection():
    if db.client:
        db.client.close()

def get_db():
    if db.is_fallback or not db.client:
        return db.fallback_db
    try:
        return db.client[settings.MONGODB_DB_NAME]
    except Exception:
        return db.fallback_db
