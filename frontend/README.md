# FitMate Frontend

FitMate Frontend is a Progressive Web App (PWA) built with Next.js 14 (App Router) and Tailwind CSS, tailored around the "Modern Apothecary" aesthetic. It provides a visual scanner for Traditional Chinese Medicine (TCM) product packaging, real-time safety analysis, an interactive 500-ingredient dictionary, and cross-device synchronization (Bridge Mode).

> **Pemberitahuan Prototipe:** Aplikasi ini berstatus prototipe riset untuk tujuan edukasi. Basis data 500 bahan bersumber dari publikasi BPOM dan SymMap tanpa validasi medis apoteker klinis perorangan. Seluruh analisis keamanan bersifat skrining awal dan bukan rekomendasi resep obat dokter.

---

## Fitur dan Komponen

### 1. Viewfinder Kamera Adaptif (`CameraViewfinder.tsx`)
- **Responsif Multi-Device:** Menghindari pemborosan ruang tampilan desktop.
  - Pada layar mobile, kamera ditampilkan dalam rasio portrait (`aspect-[3/4]`).
  - Pada layar desktop/tablet (`md:` ke atas), viewfinder bertransformasi menjadi rasio landscape lebar 16:9 (`md:aspect-video`) dengan panel kontrol sisi samping.
- **Pilihan Input Fleksibel:** Mendukung streaming kamera langsung (HTML5 MediaDevices), pemilihan kamera (depan/belakang), serta opsi unggah berkas gambar mandiri.
- **Ikon Tema Murni:** Seluruh indikator dan tombol menggunakan SVG bertema botani modern tanpa emoji kasual.

### 2. Sesi Bridge Lintas Perangkat (`QRCodeBridge.tsx`)
- **Mode Dua Arah (Desktop ke Mobile dan Sebaliknya):**
  - Desktop menampilkan kode QR dinamis dengan UUID unik (`/scanner?bridge_session=<UUID>`).
  - Pengguna dapat memindai QR menggunakan kamera smartphone untuk membuka antarmuka pemindai ponsel.
  - Hasil pemindaian pada smartphone secara instan tersinkronisasi kembali ke layar desktop secara otomatis melalui endpoint polling backend.
  - Pengguna juga dapat memilih alur mandiri (Standalone) di desktop atau HP tanpa wajib menggunakan dua perangkat.

### 3. Kartu Hasil dan Audit Keamanan (`ResultsCard.tsx` & `ScanResultCopy.tsx`)
- **Deteksi Batasan Non-Herbal:** Jika produk yang dipindai adalah makanan ringan atau camilan kemasan umum (seperti rice crackers, biskuit, tepung, penyedap rasa), sistem secara tegas mengelompokkannya sebagai non-herbal, bukan mengklaim bahan sebagai ramuan herbal terverifikasi.
- **Visualisasi Status Bahan:**
  - *Bahan Berisiko (Crimson Danger):* Menampilkan peringatan bahaya, organ target yang terpengaruh, dan kontraindikasi.
  - *Bahan Terdaftar Aman (Forest Trust):* Konfirmasi bahan herbal tradisional yang tercatat dalam kompilasi data.
  - *Bahan Tidak Terdaftar (Subtle Neutral):* Penandaan zat yang belum ada di basis data 500 bahan.
- **Salin Hasil & Deep Link WhatsApp:** Menghasilkan pesan terstruktur untuk konsultasi lanjutan dengan asisten bot WhatsApp FitMate (`wa.me`).

### 4. Kamus TCM 500 Bahan (`IngredientSearchModal.tsx`)
- Pencarian instan multibahasa (Indonesia, Mandarin Hanzi, Pinyin, dan nama Latin).
- Filter status keamanan (Berisiko vs Aman).
- Penjelasan khasiat umum, peringatan dosis, dan catatan kontraindikasi.

### 5. Floating Action Button WhatsApp (`WhatsAppFAB.tsx`)
- Akses cepat untuk memulai percakapan dengan asisten bot FitMate WhatsApp.

---

## Struktur Folder

```
frontend/
├── public/                  # Ikon PWA, manifest, favicon
├── src/
│   ├── app/
│   │   ├── layout.tsx       # Root layout, font Geist, theme wrapper
│   │   ├── page.tsx         # Halaman utama (Scanner, Bridge, Results)
│   │   └── globals.css      # Styling global, variabel CSS Modern Apothecary
│   ├── components/
│   │   ├── layout/          # Header, Footer, WhatsAppFAB
│   │   ├── results/         # ResultsCard, ScanResultCopy
│   │   ├── scanner/         # CameraViewfinder, QRCodeBridge
│   │   └── search/          # IngredientSearchModal
│   └── types/               # Definisi antarmuka TypeScript
├── tailwind.config.ts       # Konfigurasi warna, border-radius, bayangan
├── tsconfig.json            # Konfigurasi TypeScript
└── package.json             # Dependensi proyek
```

---

## Panduan Menjalankan

### Instalasi Dependensi
```bash
npm install
```

### Konfigurasi Variabel Lingkungan
Buat file `.env.local` pada direktori root frontend:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```
Untuk produksi, arahkan ke endpoint live API Hugging Face:
```env
NEXT_PUBLIC_API_URL=https://benedictpepper-fitmate-api.hf.space
```

### Server Pengembangan
```bash
npm run dev
```
Akses di `http://localhost:3000`.

### Membangun Versi Produksi
```bash
npm run build
npm run start
```
