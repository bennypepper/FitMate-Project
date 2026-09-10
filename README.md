# FitMate

FitMate is an intelligent Traditional Chinese Medicine (TCM) safety scanner and automated advisory assistant built as a Progressive Web App (PWA) with a WhatsApp chatbot companion. The system enables consumers to inspect TCM and herbal product packaging using their device camera or file upload, extracts Mandarin Hanzi and Latin ingredient text, cross-references findings against a curated 500-ingredient TCM database derived from BPOM and SymMap publications, and flags hazardous adulterants or contraindications with zero AI hallucination.

When risk indicators or unfamiliar substances are identified, users can seamlessly transition to an automated WhatsApp advisory bot via prefilled deep links for follow-up inquiries.

> **Status Prototipe Riset:** FitMate merupakan prototipe sistem berbasis kecerdasan buatan (AI bot) untuk tujuan edukasi dan skrining awal. Basis data 500 bahan TCM dikompilasi dari publikasi resmi BPOM dan literatur SymMap, namun belum divalidasi secara klinis oleh apoteker atau dokter manusia. Sistem ini bukan pengganti diagnosis atau resep medis profesional.

---

## Fitur Utama

- **Pemindai OCR Multimodal Cerdas:** Ekstraksi dan translasi karakter Hanzi, Pinyin, dan nama Latin secara cepat menggunakan pipeline multimodal Gemini 2.5 Flash Lite via OpenRouter.
- **Deteksi Batasan Produk Non-Herbal:** Membedakan produk pangan atau camilan umum (seperti biskuit beras, tepung, penyedap) dari produk herbal asli, mencegah klaim keliru bahwa produk non-herbal adalah ramuan herbal terverifikasi.
- **Pemeriksaan Toksisitas Berbasis Aturan Baku:** Validasi keamanan dilakukan murni melalui pencocokan aturan deterministik pada basis data MongoDB, menjamin rekomendasi risiko bebas dari halusinasi model bahasa.
- **Tampilan Kamera Adaptif Desktop:** Viewfinder kamera responsif yang otomatis menyesuaikan rasio layar: rasio portrait pada perangkat mobile dan rasio landscape lebar (16:9 widescreen) dengan kontrol sisi samping pada layar desktop untuk memaksimalkan ruang tampilan.
- **Fleksibilitas Alur Penggunaan (Standalone & Bridge Mode):**
  - *Standalone:* Pengguna dapat memindai atau mengunggah foto langsung di satu perangkat (baik HP maupun laptop/desktop).
  - *Bridge Mode (Dua Arah):* Pengguna desktop dapat menampilkan kode QR interaktif ber-UUID unik. Saat dipindai dengan smartphone, hasil analisis kamera ponsel langsung tersinkronisasi kembali ke layar desktop secara otomatis.
- **Kamus TCM 500 Bahan:** Pencarian cepat bahan herbal dengan dukungan nama Indonesia, Mandarin, Pinyin, nama Latin, status toksisitas, dan kontraindikasi.
- **Asisten WhatsApp Terintegrasi:** Bot edukasi WhatsApp dengan pencegah darurat medis (119 SPGDT) dan filter deteksi Bahan Kimia Obat (BKO) ilegal sebelum pesan diproses.
- **Desain Modern Apothecary:** Antarmuka bersih bernuansa botani modern menggunakan palet Forest Green, Sage, Sand/Paper, dan Crimson Warning, bebas dari emoji kasual dan didukung ikon SVG bertema.

---

## Arsitektur Sistem

```
+-------------------------------------------------------------------------+
|                              FRONTEND                                   |
|  Next.js 14 App Router | Tailwind CSS | Modern Apothecary Theme         |
|                                                                         |
|  +------------------------+  +-------------------+  +----------------+  |
|  | Standalone Mode        |  | Bridge Mode (QR)  |  | Kamus TCM      |  |
|  | (Camera / File Upload) |  | (Cross-Device)    |  | (500 Bahan)    |  |
|  +------------------------+  +-------------------+  +----------------+  |
+-----------------------------------|-------------------------------------+
                                    | REST API / Polling
                                    v
+-------------------------------------------------------------------------+
|                               BACKEND                                   |
|  FastAPI (Python 3.11) | Uvicorn                                        |
|                                                                         |
|  +-------------------------+  +---------------------------------------+  |
|  | /api/scan (OCR & Audit) |  | /api/bridge (QR Session & Sync)       |  |
|  +-------------------------+  +---------------------------------------+  |
|  | /whatsapp/webhook       |  | /api/tcm/search & /api/tcm/list       |  |
|  +-------------------------+  +---------------------------------------+  |
|                                                                         |
|  +-------------------------------------------------------------------+  |
|  | Pre-LLM Safety Interceptor                                        |  |
|  | - Emergency Detection (119 SPGDT)                                 |  |
|  | - BKO Interception (Bahan Kimia Obat BPOM)                        |  |
|  | - Non-Herbal Boundary Verifier                                    |  |
|  +-------------------------------------------------------------------+  |
+-------------------|-----------------------------------|-----------------+
                    |                                   |
                    v                                   v
+-----------------------------+       +-----------------------------------+
|       DATABASE LAYER        |       |         EXTERNAL SERVICES         |
|  MongoDB Atlas              |       |  OpenRouter (Gemini 2.5 Flash)    |
|  - 500 TCM Ingredients      |       |  Twilio WhatsApp Cloud API        |
|  - Bridge Sessions (TTL)    |       +-----------------------------------+
+-----------------------------+
```

---

## Tech Stack

- **Frontend:** Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, Custom SVGs
- **Backend:** Python 3.11, FastAPI, Pydantic v2, Motor (Async MongoDB Driver)
- **Database:** MongoDB Atlas (Koleksi `tcm_ingredients`, `bridge_sessions`)
- **Model Kecerdasan Buatan:** Gemini 2.5 Flash Lite via OpenRouter
- **Konektivitas WhatsApp:** Twilio WhatsApp Sandbox / Cloud API
- **Infrastruktur & Deployment:**
  - Frontend: Vercel Production (`https://fitmate-project.vercel.app`)
  - Backend: Hugging Face Docker Space (`https://benedictpepper-fitmate-api.hf.space`)

---

## Menjalankan Proyek Secara Lokal

### Prasyarat
- Node.js versi 18 atau lebih baru
- Python versi 3.11 atau lebih baru
- Akun dan Connection String MongoDB Atlas
- API Key OpenRouter

### 1. Setup Backend

```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
```

Salin file contoh konfigurasi dan lengkapi variabel lingkungan:
```bash
cp .env.example .env
```

Jalankan server pengembangan FastAPI:
```bash
uvicorn main:app --reload --port 8000
```

Backend aktif di `http://127.0.0.1:8000`. Dokumentasi OpenAPI interaktif tersedia di `http://127.0.0.1:8000/docs`.

### 2. Setup Frontend

```bash
cd frontend
npm install
```

Buat file `.env.local` pada folder `frontend`:
```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

Jalankan server pengembangan Next.js:
```bash
npm run dev
```

Buka peramban di `http://localhost:3000`.

---

## Endpoint API Utama

- `POST /api/scan`: Menerima berkas gambar label atau base64, menjalankan OCR multimodal, memverifikasi batas herbal vs pangan, dan mencocokkan kandungan pada basis data 500 bahan.
- `GET /api/tcm/search?q={query}`: Pencarian fuzzy multibahasa untuk bahan TCM.
- `GET /api/tcm/list?limit=500`: Mengambil katalog bahan TCM terdaftar.
- `POST /api/bridge/create`: Membuat sesi bridge cross-device baru dengan token UUID dan URL QR code.
- `GET /api/bridge/poll/{session_id}`: Polling berkala untuk sinkronisasi hasil pindai dari smartphone ke desktop.
- `POST /api/bridge/complete/{session_id}`: Mengunggah hasil pemindaian smartphone ke sesi bridge desktop.
- `POST /whatsapp/webhook`: Webhook integrasi Twilio untuk memproses pesan WhatsApp masuk melalui lapisan interceptor keselamatan dan LLM intent router.

---

## Lisensi dan Hak Cipta

Proyek ini dilisensikan di bawah Apache License 2.0. Lihat berkas [LICENSE](LICENSE) file untuk informasi lebih lanjut.
