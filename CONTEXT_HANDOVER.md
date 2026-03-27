# Context Handover: FitMate TCM — Sesi Maret 2026 (Sesi 2)

> Dokumen ini adalah kelanjutan dari `CONTEXT_HANDOVER.md` sebelumnya. Berisi semua perubahan yang dilakukan **dalam sesi ini** sehingga agent AI berikutnya dapat langsung melanjutkan tanpa perlu riset ulang.

---

## Status Saat Ini

- **Backend**: Berjalan di `http://localhost:8000` dengan `uvicorn --reload`
- **Database**: MongoDB lokal, collection `tcm_ingredients` berisi **103 bahan TCM** (berhasil di-seed)
- **WhatsApp Bot**: Twilio Sandbox aktif (perlu ngrok tunnel yang hidup)
- **Frontend**: Next.js, berjalan terpisah (biasanya `npm run dev` di `/frontend`)
- **Git branch**: `main`, semua perubahan sudah di-commit

---

## Ringkasan Perubahan Sesi Ini (Commit `705358c` & `9783cb7`)

---

## 1. Bug UI — Tombol WhatsApp Duplikat Dihapus

### File: `frontend/src/components/results/ResultsCard.tsx`

**Masalah:** Halaman hasil scan menampilkan **dua** tombol WhatsApp secara bersamaan:
1. Green bar besar (fixed, `bottom-24`) yang ada di dalam `ResultsCard.tsx`
2. FAB circle (fixed, `bottom-6 right-5`) yang ada di `layout.tsx` sebagai komponen global

Kedua tombol ini tumpang tindih dan membingungkan.

**Perbaikan:**
- Dihapus seluruh blok `{/* WhatsApp Button - Always present */}` dari `ResultsCard.tsx`
- Dihapus `mb-32` bottom margin yang awalnya untuk memberi ruang tombol tersebut
- `WhatsAppFAB` di `layout.tsx` adalah satu-satunya entry point konsultasi via WhatsApp

---

## 2. Bug Bot — "Maaf, layanan AI sedang tidak tersedia"

### File: `backend/services/llm_intent.py`

**Masalah:** Fungsi `_chat()` memiliki retry logic dengan `_RETRY_BASE_DELAY = 5` detik dan `_MAX_RETRIES = 3`. Total waktu tunggu bisa mencapai **35 detik** (5s + 10s + 20s). Ini melebihi batas toleransi webhook Twilio, menyebabkan semua pesan setelahnya gagal dan bot membalas "layanan tidak tersedia".

**Perbaikan:**
- `_RETRY_BASE_DELAY` diturunkan dari `5` → `2` detik
- `_MAX_RETRIES` diturunkan dari `3` → `2`
- Total waktu tunggu maksimum: **8 detik** (2s + 4s)
- Ditambahkan parameter `timeout` per-call ke fungsi `_chat()` (intent: 12s, reply: 15s)

---

## 3. Peningkatan Bot — Sistem 3-Intent Fleksibel

### File: `backend/services/llm_intent.py`

**Sebelumnya:** Bot hanya memiliki 2 intent: `ingredient_inquiry` dan `general_chat`. Bot terlalu kaku — pertanyaan umum kesehatan sering dibalas generik atau error.

**Sekarang:** 3 kelas intent:

| Intent | Trigger | Perilaku Bot |
|--------|---------|--------------|
| `ingredient_safety_inquiry` | "apakah X berbahaya?", "X aman tidak?", "kontraindikasi X?" | **Strict DB lookup** — tidak ada LLM untuk verdi keamanan. Hasilnya 100% dari database |
| `ingredient_info_inquiry` | "apa itu X?", "manfaat X?", "X untuk apa?" | DB lookup untuk konteks → LLM generate penjelasan informatif |
| `general_tcm_chat` | salam, pertanyaan umum kesehatan, off-topic | LLM menjawab singkat (2-3 kalimat) → selalu diakhiri redirect ke TCM |

**Fungsi baru:**
- `parse_intent(text, history)` — sekarang menerima history percakapan sebagai konteks
- `generate_chat_reply(text, history)` — menerima history untuk multi-turn
- `generate_ingredient_info_reply(ingredient_name, db_match, history)` — fungsi baru untuk info intent
- `_chat(messages, temperature, timeout)` — signature diubah dari `user_content: str` menjadi `messages: list[dict]` untuk mendukung multi-turn OpenRouter API

**Perilaku general_tcm_chat:**
- Menjawab pertanyaan kesehatan umum (misalnya "apa buah sehat?") dengan singkat
- **Selalu** mengakhiri dengan: *"Ada produk TCM atau herbal yang ingin kamu cek keamanannya? 🌿"*
- Ini mengarahkan user kembali ke konteks TCM tanpa memblokir percakapan natural

---

## 4. Fitur Baru Bot — Conversation Memory (Multi-turn)

### File: `backend/routers/whatsapp.py`

**Masalah:** Bot sebelumnya stateless — setiap pesan diproses secara independen. Referensi seperti *"bahan itu"*, *"yang tadi"*, *"apakah aman?"* tidak bisa diselesaikan tanpa konteks sebelumnya.

**Solusi:** Per-user conversation history disimpan di `TTLCache`:

```python
_conversation_store: TTLCache = TTLCache(maxsize=1000, ttl=7200)
MAX_HISTORY_USER_BUBBLES = 15
```

**Detail implementasi:**
- **Kapasitas:** Maks 1000 user berbeda secara bersamaan
- **Expiry:** 2 jam (`ttl=7200`) sejak pesan terakhir — otomatis dihapus jika tidak aktif
- **Batas history:** Maks 15 user bubble (+ paired bot reply-nya). Kalau lebih, bubble terlama otomatis di-trim
- **Fungsi helper:**
  - `_get_history(phone)` — mengambil history untuk nomor tertentu
  - `_append_history(phone, role, content)` — menambah pesan dan melakukan trimming
- **Alur:** History di-load di awal `_process_message()`, dikirim ke `parse_intent()` sebagai context snippet (5 pesan terakhir user), dan ke semua fungsi reply sebagai full `messages[]` array
- History diupdate setelah user message DAN setelah bot reply

**Efek nyata:**
- "apakah bahan itu aman?" → `parse_intent()` melihat 5 pesan terakhir user, mengekstrak nama bahan yang dimaksud dari konteks sebelumnya
- "yang tadi disebutkan" → LLM sudah punya full history, bisa resolve reference
- Follow-up pertanyaan (dosis, kontraindikasi, dll.) tetap koheren

---

## 5. Keamanan — API Rate Limiting pada Scanner

### File: `backend/routers/analyze.py`

```python
@router.post("/")
@limiter.limit("5/minute")
async def analyze_tcm_label(request: Request, ...):
```

- Endpoint `/api/v1/analyze/` sekarang dibatasi **5 request per menit per IP**
- Tambahan validasi: file size maksimum **10MB** (sebelumnya tidak ada batas)
- Parameter `request: Request` ditambahkan (wajib untuk slowapi)

### File: `backend/routers/ocr.py`

```python
@router.post("/upload")
@limiter.limit("10/minute")
async def process_image_ocr(request: Request, ...):
```

- Endpoint `/api/v1/ocr/upload` dibatasi **10 request per menit per IP**
- Tambahan validasi file size 10MB
- Parameter `request: Request` ditambahkan

---

## 6. Keamanan — Validasi Signature Webhook Twilio

### File: `backend/routers/whatsapp.py`

```python
def _validate_twilio_signature(request_url: str, params: dict, signature: str) -> bool:
    from twilio.request_validator import RequestValidator
    validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
    return validator.validate(request_url, params, signature)
```

- Setiap webhook request dari Twilio divalidasi dengan header `X-Twilio-Signature`
- Jika signature tidak cocok → request di-drop silently (return `{"status": "ok"}` tanpa proses)
- Ini mencegah siapapun menyuntikkan pesan palsu ke webhook `/whatsapp/webhook`
- URL rekonstruksi mempertimbangkan header `X-Forwarded-Proto` dan `X-Forwarded-Host` untuk kompatibilitas ngrok

---

## 7. Keamanan — Security Headers & CORS Diperketat

### File: `backend/main.py`

**Security Headers Middleware baru:**
```python
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    # Ditambahkan ke semua response:
    # X-Content-Type-Options: nosniff
    # X-Frame-Options: DENY
    # X-XSS-Protection: 1; mode=block
    # Referrer-Policy: strict-origin-when-cross-origin
    # Permissions-Policy: camera=(*), microphone=()
```

**CORS diperketat:**
- Dihapus `http://localhost:8000` dari allowed origins (port API tidak boleh di-akses browser secara CORS)
- Allowed origins: `http://localhost:3000` dan `https://fitmate-tcm.vercel.app` saja
- HTTP methods dikurangi dari `[GET, POST, PUT, DELETE, OPTIONS]` → `[GET, POST, OPTIONS]`
- Allowed headers dikurangi dari `*` → `["Content-Type", "Authorization"]`

**Endpoint baru:**
- `GET /health` — health check untuk uptime monitoring
- Docs URL diubah ke `/api/docs` (lebih tersembunyi)

---

## 8. Keamanan — `backend/.env` Dikeluarkan dari Git

**Masalah kritis:** File `backend/.env` sebelumnya **ter-track oleh git** dan berisi:
- `OPENROUTER_API_KEY=sk-or-v1-...`
- `TWILIO_ACCOUNT_SID=AC...`
- `TWILIO_AUTH_TOKEN=...`

**Perbaikan:**
```bash
git rm --cached backend/.env
```
Baris `backend/.env` ditambahkan ke `.gitignore`. File `.env` **tetap ada di disk** (tidak dihapus), hanya tidak lagi dipush ke GitHub.

> ⚠️ **PENTING UNTUK AGENT BERIKUTNYA:** History git sebelumnya masih mengandung credentials ini. Jika repo ini public atau akan dipush, **rotasikan** OpenRouter API key dan Twilio credentials dari dashboard masing-masing.

---

## 9. Config & DB — Perbaikan Settings & Startup Check

### File: `backend/core/config.py`

- Ditambahkan `MONGODB_URL` dan `MONGODB_DB_NAME` sebagai field Pydantic resmi (sebelumnya hanya dibaca langsung dari `os.environ`)
- Ditambahkan method `validate_security()` yang memanggil warning saat startup jika:
  - `JWT_SECRET_KEY` adalah nilai default yang lemah
  - `ADMIN_PASSWORD_HASH` kosong (admin login disabled)
  - `OPENROUTER_API_KEY` tidak di-set

### File: `backend/database/mongo.py`

- Migrasi dari `os.environ.get(...)` → `settings.MONGODB_URL` / `settings.MONGODB_DB_NAME`
- Ditambahkan startup check: jika `tcm_ingredients` collection kosong, cetak warning jelas:
  ```
  ⚠️ [DB] WARNING: tcm_ingredients collection is EMPTY!
     Run: python database/seed_100_tcm.py
  ```
- Jika berhasil: `✅ [DB] Connected to MongoDB — 103 ingredients in tcm_ingredients`

---

## 10. Fitur Baru Frontend — Scan Result Copy-to-WhatsApp

### File: `frontend/src/components/results/ScanResultCopy.tsx` *(baru)*

Komponen baru yang muncul di bawah hasil scan setelah setiap scan berhasil.

**Fungsi:**
```typescript
function buildCopyText(ingredients: any[]): string
// Output contoh:
// 🔍 *Hasil Scan FitMate:*
// Bahan yang terdeteksi:
//
// ✅ Lo Han Guo / Buah Biksu
// ❓ Forsythiae Fructus
// ❓ Lonicerae Japonicae Flos
//
// Tolong bantu saya memahami lebih lanjut tentang bahan-bahan di atas...
```

**UI Elements:**
1. **Header** — WhatsApp branding dengan ikon hijau
2. **Preview box** — Menampilkan teks yang akan disalin/dikirim
3. **"Salin Pesan" button** — Copy ke clipboard, berubah jadi "Tersalin! ✓" (hijau) selama 3 detik, lalu kembali normal
4. **"Buka di WhatsApp" button** — `<a href="https://wa.me/14155238886?text=...">` dengan pesan pre-filled lengkap
5. **Instruction text** — *"💡 Salin pesan di atas, lalu kirimkan ke chatbot WhatsApp FitMate untuk konsultasi lebih lanjut tentang hasil scan Anda."*

**Logic:**
- Ingredient dengan `category === "toxic"` atau `"contraindicated"` → emoji ⚠️
- `category === "safe"` → emoji ✅
- Lainnya (unknown) → emoji ❓
- Nama yang ditampilkan: `indonesian_name` → fallback ke `matched_mandarin` → fallback ke `detected_text`

### File: `frontend/src/components/results/ResultsCard.tsx`

- Import `ScanResultCopy` ditambahkan
- `<ScanResultCopy ingredients={ingredients} />` dirender setelah `</section>`
- Subtle hint text di kanan bawah kartu verifikasi: *"💬 Tap tombol WhatsApp di pojok kanan bawah..."*

---

## 11. Rate Limiting Bot WhatsApp

### File: `backend/routers/whatsapp.py`

- Diubah dari `TTLCache(maxsize=1000, ttl=60)` dengan batas 10 pesan/60 detik
- Menjadi `TTLCache(maxsize=1000, ttl=600)` dengan batas **20 pesan per 10 menit**
- Lebih fair untuk percakapan panjang (tidak memutus conversation ditengah jalan)
- Cache diberi nama eksplisit: `_rate_limit_cache` (untuk konsistensi dengan `_conversation_store`)

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
│   ├── whatsapp.py         ← 3-intent routing, conversation memory, Twilio signature validation
│   ├── admin.py            ← Admin JWT auth (tidak berubah)
│   └── upload.py           ← Excel/CSV import (tidak berubah)
├── services/
│   ├── llm_intent.py       ← _chat() multi-turn, 3 intent classes, history support
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
            ├── ScanResultCopy.tsx  ← BARU: copy-to-WhatsApp component
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

## Next Steps yang Disarankan

1. **Rotate API keys** — OpenRouter dan Twilio credentials pernah ter-commit ke git. Ganti dari dashboard masing-masing
2. **JWT secret** — Ganti `JWT_SECRET_KEY` di `.env` sebelum deploy production
3. **Test conversation memory** — Kirim "lo han guo aman?" → lalu "apakah untuk ibu hamil aman?" → bot seharusnya tetap tahu konteksnya lo han guo
4. **Test copy button** — Scan produk → lihat tombol "Salin Pesan" dan "Buka di WhatsApp" di bawah hasil
5. **Vercel deployment** — Frontend siap deploy. Backend perlu EC2/Hostinger dengan domain + HTTPS untuk Twilio webhook
6. **Database expansion** — 103 bahan saat ini. Pertimbangkan menambah data dari BPOM scraper untuk coverage lebih luas
