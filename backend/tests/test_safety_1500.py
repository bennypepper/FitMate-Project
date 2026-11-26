"""
test_safety_1500.py — Unit and integration tests for the 1,500-entry TCM database,
repository, life-safety scanner, upload upsert logic, seed validation, and MongoDB sync CLI.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path

from bson import ObjectId

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


# ---------------------------------------------------------------------------
# 1. FallbackDatabase & FallbackCollection Tests
# ---------------------------------------------------------------------------


def test_fallback_database_loads_1500_records():
    from database.mongo import FallbackDatabase

    fb = FallbackDatabase()
    count = asyncio.run(fb["tcm_ingredients"].count_documents({}))
    assert count == 1500


def test_fallback_collection_update_one_sets_upserted_id():
    from database.mongo import FallbackCollection

    async def _run():
        col = FallbackCollection(
            "tcm_ingredients",
            [{"_id": "1", "mandarin_name": "人参", "indonesian_name": "Ginseng"}],
        )

        update_res = await col.update_one(
            {"mandarin_name": "人参"},
            {"$set": {"indonesian_name": "Panax Ginseng"}},
            upsert=True,
        )
        assert update_res.matched_count == 1
        assert update_res.upserted_id is None

        upsert_res = await col.update_one(
            {"mandarin_name": "附子"},
            {"$set": {"mandarin_name": "附子", "indonesian_name": "Aconite"}},
            upsert=True,
        )
        assert upsert_res.matched_count == 0
        assert upsert_res.upserted_id is not None
        assert isinstance(upsert_res.upserted_id, str)

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# 2. IngredientRepository Tests
# ---------------------------------------------------------------------------


def test_repository_get_all_and_search_stringify_object_ids():
    from database.ingredient_repository import IngredientRepository

    class _FakeCursor:
        def __init__(self, docs):
            self._docs = docs
            self.last_length = "UNSET"

        async def to_list(self, length=None):
            self.last_length = length
            return list(self._docs)

    oid = ObjectId()
    cursor = _FakeCursor([
        {
            "_id": oid,
            "mandarin_name": "人参",
            "pinyin_name": "Ren Shen",
            "indonesian_name": "Panax Ginseng",
            "english_name": "Asian Ginseng",
            "latin_name": "Panax ginseng",
            "is_toxic": False,
        }
    ])

    class _FakeCollection:
        def find(self, query):
            return cursor

    fake_db = {"tcm_ingredients": _FakeCollection()}
    repo = IngredientRepository()

    async def _run():
        all_items = await repo.get_all_ingredients(fake_db)
        assert cursor.last_length is None, "get_all_ingredients must not truncate with length=3000"
        assert len(all_items) == 1
        assert isinstance(all_items[0]["_id"], str)
        assert all_items[0]["_id"] == str(oid)

        search_results = await repo.search_ingredients("ginseng", fake_db, limit=5)
        assert len(search_results) == 1
        assert isinstance(search_results[0]["_id"], str)
        serialized = json.dumps(search_results)
        assert str(oid) in serialized

    asyncio.run(_run())


def test_repository_admin_list_pagination_across_1500_and_zero_guards():
    from database.ingredient_repository import IngredientRepository
    from database.mongo import FallbackDatabase

    fb = FallbackDatabase()
    repo = IngredientRepository()

    async def _run():
        items, total, pages = await repo.admin_list(fb, page=1, limit=50)
        assert total == 1500
        assert pages == 30
        assert len(items) == 50
        assert all(isinstance(it["_id"], str) for it in items)

        # Guard against limit=0 / page=0 ZeroDivisionError
        items_guard, total_guard, pages_guard = await repo.admin_list(fb, page=0, limit=0)
        assert total_guard == 1500
        assert pages_guard == 1500
        assert len(items_guard) == 1

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# 3. Life-Safety Scanner (services/safety.py) Tests
# ---------------------------------------------------------------------------


def test_safety_catches_perbpom_and_symmap_dadu_herbs():
    from database.ingredient_repository import ingredient_repository
    from database.mongo import FallbackDatabase
    from services.safety import match_ingredients

    fb = FallbackDatabase()
    ingredient_repository.invalidate_cache()

    async def _run():
        for herb in ("草乌", "马兜铃", "麻黄", "黄连", "闹羊花", "天仙子"):
            res = await match_ingredients([herb], fb)
            assert len(res["toxic"]) >= 1, f"Expected {herb} to be flagged toxic, got: {res}"
            assert res["meta"]["classification"] == "toxic"

    asyncio.run(_run())


def test_safety_catches_compound_hanzi_without_word_boundary_bug():
    from database.ingredient_repository import ingredient_repository
    from database.mongo import FallbackDatabase
    from services.safety import match_ingredients

    fb = FallbackDatabase()
    ingredient_repository.invalidate_cache()

    async def _run():
        res = await match_ingredients(["制附子"], fb)
        assert len(res["toxic"]) >= 1, f"Expected compound Hanzi '制附子' to match '附子' as toxic, got: {res}"
        assert any(item["matched_mandarin"] == "附子" for item in res["toxic"])

    asyncio.run(_run())


def test_safety_multi_herb_ocr_block_catches_both_safe_and_toxic():
    from database.ingredient_repository import ingredient_repository
    from database.mongo import FallbackDatabase
    from services.safety import match_ingredients

    fb = FallbackDatabase()
    ingredient_repository.invalidate_cache()

    async def _run():
        res = await match_ingredients(["Panax Ginseng, Aristolochia, 马兜铃"], fb)
        assert len(res["toxic"]) >= 1, f"Expected toxic herb 马兜铃 in multi-herb OCR block, got: {res}"
        assert any(item["matched_mandarin"] == "马兜铃" for item in res["toxic"])
        assert len(res["safe"]) >= 1, f"Expected safe herb Ginseng also detected in multi-herb OCR block, got: {res}"
        assert res["meta"]["classification"] == "toxic"

    asyncio.run(_run())


def test_safety_routes_moderate_severity_to_toxic_not_safe():
    from database.ingredient_repository import ingredient_repository
    from database.mongo import FallbackCollection
    from services.safety import match_ingredients

    col = FallbackCollection(
        "tcm_ingredients",
        [
            {
                "_id": "mod-1",
                "mandarin_name": "测试中度毒草",
                "pinyin_name": "Ce Shi Moderate",
                "indonesian_name": "Herba Toksik Sedang",
                "english_name": "Moderate Herb",
                "latin_name": "Testus moderatus",
                "is_toxic": False,
                "toxicity_level": "moderate",
                "toxicity_class": "moderate",
                "description": "Test moderate severity routing",
                "source_reference": "PerBPOM-Test",
            }
        ],
    )
    fake_db = {"tcm_ingredients": col}
    ingredient_repository.invalidate_cache()

    async def _run():
        try:
            res = await match_ingredients(["测试中度毒草"], fake_db)
            assert len(res["toxic"]) == 1, f"Expected 'moderate' severity routed to results['toxic'], got: {res}"
            assert len(res["safe"]) == 0
            assert res["toxic"][0]["is_toxic"] is True
        finally:
            ingredient_repository.invalidate_cache()

    asyncio.run(_run())


def test_lookup_key_collision_never_shadows_toxic_entry():
    from database.ingredient_repository import ingredient_repository
    from database.mongo import FallbackDatabase
    from services.safety import match_ingredients

    fb = FallbackDatabase()
    ingredient_repository.invalidate_cache()

    async def _run():
        res = await match_ingredients(["Ginkgo Biloba"], fb)
        assert len(res["toxic"]) >= 1, f"Expected toxic Ginkgo seed (白果) not shadowed by safe alias, got: {res}"
        assert res["meta"]["classification"] == "toxic"

    asyncio.run(_run())


def test_non_herbal_food_packaging_not_falsely_flagged_as_herbal():
    from database.ingredient_repository import ingredient_repository
    from database.mongo import FallbackDatabase
    from services.safety import match_ingredients

    fb = FallbackDatabase()
    ingredient_repository.invalidate_cache()

    async def _run():
        res = await match_ingredients(["Naraya Rice Crackers", "Krekers Beras Rasa Asin"], fb)
        assert res["meta"]["is_herbal_product"] is False
        assert res["meta"]["classification"] == "non_herbal"
        assert len(res["toxic"]) == 0
        assert len(res["safe"]) == 0
        assert len(res["unknown"]) == 2

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# 4. Upload Upsert Compound Key Tests
# ---------------------------------------------------------------------------


def test_upload_upsert_filter_uses_compound_key_for_non_mandarin_herbs():
    from routers.upload import build_upsert_filter

    tcm_doc = {"mandarin_name": "附子", "indonesian_name": "Aconite", "latin_name": "Aconitum carmichaelii"}
    assert build_upsert_filter(tcm_doc) == {"mandarin_name": "附子"}

    bpom_doc_1 = {"mandarin_name": "", "indonesian_name": "Temulawak", "latin_name": "Curcuma xanthorrhiza"}
    bpom_doc_2 = {"mandarin_name": "", "indonesian_name": "Jahe", "latin_name": "Zingiber officinale"}
    f1 = build_upsert_filter(bpom_doc_1)
    f2 = build_upsert_filter(bpom_doc_2)
    assert f1 == {"indonesian_name": "Temulawak", "latin_name": "Curcuma xanthorrhiza"}
    assert f2 == {"indonesian_name": "Jahe", "latin_name": "Zingiber officinale"}
    assert f1 != f2


# ---------------------------------------------------------------------------
# 5. sync_mongodb.py --dry-run CLI Test
# ---------------------------------------------------------------------------


def test_sync_mongodb_dry_run_validates_1500_records():
    proc = subprocess.run(
        [sys.executable, "-m", "database.sync_mongodb", "--dry-run"],
        cwd=str(BACKEND_DIR),
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert proc.returncode == 0, f"sync_mongodb --dry-run failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    assert "1500" in proc.stdout
