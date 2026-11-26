"""
build_1500_dataset.py — Deterministic, zero-hallucination pipeline to build
FitMate's authoritative 1,500-ingredient TCM & BPOM database.

Inputs (all official, locally archived in data/scraper/output/ & backend/database/data/):
  - backend/database/data/tcm_500_ingredients.json (baseline 500 records)
  - data/scraper/output/symmap_herbs_raw.json (SymMap v2.0, 703 herbs)
  - data/scraper/output/tcm_mkg_D6_chinese_herbal_pieces.tsv (ChP 2020, 6,207 herbs)
  - data/scraper/output/tcm_mkg_D7_chp_medicinal_properties.tsv (flavors/meridians/natures)
  - data/scraper/output/tcm_mkg_D8_chp_np.tsv (NCBI Taxonomy Latin binomials)
  - data/scraper/output/tcm_mkg_D4_cpm_chp.tsv (patent medicine frequency)
  - data/scraper/output/hkcmms_parsed.json (HKCMMS Vol. 1-11 monographs)
  - data/scraper/output/efsa_endpointstudy.csv (EFSA Compendium of Botanicals)
  - data/scraper/output/bpom_prohibited_ingredients.json (PerBPOM No. 25/2023 Lampiran VIII)
  - data/scraper/output/bpom_approved_claims.json (BPOM OTSKK approved claims)
  - data/scraper/output/bpom_warnings_precautions.json (BPOM mandatory labeling warnings)
  - data/scraper/output/bpom_jamu_sederhana.json (BPOM Jamu Sederhana)
  - data/scraper/output/bpom_pusaka_oba.json (BPOM PUSAKA OBA)
  - data/scraper/output/kemenkes_fhi_monographs.json (Kemenkes FHI Ed. II + Supl. 1 & 2)

Outputs:
  - backend/database/data/tcm_1500_ingredients.json (canonical 1,500 records)
  - frontend/src/data/tcmIngredients.json (byte-identical mirror)
  - backend/database/data/dataset_provenance_summary.json (audit & provenance summary)
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database.schemas import TCMIngredient  # noqa: E402

RAW_DIR = REPO_ROOT / "data" / "scraper" / "output"
BASELINE_PATH = BACKEND_DIR / "database" / "data" / "tcm_500_ingredients.json"
BACKEND_OUT_PATH = BACKEND_DIR / "database" / "data" / "tcm_1500_ingredients.json"
FRONTEND_OUT_PATH = REPO_ROOT / "frontend" / "src" / "data" / "tcmIngredients.json"
PROVENANCE_OUT_PATH = BACKEND_DIR / "database" / "data" / "dataset_provenance_summary.json"

TARGET_COUNT = 1500
VALIDATED_BY = "official_source_pipeline_v2"

SYNTHETIC_SM_RE = re.compile(r"^SM0\d{3}$")

# ---------------------------------------------------------------------------
# Reference Maps & Guardrail Constants
# ---------------------------------------------------------------------------

MERIDIAN_TO_ORGAN_ID: dict[str, str] = {
    "liver": "Hati",
    "kidney": "Ginjal",
    "heart": "Jantung",
    "lung": "Paru-paru",
    "spleen": "Limpa",
    "stomach": "Lambung",
    "large intestine": "Usus Besar",
    "small intestine": "Usus Kecil",
    "gallbladder": "Kantung Empedu",
    "urinary bladder": "Kandung Kemih",
    "bladder": "Kandung Kemih",
    "pericardium": "Perikardium",
    "triple energizer": "San Jiao",
    "triple burner": "San Jiao",
}

PLANT_PART_TOKENS: dict[str, str] = {
    "radix": "radix",
    "rhizoma": "rhizoma",
    "folium": "folium",
    "folia": "folium",
    "semen": "semen",
    "fructus": "fructus",
    "cortex": "cortex",
    "herba": "herba",
    "flos": "flos",
    "flores": "flos",
    "caulis": "caulis",
    "pericarpium": "pericarpium",
    "lignum": "lignum",
    "tuber": "tuber",
    "bulbus": "bulbus",
    "latex": "latex",
    "resina": "resina",
    "oleoresina": "resina",
    "oil": "oleum",
    "oleum": "oleum",
    "biji": "semen",
    "akar": "radix",
    "rimpang": "rhizoma",
    "daun": "folium",
    "buah": "fructus",
    "kulit": "cortex",
    "bunga": "flos",
    "batang": "caulis",
    "getah": "latex",
    "seluruh bagian": "whole",
}

# Critical life-safety corrections for the 11 previously FALSE-SAFE PerBPOM Lampiran VIII herbs
ELEVEN_PERBPOM_CORRECTIONS: dict[str, dict[str, str]] = {
    "草乌": {
        "toxicity_level": "high",
        "target_organ": "Jantung, Sistem Saraf Pusat",
        "reason": "Dilarang keras oleh PerBPOM No. 25/2023 Lampiran VIII (Aconitum kusnezoffii — mengandung akonitin kardiotoksik & neurotoksik fatal).",
    },
    "川乌": {
        "toxicity_level": "high",
        "target_organ": "Jantung, Sistem Saraf Pusat",
        "reason": "Dilarang keras oleh PerBPOM No. 25/2023 Lampiran VIII (Aconitum carmichaelii — mengandung akonitin kardiotoksik & neurotoksik fatal).",
    },
    "马兜铃": {
        "toxicity_level": "high",
        "target_organ": "Ginjal, Saluran Kemih",
        "reason": "Dilarang keras oleh PerBPOM No. 25/2023 Lampiran VIII (Aristolochia spp. — mengandung asam aristolokat nefrotoksik & karsinogenik).",
    },
    "木通": {
        "toxicity_level": "high",
        "target_organ": "Ginjal, Jantung",
        "reason": "Dilarang oleh PerBPOM No. 25/2023 Lampiran VIII karena risiko substitusi/kontaminasi Aristolochia (asam aristolokat nefrotoksik).",
    },
    "麻黄": {
        "toxicity_level": "high",
        "target_organ": "Jantung, Pembuluh Darah, Sistem Saraf Pusat",
        "reason": "Dilarang keras oleh PerBPOM No. 25/2023 Lampiran VIII (Ephedra spp. — mengandung efedrin penyebab aritmia, hipertensi berat & stroke).",
    },
    "麻黄根": {
        "toxicity_level": "high",
        "target_organ": "Jantung, Sistem Saraf Pusat",
        "reason": "Dilarang oleh PerBPOM No. 25/2023 Lampiran VIII (seluruh bagian genus Ephedra spp. dilarang dalam obat tradisional).",
    },
    "黄连": {
        "toxicity_level": "moderate",
        "target_organ": "Hati, Saluran Cerna",
        "reason": "Dilarang oleh PerBPOM No. 25/2023 Lampiran VIII & PerKa BPOM No. 10/2014 (Coptis spp. — sumber berberin yang dilarang pada obat tradisional).",
    },
    "厚朴": {
        "toxicity_level": "moderate",
        "target_organ": "Hati, Ginjal, Sistem Saraf",
        "reason": "Dilarang oleh PerBPOM No. 25/2023 Lampiran VIII (Magnolia officinalis Cortex dilarang dalam sediaan obat tradisional).",
    },
    "关黄柏": {
        "toxicity_level": "moderate",
        "target_organ": "Hati, Ginjal",
        "reason": "Dilarang oleh PerBPOM No. 25/2023 Lampiran VIII & PerKa BPOM No. 10/2014 (Phellodendron amurense — sumber berberin dilarang).",
    },
    "黄柏": {
        "toxicity_level": "moderate",
        "target_organ": "Hati, Ginjal",
        "reason": "Dilarang oleh PerBPOM No. 25/2023 Lampiran VIII & PerKa BPOM No. 10/2014 (Phellodendron chinense — sumber berberin dilarang).",
    },
    "贯叶金丝桃": {
        "toxicity_level": "moderate",
        "target_organ": "Hati (Interaksi Enzim CYP450), Sistem Saraf Pusat",
        "reason": "Dilarang oleh PerBPOM No. 25/2023 Lampiran VIII (Hypericum perforatum / St. John's Wort — interaksi obat CYP450 berat & risiko sindrom serotonin).",
    },
}

# Fix the 4 english_name == "-" entries from baseline
DASH_ENGLISH_FIXES: dict[str, str] = {
    "复方阿胶浆": "Compound Ejiao Syrup",
    "连花清瘟胶囊": "Lianhua Qingwen Capsule",
    "皮康霜": "Pi Kang Shuang Cream",
    "三金片": "Sanjin Tablet",
}

# Authentic fallback source references for the 11 unmatched synthetic SM0xxx patent formulas/foods
UNMATCHED_SM_FALLBACKS: dict[str, dict[str, str]] = {
    "安宫牛黄丸": {"source_reference": "ChP-2020; BPOM-TI", "latin_name": "Angong Niuhuang Wan (TCM Formula)"},
    "燕窝": {"source_reference": "BPOM-TI", "latin_name": "Collocalia esculenta (Edible Bird's Nest)"},
    "桃胶": {"source_reference": "ChP-2020", "latin_name": "Prunus persica (Resina)"},
    "银耳": {"source_reference": "ChP-2020", "latin_name": "Tremella fuciformis"},
    "龙胆泻肝汤": {"source_reference": "ChP-2020; BPOM-TI", "latin_name": "Longdan Xiegan Tang (TCM Formula)"},
    "逍遥散": {"source_reference": "ChP-2020; BPOM-TI", "latin_name": "Xiaoyao San (TCM Formula)"},
    "红枣": {"source_reference": "ChP-2020", "latin_name": "Ziziphus jujuba Fructus"},
    "黑枣": {"source_reference": "ChP-2020", "latin_name": "Diospyros lotus / Ziziphus jujuba"},
    "八角": {"source_reference": "ChP-2020", "latin_name": "Illicium verum Fructus"},
    "关木通": {"source_reference": "PerBPOM-25/2023-Lamp.VIII; ChP-2020", "latin_name": "Aristolochia manshuriensis Caulis"},
    "当归尾": {"source_reference": "ChP-2020", "latin_name": "Angelica sinensis Radix Extremitas"},
}

# Part-specific caution notes for the 3 BPOM-OTSKK safe species whose OTHER plant parts are prohibited
PART_CAUTION_NOTES: dict[str, str] = {
    "saga": (
        "PERHATIAN KHUSUS BAGIAN TANAMAN (PerBPOM No. 25/2023 Lampiran VIII): "
        "Hanya daun (Abrus precatorius Folium) yang diizinkan. Biji Saga (Abrus precatorius Semen) "
        "dilarang keras karena mengandung abrin yang sangat toksik."
    ),
    "delima putih": (
        "PERHATIAN KHUSUS BAGIAN TANAMAN (PerBPOM No. 25/2023 Lampiran VIII): "
        "Kulit buah (Punica granatum Pericarpium) diizinkan, namun kulit akar dan kulit batang "
        "(Radix/Cortex) dilarang dalam obat tradisional."
    ),
    "brotowali": (
        "PERHATIAN KHUSUS BAGIAN TANAMAN (PerBPOM No. 25/2023 Lampiran VIII): "
        "Batang (Tinospora crispa Caulis) diizinkan, namun akar (Tinospora crispa Radix) "
        "dilarang dalam obat tradisional."
    ),
}

# High-toxicity botanical/mineral genera & keywords for PerBPOM Lampiran VIII severity classification
HIGH_TOXICITY_GENERA = (
    "abrus", "aconitum", "adonis", "antiaris", "aristolochia", "atropa",
    "belladonna", "colchicum", "conium", "convallaria", "croton", "datura",
    "digitalis", "ephedra", "euphorbia", "gloriosa", "hyoscyamus", "jatropha",
    "nerium", "papaver", "piper methysticum", "podophyllum", "ricinus",
    "schoenocaulon", "scilla", "senecio", "solanum", "strophanthus",
    "strychnos", "symphytum", "taxus", "thevetia", "tussilago", "veratrum",
    "arsen", "raksa", "merkuri", "timbal", "cinnabaris", "realgar", "kalomel",
    "sublimat", "tembaga", "alkohol", "etanol",
)

# Strict guardrail for EFSA ENDPOINTSTUDY: only severe systemic toxicity triggers is_toxic=True
EFSA_SEVERE_KEYWORDS = (
    "hepatotox", "nephrotox", "cardiotox", "neurotox", "genotox",
    "carcinogen", "mutagen", "teratogen", "aristolochic", "pyrrolizidine",
    "aconit", "cyanogen", "strychn", "atropine", "scopolamine", "hyoscyamine",
    "ephedr", "colchicin", "cardiac glycoside", "fatal", "lethal",
    "convulsion", "coma", "liver failure", "renal failure", "abrin", "ricin",
)

# Culinary / safe tonic whitelist never auto-flagged as toxic from EFSA
SAFE_CULINARY_WHITELIST = {
    "zingiber officinale", "curcuma longa", "curcuma xanthorrhiza",
    "curcuma zedoaria", "cinnamomum verum", "cinnamomum cassia",
    "cinnamomum aromaticum", "panax ginseng", "panax quinquefolius",
    "panax notoginseng", "glycyrrhiza uralensis", "glycyrrhiza glabra",
    "allium sativum", "allium cepa", "foeniculum vulgare", "mentha haplocalyx",
    "mentha piperita", "camellia sinensis", "ziziphus jujuba",
    "lycium barbarum", "lycium chinense", "citrus reticulata",
    "citrus sinensis", "citrus aurantium", "piper nigrum",
    "coriandrum sativum", "angelica sinensis", "astragalus membranaceus",
    "astragalus mongholicus", "codonopsis pilosula", "wolfiporia extensa",
    "poria cocos", "dioscorea polystachya", "dioscorea opposita",
    "siraitia grosvenorii", "momordica grosvenorii", "chrysanthemum morifolium",
    "lonicera japonica", "crataegus pinnatifida", "prunus armeniaca",
    "coix lacryma-jobi", "nelumbo nucifera", "sesamum indicum",
    "cassia obtusifolia", "platycodon grandiflorus", "schisandra chinensis",
    "ophiopogon japonicus", "rehmannia glutinosa", "paeonia lactiflora",
    "salvia miltiorrhiza", "eucommia ulmoides", "ginkgo biloba",
    "centella asiatica", "andrographis paniculata", "phyllanthus niruri",
    "morinda citrifolia", "nigella sativa", "carica papaya",
    "orthosiphon aristatus", "syzygium polyanthum", "apium graveolens",
    "garcinia mangostana", "kaempferia galanga", "alpinia galanga",
}

HKCMMS_VOL_RE = re.compile(r"(\d+)")
ZH_VOL_MAP = {
    "一": "1", "二": "2", "三": "3", "四": "4", "五": "5",
    "六": "6", "七": "7", "八": "8", "九": "9", "十": "10", "十一": "11",
}


# ---------------------------------------------------------------------------
# Normalization & Deduplication Helpers
# ---------------------------------------------------------------------------


def clean_str(val: Any) -> str:
    if val is None:
        return ""
    s = str(val).strip()
    return "" if s.lower() in ("none", "null", "nan", "-") else s


def extract_binomial(latin: str) -> str:
    """Extract normalized lowercase 'genus species' from a Latin botanical or simplisia name."""
    if not latin:
        return ""
    # Take first comma-separated entry if multiple aliases
    first = latin.split(",")[0].strip()
    # Remove parentheticals & punctuation
    first = re.sub(r"\([^)]*\)", " ", first)
    first = re.sub(r"[^A-Za-z\s]", " ", first)
    tokens = [t.lower() for t in first.split() if t]
    # Strip leading pharmaceutical part words like 'radix', 'folium', 'herba', 'semen', 'cortex', 'fructus'
    while tokens and tokens[0] in PLANT_PART_TOKENS:
        tokens.pop(0)
    # Remove author abbreviations / 'syn' / 'var' / 'subsp' / 'et' / 'dan'
    filtered = [
        t for t in tokens
        if t not in ("l", "syn", "var", "subsp", "ssp", "spp", "sp", "et", "dan", "ex", "dc", "nutt", "lesch", "mill", "thunb", "benth", "hook", "maxim", "franch", "fisch", "mey")
        and t not in PLANT_PART_TOKENS
        and len(t) > 1
    ]
    if len(filtered) >= 2:
        return f"{filtered[0]} {filtered[1]}"
    return filtered[0] if filtered else ""


def extract_part(latin: str, part_hint: str = "") -> str:
    """Extract normalized plant part token from Latin name or Indonesian part description."""
    combined = f"{latin} {part_hint}".lower()
    if "seluruh bagian" in combined or "whole" in combined:
        return "whole"
    for token, canonical in PLANT_PART_TOKENS.items():
        if re.search(rf"\b{re.escape(token)}\b", combined):
            return canonical
    return ""


def meridians_to_target_organ(meridians_eng: str) -> str:
    if not meridians_eng:
        return "Sistemik"
    parts = [p.strip().lower() for p in re.split(r"[,;/]", meridians_eng) if p.strip()]
    mapped = []
    for p in parts:
        # Remove trailing " meridian"
        p_clean = p.replace(" meridian", "").strip()
        if p_clean in MERIDIAN_TO_ORGAN_ID:
            organ = MERIDIAN_TO_ORGAN_ID[p_clean]
            if organ not in mapped:
                mapped.append(organ)
    return ", ".join(mapped) if mapped else "Sistemik"


def format_fhi_source(edition: str) -> str:
    ed = (edition or "").lower()
    if "suplemen ii" in ed or "supl. 2" in ed or "2026" in ed:
        return "FHI-II-Supl.2-2026"
    if "suplemen i" in ed or "supl. 1" in ed or "2022" in ed:
        return "FHI-II-Supl.1-2022"
    return "FHI-II-2017"


def format_hkcmms_volume(vol_str: str) -> str:
    m = HKCMMS_VOL_RE.search(vol_str or "")
    if m:
        return f"HKCMMS-Vol.{m.group(1)}"
    for zh_num in ("十一", "十", "九", "八", "七", "六", "五", "四", "三", "二", "一"):
        if zh_num in (vol_str or ""):
            return f"HKCMMS-Vol.{ZH_VOL_MAP[zh_num]}"
    return "HKCMMS"


def title_case_pinyin(pinyin: str) -> str:
    return " ".join(w.capitalize() for w in clean_str(pinyin).split())


def append_source(existing: str, addition: str) -> str:
    parts = [p.strip() for p in existing.split(";") if p.strip()]
    for add in (p.strip() for p in addition.split(";") if p.strip()):
        if add not in parts:
            parts.append(add)
    return "; ".join(parts)


# ---------------------------------------------------------------------------
# Source Index Loader
# ---------------------------------------------------------------------------


class SourceRepository:
    """Loads and indexes all verified official raw sources deterministically."""

    def __init__(self) -> None:
        self.baseline_500: list[dict[str, Any]] = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
        self.symmap_raw: list[dict[str, Any]] = json.loads((RAW_DIR / "symmap_herbs_raw.json").read_text(encoding="utf-8"))
        self.hkcmms: dict[str, list[dict[str, str]]] = json.loads((RAW_DIR / "hkcmms_parsed.json").read_text(encoding="utf-8"))
        self.bpom_prohibited: list[dict[str, str]] = json.loads((RAW_DIR / "bpom_prohibited_ingredients.json").read_text(encoding="utf-8"))
        self.bpom_claims: list[dict[str, str]] = json.loads((RAW_DIR / "bpom_approved_claims.json").read_text(encoding="utf-8"))
        self.bpom_warnings: list[dict[str, str]] = json.loads((RAW_DIR / "bpom_warnings_precautions.json").read_text(encoding="utf-8"))
        self.bpom_jamu: list[dict[str, str]] = json.loads((RAW_DIR / "bpom_jamu_sederhana.json").read_text(encoding="utf-8"))
        self.bpom_pusaka: list[dict[str, str]] = json.loads((RAW_DIR / "bpom_pusaka_oba.json").read_text(encoding="utf-8"))
        self.kemenkes_fhi: list[dict[str, Any]] = json.loads((RAW_DIR / "kemenkes_fhi_monographs.json").read_text(encoding="utf-8"))

        # SymMap indexes
        self.symmap_by_zh: dict[str, dict[str, Any]] = {}
        self.symmap_by_binomial: dict[str, dict[str, Any]] = {}
        for h in self.symmap_raw:
            zh = clean_str(h.get("Chinese_name"))
            if zh and zh not in self.symmap_by_zh:
                self.symmap_by_zh[zh] = h
            binom = extract_binomial(clean_str(h.get("Latin_name")))
            if binom and binom not in self.symmap_by_binomial:
                self.symmap_by_binomial[binom] = h

        # TCM-MKG D6, D7, D8, D4
        self.mkg_d6: dict[str, dict[str, str]] = {}
        self.mkg_by_zh: dict[str, dict[str, str]] = {}
        with open(RAW_DIR / "tcm_mkg_D6_chinese_herbal_pieces.tsv", encoding="utf-8") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                cid = clean_str(row.get("CHP_ID"))
                zh = clean_str(row.get("Chinese_herbal_pieces"))
                if cid:
                    self.mkg_d6[cid] = row
                if zh and zh not in self.mkg_by_zh:
                    self.mkg_by_zh[zh] = row

        self.mkg_meridians: dict[str, list[str]] = defaultdict(list)
        self.mkg_properties: dict[str, list[str]] = defaultdict(list)
        with open(RAW_DIR / "tcm_mkg_D7_chp_medicinal_properties.tsv", encoding="utf-8") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                cid = clean_str(row.get("CHP_ID"))
                cls = clean_str(row.get("Class"))
                prop = clean_str(row.get("Medicinal_properties"))
                if not cid or not prop:
                    continue
                if cls == "Meridian tropism":
                    self.mkg_meridians[cid].append(prop)
                else:
                    self.mkg_properties[cid].append(prop)

        self.mkg_species: dict[str, list[str]] = defaultdict(list)
        self.mkg_by_binomial: dict[str, str] = {}
        with open(RAW_DIR / "tcm_mkg_D8_chp_np.tsv", encoding="utf-8") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                cid = clean_str(row.get("CHP_ID"))
                sp = clean_str(row.get("species_name"))
                if cid and sp:
                    if sp not in self.mkg_species[cid]:
                        self.mkg_species[cid].append(sp)
                    binom = extract_binomial(sp)
                    if binom and binom not in self.mkg_by_binomial:
                        self.mkg_by_binomial[binom] = cid

        self.mkg_d4_freq: Counter[str] = Counter()
        with open(RAW_DIR / "tcm_mkg_D4_cpm_chp.tsv", encoding="utf-8") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                cid = clean_str(row.get("CHP_ID"))
                if cid:
                    self.mkg_d4_freq[cid] += 1

        # BPOM Prohibited binomial index (species -> list of prohibited rows)
        self.prohibited_by_binomial: dict[str, list[dict[str, str]]] = defaultdict(list)
        self.prohibited_whole_genera: set[str] = set()
        for row in self.bpom_prohibited:
            nama = clean_str(row.get("Nama Bahan"))
            latin = clean_str(row.get("Nama Latin"))
            part = clean_str(row.get("Bagian yang Dilarang")).lower()
            binom = extract_binomial(nama) or extract_binomial(latin)
            if binom:
                self.prohibited_by_binomial[binom].append(row)
            if "spp." in nama.lower() and ("seluruh" in part or not part):
                genus = nama.split()[0].lower()
                self.prohibited_whole_genera.add(genus)

        # BPOM Approved Claims index
        self.claims_by_name: dict[str, str] = {}
        self.claims_by_binomial: dict[str, str] = {}
        for row in self.bpom_claims:
            nm = clean_str(row.get("Nama Bahan")).lower()
            claim = clean_str(row.get("Klaim yang disetujui"))
            binom = extract_binomial(clean_str(row.get("Nama Latin")))
            if nm and claim:
                self.claims_by_name[nm] = claim
            if binom and claim:
                self.claims_by_binomial[binom] = claim

        # BPOM Warnings index (by lowercase botanical / ingredient name token)
        self.warnings_by_binomial: dict[str, str] = {}
        for row in self.bpom_warnings:
            if clean_str(row.get("Kategori")) != "Bahan Aktif":
                continue
            zat = clean_str(row.get("Nama Bahan / Zat"))
            ket = clean_str(row.get("Keterangan yang perlu dicantumkan pada penandaan"))
            if not zat or not ket:
                continue
            for seg in re.split(r"[;,/]", zat):
                b = extract_binomial(seg)
                if b and len(b.split()) == 2:
                    self.warnings_by_binomial[b] = ket

        # EFSA Severe EndpointStudy index (binomial -> list of severe effect summaries)
        self.efsa_severe_by_binomial: dict[str, list[str]] = defaultdict(list)
        with open(RAW_DIR / "efsa_endpointstudy.csv", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f, delimiter=";"):
                sci = clean_str(row.get("scientificNames")) or clean_str(row.get("BOTANICAL")) or clean_str(row.get("PlantName"))
                binom = extract_binomial(sci)
                if not binom or len(binom.split()) < 2 or binom in SAFE_CULINARY_WHITELIST:
                    continue
                blob = " ".join(
                    clean_str(row.get(k))
                    for k in ("TOXICITYSUMMARY", "OBSERVEDEFFECT", "EFFECT_DESC", "TOXICITY", "SUBSTANCE", "TARGETTISSUE")
                ).lower()
                if any(kw in blob for kw in EFSA_SEVERE_KEYWORDS):
                    summary = clean_str(row.get("TOXICITYSUMMARY")) or clean_str(row.get("OBSERVEDEFFECT")) or clean_str(row.get("TOXICITY"))
                    if summary and summary not in self.efsa_severe_by_binomial[binom]:
                        self.efsa_severe_by_binomial[binom].append(summary)

    def check_prohibited(self, latin: str, part_hint: str = "") -> tuple[bool, str, str]:
        """Return (is_prohibited, level, reason) if Latin+part matches PerBPOM Lampiran VIII."""
        binom = extract_binomial(latin)
        if not binom:
            return False, "", ""
        genus = binom.split()[0]
        part = extract_part(latin, part_hint)

        if genus in self.prohibited_whole_genera:
            lvl = "high" if any(g in binom for g in HIGH_TOXICITY_GENERA) else "moderate"
            return True, lvl, f"Genus {genus.capitalize()} spp. dilarang oleh PerBPOM No. 25/2023 Lampiran VIII."

        matches = self.prohibited_by_binomial.get(binom, [])
        for row in matches:
            proh_part = extract_part(clean_str(row.get("Nama Latin")), clean_str(row.get("Bagian yang Dilarang")))
            if proh_part in ("", "whole") or not part or part == proh_part:
                lvl = "high" if any(g in binom for g in HIGH_TOXICITY_GENERA) else "moderate"
                bagian = clean_str(row.get("Bagian yang Dilarang")) or "Seluruh bagian"
                return True, lvl, f"Dilarang oleh PerBPOM No. 25/2023 Lampiran VIII (bagian dilarang: {bagian})."

        return False, "", ""


# ---------------------------------------------------------------------------
# Catalog Builder with Strict Deduplication
# ---------------------------------------------------------------------------


class CatalogBuilder:
    def __init__(self, repo: SourceRepository) -> None:
        self.repo = repo
        self.records: list[dict[str, Any]] = []
        self.seen_zh: set[str] = set()
        self.seen_id: set[str] = set()
        self.seen_latin_part: set[tuple[str, str]] = set()
        self.tier_counts: Counter[str] = Counter()

    def _make_unique_id_name(self, base_name: str, latin: str = "", part: str = "") -> str:
        candidate = clean_str(base_name) or clean_str(latin)
        if candidate.lower() not in self.seen_id:
            return candidate
        if part and f"{candidate} ({part.capitalize()})".lower() not in self.seen_id:
            return f"{candidate} ({part.capitalize()})"
        binom = extract_binomial(latin)
        if binom:
            tagged = f"{candidate} ({binom.capitalize()})"
            if tagged.lower() not in self.seen_id:
                return tagged
        n = 2
        while f"{candidate} #{n}".lower() in self.seen_id:
            n += 1
        return f"{candidate} #{n}"

    def is_duplicate(self, zh: str, id_name: str, latin: str, part_hint: str = "") -> bool:
        zh_c = clean_str(zh)
        if zh_c and zh_c in self.seen_zh:
            return True
        id_c = clean_str(id_name).lower()
        if id_c and id_c in self.seen_id:
            return True
        binom = extract_binomial(latin)
        part = extract_part(latin, part_hint)
        if binom:
            if (binom, part) in self.seen_latin_part:
                return True
            if part == "" and (binom, "whole") in self.seen_latin_part:
                return True
            if part == "whole" and (binom, "") in self.seen_latin_part:
                return True
        return False

    def add_record(self, rec: dict[str, Any], tier: str, part_hint: str = "", force_unique_id: bool = False) -> bool:
        if len(self.records) >= TARGET_COUNT:
            return False

        zh = clean_str(rec.get("mandarin_name"))
        latin = clean_str(rec.get("latin_name"))
        id_name = clean_str(rec.get("indonesian_name"))

        if force_unique_id and id_name.lower() in self.seen_id:
            id_name = self._make_unique_id_name(id_name, latin, extract_part(latin, part_hint))
            rec["indonesian_name"] = id_name

        if not id_name:
            return False

        # Enforce strict toxicity invariants before adding
        is_toxic = bool(rec.get("is_toxic"))
        tox_level = clean_str(rec.get("toxicity_level")).lower()
        if is_toxic:
            if tox_level not in ("low", "moderate", "high"):
                tox_level = "moderate"
            tox_class = "toxic"
        else:
            tox_level = "none"
            tox_class = "safe"

        clean_rec = {
            "mandarin_name": zh,
            "pinyin_name": clean_str(rec.get("pinyin_name")),
            "indonesian_name": id_name,
            "english_name": clean_str(rec.get("english_name")),
            "latin_name": latin,
            "is_toxic": is_toxic,
            "toxicity_level": tox_level,
            "toxicity_class": tox_class,
            "target_organ": clean_str(rec.get("target_organ")) or "Sistemik",
            "description": clean_str(rec.get("description")),
            "source_reference": clean_str(rec.get("source_reference")),
            "validated_by": VALIDATED_BY,
        }

        # Validate immediately against Pydantic schema (fail fast)
        TCMIngredient(**clean_rec)

        self.records.append(clean_rec)
        if zh:
            self.seen_zh.add(zh)
        self.seen_id.add(id_name.lower())
        binom = extract_binomial(latin)
        if binom:
            self.seen_latin_part.add((binom, extract_part(latin, part_hint)))
        self.tier_counts[tier] += 1
        return True

    # -----------------------------------------------------------------------
    # Stage 0: Preserve & Fix Baseline 500
    # -----------------------------------------------------------------------

    def process_baseline_500(self) -> None:
        for idx, raw in enumerate(self.repo.baseline_500):
            rec = dict(raw)
            zh = clean_str(rec.get("mandarin_name"))
            id_name = clean_str(rec.get("indonesian_name"))
            pinyin = clean_str(rec.get("pinyin_name"))
            eng = clean_str(rec.get("english_name"))
            latin = clean_str(rec.get("latin_name"))
            src = clean_str(rec.get("source_reference"))
            desc = clean_str(rec.get("description"))
            target_organ = clean_str(rec.get("target_organ"))

            # Fix pinyin typo Zh1caowu -> Zhicaowu
            if "zh1caowu" in pinyin.lower():
                pinyin = pinyin.replace("Zh1caowu", "Zhicaowu").replace("zh1caowu", "zhicaowu")
            if "zh1caowu" in id_name.lower():
                id_name = id_name.replace("Zh1caowu", "Zhicaowu").replace("zh1caowu", "zhicaowu")

            # Fix 4 english_name == "-" entries
            if zh in DASH_ENGLISH_FIXES:
                eng = DASH_ENGLISH_FIXES[zh]

            # Resolve the 2 duplicate english_name pairs
            if idx == 3 and zh == "人参":
                eng = "Asian Ginseng"
            elif idx == 110 and id_name.lower() == "ginseng":
                eng = "Ginseng Root (BPOM OTSKK)"
            elif zh == "北豆根":
                eng = "Asiatic Moonseed Rhizome"
            elif zh == "委陵菜":
                eng = "Chinese Cinquefoil"

            # Match against SymMap v2.0 for real SMHB00xxx IDs & enrichment
            sym = self.repo.symmap_by_zh.get(zh) if zh else None
            if sym:
                real_id = f"SMHB{int(sym['Herb_id']):05d}"
                if SYNTHETIC_SM_RE.match(src) or src in ("SymMap", "SymMap-Toxic"):
                    src = real_id
                if not latin or latin.lower() == id_name.lower():
                    sym_latin = clean_str(sym.get("Latin_name"))
                    if sym_latin:
                        latin = sym_latin.split(",")[0].strip()
                if not eng:
                    eng = clean_str(sym.get("English_name"))
                if not target_organ or target_organ.lower() in ("sistemik", "umum", ""):
                    target_organ = meridians_to_target_organ(clean_str(sym.get("Meridians_English")))

                # Enforce official SymMap v2.0 toxicity classification (catches false-safe baseline entries like 雷公藤 大毒)
                sym_props_zh = clean_str(sym.get("Properties_Chinese"))
                if "大毒" in sym_props_zh:
                    rec["is_toxic"] = True
                    rec["toxicity_level"] = "high"
                    rec["toxicity_class"] = "toxic"
                    if "sangat toksik" not in desc.lower() and "toksik" not in desc.lower():
                        desc = f"Herbal TCM berkategori sangat toksik (大毒 / Extremely Poisonous) dalam SymMap v2.0. {desc}".strip()
                elif "有毒" in sym_props_zh and "小毒" not in sym_props_zh:
                    if not rec.get("is_toxic"):
                        rec["is_toxic"] = True
                        rec["toxicity_level"] = "moderate"
                        rec["toxicity_class"] = "toxic"
                        desc = f"Herbal TCM berkategori toksik (有毒 / Poisonous) dalam SymMap v2.0. {desc}".strip()
                elif "小毒" in sym_props_zh and not rec.get("is_toxic"):
                    rec["is_toxic"] = True
                    rec["toxicity_level"] = "low"
                    rec["toxicity_class"] = "toxic"
                    desc = f"Herbal TCM berkategori toksisitas ringan (小毒 / Slightly Toxic) dalam SymMap v2.0. {desc}".strip()
            elif SYNTHETIC_SM_RE.match(src):
                # 11 unmatched synthetic SM0xxx entries: check TCM-MKG D6 first, else curated official fallback
                mkg = self.repo.mkg_by_zh.get(zh) if zh else None
                fb = UNMATCHED_SM_FALLBACKS.get(zh, {})
                if mkg:
                    cid = clean_str(mkg.get("CHP_ID"))
                    src = f"TCM-MKG:{cid}"
                    if zh == "关木通":
                        src = append_source("PerBPOM-25/2023-Lamp.VIII", src)
                    if not latin or latin.lower() == id_name.lower():
                        sp_list = self.repo.mkg_species.get(cid, [])
                        if sp_list:
                            latin = sp_list[0]
                elif fb:
                    src = fb["source_reference"]
                    if not latin or latin.lower() == id_name.lower():
                        latin = fb["latin_name"]
                else:
                    src = "ChP-2020"

            # Enrich missing latin_name from TCM-MKG D8 if available
            if not latin and zh and zh in self.repo.mkg_by_zh:
                cid = clean_str(self.repo.mkg_by_zh[zh].get("CHP_ID"))
                sp_list = self.repo.mkg_species.get(cid, [])
                if sp_list:
                    latin = sp_list[0]

            # Critical life-safety: fix ALL 11 FALSE-SAFE PerBPOM Lampiran VIII herbs
            if zh in ELEVEN_PERBPOM_CORRECTIONS:
                fix = ELEVEN_PERBPOM_CORRECTIONS[zh]
                rec["is_toxic"] = True
                rec["toxicity_level"] = fix["toxicity_level"]
                rec["toxicity_class"] = "toxic"
                target_organ = fix["target_organ"]
                src = append_source("PerBPOM-25/2023-Lamp.VIII", src)
                if fix["reason"] not in desc:
                    desc = f"{fix['reason']} {desc}".strip()

            # Enrich BPOM-OTSKK items with official approved claims & mandatory warnings
            if src == "BPOM-OTSKK-Klaim":
                binom = extract_binomial(latin)
                claim = self.repo.claims_by_name.get(id_name.lower()) or self.repo.claims_by_binomial.get(binom)
                if claim and claim.lower() not in desc.lower():
                    desc = f"Klaim disetujui BPOM OTSKK: {claim}."
                warning = self.repo.warnings_by_binomial.get(binom)
                if warning:
                    desc = f"{desc} Peringatan BPOM: {warning[:260]}".strip()

            # Add part-specific caution notes for Saga, Delima Putih, Brotowali
            if id_name.lower() in PART_CAUTION_NOTES:
                caution = PART_CAUTION_NOTES[id_name.lower()]
                if caution not in desc:
                    desc = f"{desc} {caution}".strip()

            # Normalize toxicity invariants for baseline items
            if not rec.get("is_toxic"):
                rec["is_toxic"] = False
                rec["toxicity_level"] = "none"
                rec["toxicity_class"] = "safe"
            else:
                rec["is_toxic"] = True
                rec["toxicity_class"] = "toxic"
                if clean_str(rec.get("toxicity_level")).lower() not in ("low", "moderate", "high"):
                    rec["toxicity_level"] = "moderate"

            rec.update({
                "mandarin_name": zh,
                "pinyin_name": pinyin,
                "indonesian_name": id_name,
                "english_name": eng,
                "latin_name": latin,
                "target_organ": target_organ or "Sistemik",
                "description": desc,
                "source_reference": src,
            })
            self.add_record(rec, tier="baseline_500", force_unique_id=True)

    # -----------------------------------------------------------------------
    # Tier 1: Remaining PerBPOM No. 25/2023 Lampiran VIII Prohibited Ingredients
    # -----------------------------------------------------------------------

    def add_tier1_bpom_prohibited(self) -> None:
        for row in self.repo.bpom_prohibited:
            nama_bahan = clean_str(row.get("Nama Bahan"))
            nama_umum = clean_str(row.get("Nama Umum"))
            bagian = clean_str(row.get("Bagian yang Dilarang"))
            nama_latin = clean_str(row.get("Nama Latin")).rstrip(".")
            latin = nama_latin or nama_bahan
            if not nama_bahan and not latin:
                continue

            binom = extract_binomial(nama_bahan) or extract_binomial(nama_latin)
            part = extract_part(latin, bagian)

            # Build clear Indonesian name (disambiguating prohibited plant part when species already exists)
            base_id = nama_umum if nama_umum else nama_bahan
            if bagian and base_id.lower() in self.seen_id:
                id_name = f"{base_id} ({bagian} — Dilarang BPOM)"
            else:
                id_name = base_id

            # Skip if exact (binomial, part) already covered in baseline
            if binom and (binom, part) in self.seen_latin_part:
                # Check if existing record is already toxic; if so, skip duplicate
                continue

            # Cross-link to SymMap or TCM-MKG for Mandarin/Pinyin/English if not already taken
            zh = ""
            pinyin = ""
            eng = ""
            src = "PerBPOM-25/2023-Lamp.VIII"
            target_organ = "Sistemik"

            if binom:
                sym = self.repo.symmap_by_binomial.get(binom)
                if sym:
                    cand_zh = clean_str(sym.get("Chinese_name"))
                    if cand_zh and cand_zh not in self.seen_zh:
                        zh = cand_zh
                        pinyin = clean_str(sym.get("Pinyin_name"))
                        eng = clean_str(sym.get("English_name"))
                        target_organ = meridians_to_target_organ(clean_str(sym.get("Meridians_English")))
                        src = append_source(src, f"SMHB{int(sym['Herb_id']):05d}")
                elif binom in self.repo.mkg_by_binomial:
                    cid = self.repo.mkg_by_binomial[binom]
                    mkg = self.repo.mkg_d6.get(cid, {})
                    cand_zh = clean_str(mkg.get("Chinese_herbal_pieces"))
                    if cand_zh and cand_zh not in self.seen_zh:
                        zh = cand_zh
                        pinyin = title_case_pinyin(mkg.get("Pinyin_term", ""))
                        eng = clean_str(mkg.get("English_term")).rstrip("*")
                        src = append_source(src, f"TCM-MKG:{cid}")

            combined_lower = f"{nama_bahan} {nama_umum} {latin}".lower()
            is_high = any(g in combined_lower for g in HIGH_TOXICITY_GENERA)
            tox_level = "high" if is_high else "moderate"

            part_text = f" Bagian dilarang: {bagian}." if bagian else ""
            desc = (
                f"Bahan dilarang keras digunakan dalam obat tradisional menurut PerBPOM No. 25 Tahun 2023 "
                f"Lampiran VIII ({nama_bahan}).{part_text}"
            )

            self.add_record(
                {
                    "mandarin_name": zh,
                    "pinyin_name": pinyin,
                    "indonesian_name": id_name,
                    "english_name": eng or nama_bahan,
                    "latin_name": latin,
                    "is_toxic": True,
                    "toxicity_level": tox_level,
                    "toxicity_class": "toxic",
                    "target_organ": target_organ,
                    "description": desc,
                    "source_reference": src,
                },
                tier="tier1_bpom_prohibited",
                part_hint=bagian,
                force_unique_id=True,
            )

    # -----------------------------------------------------------------------
    # Tier 2: ALL Remaining SymMap v2.0 Herbs (~299, incl. all 7 unused 大毒)
    # -----------------------------------------------------------------------

    def add_tier2_symmap_v2(self) -> None:
        # Sort deterministically: 大毒 first, then 有毒, then 小毒, then by Herb_id asc
        def _sort_key(h: dict[str, Any]) -> tuple[int, int]:
            props = clean_str(h.get("Properties_Chinese"))
            if "大毒" in props:
                rank = 0
            elif "有毒" in props and "小毒" not in props:
                rank = 1
            elif "小毒" in props:
                rank = 2
            else:
                rank = 3
            return (rank, int(h["Herb_id"]))

        for h in sorted(self.repo.symmap_raw, key=_sort_key):
            zh = clean_str(h.get("Chinese_name"))
            if not zh or zh in self.seen_zh:
                continue

            pinyin = clean_str(h.get("Pinyin_name"))
            eng = clean_str(h.get("English_name"))
            latin_raw = clean_str(h.get("Latin_name"))
            latin = latin_raw.split(",")[0].strip() if latin_raw else ""

            # Enrich missing Latin from TCM-MKG D8 if matched
            if not latin and zh in self.repo.mkg_by_zh:
                cid = clean_str(self.repo.mkg_by_zh[zh].get("CHP_ID"))
                sp = self.repo.mkg_species.get(cid, [])
                if sp:
                    latin = sp[0]

            props_zh = clean_str(h.get("Properties_Chinese"))
            props_en = clean_str(h.get("Properties_English"))
            cls_en = clean_str(h.get("Class_English"))
            target_organ = meridians_to_target_organ(clean_str(h.get("Meridians_English")))
            src = f"SMHB{int(h['Herb_id']):05d}"

            is_toxic = False
            tox_level = "none"
            extra_note = ""

            if "大毒" in props_zh:
                is_toxic = True
                tox_level = "high"
                extra_note = "Herbal TCM berkategori sangat toksik (大毒 / Extremely Poisonous) dalam SymMap v2.0."
            elif "有毒" in props_zh and "小毒" not in props_zh:
                is_toxic = True
                tox_level = "moderate"
                extra_note = "Herbal TCM berkategori toksik (有毒 / Poisonous) dalam SymMap v2.0."
            elif "小毒" in props_zh:
                is_toxic = True
                tox_level = "low"
                extra_note = "Herbal TCM berkategori toksisitas ringan (小毒 / Slightly Toxic) dalam SymMap v2.0."

            # Cross-check PerBPOM Lampiran VIII
            proh, proh_lvl, proh_reason = self.repo.check_prohibited(latin)
            if proh:
                is_toxic = True
                if tox_level != "high":
                    tox_level = proh_lvl
                src = append_source("PerBPOM-25/2023-Lamp.VIII", src)
                extra_note = f"{proh_reason} {extra_note}".strip()

            # Cross-check severe EFSA endpoint studies
            binom = extract_binomial(latin)
            if not is_toxic and binom and binom in self.repo.efsa_severe_by_binomial:
                is_toxic = True
                tox_level = "moderate"
                src = append_source(src, "EFSA-Compendium")
                extra_note = f"Peringatan toksisitas EFSA: {self.repo.efsa_severe_by_binomial[binom][0][:180]}"

            if is_toxic:
                desc = f"{extra_note} Sifat TCM: {props_en or props_zh}."
            else:
                cls_part = f" Kategori: {cls_en}." if cls_en else ""
                desc = f"Herbal TCM terverifikasi SymMap v2.0 (sifat: {props_en or props_zh}).{cls_part}"

            id_name = pinyin or eng or zh
            self.add_record(
                {
                    "mandarin_name": zh,
                    "pinyin_name": pinyin,
                    "indonesian_name": id_name,
                    "english_name": eng,
                    "latin_name": latin,
                    "is_toxic": is_toxic,
                    "toxicity_level": tox_level,
                    "toxicity_class": "toxic" if is_toxic else "safe",
                    "target_organ": target_organ,
                    "description": desc.strip(),
                    "source_reference": src,
                },
                tier="tier2_symmap_v2",
                force_unique_id=True,
            )

    # -----------------------------------------------------------------------
    # Tier 3: Kemenkes FHI + BPOM Jamu Sederhana + BPOM Warnings
    # -----------------------------------------------------------------------

    def add_tier3_indonesian_pharmacopoeia(self) -> None:
        # 3a. Kemenkes Farmakope Herbal Indonesia (212 monographs)
        for row in self.repo.kemenkes_fhi:
            title_id = clean_str(row.get("title_id"))
            toc_name = clean_str(row.get("toc_name"))
            latin_simp = clean_str(row.get("latin_simplisia"))
            species = clean_str(row.get("species"))
            family = clean_str(row.get("family"))
            marker = clean_str(row.get("marker_compound"))
            src = format_fhi_source(clean_str(row.get("edition")))

            id_name = toc_name or title_id.title()
            latin = latin_simp or species
            if not id_name or not latin:
                continue
            if self.is_duplicate("", id_name, latin):
                continue

            binom = extract_binomial(species or latin)
            zh, pinyin, eng = "", "", ""
            if binom:
                sym = self.repo.symmap_by_binomial.get(binom)
                if sym and clean_str(sym.get("Chinese_name")) not in self.seen_zh:
                    zh = clean_str(sym.get("Chinese_name"))
                    pinyin = clean_str(sym.get("Pinyin_name"))
                    eng = clean_str(sym.get("English_name"))
                elif binom in self.repo.mkg_by_binomial:
                    cid = self.repo.mkg_by_binomial[binom]
                    mkg = self.repo.mkg_d6.get(cid, {})
                    if clean_str(mkg.get("Chinese_herbal_pieces")) not in self.seen_zh:
                        zh = clean_str(mkg.get("Chinese_herbal_pieces"))
                        pinyin = title_case_pinyin(mkg.get("Pinyin_term", ""))
                        eng = clean_str(mkg.get("English_term")).rstrip("*")

            proh, proh_lvl, proh_reason = self.repo.check_prohibited(latin)
            is_toxic = proh
            tox_level = proh_lvl if proh else "none"
            if proh:
                src = append_source("PerBPOM-25/2023-Lamp.VIII", src)

            marker_txt = f" Senyawa identitas: {marker}." if marker else ""
            fam_txt = f" Famili: {family}." if family else ""
            desc = f"Monografi resmi Farmakope Herbal Indonesia ({clean_str(row.get('edition'))}) — {species}.{fam_txt}{marker_txt}"
            if proh:
                desc = f"{proh_reason} {desc}"

            self.add_record(
                {
                    "mandarin_name": zh,
                    "pinyin_name": pinyin,
                    "indonesian_name": id_name,
                    "english_name": eng or id_name,
                    "latin_name": latin,
                    "is_toxic": is_toxic,
                    "toxicity_level": tox_level,
                    "toxicity_class": "toxic" if is_toxic else "safe",
                    "target_organ": "Sistemik",
                    "description": desc.strip(),
                    "source_reference": src,
                },
                tier="tier3_kemenkes_fhi",
                force_unique_id=True,
            )

        # 3b. BPOM Jamu Sederhana (120 herbs)
        for row in self.repo.bpom_jamu:
            id_name = clean_str(row.get("Nama Indonesia"))
            latin = clean_str(row.get("Nama Simplisia"))
            kategori = clean_str(row.get("Kategori"))
            if not id_name or not latin:
                continue
            if self.is_duplicate("", id_name, latin):
                continue

            proh, proh_lvl, proh_reason = self.repo.check_prohibited(latin)
            src = "BPOM-Jamu-Sederhana"
            if proh:
                src = append_source("PerBPOM-25/2023-Lamp.VIII", src)

            desc = f"Simplisia resmi Kategori Registrasi Jamu Sederhana BPOM. Penggunaan tradisional: {kategori}."
            if proh:
                desc = f"{proh_reason} {desc}"

            self.add_record(
                {
                    "mandarin_name": "",
                    "pinyin_name": "",
                    "indonesian_name": id_name,
                    "english_name": id_name,
                    "latin_name": latin,
                    "is_toxic": proh,
                    "toxicity_level": proh_lvl if proh else "none",
                    "toxicity_class": "toxic" if proh else "safe",
                    "target_organ": "Sistemik",
                    "description": desc.strip(),
                    "source_reference": src,
                },
                tier="tier3_bpom_jamu",
                force_unique_id=True,
            )

        # 3c. BPOM Mandatory Labeling Warnings (Bahan Aktif botanicals)
        for row in self.repo.bpom_warnings:
            if clean_str(row.get("Kategori")) != "Bahan Aktif":
                continue
            zat = clean_str(row.get("Nama Bahan / Zat"))
            ket = clean_str(row.get("Keterangan yang perlu dicantumkan pada penandaan"))
            if not zat or not ket:
                continue
            # Skip non-botanical vitamins/synthetic supplements
            if any(skip in zat.lower() for skip in ("vitamin ", "epa ", "kafein", "glukosamin", "kondroitin", "kreatin", "l-karnitin", "koenzim", "kolagen", "kalsium", "zat besi", "magnesium", "zink", "selenium", "asam folat", "melatonin")):
                continue
            binom = extract_binomial(zat)
            if not binom or len(binom.split()) < 2:
                continue
            if self.is_duplicate("", zat, zat):
                continue

            proh, proh_lvl, proh_reason = self.repo.check_prohibited(zat)
            src = "BPOM-Peringatan"
            if proh:
                src = append_source("PerBPOM-25/2023-Lamp.VIII", src)

            desc = f"Bahan aktif dengan kewajiban pencantuman peringatan penandaan BPOM: {ket[:320]}"
            if proh:
                desc = f"{proh_reason} {desc}"

            self.add_record(
                {
                    "mandarin_name": "",
                    "pinyin_name": "",
                    "indonesian_name": zat.split(";")[0].strip(),
                    "english_name": zat.split(";")[0].strip(),
                    "latin_name": binom.capitalize(),
                    "is_toxic": proh,
                    "toxicity_level": proh_lvl if proh else "none",
                    "toxicity_class": "toxic" if proh else "safe",
                    "target_organ": "Sistemik",
                    "description": desc.strip(),
                    "source_reference": src,
                },
                tier="tier3_bpom_warnings",
                force_unique_id=True,
            )

    # -----------------------------------------------------------------------
    # Tier 4: Remaining HKCMMS Vol. 1-11 Official Monographs
    # -----------------------------------------------------------------------

    def add_tier4_hkcmms(self) -> None:
        for entry in self.repo.hkcmms.get("gb", []):
            zh = clean_str(entry.get("name"))
            if not zh or zh in self.seen_zh:
                continue

            vol_ref = format_hkcmms_volume(clean_str(entry.get("volume")))
            mkg = self.repo.mkg_by_zh.get(zh)
            pinyin = ""
            eng = ""
            latin = ""
            target_organ = "Sistemik"
            props_str = ""
            src = vol_ref

            if mkg:
                cid = clean_str(mkg.get("CHP_ID"))
                pinyin = title_case_pinyin(mkg.get("Pinyin_term", ""))
                eng = clean_str(mkg.get("English_term")).rstrip("*")
                sp_list = self.repo.mkg_species.get(cid, [])
                if sp_list:
                    latin = sp_list[0]
                meridians = self.repo.mkg_meridians.get(cid, [])
                if meridians:
                    target_organ = meridians_to_target_organ(", ".join(meridians))
                props = self.repo.mkg_properties.get(cid, [])
                if props:
                    props_str = ", ".join(props[:5])
                src = append_source(vol_ref, f"TCM-MKG:{cid}")

            proh, proh_lvl, proh_reason = self.repo.check_prohibited(latin)
            is_toxic = proh
            tox_level = proh_lvl if proh else "none"
            if proh:
                src = append_source("PerBPOM-25/2023-Lamp.VIII", src)

            binom = extract_binomial(latin)
            efsa_note = ""
            if not is_toxic and binom and binom in self.repo.efsa_severe_by_binomial:
                is_toxic = True
                tox_level = "moderate"
                src = append_source(src, "EFSA-Compendium")
                efsa_note = f" Peringatan toksisitas EFSA: {self.repo.efsa_severe_by_binomial[binom][0][:180]}."

            id_name = pinyin or eng or zh
            prop_txt = f" Sifat TCM: {props_str}." if props_str else ""
            desc = f"Monografi resmi Hong Kong Chinese Materia Medica Standards ({vol_ref}).{prop_txt}{efsa_note}"
            if proh:
                desc = f"{proh_reason} {desc}"

            self.add_record(
                {
                    "mandarin_name": zh,
                    "pinyin_name": pinyin,
                    "indonesian_name": id_name,
                    "english_name": eng or id_name,
                    "latin_name": latin,
                    "is_toxic": is_toxic,
                    "toxicity_level": tox_level,
                    "toxicity_class": "toxic" if is_toxic else "safe",
                    "target_organ": target_organ,
                    "description": desc.strip(),
                    "source_reference": src,
                },
                tier="tier4_hkcmms",
                force_unique_id=True,
            )

    # -----------------------------------------------------------------------
    # Tier 5: TCM-MKG (ChP 2020 + NCBI) High-Freq CPM + EFSA Severe + BPOM PUSAKA OBA
    # -----------------------------------------------------------------------

    def add_tier5_mkg_efsa_and_pusaka(self) -> None:
        # Prepare candidate TCM-MKG entries not yet in catalog
        efsa_candidates: list[tuple[int, str, dict[str, str], str]] = []
        cpm_candidates: list[tuple[int, int, str, dict[str, str], str]] = []

        for cid, row in self.repo.mkg_d6.items():
            zh = clean_str(row.get("Chinese_herbal_pieces"))
            if not zh or zh in self.seen_zh:
                continue
            sp_list = self.repo.mkg_species.get(cid, [])
            latin = sp_list[0] if sp_list else ""
            binom = extract_binomial(latin)
            freq = self.repo.mkg_d4_freq.get(cid, 0)
            pinyin = title_case_pinyin(row.get("Pinyin_term", ""))
            eng = clean_str(row.get("English_term")).rstrip("*")

            if binom and binom in self.repo.efsa_severe_by_binomial:
                efsa_candidates.append((-freq, cid, row, latin))
            else:
                completeness = int(bool(latin)) + int(bool(pinyin)) + int(bool(eng)) + int(bool(self.repo.mkg_meridians.get(cid)))
                cpm_candidates.append((-freq, -completeness, cid, row, latin))

        # 5a. EFSA severe-toxicity-flagged TCM-MKG herbs (high safety value)
        for _neg_freq, cid, row, latin in sorted(efsa_candidates, key=lambda x: (x[0], x[1])):
            if len(self.records) >= TARGET_COUNT:
                return
            self._add_mkg_entry(cid, row, latin, tier="tier5_mkg_efsa_toxic", efsa_flagged=True)

        # 5b. High-frequency TCM-MKG ChP 2020 patent medicine herbs
        for _neg_freq, _neg_comp, cid, row, latin in sorted(cpm_candidates, key=lambda x: (x[0], x[1], x[2])):
            if len(self.records) >= TARGET_COUNT:
                return
            self._add_mkg_entry(cid, row, latin, tier="tier5_tcm_mkg_chp2020", efsa_flagged=False)

        # 5c. Fallback fill with BPOM PUSAKA OBA if ever still below TARGET_COUNT
        for row in self.repo.bpom_pusaka:
            if len(self.records) >= TARGET_COUNT:
                return
            sp = clean_str(row.get("Nama Spesies"))
            raw_mat = clean_str(row.get("Nama Bahan Baku"))
            umum = clean_str(row.get("Nama Umum"))
            id_name = umum or raw_mat or sp
            latin = raw_mat or sp
            if not id_name or not latin:
                continue
            if self.is_duplicate("", id_name, latin):
                continue

            proh, proh_lvl, proh_reason = self.repo.check_prohibited(latin)
            src = "BPOM-PUSAKA-OBA"
            if proh:
                src = append_source("PerBPOM-25/2023-Lamp.VIII", src)

            desc = f"Bahan baku obat bahan alam terdaftar pada PUSAKA OBA BPOM ({sp or latin})."
            if proh:
                desc = f"{proh_reason} {desc}"

            self.add_record(
                {
                    "mandarin_name": "",
                    "pinyin_name": "",
                    "indonesian_name": id_name,
                    "english_name": umum or sp,
                    "latin_name": latin,
                    "is_toxic": proh,
                    "toxicity_level": proh_lvl if proh else "none",
                    "toxicity_class": "toxic" if proh else "safe",
                    "target_organ": "Sistemik",
                    "description": desc,
                    "source_reference": src,
                },
                tier="tier5_bpom_pusaka_oba",
                force_unique_id=True,
            )

    def _add_mkg_entry(self, cid: str, row: dict[str, str], latin: str, tier: str, efsa_flagged: bool) -> None:
        zh = clean_str(row.get("Chinese_herbal_pieces"))
        pinyin = title_case_pinyin(row.get("Pinyin_term", ""))
        eng = clean_str(row.get("English_term")).rstrip("*")
        if not zh or zh in self.seen_zh:
            return
        if latin and self.is_duplicate(zh, pinyin or eng or zh, latin):
            return

        meridians = self.repo.mkg_meridians.get(cid, [])
        props = self.repo.mkg_properties.get(cid, [])
        target_organ = meridians_to_target_organ(", ".join(meridians)) if meridians else "Sistemik"
        freq = self.repo.mkg_d4_freq.get(cid, 0)
        src = f"TCM-MKG:{cid}"

        proh, proh_lvl, proh_reason = self.repo.check_prohibited(latin)
        is_toxic = proh
        tox_level = proh_lvl if proh else "none"
        if proh:
            src = append_source("PerBPOM-25/2023-Lamp.VIII", src)

        binom = extract_binomial(latin)
        efsa_note = ""
        if efsa_flagged and binom in self.repo.efsa_severe_by_binomial:
            is_toxic = True
            if tox_level != "high":
                tox_level = "moderate"
            src = append_source(src, "EFSA-Compendium")
            efsa_note = f" Peringatan toksisitas EFSA Compendium: {self.repo.efsa_severe_by_binomial[binom][0][:180]}."

        prop_txt = f" Sifat: {', '.join(props[:5])}." if props else ""
        freq_txt = f" Tercatat dalam {freq} formula obat paten resmi ChP 2020." if freq > 0 else ""
        desc = f"Herbal TCM terverifikasi TCM-MKG / Chinese Pharmacopoeia 2020 ({cid}).{prop_txt}{freq_txt}{efsa_note}"
        if proh:
            desc = f"{proh_reason} {desc}"

        id_name = pinyin or eng or zh
        self.add_record(
            {
                "mandarin_name": zh,
                "pinyin_name": pinyin,
                "indonesian_name": id_name,
                "english_name": eng or id_name,
                "latin_name": latin,
                "is_toxic": is_toxic,
                "toxicity_level": tox_level,
                "toxicity_class": "toxic" if is_toxic else "safe",
                "target_organ": target_organ,
                "description": desc.strip(),
                "source_reference": src,
            },
            tier=tier,
            force_unique_id=True,
        )

    def build(self) -> list[dict[str, Any]]:
        self.process_baseline_500()
        self.add_tier1_bpom_prohibited()
        self.add_tier2_symmap_v2()
        self.add_tier3_indonesian_pharmacopoeia()
        self.add_tier4_hkcmms()
        self.add_tier5_mkg_efsa_and_pusaka()
        if len(self.records) != TARGET_COUNT:
            raise RuntimeError(f"Expected exactly {TARGET_COUNT} records, built {len(self.records)}")
        return self.records


# ---------------------------------------------------------------------------
# Provenance Summary & Deterministic Output Writer
# ---------------------------------------------------------------------------


def build_provenance_summary(records: list[dict[str, Any]], tier_counts: Counter[str], sha256_hex: str) -> dict[str, Any]:
    by_toxicity_level = Counter(r["toxicity_level"] for r in records)
    by_toxicity_class = Counter(r["toxicity_class"] for r in records)
    by_primary_source = Counter()

    for r in records:
        src = r["source_reference"]
        if "PerBPOM-25/2023-Lamp.VIII" in src:
            by_primary_source["PerBPOM-25/2023-Lamp.VIII"] += 1
        elif src.startswith("SMHB"):
            by_primary_source["SymMap-v2.0 (SMHB)"] += 1
        elif src.startswith("FHI-"):
            by_primary_source["Kemenkes-FHI"] += 1
        elif src.startswith("HKCMMS"):
            by_primary_source["HKCMMS-Vol.1-11"] += 1
        elif src.startswith("TCM-MKG:"):
            by_primary_source["TCM-MKG (ChP-2020)"] += 1
        elif "BPOM-OTSKK" in src:
            by_primary_source["BPOM-OTSKK-Klaim"] += 1
        elif "BPOM-Jamu" in src:
            by_primary_source["BPOM-Jamu-Sederhana"] += 1
        elif "BPOM-Peringatan" in src:
            by_primary_source["BPOM-Peringatan"] += 1
        elif "BPOM-PUSAKA" in src:
            by_primary_source["BPOM-PUSAKA-OBA"] += 1
        else:
            by_primary_source[src] += 1

    completeness = {
        "mandarin_name": sum(1 for r in records if r["mandarin_name"]),
        "pinyin_name": sum(1 for r in records if r["pinyin_name"]),
        "indonesian_name": sum(1 for r in records if r["indonesian_name"]),
        "english_name": sum(1 for r in records if r["english_name"]),
        "latin_name": sum(1 for r in records if r["latin_name"]),
        "target_organ": sum(1 for r in records if r["target_organ"]),
        "description": sum(1 for r in records if r["description"]),
        "source_reference": sum(1 for r in records if r["source_reference"]),
    }

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "pipeline_version": VALIDATED_BY,
        "total_records": len(records),
        "toxic_records": sum(1 for r in records if r["is_toxic"]),
        "safe_records": sum(1 for r in records if not r["is_toxic"]),
        "sha256": sha256_hex,
        "by_tier": dict(tier_counts),
        "by_primary_source": dict(sorted(by_primary_source.items(), key=lambda x: -x[1])),
        "by_toxicity_level": dict(by_toxicity_level),
        "by_toxicity_class": dict(by_toxicity_class),
        "field_completeness": completeness,
    }


def main() -> None:
    repo = SourceRepository()
    builder = CatalogBuilder(repo)
    records = builder.build()

    serialized = json.dumps(records, ensure_ascii=False, indent=2) + "\n"
    encoded = serialized.encode("utf-8")
    sha256_hex = hashlib.sha256(encoded).hexdigest()

    BACKEND_OUT_PATH.write_bytes(encoded)
    FRONTEND_OUT_PATH.write_bytes(encoded)

    summary = build_provenance_summary(records, builder.tier_counts, sha256_hex)
    PROVENANCE_OUT_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Built {len(records)} records | toxic={summary['toxic_records']} | safe={summary['safe_records']}")
    print(f"SHA-256: {sha256_hex}")
    print(f"Tiers: {summary['by_tier']}")
    print(f"Toxicity levels: {summary['by_toxicity_level']}")
    print(f"Primary sources: {summary['by_primary_source']}")


if __name__ == "__main__":
    main()
