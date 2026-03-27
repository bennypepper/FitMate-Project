# Context Handover: FitMate TCM Bot & Scanner Updates (Maret 2026)

Dokumen ini berisi rangkuman perubahan dan perbaikan fundamental yang baru saja dilakukan pada arsitektur **backend FitMate** untuk memandu pengembangan tahap selanjutnya oleh agen AI lain di *conversation* berikutnya.

---

## 1. Perbaikan Skema & Seed Database (`backend/database/`)
- **Masalah Sebelumnya:** *WhatsApp Bot* gagal menemukan data (*“tidak ditemukan dalam database kami”*) karena mencoba melakukan pencarian pada collection `ingredients` yang kosong, sementara skema Pydantic (`schemas.py`) mengharuskan nama collection `tcm_ingredients`.
- **Perbaikan:** 
  - Melakukan riset komprehensif terhadap **100 bahan dan suplemen TCM paling populer** di Indonesia (seperti *Lo Han Guo*, *Ginseng*, *Pien Tze Huang*, hingga herbal masakan Ciakpo).
  - Menyimpan referensi murni ke dalam `backend/data/100_popular_tcm_indonesia.md`.
  - Merancang script _direct-injection_ baru yaitu `backend/database/seed_100_tcm.py` yang melompati validasi Excel dan menanam 100 data tersebut secara langsung ke collection `tcm_ingredients`.

## 2. Refaktorisasi Logika Pencarian Bot WhatsApp (`backend/routers/whatsapp.py`)
- **Masalah Sebelumnya:** Pencarian fuzzy match masih kaku untuk nama string parsial. Algoritma `fuzz.token_sort_ratio` memberikan skor sangat rendah (< 65%) ketika *user* mencari `"ginseng"` namun terdata di *database* sebagai `"Panax Ginseng"`.
- **Perbaikan:**
  - Mengubah penargetan MongoDB collection dari `db["ingredients"]` menjadi `db["tcm_ingredients"]`.
  - Memperluas array variabel *candidate matching* untuk meliputi `pinyin_name`, `english_name`, `latin_name`, `mandarin_name`, dan `indonesian_name`.
  - Mengganti fungsi `fuzz.token_sort_ratio` menjadi **`fuzz.token_set_ratio`**. Fungsi set-ratio bertindak sebagai subset-matcher, sehingga `"ginseng"` memiliki skor kecocokan nyaris 100% apabila ditemukan di dalam string *"Panax Ginseng"*.
  - *Threshold* batas minimum pencarian diturunkan sedikit dari 75% menjadi 70% dengan *token_set_ratio*.

## 3. Penggantian Engine OCR & Vision (`backend/services/vision.py`)
- **Masalah Sebelumnya:** Arsitektur lama mengandalkan Google Cloud Vision API SDK (`google-cloud-vision`) yang kuat secara murni untuk mengelola _Bounding Box OCR_, namun tidak mampu membedah konteks multibahasa label botol TCM secara _semantic_, sehingga memunculkan string teks yang kotor.
- **Perbaikan:** 
  - Mengimplementasikan penghapusan SDK **Google Cloud Vision** dan memigrasikan fungsi `extract_and_translate_text(image_bytes: bytes)` agar menggunakan **OpenRouter API** dengan model multimodal terjangkau, yaitu **`google/gemini-2.5-flash-lite`**.
  - Menggunakan modul HTTP async `httpx` dengan payload spesifikasi OpenAI-compatible *Chat Compeletions* + parameter `image_url` bertipe *Base64 string data URI*.
  - Prompt diset secara khusus (Zero-Shot) untuk menginstruksikan LLM membuang "sampah marketing" dan hanya mengeluarkan format JSON list array berisi bahan-bahan dalam bahasa asli beserta translasi/padanan bahasa Indonesianya.

## 4. Adaptasi Endpoint Asynchronous (`backend/routers/analyze.py` & `ocr.py`)
- **Perbaikan:** Menjadikan `extract_and_translate_text` sebagai `async def`, sehingga membutuhkan adaptasi pada _caller_-nya:
  - Di dalam `backend/routers/analyze.py`, memanggil dengan sintaks asinkron `ocr_blocks = await extract_and_translate_text(content)`.
  - Di dalam `backend/routers/ocr.py`, logika juga ditambahkan *awaitable* `results = await extract_and_translate_text(content)`.
  - Mapping return LLM divalidasi dan di-wrap kembali ke skema JSON `[{"text": "...", "bounding_box": [{...}]}]` palsu/*dummy box* agar frontend atau router yang belum berubah (*backward compatible*) tidak _crash_ menangkap respon list tersebut.

## 5. Konfigurasi Sistem Model Dasar (`backend/.env` & `core/config.py`)
- **Perbaikan:** 
  - Variabel Lingkungan `OPENROUTER_MODEL` pada file `.env` diubah dari yang asalnya model gratis `google/gemma-3-12b-it:free` ke `google/gemini-2.5-flash-lite`.
  - Memperbarui *fallback value* pada `backend/core/config.py` menjadi `google/gemini-2.5-flash-lite` agar sejalan.
  - Memperbarui teks dokumentasi *docstring* pada `backend/services/llm_intent.py` yang sebelumnya menjelaskan penggunaan Gemma-3 menjadi penjelasan tentang Gemini 1.5/2.5.
  
---
**Next Step Developer Action:**
Lanjutkan integrasi `safety_analysis` (mengomparasikan hasil OCR teks dari array *gemini-flash-lite* dengan MongoDB *tcm_ingredients*). Frontend juga sudah bisa menjalankan API scanning gambar (`/api/v1/analyze`) ini dengan performa yang jauh lebih cerdas!
