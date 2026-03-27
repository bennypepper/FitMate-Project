# Context Handover: FitMate TCM — Sesi Maret 2026 (Sesi 3)

> Dokumen ini adalah kelanjutan dari `CONTEXT_HANDOVER.md` sebelumnya. Berisi semua perubahan yang dilakukan **dalam sesi ini** sehingga agent AI berikutnya dapat langsung melanjutkan tanpa perlu riset ulang.

---

## Status Saat Ini

- **Backend**: Berjalan di `http://localhost:8000` dengan `uvicorn --reload`
- **Database**: MongoDB lokal, collection `tcm_ingredients` berisi **103 bahan TCM** (sudah di-seed)
- **WhatsApp Bot**: Twilio Sandbox aktif (perlu ngrok tunnel yang hidup)
- **Frontend**: Next.js, berjalan terpisah (biasanya `npm run dev` di `/frontend`)
- **Git branch**: `main`, commit terakhir: `6d9bd3e`

---

## Ringkasan Perubahan Sesi Ini (Commit `6d9bd3e`)

---

## 1. Peningkatan Bot — Reply Sadar Kondisi Kesehatan (Health-Aware)

### Masalah yang Diperbaiki

Dari screenshot Twilio: ketika user berkata *"saya memiliki riwayat diabetes, apakah minuman tersebut aman?"*, bot membalas dengan template generik yang **sama persis** dengan reply sebelumnya — tidak menyebut diabetes sama sekali. User merasa tidak diacuhkan.

**Root cause:** Route 3 (`ingredient_safety_inquiry`) menggunakan f-string template hardcoded yang tidak pernah membaca ulang pesan user setelah mengekstrak nama bahan. Kondisi kesehatan yang disebutkan user benar-benar dihiraukan.

---

## 2. Fitur Baru — `generate_safety_reply()` di `llm_intent.py`

### File: `backend/services/llm_intent.py`

Fungsi baru yang menjadi inti perbaikan:

```python
async def generate_safety_reply(
    ingredient_name: str,
    db_match: dict | None,
    safety_verdict: str,        # "safe" | "toxic" | "not_found" — SELALU dari rule-based code
    user_message: str,          # pesan asli user — mengandung kondisi kesehatan
    history: list[dict] | None = None,
) -> str:
```

**Prinsip kerja:**
- `safety_verdict` ditentukan **100% oleh kode rule-based** (`_build_safety_verdict()`) berdasarkan field `is_toxic` di MongoDB — LLM tidak pernah menentukan ini
- LLM hanya menulis bahasa reply yang empatik, anchor ke verdict yang sudah ditetapkan
- System prompt secara eksplisit memerintahkan LLM untuk menyebut kondisi kesehatan yang disebutkan user (diabetes, hamil, hipertensi, dll.)
- Jika safe tapi ada kondisi khusus → tetap sarankan konsultasi dokter
- Jika toxic → tegas tapi sopan, dorong konsultasi segera
- Panjang reply: 4–6 kalimat + CTA

**Zero-hallucination guarantee tetap terjaga:** LLM tidak bisa mengubah verdict karena verdict adalah string constant yang di-inject ke system prompt sebagai fakta.

---

## 3. Perubahan Route 3 di `whatsapp.py`

### File: `backend/routers/whatsapp.py`

**Sebelumnya:** f-string template hardcoded 3 cabang (not_found / toxic / safe).

**Sekarang:**

```python
# Rule-based verdict — LLM tidak menyentuh ini
safety_verdict = _build_safety_verdict(best_match, highest_score, ingredient_name)

# LLM menulis reply empatik yang anchor ke verdict
llm_reply = await generate_safety_reply(
    ingredient_name=ingredient_name,
    db_match=best_match if safety_verdict != "not_found" else None,
    safety_verdict=safety_verdict,
    user_message=text,     # ← mengandung kondisi kesehatan user
    history=history,
)
reply = DISCLAIMER + llm_reply
```

**Fungsi helper baru:**
```python
def _build_safety_verdict(best_match, highest_score, ingredient_name) -> str:
    # Returns "safe" | "toxic" | "not_found"
    # Pure rule-based, tidak pernah memanggil LLM
```

---

## 4. Fitur Baru — Welcome Message untuk First-Time User

### File: `backend/routers/whatsapp.py`

Bot sekarang bisa digunakan **langsung via WhatsApp tanpa membuka web app** (standalone consultation channel). User yang bisa baca label bisa langsung konsultasi dengan mengetik nama bahan.

Ketika `_get_history(sender)` kosong (pesan pertama), bot mengirim welcome card sebelum memproses pesan:

```
Halo! Saya *FitMate* 🌿 — asisten keamanan produk TCM kamu.

Kamu bisa:
• Ketik nama bahan herbal untuk cek keamanannya
• Tanya "apakah [bahan] aman untuk [kondisimu]?"
• Minta info/manfaat bahan TCM apa saja

📋 *Catatan:* Jawaban saya berdasarkan database bahan TCM tervalidasi — bukan pengganti saran medis.

Langsung ketik nama bahan atau produk TCM yang ingin kamu cek! 💊
```

Welcome message ini hanya muncul **satu kali** (saat history masih kosong).

---

## 5. Fitur Baru — Multi-Ingredient List Detection

### File: `backend/routers/whatsapp.py`

User yang membaca label TCM seringkali ingin cek beberapa bahan sekaligus dengan cara mengetikkan daftar:

```
lo han guo, akar manis, jahe merah
```

Bot mendeteksi ini sebagai daftar (≥2 item, dipisah koma/newline, bukan kalimat penuh) dan menjalankan DB lookup untuk setiap bahan, lalu mengembalikan safety card gabungan:

```
⚕️ *Disclaimer:* Informasi ini bukan pengganti saran medis.

🔍 *Hasil cek 3 bahan:*

✅ *Lo Han Guo / Buah Biksu* — Aman
✅ *Akar Manis* — Aman
❓ *Jahe Merah* — Tidak ditemukan di database

Ada bahan lain yang ingin dicek, atau ingin tahu lebih detail? 🌿
```

Fungsi `_parse_multi_ingredient_list(text)` mendeteksi pola ini dengan heuristik:
- Tidak ada tanda `?` (bukan kalimat pertanyaan)
- Panjang total ≤ 20 kata
- Ada ≥ 2 token setelah split koma/newline

---

## 6. Perbaikan `generate_chat_reply()` untuk Standalone UX

### File: `backend/services/llm_intent.py`

**Sebelumnya:** Dibatasi keras "2-3 kalimat" — terlalu pendek untuk pertanyaan kompleks atau user yang menyebut kondisi kesehatan.

**Sekarang:**
- Batas diubah ke "3–5 kalimat" (lebih panjang jika pertanyaan kompleks atau ada kondisi kesehatan)
- System prompt secara eksplisit instruksikan LLM untuk **mengakui kondisi kesehatan yang disebutkan user**
- Menjelaskan kemampuan bot (standalone mode) dalam system prompt
- Jika pesan pertama (`is_first_message=True`): instruksi tambahan untuk perkenalkan diri

---

## Perbandingan Perilaku Bot

| Skenario | Sebelum | Setelah |
|---|---|---|
| `"Lo Han Guo aman?"` | Template generik | Reply empatik (verdict tetap dari DB) |
| `"Saya punya diabetes, aman?"` | Verdict saja, diabetes diabaikan | Verdict + **menyebut diabetes** + saran dokter |
| `"Saya hamil, apakah ginseng aman?"` | Generik, hamil tidak disebut | Verdict + **menyebut kehamilan** + peringatan ekstra |
| `"Apa itu Lo Han Guo?"` | LLM info reply | Sama (tidak berubah) |
| Pesan pertama `"halo"` | Nudge generik | **Welcome card** + penjelasan kemampuan bot |
| `"lo han guo, akar manis, jahe"` | Error / jawaban ngawur | **Multi-ingredient safety card** |

---

## Arsitektur File Saat Ini

```
backend/
├── .env                    ← TIDAK di-git, ada di disk, berisi semua secrets
├── core/
│   └── config.py           ← Settings pydantic + validate_security() startup check
├── database/
│   ├── mongo.py            ← Startup collection check + settings-based config
│   ├── seed_100_tcm.py     ← Script seed 100 bahan TCM ke MongoDB (sudah dijalankan)
│   └── check_db.py         ← Helper script untuk cek isi DB
├── routers/
│   ├── analyze.py          ← Rate limited 5/min, size check 10MB
│   ├── ocr.py              ← Rate limited 10/min, size check 10MB
│   ├── whatsapp.py         ← Health-aware replies, welcome msg, multi-ingredient, Twilio sig
│   ├── admin.py            ← Admin JWT auth (tidak berubah)
│   └── upload.py           ← Excel/CSV import (tidak berubah)
├── services/
│   ├── llm_intent.py       ← generate_safety_reply() baru, improved generate_chat_reply()
│   ├── vision.py           ← OpenRouter multimodal OCR (tidak berubah)
│   ├── safety.py           ← Fuzzy match OCR vs DB (tidak berubah)
│   └── whatsapp_service.py ← Twilio client wrapper (tidak berubah)
└── main.py                 ← SecurityHeadersMiddleware, CORS ketat, /health endpoint

frontend/
└── src/
    └── components/
        ├── layout/
        │   ├── TopAppBar.tsx       ← (tidak berubah)
        │   └── WhatsAppFAB.tsx     ← Global FAB (tidak berubah)
        └── results/
            ├── ResultsCard.tsx     ← Hapus duplicate WA button, tambah ScanResultCopy
            ├── ScanResultCopy.tsx  ← Copy-to-WhatsApp component
            ├── ToxicityWarning.tsx ← (tidak berubah)
            └── IngredientList.tsx  ← (tidak berubah)
```

---

## Konfigurasi `.env` (Referensi — Jangan Commit)

```env
# MongoDB
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=fitmate_db

# Twilio WhatsApp Sandbox
TWILIO_ACCOUNT_SID=AC0e96a5653592b0fb5cd9370b4349bdbe
TWILIO_AUTH_TOKEN=[REDACTED — ada di file .env lokal]
TWILIO_WHATSAPP_FROM=+14155238886

# OpenRouter — gemini-2.5-flash-lite
OPENROUTER_API_KEY=sk-or-v1-[REDACTED — ada di file .env lokal]
OPENROUTER_MODEL=google/gemini-2.5-flash-lite

# JWT Admin
JWT_SECRET_KEY=fitmate-dev-secret-key-change-in-production-32chars
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=8
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=[bcrypt hash 'admin123']
```

---

## Cara Menjalankan Development

```bash
# Backend
cd backend
.\venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (terminal terpisah)
cd frontend
npm run dev

# Ngrok tunnel untuk Twilio webhook (terminal terpisah)
ngrok http 8000
# Setelah ngrok jalan, update URL webhook di Twilio Console:
# https://console.twilio.com → WhatsApp Sandbox → Webhook URL
# → set ke: https://[ngrok-id].ngrok-free.app/whatsapp/webhook
```

---

## Test Cases untuk Verifikasi Bot

Kirimkan pesan-pesan berikut ke bot WhatsApp untuk memverifikasi perbaikan:

1. **Pesan pertama** — `"halo"` → harus muncul welcome card dulu, baru reply general
2. **Safety normal** — `"lo han guo aman?"` → reply empatik dengan verdict DB
3. **Safety + kondisi** — `"saya punya diabetes, apakah lo han guo aman?"` → **harus menyebut "diabetes"**
4. **Safety + hamil** — `"saya hamil, apakah ginseng aman?"` → **harus menyebut "hamil"/"kehamilan"**
5. **Multi-ingredient** — `"lo han guo, akar manis, jahe merah"` → safety card untuk 3 bahan
6. **Info intent** — `"apa itu lo han guo?"` → informational reply (tidak berubah)
7. **Multi-turn memory** — kirim `"lo han guo aman?"` lalu `"bahan tadi aman untuk hipertensi?"` → bot harus tahu "bahan tadi" = lo han guo

---

## Next Steps yang Disarankan

1. **Test semua test cases** di atas via Twilio sandbox sebelum melanjutkan
2. **Rotate API keys** — OpenRouter dan Twilio credentials pernah ter-commit ke git. Ganti dari dashboard masing-masing
3. **JWT secret** — Ganti `JWT_SECRET_KEY` di `.env` sebelum deploy production
4. **Database expansion** — 103 bahan saat ini. Pertimbangkan menambah data dari BPOM scraper untuk coverage lebih luas
5. **Vercel deployment** — Frontend siap deploy. Backend perlu EC2/Hostinger dengan domain + HTTPS untuk Twilio webhook
6. **Prompt tuning** — Setelah test, mungkin perlu adjust panjang reply atau tone sesuai user feedback

> ⚠️ **PENTING UNTUK AGENT BERIKUTNYA:** History git sebelumnya masih mengandung credentials OpenRouter dan Twilio. Jika repo ini public atau akan dipush, **rotasikan** credentials tersebut dari dashboard masing-masing segera.
