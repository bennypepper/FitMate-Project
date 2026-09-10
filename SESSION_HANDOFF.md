# Session Handoff: FitMate: Production System State & Architecture

- Tanggal: 2026-09-10
- Status: Production Ready (Vercel + Hugging Face Spaces Live)
- Klasifikasi: Prototipe Riset (Edukasi & Skrining Keamanan TCM Berbasis AI)

---

## 1. Ringkasan Status Sistem (System Summary)

FitMate adalah sistem pemindai keamanan obat tradisional Tiongkok (Traditional Chinese Medicine / TCM) dan asisten bot konsultasi berbasis Progressive Web App (PWA) dan WhatsApp. Sistem ini mengatasi hambatan bahasa kemasan Hanzi Mandarin dan mencegah bahaya swamedikasi tanpa pengawasan bagi konsumen Indonesia.

### Pencapaian Terkini:
1. **Basis Data 500 Bahan TCM:**
   - Dikompilasi secara terstruktur dari publikasi resmi Badan Pengawas Obat dan Makanan (BPOM) dan basis data farmakologi SymMap.
   - Menyimpan variasi nama Indonesia, Mandarin Hanzi, Pinyin, nama ilmiah Latin, status toksisitas, organ target, deskripsi, dan catatan kontraindikasi.
   - Status prototipe: data dikompilasi secara algoritmik dan belum melalui uji klinis tatap muka oleh apoteker manusia perorangan.
2. **Kamera Adaptif Desktop (Widescreen 16:9):**
   - Menghindari pemborosan ruang layar horizontal pada monitor desktop atau laptop.
   - Pada layar mobile: aspect ratio portrait (3:4) untuk kenyamanan satu tangan.
   - Pada layar desktop (`md:` ke atas): aspect ratio landscape lebar (16:9 widescreen) dengan kontrol dan instruksi di sisi samping.
3. **Fleksibilitas Alur Penggunaan (Standalone & Bridge Mode):**
   - *Standalone:* Pengguna dapat memindai atau mengunggah gambar langsung di satu perangkat (baik HP maupun desktop/laptop) tanpa dipaksa menggunakan dua perangkat.
   - *Bridge Mode:* Pengguna desktop dapat menampilkan kode QR dinamis dengan UUID unik. Ketika dipindai menggunakan smartphone, ponsel menjalankan pemindaian dan hasilnya langsung tersinkronisasi kembali ke layar desktop secara otomatis via polling backend.
4. **Verifikasi Batas Produk Non-Herbal:**
   - Model multimodal Gemini 2.5 Flash Lite membedakan camilan pangan kemasan (seperti biskuit beras, kerupuk, tepung, penyedap rasa) dari produk herbal obat tradisional.
   - Produk pangan diberi label non-herbal secara transparan, mencegah klaim keliru bahwa camilan pangan adalah obat herbal terverifikasi.
5. **WhatsApp Bot & Pre-LLM Safety Interceptor:**
   - Integrasi Twilio WhatsApp Webhook dengan perlindungan interceptor keselamatan berlapis:
     - Deteksi darurat medis (nyeri dada, sesak napas, muntah darah) langsung mengarahkan ke Ambulans Nasional (119 SPGDT).
     - Deteksi Bahan Kimia Obat (BKO ilegal BPOM: Sildenafil, Dexamethasone, Paracetamol, dll.) langsung memberikan peringatan keras dan kontak BPOM (1500-533).
     - Asisten secara eksplisit memposisikan diri sebagai program bot komputer otomatis (AI bot), tidak mengaku atau menggantikan apoteker/dokter manusia.
6. **Desain Modern Apothecary & Zero Emojis:**
   - Seluruh emoji kasual di frontend dan respon otomatis backend telah dihapus dan diganti dengan ikon SVG bertema (Forest Green, Sage, Sand/Paper, Crimson) atau tag teks terstruktur (`[Aman]`, `[Berisiko]`, `[Peringatan]`).
   - Tidak ada penggunaan em dash pada antarmuka maupun seluruh dokumen proyek.

---

## 2. Arsitektur & Lingkungan Produksi (Environments)

- **Frontend Live URL:** `https://fitmate-project.vercel.app` (Next.js 14 di Vercel)
- **Backend Live URL:** `https://benedictpepper-fitmate-api.hf.space` (FastAPI Docker di Hugging Face Spaces)
- **Local Dev Endpoints:**
  - Backend API: `http://127.0.0.1:8000` (FastAPI / Uvicorn)
  - Frontend PWA: `http://localhost:3000` (Next.js 14)
- **Database:** MongoDB Atlas (Koleksi `tcm_ingredients` 500 item, `bridge_sessions` TTL 30 menit)

---

## 3. Struktur Berkas & Komponen Kunci

### Backend (`/backend`)
- `main.py`: Entrypoint FastAPI, routing CORS untuk Vercel & local, konfigurasi middleware.
- `routers/whatsapp.py`: Webhook WhatsApp Twilio, rate limiter, intent routing, format pesan teks bersih tanpa emoji.
- `services/llm_intent.py`: Classifier intent multimodal dan generator respon terarah menggunakan Gemini 2.5 Flash Lite via OpenRouter.
- `services/safety_interceptor.py`: Interceptor pra-LLM darurat (119 SPGDT) dan BKO BPOM.
- `data/bko_substances.json`: Kamus alias Bahan Kimia Obat berbahaya dari data resmi BPOM.
- `seed_500_tcm.py`: Skrip seeding 500 bahan TCM ke MongoDB Atlas.
- `deploy_hf.py`: Otomasi deployment backend ke Hugging Face Docker Space.

### Frontend (`/frontend`)
- `src/app/page.tsx`: Halaman utama aplikasi dengan tab Standalone, Bridge Mode, banner non-herbal, dan kartu hasil.
- `src/components/scanner/CameraViewfinder.tsx`: Viewfinder kamera responsif (portrait di HP, widescreen 16:9 di desktop) dengan kontrol SVG.
- `src/components/scanner/QRCodeBridge.tsx`: Generator QR session lintas perangkat dengan sistem polling otomatis.
- `src/components/results/ResultsCard.tsx` & `ScanResultCopy.tsx`: Kartu audit keamanan bahan herbal dan non-herbal dengan tombol konsultasi WhatsApp.
- `src/components/search/IngredientSearchModal.tsx`: Kamus pencarian interaktif 500 bahan TCM.
- `src/components/layout/WhatsAppFAB.tsx`: Tombol aksi melayang menuju asisten bot WhatsApp FitMate.

---

## 4. Status Pengujian & Verifikasi

- **Emoji Audit:** 0 emoji di seluruh backend python files, 0 emoji di seluruh frontend TypeScript/React files.
- **Em Dash Audit:** 0 em dash di seluruh dokumentasi proyek (`README.md`, `frontend/README.md`, `docs/PRD.md`, `docs/RESEARCH_PAPER.md`, `docs/FUTURE_DEVELOPMENTS.md`, `SESSION_HANDOFF.md`).
- **Verifikasi Build:**
  - Frontend build: `npm run build` sukses tanpa error.
  - Backend integration test: semua unit & integrasi tes lulus.
