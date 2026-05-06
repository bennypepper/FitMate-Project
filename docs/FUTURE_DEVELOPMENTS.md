# FitMate — Future Developments Roadmap

> This document captures planned improvements, research directions, and architectural enhancements for FitMate beyond the PIMNAS v1.0 prototype. It is intended for use in research proposals, funding applications, and continued development post-submission.
>
> Items are grouped by system area and tagged with effort level and impact potential.

---

## Table of Contents

1. [Ingredient Matching — From Fuzzy to Semantic Embeddings](#1-ingredient-matching)
2. [Database — Coverage, Interactions, and Validation](#2-database)
3. [WhatsApp Bot — Persistent Memory & Advanced UX](#3-whatsapp-bot)
4. [OCR & Label Scanning — Accuracy and Format Support](#4-ocr--label-scanning)
5. [User Health Profile — Personalized Safety Checks](#5-user-health-profile)
6. [Drug-Herb Interaction Checking](#6-drug-herb-interaction-checking)
7. [Product-Level Recognition](#7-product-level-recognition)
8. [Frontend & PWA Improvements](#8-frontend--pwa-improvements)
9. [Backend Scalability & Reliability](#9-backend-scalability--reliability)
10. [Analytics & Monitoring](#10-analytics--monitoring)
11. [Governance & Medical Validation](#11-governance--medical-validation)

---

## 1. Ingredient Matching

### Current State

Ingredient lookup uses `thefuzz` (Levenshtein distance / token set ratio) against five name variants per DB entry: Indonesian, Mandarin, Pinyin, English, Latin. The LLM normalization step (added in v1.1) translates foreign-language names (German, Dutch, etc.) before fuzzy matching runs.

**Failure modes of current approach:**
- Foreign-language names not normalized by LLM will miss (rare but possible)
- Abbreviations with no lexical overlap fail (e.g., "LHG" → "Lo Han Guo")
- Semantic queries ("obat batuk cina") cannot resolve to a known ingredient

---

### FD-1.1 — Multilingual Semantic Embeddings *(High Impact, Medium Effort)*

**Proposal:** Pre-compute vector embeddings for all ingredient name variants at database seed time. At query time, embed the normalized ingredient name and perform cosine similarity against the stored vectors.

**Recommended model:** `paraphrase-multilingual-MiniLM-L12-v2` (Sentence Transformers)
- Free, local, no API cost
- Handles Indonesian, Mandarin, Pinyin, English, Latin natively
- 500MB one-time download; ~384-dimensional vectors
- Pre-computing 103 × 5 name variants takes < 5 seconds

**Architecture:**
```
Seed time:
  for each ingredient:
    for each name variant:
      embedding = model.encode(name_variant)
      store embedding in MongoDB alongside ingredient doc

Query time:
  query_embedding = model.encode(normalized_query)
  similarities = [cosine_sim(query_embedding, ing.embedding) for ing in DB]
  best_match = max(similarities)
  if best_match.score > 0.75: use it
  else: "not found"
```

**Why not now (PIMNAS):** Adds a ~500MB model dependency and increases system complexity beyond what's testable in the available timeline. The LLM normalization layer already handles the most common failure cases (foreign language names).

**Why it matters long-term:**
- "Sibirischer Ginseng" (German) → correctly identified as Eleutherococcus senticosus even without LLM normalization
- Semantic queries: "akar yang sering bikin gagal ginjal" (root that causes kidney failure) → surfaces aristolochic acid entries
- Cross-script matching: "龙胆" → "Long Dan" → "Gentiana" through semantic space rather than string edit distance

**For the research paper:** This is a legitimate methodological contribution — _"we propose augmenting rule-based fuzzy matching with multilingual sentence embeddings to bridge the language gap between user-provided TCM names across 6+ scripts and our pharmacist-validated safety database."_

---

### FD-1.2 — Hybrid Confidence Display *(Low Effort, High Safety Impact)*

When fuzzy score is between 68–79 (borderline match), display:
> _"❓ Kemungkinan cocok: Lo Han Guo — tingkat keyakinan medium. Ketik nama lain jika kurang tepat."_

This prevents silent misidentification while keeping the system useful.

---

### FD-1.3 — "Did You Mean?" Clarification Flow *(Medium Effort)*

When top-2 matches are close in score (within 5 points), offer disambiguation:
> _"Saya temukan dua kemungkinan: (1) Lo Han Guo atau (2) Luo Han Guo. Yang mana yang kamu maksud?"_

User replies "1" or "2". Conversation continues from there.

---

## 2. Database

### Current State

103 pharmacist-validated TCM ingredients in MongoDB. Fields: `indonesian_name`, `mandarin_name`, `pinyin_name`, `latin_name`, `is_toxic`, `toxicity_level`, `target_organ`, `contraindications`, `description`.

---

### FD-2.1 — Database Expansion to 500+ Ingredients *(High Impact)*

The current 103-ingredient dataset is sufficient for PIMNAS demonstration but covers only the most common products. Real-world TCM labels may contain many more ingredients.

**Sources to integrate:**
- BPOM scraper (partially implemented) — Indonesia's national drug regulator
- SymMap database (TCM → pharmacological mechanisms)
- TCMID (TCM Integrated Database) — over 7,000 herbal records
- WHO monographs on traditional medicine

**Workflow:** Scraper → pharmacist review checklist → approved entries seeded into MongoDB. The review step is non-negotiable (zero-hallucination mandate).

---

### FD-2.2 — Richness of Safety Data Fields *(Medium Effort)*

Current safety data is binary (`is_toxic: bool`) with free-text contraindications. Structured expansion:

| New Field | Example | Purpose |
|---|---|---|
| `contraindicated_conditions[]` | `["diabetes", "kehamilan", "hipertensi"]` | Enable rule-based condition matching |
| `drug_class_interactions[]` | `["ACE inhibitor", "SSRI"]` | Pharmacological drug-herb interaction |
| `max_daily_dose_mg` | `500` | Dosage safety checking |
| `processing_method_risk` | `"Aconiti Radix: toksik mentah, aman setelah diproses"` | Processing-dependent safety |
| `evidence_level` | `"A" / "B" / "C" / "traditional"` | Confidence in safety claim |
| `source_doi` | `"10.1234/..."` | Citation for validated entries |

---

### FD-2.3 — Structured Contraindication Engine *(High Safety Impact)*

Currently, contraindications are stored as free-text strings and referenced by the LLM in natural language replies. A structured approach would enable **deterministic contraindication checking**:

```python
# Instead of:
contraindications = "Tidak untuk ibu hamil dan penderita diabetes"

# Use:
contraindicated_conditions = ["kehamilan", "diabetes_tipe_1", "diabetes_tipe_2"]
```

The bot then does an exact rule match between `contraindicated_conditions` and the user's stored health profile — no LLM needed for this critical step. True zero-hallucination.

---

## 3. WhatsApp Bot

### Current State

In-memory `TTLCache` for conversation history (2h TTL, wipes on restart). Per-sender rate limiting. Twilio Sandbox. Intent classification + LLM replies via OpenRouter.

---

### FD-3.1 — Persistent Conversation History in MongoDB *(High UX Impact)*

**Problem:** Every server restart (including `uvicorn --reload` during development) wipes all conversation history. Users lose context.

**Solution:** Persist history to MongoDB with TTL index:

```javascript
// MongoDB document
{
  phone: "+628123456789",
  history: [{"role": "user", "content": "..."}, ...],
  last_active: ISODate("2026-03-27T12:00:00Z")
}
// TTL index: expires after 48h of inactivity
db.conversations.createIndex({"last_active": 1}, {expireAfterSeconds: 172800})
```

History loads from DB at message start, appended on each turn, persists through restarts.

---

### FD-3.2 — Typing Indicator Support *(Low Effort, Nice UX)*

Twilio supports sending typing indicators. While the backend processes the LLM response, send a "typing..." status. Users see the bot is working rather than wondering if it crashed.

```python
await whatsapp_client.send_typing_indicator(to_phone=sender)
# ... LLM processing ...
await whatsapp_client.send_text_message(to_phone=sender, text=reply)
```

---

### FD-3.3 — Image Scanning via WhatsApp *(Medium Effort)*

Currently out of scope due to Meta/Twilio webhook timeout complexity. When resolved:
- User sends a photo of a TCM label directly in WhatsApp
- Bot runs the same Gemini Vision OCR pipeline
- Returns ingredient safety results inline, no web app needed

This removes the friction of needing the PWA entirely for label-scanning users.

---

### FD-3.4 — Smarter General Chat (Less Robotic CTA) *(Low Effort)*

Remove the rule that every message must end with the same TCM redirect phrase. Let the LLM decide when redirection is natural vs. forced. The current "Ada bahan TCM lain yang ingin dicek? 🌿" appearing after every reply feels mechanical in extended conversations.

---

## 4. OCR & Label Scanning

### Current State

Gemini 2.5 Flash Lite multimodal: image → structured JSON of detected ingredients (Mandarin text + Indonesian translations). Better semantic understanding than Google Cloud Vision (which was the original plan).

---

### FD-4.1 — Image Preprocessing Pipeline *(Medium Effort)*

Before sending to the LLM, apply basic preprocessing to improve OCR accuracy on real-world label photos:
- **Auto-rotation** — labels photographed at angles
- **Contrast enhancement** — faded or shiny packaging
- **Crop detection** — isolate the ingredient list region from the full label image
- **Glare reduction** — common on plastic-wrapped products

Libraries: `Pillow`, `OpenCV`. Preprocessing is local and adds <200ms.

---

### FD-4.2 — Barcode / QR Scanning *(Medium Effort)*

Many Indonesian TCM products have BPOM registration barcodes. Scan the barcode → look up in BPOM database → retrieve the full registered ingredient list automatically. Eliminates OCR uncertainty for registered products entirely.

---

### FD-4.3 — Batch Label Scanning *(UX Improvement)*

Allow users to scan multiple labels per session and track all queried ingredients. Useful for users comparing products or checking everything in their cabinet at once.

---

## 5. User Health Profile

### Current State

Users manually type their health conditions in each conversation. The bot acknowledges conditions mentioned in the current message and history, but forgets everything after the 2h TTL expires or server restarts.

---

### FD-5.1 — Persistent Health Profile per WhatsApp Number *(Very High UX + Safety Impact)*

Store a health profile keyed by WhatsApp phone number in MongoDB:

```javascript
{
  phone: "+628123456789",
  conditions: ["diabetes_tipe_2", "hipertensi"],
  allergies: ["seafood"],
  medications: ["metformin", "amlodipine"],
  age_group: "lansia",  // dewasa, lansia, anak
  is_pregnant: false,
  profile_set_at: ISODate(...)
}
```

**Onboarding flow (first time):**
> _"Untuk memberi saran yang lebih akurat, boleh aku tahu sedikit tentang kondisi kesehatanmu? Misalnya: diabetes, hipertensi, hamil, atau kondisi lainnya. Ketik atau skip kalau tidak mau."_

**Effect:** Every subsequent safety check automatically cross-references the stored profile. User never has to re-state "saya punya diabetes" — the bot just knows.

---

### FD-5.2 — Proactive Safety Alerts *(High Safety Impact)*

With a stored health profile, the bot can proactively warn:
> _"Kamu pernah cerita punya hipertensi. Licorice Root (Akar Manis) bisa meningkatkan tekanan darah — hati-hati ya kalau produk ini mengandung bahan ini."_

This shifts FitMate from reactive (user asks) to proactive (bot warns).

---

## 6. Drug-Herb Interaction Checking

### Current State

Not implemented. The system checks individual ingredient safety but does not check herb-drug interactions (e.g., St. John's Wort reduces efficacy of many prescription drugs).

---

### FD-6.1 — Drug-Herb Interaction Database *(Very High Safety Impact, High Effort)*

This is arguably the most medically important future feature. Known critical interactions in TCM context:

| Herb | Drug Class | Interaction |
|---|---|---|
| Danshen (Salvia miltiorrhiza) | Warfarin | Increased bleeding risk |
| Licorice Root | Corticosteroids, antihypertensives | Potassium depletion, BP increase |
| Ginkgo Biloba | Anticoagulants, SSRIs | Bleeding risk, serotonin syndrome |
| Kava | Benzodiazepines, alcohol | CNS depression |
| Asian Ginseng | Insulin, MAOIs | Hypoglycemia, serotonin syndrome |

**Implementation:** Add `drug_interactions[]` field to each ingredient document. If user profile includes `medications[]`, the system performs an exact match check against known interactions and flags them before giving a safety verdict.

This would be a significant research contribution: _"FitMate is the first consumer TCM safety tool to perform automated herb-drug interaction screening against the user's personal medication list."_

---

## 7. Product-Level Recognition

### Current State

FitMate operates at the individual ingredient level. It cannot recognize packaged product brands (e.g., "Tolak Angin", "Antangin", "Tju Beng").

---

### FD-7.1 — Brand Product Database *(High UX Impact)*

Create a product-level collection mapping common Indonesian TCM brand names to their known ingredient lists:

```javascript
{
  brand_name: "Tolak Angin",
  manufacturer: "Sido Muncul",
  bpom_registration: "POM TR...",
  ingredients: ["jahe", "kayu manis", "cengkeh", "biji pala", "mint"],
  last_verified: ISODate(...)
}
```

User asks: _"Tolak Angin aman tidak untuk ibu hamil?"_ → Bot looks up the product, gets the ingredient list, runs safety check on all of them, and gives a consolidated verdict. No scanning needed.

---

### FD-7.2 — User-Contributed Product Labels *(Community Feature)*

Allow users to submit verified scan results. After successful OCR, ask: _"Mau bantu FitMate? Konfirmasi apakah hasil scan ini sudah benar."_ Validated submissions build the product-level database over time.

---

## 8. Frontend & PWA Improvements

---

### FD-8.1 — Push Notifications *(Medium Effort)*

With PWA push notifications:
- Alert user when a product they previously checked gets a safety update
- Proactive health tips
- Requires a subscription model and notification infrastructure

---

### FD-8.2 — Offline Mode for Scan Results *(Low Effort)*

Cache the last 10 scan results locally in IndexedDB. Users can review past results offline without internet.

---

### FD-8.3 — Ingredient History with Personal Archive *(Medium UX Impact)*

Let users bookmark ingredients they've checked. Simple localStorage implementation:
- _"Tandai bahan ini"_ → saved to device
- History tab showing all previously checked ingredients
- Export as PDF for sharing with a doctor

---

### FD-8.4 — Accessibility Improvements

- Screen reader support for all scan results (ARIA labels on toxicity warnings)
- Font size controls for elderly users (key demographic in Indonesia)
- High-contrast mode
- Simplified language mode ("Bahasa sederhana") for low-literacy users

---

## 9. Backend Scalability & Reliability

---

### FD-9.1 — Conversation History Persistence *(solves restart wipe issue)*

See FD-3.1 — same priority. MongoDB TTL collections are the right solution.

---

### FD-9.2 — Message Queue for WhatsApp Processing *(Medium Effort)*

Currently, incoming WhatsApp messages are processed in FastAPI `BackgroundTask` — simple but not durable. If the server crashes mid-processing, the reply is lost.

**Solution:** Redis + Celery worker queue. Messages are enqueued, workers process them independently. Processing survives server restarts. Dead-letter queue for failed messages.

---

### FD-9.3 — LLM Response Caching *(Performance + Cost)*

Cache common LLM responses by (ingredient_name, safety_verdict, language) tuple. If 100 users ask "lo han guo aman?" in the same hour, the LLM is called once and cached Redis responses are served for the rest. TTL: 24h.

Estimated cost reduction: 60–80% fewer LLM calls for popular ingredients.

---

### FD-9.4 — Model Fallback Chain *(Reliability)*

Currently: one model (Gemini 2.5 Flash Lite via OpenRouter). If it's down → bot replies "layanan tidak tersedia".

**Solution:** model fallback chain:
1. Primary: `google/gemini-2.5-flash-lite` (fast, cheap)
2. Fallback 1: `google/gemini-flash-1.5` (slightly more expensive)
3. Fallback 2: `meta-llama/llama-3.2-3b-instruct:free` (free tier, simpler)
4. Final fallback: hardcoded template replies (zero LLM dependency)

---

## 10. Analytics & Monitoring

---

### FD-10.1 — Usage Analytics Dashboard

Track and display in the admin panel:
- **Most queried ingredients** → prioritize expanding data for these
- **Most common health conditions** mentioned by users
- **Ingredients not found** (missed DB coverage) → direct the pharmacist team
- **Daily active users** split by channel (web scan vs. WhatsApp bot)
- **Toxic flag rate** → what % of scans detect dangerous ingredients

---

### FD-10.2 — Automated DB Gap Detection

Build a cron job that:
1. Reads all "not found" queries from the last 7 days
2. Groups them by ingredient name frequency
3. Emails the admin: _"The most un-matched queries this week: Gynostemma (47 queries), Eucommia (31 queries), Rehmannia (28 queries) — consider adding these to the database."_

This creates a data-driven database expansion pipeline.

---

### FD-10.3 — Response Quality Feedback

After each WhatsApp reply, add a simple feedback prompt every N conversations:
> _"Apakah jawaban tadi membantu? Ketik 👍 atau 👎"_

Track thumbs-up/down by intent type and ingredient. Low-rated responses trigger a review of the prompt or data quality for that ingredient.

---

## 11. Governance & Medical Validation

---

### FD-11.1 — Pharmacist Review Workflow for LLM Replies

Currently, LLM-generated reply language is never reviewed by a healthcare professional. For a post-PIMNAS production deployment:

- Sample 5% of LLM-generated replies weekly
- Route to pharmacist reviewer in the admin panel
- Flag patterns that misrepresent DB data
- Use findings to improve system prompts

---

### FD-11.2 — Versioned Safety Database with Audit Log

Every change to a safety record should be versioned:
```javascript
{
  ingredient_id: ObjectId,
  field: "is_toxic",
  old_value: false,
  new_value: true,
  changed_by: "pharmacist_rina@team.com",
  reason: "New WHO monograph 2025 reclassification",
  timestamp: ISODate()
}
```

This is critical for a medical application: you need to know who changed what safety data and why.

---

### FD-11.3 — Expert TCM Practitioner Partnership

Formalize a review panel of licensed TCM practitioners (Sinse) and clinical pharmacists:
- Each DB entry is assigned an "evidence grade" (A/B/C)
- Grade A: peer-reviewed literature + practitioner review
- Grade B: practitioner review only
- Grade C: traditional use / community knowledge, not formally validated

Display evidence grade in scan results. Users can make informed decisions about how much to trust the data.

---

## Priority Matrix (Post-PIMNAS)

| Feature | Impact | Effort | Priority |
|---|---|---|---|
| FD-5.1 Persistent Health Profile | Very High | Medium | 🔴 Do First |
| FD-6.1 Drug-Herb Interactions | Very High | High | 🔴 Do First |
| FD-3.1 Persistent Conversation History | High | Low | 🔴 Do First |
| FD-2.1 Database Expansion to 500+ | High | Medium | 🟡 Do Soon |
| FD-7.1 Brand Product Database | High | Medium | 🟡 Do Soon |
| FD-1.1 Multilingual Embeddings | Medium | Medium | 🟡 Do Soon |
| FD-10.2 DB Gap Detection | High | Low | 🟡 Do Soon |
| FD-9.3 LLM Response Caching | Medium | Low | 🟢 Quick Win |
| FD-1.2 Fuzzy Confidence Display | Medium | Low | 🟢 Quick Win |
| FD-3.2 Typing Indicators | Low | Low | 🟢 Quick Win |
| FD-3.3 Image via WhatsApp | High | High | 🔵 Later |
| FD-9.2 Message Queue (Celery) | Medium | High | 🔵 Later |
| FD-8.1 Push Notifications | Medium | High | 🔵 Later |
| FD-11.3 Expert Panel | Very High | Very High | 🔵 Post-Funding |

---

*Last updated: 2026-03-27 | FitMate v1.1 (post-PIMNAS sesi 3)*
