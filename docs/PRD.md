# Product Requirements Document (PRD): FitMate

- Project: FitMate (TCM Safety Scanner & Advisory Bot)
- Document Version: 3.0 (Production State: 500-Ingredient Database, Adaptive Widescreen Scanner, Bridge Mode, Non-Herbal Boundary Verification)
- Classification: Research Prototype Document

---

## 1. Overview

The widespread practice of unsupervised self-medication using Traditional Chinese Medicine (TCM) presents a significant public health challenge in Indonesia. Most consumers cannot read Mandarin packaging and are unaware of potential nephrotoxic, hepatotoxic, or cardiotoxic risks. FitMate provides an automated safety net by combining a Web-Based Multimodal OCR Scanner and an intelligent WhatsApp Advisory Bot.

FitMate allows users to capture or upload images of TCM product packaging, extracts Mandarin Hanzi and Latin ingredient text, cross-references ingredients against a 500-substance database compiled from official BPOM public warning lists and SymMap literature, and flags toxic compounds and contraindications with strict rule-based determinism (zero AI hallucination in safety verdicts).

> **Prototype Disclaimer:** FitMate is an automated research prototype powered by artificial intelligence. The database consists of 500 TCM substances compiled from public BPOM releases and pharmacological literature; it has not undergone individual clinical validation by registered pharmacists or physicians. The application does not provide clinical diagnoses or replace professional medical consultations.

---

## 2. Core Objectives & System Constraints

- **Accessibility & Device Flexibility:**
  - *Standalone Mode:* Works seamlessly on any single device (smartphone or desktop/laptop) via camera streaming or file upload without requiring two devices.
  - *Bridge Mode:* Allows desktop users to scan a dynamic QR code with a smartphone, transferring mobile camera capture results back to the desktop in real time via asynchronous polling.
- **Adaptive Viewfinder Layout:**
  - Mobile: Portrait orientation optimized for one-handed phone usage (`aspect-[3/4]`).
  - Desktop/Tablet (`md:` breakpoint): Widescreen landscape view (`16:9` ratio) with side-by-side controls, preventing wasted screen real estate on wide monitors.
- **Strict Boundary & Anti-Hallucination:**
  - Non-herbal food and snack items (e.g. rice crackers, biscuits, flour, seasoning) are strictly detected and identified as non-herbal, preventing false-positive verification as herbal medicines.
  - Medical safety verdicts are determined purely by rule-based database matching, not generated or guessed by language models.
- **Pre-LLM Safety Interceptor:**
  - Emergency symptoms (chest pain, shortness of breath, vomiting blood) immediately trigger the National Emergency Ambulance hotline (119 SPGDT).
  - Adulterated chemical drugs (Bahan Kimia Obat / BKO like Sildenafil, Dexamethasone, Paracetamol) trigger immediate illegal substance warnings with BPOM reporting contacts (1500-533).
- **Design Standard:**
  - Strict adherence to the Modern Apothecary visual theme (Forest Green, Sage, Sand/Paper, and Crimson Warning).
  - Complete elimination of informal emojis across both web and WhatsApp plain-text responses, utilizing theme-aligned SVG icons and structured textual tags (`[Aman]`, `[Berisiko]`, `[Peringatan]`).

---

## 3. Detailed Feature Specifications

### 3.1 Web-Based Multimodal Scanner (`/`)

- **Camera Capture Engine:** HTML5 MediaDevices API with support for rear and front camera selection, live torch/flash (where supported), and direct file/gallery upload fallback.
- **Adaptive Viewfinder:**
  - Viewfinder layout automatically switches between portrait (`aspect-[3/4]`) on mobile and 16:9 widescreen (`md:aspect-video`) on desktop screens.
  - Desktop view features side-by-side layout with camera feed on one side and controls/instructions on the other.
- **Multimodal OCR Extraction:** Image sent to backend `POST /api/scan`, processed via Gemini 2.5 Flash Lite through OpenRouter. Returns structured JSON containing product classification, detected ingredients (Mandarin, Pinyin, Indonesian), and confidence metrics.
- **Non-Herbal Product Classifier:**
  - Detects whether the item is a conventional packaged food/snack.
  - Displays a dedicated informative banner stating that the item is non-herbal, preventing misleading herbal verification notices.

### 3.2 Cross-Device Bridge Mode (`/scanner?bridge_session=<UUID>`)

- **Session Generation:** Backend endpoint `POST /api/bridge/create` generates a UUID-based session stored in MongoDB with a 30-minute TTL.
- **QR Code Rendering:** Desktop displays a dynamic QR code containing the mobile session URL.
- **Real-Time Polling:** Desktop client polls `GET /api/bridge/poll/{session_id}` every 3 seconds.
- **Cross-Device Completion:** When the mobile device completes image capture and analysis, it posts the payload to `POST /api/bridge/complete/{session_id}`. The desktop automatically transitions to the results view.

### 3.3 Safety Results & Consultation Handoff

- **Imperial Warning Card:** Items flagged with `is_toxic = true` are highlighted with high-contrast crimson styling, detailing target organs (e.g., Ginjal, Hati, Jantung) and medical contraindications.
- **Verified Herbal Card:** Safe TCM substances listed in the 500-item repository display verified botanical details and standard descriptions.
- **WhatsApp Deep Link Generation:** Generates dynamic `wa.me/628...?text=...` links pre-filled with structured text tags for immediate follow-up with the automated chatbot.

### 3.4 500-Ingredient TCM Dictionary Modal

- Real-time client-side search across 500 TCM substances.
- Multilingual lookup matching Indonesian common names, Chinese Hanzi, Pinyin transliteration, and scientific Latin names.
- Filter toggle between all ingredients, verified safe items, and restricted/toxic compounds.

### 3.5 Automated WhatsApp Advisory Bot

- Operates as an automated software assistant (AI bot), explicitly disclaiming human doctor or pharmacist identities.
- Integrated multi-layer safety architecture:
  1. Rate limiter (TTLCache).
  2. Emergency symptom regex interceptor.
  3. BKO adulteration regex and context classifier.
  4. Off-topic conversational throttle.
  5. Multi-ingredient batch database matcher.
  6. Rule-grounded LLM reply generator.

---

## 4. System Architecture

```
[ Client Browser (PWA) ]
   |
   +--> Standalone Mode (Local Camera / Upload)
   |
   +--> Bridge Mode (QR Code pairing with Mobile)
   |
   v (HTTPS REST API)
[ FastAPI Backend Application ]
   |
   +--> /api/scan (Multimodal Vision OCR via OpenRouter Gemini 2.5 Flash Lite)
   +--> /api/bridge (Create, Complete, and Poll Cross-Device Sessions)
   +--> /api/tcm (500-Ingredient Catalog & Search)
   +--> /whatsapp/webhook (Twilio Messaging Webhook)
   |
   +--> [ Safety Interceptor Layer ]
   |       |-- Emergency Check (119 SPGDT)
   |       |-- BKO Adulteration Check (BPOM Warning Rules)
   |       \-- Deterministic Safety Verdict Engine
   |
   +--> [ MongoDB Atlas ]
           |-- tcm_ingredients (500 Curated TCM Records)
           \-- bridge_sessions (TTL Cache for Cross-Device Pairing)
```

---

## 5. Database Schema

### Collection: `tcm_ingredients` (500 Records)
```json
{
  "_id": "ObjectId",
  "id": "tcm_001",
  "indonesian_name": "Akar Manis / Licorice",
  "mandarin_name": "甘草",
  "pinyin": "Gān Cǎo",
  "latin_name": "Glycyrrhiza glabra",
  "is_toxic": false,
  "target_organ": "Limpa, Lambung, Paru-paru",
  "description": "Herbal tonik untuk menyelaraskan ramuan dan meredakan batuk.",
  "contraindications": "Penggunaan dosis tinggi jangka panjang dapat memicu retensi cairan dan hipertensi.",
  "source": "BPOM & SymMap Curated Dataset"
}
```

### Collection: `bridge_sessions`
```json
{
  "_id": "ObjectId",
  "session_id": "c61fd748-0c20-4a87-a2f0-e9bca93b8908",
  "status": "pending | completed",
  "created_at": "ISODate",
  "expires_at": "ISODate",
  "scan_data": {
    "product_name": "...",
    "is_non_herbal": false,
    "ingredients": []
  }
}
```

---

## 6. Technical Stack & Live Environments

- **Frontend:** Next.js 14, React 18, TypeScript, Tailwind CSS, Inline Theme SVGs.
- **Backend:** Python 3.11, FastAPI, Uvicorn, Motor, Pydantic v2, HTTPX.
- **Database:** MongoDB Atlas (M0 Shared Cluster).
- **AI / LLM:** Google Gemini 2.5 Flash Lite via OpenRouter API.
- **Messaging:** Twilio WhatsApp Cloud Sandbox.
- **Production Endpoints:**
  - Frontend: `https://fitmate-project.vercel.app`
  - Backend API: `https://benedictpepper-fitmate-api.hf.space`

---

## 7. Verification & Safety Guidelines

- **Zero Hallucination Guarantee:** AI models never determine ingredient toxicity. Every safety verdict originates from exact database flags (`is_toxic`).
- **Medical Responsibility Boundary:** All communications, landing pages, and bot conversations carry clear statements identifying FitMate as an automated research tool, preventing false reliance during acute medical emergencies.