"""
safety_interceptor.py

Pre-LLM safety gate for the FitMate chatbot.

Runs BEFORE parse_intent() in both _process_message and test_chat.
Each check is synchronous except check_bko() which may call the LLM.

Execution flow from whatsapp.py:
  1. emergency_response = check_emergency(text)
     → if not None: send and return immediately
  2. bko_result = await check_bko(text)
     → {"action": "block",   "response": "..."}  → send and return immediately
     → {"action": "clarify", "response": "..."}  → send and return immediately
     → {"action": "educate", "soft_warning": "..."} → continue flow, append to reply
     → {"action": "pass"}                          → continue normally

Decisions applied:
  - BKO context LLM returns YES  → block with static warning
  - BKO context LLM returns NO   → educate (pass through + soft informational note)
  - BKO context LLM is ambiguous → ask user for clarification
"""

import re
import json
import asyncio
from pathlib import Path


# ── Load BKO data at import time ──────────────────────────────────────────────
_BKO_DATA_PATH = Path(__file__).parent.parent / "data" / "bko_substances.json"

# Maps lowercase alias → {"display_name_id", "risk_summary_id", "category_id", "category_name_id"}
_BKO_ALIAS_MAP: dict[str, dict] = {}
_BKO_PATTERN: re.Pattern | None = None


def _load_bko_data() -> None:
    global _BKO_PATTERN, _BKO_ALIAS_MAP
    try:
        with open(_BKO_DATA_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[Interceptor] ⚠️  Could not load BKO data: {e}")
        return

    all_aliases: list[str] = []
    for category in data.get("categories", []):
        cat_id = category["id"]
        cat_name_id = category["name_id"]
        for substance in category.get("substances", []):
            display = substance["display_name_id"]
            risk = substance["risk_summary_id"]
            for alias in substance.get("aliases", []):
                key = alias.lower().strip()
                if key:
                    _BKO_ALIAS_MAP[key] = {
                        "display_name_id": display,
                        "risk_summary_id": risk,
                        "category_id": cat_id,
                        "category_name_id": cat_name_id,
                    }
                    all_aliases.append(re.escape(key))

    if all_aliases:
        # Sort by length descending so longer aliases match first (e.g. "sildenafil sitrat" before "sildenafil")
        all_aliases.sort(key=len, reverse=True)
        _BKO_PATTERN = re.compile(
            r"(?i)(?<!\w)(" + "|".join(all_aliases) + r")(?!\w)"
        )
        print(f"[Interceptor] ✅ BKO database loaded: {len(_BKO_ALIAS_MAP)} aliases across {len(data['categories'])} categories")
    else:
        print("[Interceptor] ⚠️  BKO alias list is empty — check bko_substances.json")


_load_bko_data()


# ── Emergency keywords ─────────────────────────────────────────────────────────
_EMERGENCY_PHRASES = [
    r"nyeri dada", r"sakit dada", r"dada nyeri", r"dada sakit",
    r"sesak napas", r"sesak nafas", r"sulit bernapas", r"susah napas", r"sulit nafas",
    r"napas sesak", r"nafas sesak",
    r"muntah darah", r"batuk darah", r"berak darah", r"bab darah",
    r"pingsan", r"tidak sadarkan diri", r"ga sadar", r"nggak sadar",
    r"kejang", r"kejang-kejang",
    r"stroke", r"serangan jantung", r"jantung berhenti",
    r"overdosis", r"overdose", r"overdos",
    r"keracunan parah", r"keracunan berat",
    r"syok anafilaksis", r"anafilaksis", r"anafilaktik",
    r"mau mati", r"hampir mati", r"sekarat",
    r"reaksi alergi parah", r"alergi parah",
    r"tidak bisa bernafas", r"tidak bisa bernapas",
]
_EMERGENCY_PATTERN = re.compile(
    r"(?i)(?<!\w)(" + "|".join(_EMERGENCY_PHRASES) + r")(?!\w)"
)

EMERGENCY_RESPONSE = (
    "🚨 *DARURAT MEDIS — SEGERA CARI PERTOLONGAN*\n\n"
    "Gejala yang kamu sebutkan bisa mengancam jiwa. *Jangan tunggu* — ambil tindakan sekarang:\n\n"
    "📞 *119* — SPGDT / Ambulans Nasional _(gratis, 24 jam)_\n"
    "🏥 Pergi ke *IGD rumah sakit terdekat* sekarang juga\n\n"
    "Hentikan konsumsi produk apapun sementara waktu dan bawa ke tenaga medis untuk diidentifikasi.\n\n"
    "_FitMate adalah alat edukasi — saya tidak bisa menangani keadaan darurat. "
    "Keselamatanmu adalah prioritas utama._ ❤️"
)


# ── Static BKO responses ───────────────────────────────────────────────────────
def _build_bko_warning(substance_info: dict) -> str:
    name = substance_info["display_name_id"]
    risk = substance_info["risk_summary_id"]
    cat = substance_info["category_name_id"]
    return (
        f"⚠️ *PERINGATAN: BKO Terdeteksi — {name}*\n\n"
        f"*{name}* adalah bahan kimia obat keras kategori *{cat}*.\n\n"
        f"❌ Keberadaannya dalam produk herbal atau TCM adalah *ILEGAL* dan sangat berbahaya:\n"
        f"• *Risiko kesehatan:* {risk}\n"
        f"• Dosis tidak terkontrol — jauh lebih berbahaya dibanding obat resep yang diawasi dokter\n"
        f"• Merupakan pemalsuan produk yang melanggar regulasi BPOM\n\n"
        f"🔴 *Hentikan konsumsi produk ini segera.*\n\n"
        f"📋 Laporkan ke BPOM: *1500-533* atau _cekbpom.pom.go.id_\n\n"
        f"⚕️ _Ini adalah informasi keselamatan berbasis regulasi, bukan saran medis personal._"
    )


def _build_bko_soft_warning(substance_info: dict) -> str:
    """Appended to educational/general replies when BKO detected but context is not product-specific."""
    name = substance_info["display_name_id"]
    cat = substance_info["category_name_id"]
    return (
        f"\n\n---\n"
        f"💡 *Catatan penting:* *{name}* adalah {cat} yang hanya boleh digunakan di bawah pengawasan dokter. "
        f"*Keberadaannya dalam produk herbal atau TCM adalah ilegal* dan merupakan tanda pemalsuan berbahaya. "
        f"Jika kamu menemukan bahan ini pada label produk herbal, segera hentikan konsumsi dan laporkan ke BPOM (1500-533)."
    )


CLARIFICATION_RESPONSE = (
    "Hmm, saya mendeteksi nama bahan kimia obat di pesanmu, tapi saya kurang yakin konteksnya. 🤔\n\n"
    "Bisa ceritakan lebih jelas:\n"
    "• Apakah bahan ini *tertera di label produk herbal/TCM* yang kamu punya?\n"
    "• Atau kamu sedang ingin belajar tentang bahan tersebut secara umum?\n\n"
    "Dengan begitu saya bisa kasih jawaban yang tepat untuk situasimu ya! 🌿"
)

OUT_OF_SCOPE_STATIC = (
    "Hei! Saya FitMate, asisten khusus untuk keamanan bahan herbal & TCM. 🌿\n\n"
    "Pertanyaan itu di luar area keahlian saya ya. Saya bisa bantu:\n"
    "• Cek keamanan bahan/produk TCM atau herbal\n"
    "• Info manfaat & kontraindikasi bahan TCM\n"
    "• Pertanyaan seputar kesehatan & obat tradisional\n\n"
    "Ada bahan herbal atau produk TCM yang ingin kamu cek keamanannya? 🌿"
)

OUT_OF_SCOPE_TERSE = (
    "Maaf, itu di luar spesialisasi saya nih. "
    "Saya hanya bisa bantu soal keamanan bahan herbal & TCM. "
    "Ada bahan yang ingin dicek? 🌿"
)

OUT_OF_SCOPE_COOLDOWN = (
    "Kamu sudah beberapa kali bertanya di luar topik saya. "
    "Saya perlu fokus pada pertanyaan seputar herbal & TCM saja. "
    "Silakan coba lagi dalam beberapa menit ya. 🌿\n\n"
    "_FitMate hanya melayani pertanyaan keamanan bahan herbal dan TCM._"
)


# ── Health-related keyword check (for off-topic detection) ────────────────────
_HEALTH_KEYWORDS_PATTERN = re.compile(
    r"(?i)\b(sehat|sakit|penyakit|obat|herbal|tcm|jamu|bahan|vitamin|suplemen|"
    r"kondisi|dokter|apoteker|hamil|menyusui|diabetes|hipertensi|kolesterol|"
    r"asam urat|ginjal|hati|liver|lambung|maag|usus|pencernaan|imun|alergi|"
    r"infeksi|demam|nyeri|pegal|rematik|sendi|tulang|darah|tekanan darah|"
    r"jantung|kanker|tumor|hepatitis|tifus|virus|bakteri|jamur|parasit|"
    r"nutrisi|gizi|diet|kapsul|tablet|ekstrak|akar|daun|biji|buah|rimpang|"
    r"tanaman|tumbuhan|ramuan|rebusan|teh herbal|teh|suplemen|olesan|"
    r"OT|jamu|fitofarmaka|herba|minyak atsiri|empon-empon)\b",
    re.IGNORECASE,
)


def is_health_related(text: str) -> bool:
    """Returns True if the message contains health/TCM-related keywords."""
    return bool(_HEALTH_KEYWORDS_PATTERN.search(text))


# ── Public API ─────────────────────────────────────────────────────────────────

def check_emergency(text: str) -> str | None:
    """
    Synchronous emergency keyword check.
    Returns static emergency response string if triggered, else None.
    Call this BEFORE any LLM interaction.
    """
    if _EMERGENCY_PATTERN.search(text):
        print(f"[Interceptor] 🚨 Emergency keyword triggered in: '{text[:60]}...'")
        return EMERGENCY_RESPONSE
    return None


async def check_bko(text: str) -> dict:
    """
    Async BKO check. Runs keyword regex first, then LLM context classifier if keyword found.

    Returns one of:
      {"action": "block",   "response": str}         → send and stop
      {"action": "clarify", "response": str}         → ask user to clarify, stop
      {"action": "educate", "soft_warning": str}     → continue flow, append soft_warning to final reply
      {"action": "pass"}                             → no BKO detected
    """
    if _BKO_PATTERN is None:
        return {"action": "pass"}

    match = _BKO_PATTERN.search(text)
    if not match:
        return {"action": "pass"}

    matched_alias = match.group(1).lower()
    substance_info = _BKO_ALIAS_MAP.get(matched_alias)
    if not substance_info:
        return {"action": "pass"}

    substance_name = substance_info["display_name_id"]
    print(f"[Interceptor] ⚠️  BKO keyword '{matched_alias}' ({substance_name}) detected. Running context check...")

    context_result = await _bko_context_llm_check(text, substance_name)
    print(f"[Interceptor] BKO context LLM result: {context_result}")

    if context_result == "YES":
        return {
            "action": "block",
            "response": _build_bko_warning(substance_info),
        }
    elif context_result == "NO":
        return {
            "action": "educate",
            "soft_warning": _build_bko_soft_warning(substance_info),
        }
    else:
        # AMBIGUOUS — ask for clarification rather than making assumptions
        return {
            "action": "clarify",
            "response": CLARIFICATION_RESPONSE,
        }


async def _bko_context_llm_check(text: str, substance_name: str) -> str:
    """
    Lightweight binary LLM classifier.
    Returns "YES", "NO", or "AMBIGUOUS".

    YES  — user is asking about this pharmaceutical drug found IN or taken WITH a herbal/TCM product
    NO   — educational, academic, or general medical context (not herbal product specific)
    AMBIGUOUS — cannot determine from message alone
    """
    prompt = (
        f"You are a safety classifier for a TCM/herbal supplement safety app in Indonesia.\n"
        f"A message contains the name of a pharmaceutical drug: '{substance_name}'.\n\n"
        f"Determine the CONTEXT of this message:\n"
        f"- Reply 'YES' if the user seems to be asking whether this drug is found in, "
        f"mixed with, or safe in a HERBAL or TCM product.\n"
        f"- Reply 'NO' if the user is asking about this drug in a general, educational, "
        f"purely clinical, or standalone pharmaceutical context (not related to herbal).\n"
        f"- Reply 'AMBIGUOUS' if the message is too short or unclear to determine context.\n\n"
        f"Reply with ONLY one word: YES, NO, or AMBIGUOUS.\n\n"
        f"Message: {text}"
    )

    try:
        # Lazy import to avoid circular import and import-time failures
        from services.llm_intent import _chat

        result = await _chat(
            [{"role": "user", "content": prompt}],
            temperature=0.0,
            timeout=8.0,
        )
        result = result.strip().upper().split()[0]  # take first word only
        if result in ("YES", "NO", "AMBIGUOUS"):
            return result
        print(f"[Interceptor] Unexpected BKO context reply: '{result}' — defaulting to AMBIGUOUS")
        return "AMBIGUOUS"
    except Exception as e:
        print(f"[Interceptor] BKO context LLM error: {e} — defaulting to AMBIGUOUS")
        return "AMBIGUOUS"
