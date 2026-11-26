"""
test_dataset_1500.py — Comprehensive TDD validation suite for:
  1. TCMIngredient schema alignment & invariants (schemas.py)
  2. Excel/CSV parser None-guard, 'none' toxicity_level, and non-TCM herb support (excel_parser.py)
  3. Authoritative 1,500-ingredient dataset integrity, provenance, and life-safety recall
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

BACKEND_DATA_PATH = BACKEND_DIR / "database" / "data" / "tcm_1500_ingredients.json"
FRONTEND_DATA_PATH = REPO_ROOT / "frontend" / "src" / "data" / "tcmIngredients.json"
PROVENANCE_PATH = BACKEND_DIR / "database" / "data" / "dataset_provenance_summary.json"

SYNTHETIC_SM_RE = re.compile(r"\bSM0\d{3}\b")

ELEVEN_PERBPOM_FALSE_SAFE = [
    "草乌",
    "川乌",
    "马兜铃",
    "木通",
    "麻黄",
    "麻黄根",
    "黄连",
    "厚朴",
    "关黄柏",
    "黄柏",
    "贯叶金丝桃",
]

SEVEN_SYMMAP_DADU = [
    "闹羊花",
    "三分三",
    "天仙子",
    "马钱子粉",
    "巴豆霜",
    "水蛭",
    "红粉",
]

CORE_LETHAL_HERBS = [
    "附子",
    "马钱子",
    "朱砂",
    "雄黄",
    "巴豆",
    "雷公藤",
    "甘遂",
    "斑蝥",
    "蟾酥",
    "洋金花",
    "关木通",
    "广防己",
]


# ---------------------------------------------------------------------------
# 1. Schema Alignment Tests (backend/database/schemas.py)
# ---------------------------------------------------------------------------


def test_schema_accepts_non_tcm_indonesian_herb_with_empty_mandarin():
    from database.schemas import TCMIngredient

    item = TCMIngredient(
        mandarin_name="",
        latin_name="Curcuma xanthorrhiza",
        indonesian_name="Temulawak",
        is_toxic=False,
        toxicity_level="none",
        toxicity_class="safe",
        source_reference="BPOM-OTSKK-Klaim",
    )
    assert item.mandarin_name == ""
    assert item.toxicity_level == "none"
    assert item.toxicity_class == "safe"
    assert item.created_at.tzinfo is not None


def test_schema_rejects_toxic_with_none_toxicity_level():
    from database.schemas import TCMIngredient

    with pytest.raises(ValidationError):
        TCMIngredient(
            mandarin_name="附子",
            indonesian_name="Aconite",
            is_toxic=True,
            toxicity_level="none",
            toxicity_class="toxic",
            source_reference="SMHB00163",
        )


def test_schema_rejects_toxic_with_safe_toxicity_class():
    from database.schemas import TCMIngredient

    with pytest.raises(ValidationError):
        TCMIngredient(
            mandarin_name="附子",
            indonesian_name="Aconite",
            is_toxic=True,
            toxicity_level="high",
            toxicity_class="safe",
            source_reference="SMHB00163",
        )


def test_schema_rejects_safe_with_toxic_class():
    from database.schemas import TCMIngredient

    with pytest.raises(ValidationError):
        TCMIngredient(
            mandarin_name="人参",
            indonesian_name="Panax Ginseng",
            is_toxic=False,
            toxicity_level="none",
            toxicity_class="toxic",
            source_reference="SMHB00336",
        )


def test_schema_rejects_placeholder_source_reference():
    from database.schemas import TCMIngredient

    for bad_source in ("", "unknown", "none", "-"):
        with pytest.raises(ValidationError):
            TCMIngredient(
                mandarin_name="人参",
                indonesian_name="Panax Ginseng",
                is_toxic=False,
                toxicity_level="none",
                toxicity_class="safe",
                source_reference=bad_source,
            )


# ---------------------------------------------------------------------------
# 2. Excel Parser Alignment Tests (backend/utils/excel_parser.py)
# ---------------------------------------------------------------------------


def test_excel_parser_accepts_none_toxicity_level():
    from utils.excel_parser import normalize_row, validate_row

    row = {
        "mandarin_name": "人参",
        "pinyin_name": "Renshen",
        "latin_name": "Panax ginseng",
        "indonesian_name": "Panax Ginseng",
        "is_toxic": "false",
        "toxicity_level": "none",
        "source_reference": "SMHB00336",
    }
    assert validate_row(row, 2) == []
    normalized = normalize_row(row)
    assert normalized["toxicity_level"] == "none"


def test_excel_parser_guards_none_cells_from_becoming_literal_none():
    from utils.excel_parser import normalize_row

    row = {
        "mandarin_name": None,
        "pinyin_name": None,
        "latin_name": "Curcuma xanthorrhiza",
        "indonesian_name": "Temulawak",
        "english_name": None,
        "is_toxic": False,
        "target_organ": None,
        "toxicity_level": "none",
        "description": None,
        "source_reference": "BPOM-OTSKK-Klaim",
    }
    normalized = normalize_row(row)
    assert normalized["mandarin_name"] == ""
    assert normalized["pinyin_name"] is None
    assert normalized["english_name"] is None
    assert normalized["target_organ"] is None
    assert normalized["description"] is None


def test_excel_parser_allows_empty_mandarin_for_non_tcm_herb():
    from utils.excel_parser import validate_row

    row = {
        "mandarin_name": "",
        "pinyin_name": "",
        "latin_name": "Curcuma xanthorrhiza",
        "indonesian_name": "Temulawak",
        "is_toxic": "false",
        "toxicity_level": "none",
        "source_reference": "BPOM-OTSKK-Klaim",
    }
    assert validate_row(row, 2) == []


# ---------------------------------------------------------------------------
# 3. 1,500-Ingredient Dataset Validation Tests
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def dataset_1500() -> list[dict]:
    assert BACKEND_DATA_PATH.exists(), f"Missing canonical dataset: {BACKEND_DATA_PATH}"
    return json.loads(BACKEND_DATA_PATH.read_text(encoding="utf-8"))


def test_dataset_exact_count_is_1500(dataset_1500: list[dict]):
    assert len(dataset_1500) == 1500


def test_dataset_all_1500_records_pass_pydantic_schema(dataset_1500: list[dict]):
    from database.schemas import TCMIngredient

    failures = []
    for idx, rec in enumerate(dataset_1500):
        try:
            TCMIngredient(**rec)
        except ValidationError as exc:
            failures.append((idx, rec.get("indonesian_name"), str(exc)))
    assert failures == [], f"{len(failures)} schema validation errors; first 3: {failures[:3]}"


def test_backend_and_frontend_json_sha256_identical():
    assert BACKEND_DATA_PATH.exists()
    assert FRONTEND_DATA_PATH.exists()
    assert PROVENANCE_PATH.exists()

    backend_sha = hashlib.sha256(BACKEND_DATA_PATH.read_bytes()).hexdigest()
    frontend_sha = hashlib.sha256(FRONTEND_DATA_PATH.read_bytes()).hexdigest()
    assert backend_sha == frontend_sha

    provenance = json.loads(PROVENANCE_PATH.read_text(encoding="utf-8"))
    assert provenance["total_records"] == 1500
    assert provenance["sha256"] == backend_sha


def test_dataset_zero_synthetic_ids_placeholders_or_typos(dataset_1500: list[dict]):
    synthetic_hits = []
    dash_hits = []
    bad_sources = []
    pinyin_typos = []

    for idx, rec in enumerate(dataset_1500):
        src = (rec.get("source_reference") or "").strip()
        if not src or src.lower() in ("unknown", "none", "-", "n/a"):
            bad_sources.append((idx, rec.get("indonesian_name"), src))
        if SYNTHETIC_SM_RE.search(src):
            synthetic_hits.append((idx, rec.get("indonesian_name"), src))

        for field in ("mandarin_name", "pinyin_name", "indonesian_name", "english_name", "latin_name"):
            val = (rec.get(field) or "").strip()
            if val in ("-", "N/A", "n/a", "None"):
                dash_hits.append((idx, field, val, rec.get("indonesian_name")))

        if "zh1caowu" in (rec.get("pinyin_name") or "").lower() or "zh1caowu" in (rec.get("indonesian_name") or "").lower():
            pinyin_typos.append((idx, rec.get("pinyin_name"), rec.get("indonesian_name")))

    assert synthetic_hits == [], f"Synthetic SM0xxx IDs found: {synthetic_hits[:5]}"
    assert dash_hits == [], f"Placeholder values found: {dash_hits[:5]}"
    assert bad_sources == [], f"Empty/invalid source_reference found: {bad_sources[:5]}"
    assert pinyin_typos == [], f"Pinyin typo found: {pinyin_typos}"


def test_dataset_zero_duplicate_names(dataset_1500: list[dict]):
    seen_zh: dict[str, int] = {}
    seen_id: dict[str, int] = {}
    dup_zh = []
    dup_id = []

    for idx, rec in enumerate(dataset_1500):
        zh = (rec.get("mandarin_name") or "").strip()
        if zh:
            if zh in seen_zh:
                dup_zh.append((zh, seen_zh[zh], idx))
            else:
                seen_zh[zh] = idx

        id_name = (rec.get("indonesian_name") or "").strip().lower()
        if id_name in seen_id:
            dup_id.append((id_name, seen_id[id_name], idx))
        else:
            seen_id[id_name] = idx

    assert dup_zh == [], f"Duplicate mandarin_name entries: {dup_zh[:10]}"
    assert dup_id == [], f"Duplicate indonesian_name entries: {dup_id[:10]}"


def test_dataset_zero_toxicity_contradictions(dataset_1500: list[dict]):
    contradictions = []
    for idx, rec in enumerate(dataset_1500):
        is_toxic = rec["is_toxic"]
        level = rec["toxicity_level"]
        tclass = rec["toxicity_class"]
        if is_toxic:
            if level == "none" or tclass not in ("toxic", "contraindicated"):
                contradictions.append((idx, rec["indonesian_name"], is_toxic, level, tclass))
        else:
            if level != "none" or tclass != "safe":
                contradictions.append((idx, rec["indonesian_name"], is_toxic, level, tclass))

    assert contradictions == [], f"Toxicity contradictions found: {contradictions[:10]}"


def test_life_safety_all_11_perbpom_false_safe_corrected(dataset_1500: list[dict]):
    by_zh = {rec["mandarin_name"]: rec for rec in dataset_1500 if rec.get("mandarin_name")}
    missing = []
    not_toxic = []
    missing_citation = []

    for zh in ELEVEN_PERBPOM_FALSE_SAFE:
        rec = by_zh.get(zh)
        if not rec:
            missing.append(zh)
            continue
        if not rec["is_toxic"] or rec["toxicity_class"] not in ("toxic", "contraindicated"):
            not_toxic.append((zh, rec["is_toxic"], rec["toxicity_level"], rec["toxicity_class"]))
        if "PerBPOM-25/2023-Lamp.VIII" not in rec["source_reference"]:
            missing_citation.append((zh, rec["source_reference"]))

    assert missing == [], f"Missing PerBPOM herbs: {missing}"
    assert not_toxic == [], f"PerBPOM herbs still marked safe: {not_toxic}"
    assert missing_citation == [], f"PerBPOM citation missing: {missing_citation}"


def test_life_safety_all_7_symmap_dadu_and_core_lethal_herbs(dataset_1500: list[dict]):
    by_zh = {rec["mandarin_name"]: rec for rec in dataset_1500 if rec.get("mandarin_name")}

    for zh in SEVEN_SYMMAP_DADU:
        assert zh in by_zh, f"Missing SymMap 大毒 herb: {zh}"
        rec = by_zh[zh]
        assert rec["is_toxic"] is True, f"SymMap 大毒 herb not toxic: {zh}"
        assert rec["toxicity_level"] == "high", f"SymMap 大毒 herb not high toxicity: {zh} ({rec['toxicity_level']})"

    for zh in CORE_LETHAL_HERBS:
        assert zh in by_zh, f"Missing core lethal herb: {zh}"
        rec = by_zh[zh]
        assert rec["is_toxic"] is True, f"Core lethal herb not toxic: {zh}"


def test_part_specific_caution_notes_on_prohibited_part_species(dataset_1500: list[dict]):
    by_id = {rec["indonesian_name"].lower(): rec for rec in dataset_1500}
    for name in ("saga", "delima putih", "brotowali"):
        assert name in by_id, f"Missing species: {name}"
        desc = (by_id[name].get("description") or "").lower()
        assert "dilarang" in desc or "perhatian" in desc or "perbpom" in desc, (
            f"Missing part-specific PerBPOM caution note on {name}: {desc}"
        )


def test_safe_culinary_and_tonic_herbs_not_misclassified_as_toxic(dataset_1500: list[dict]):
    by_zh = {rec["mandarin_name"]: rec for rec in dataset_1500 if rec.get("mandarin_name")}
    by_id = {rec["indonesian_name"].lower(): rec for rec in dataset_1500}

    for zh in ("人参", "枸杞子", "红枣", "甘草"):
        assert zh in by_zh, f"Missing safe tonic herb: {zh}"
        assert by_zh[zh]["is_toxic"] is False, f"Safe tonic herb misclassified as toxic: {zh}"
        assert by_zh[zh]["toxicity_level"] == "none"

    for id_name in ("temulawak", "jahe"):
        assert id_name in by_id, f"Missing safe Indonesian herb: {id_name}"
        assert by_id[id_name]["is_toxic"] is False, f"Safe Indonesian herb misclassified as toxic: {id_name}"
        assert by_id[id_name]["toxicity_level"] == "none"
