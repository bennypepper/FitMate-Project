# FitMate: Future Developments Roadmap

> This document captures planned improvements, research directions, and architectural enhancements for FitMate beyond the current prototype. It is intended for use in research proposals, funding applications, and continued development.
>
> Items are grouped by system area and tagged with effort level and impact potential.

---

## Table of Contents

1. [Ingredient Matching: From Fuzzy to Semantic Embeddings](#1-ingredient-matching)
2. [Database: Coverage, Interactions, and Validation](#2-database)
3. [WhatsApp Bot: Persistent Memory and Advanced UX](#3-whatsapp-bot)
4. [OCR and Label Scanning: Accuracy and Format Support](#4-ocr-and-label-scanning)
5. [User Health Profile: Personalized Safety Checks](#5-user-health-profile)
6. [Drug-Herb Interaction Checking](#6-drug-herb-interaction-checking)
7. [Product-Level Recognition](#7-product-level-recognition)
8. [Frontend and PWA Improvements](#8-frontend-and-pwa-improvements)
9. [Backend Scalability and Reliability](#9-backend-scalability-and-reliability)
10. [Analytics and Monitoring](#10-analytics-and-monitoring)
11. [Governance and Medical Validation](#11-governance-and-medical-validation)

---

## 1. Ingredient Matching

### Current State

Ingredient lookup uses `thefuzz` (Levenshtein distance / token set ratio) against multiple name variants per DB entry: Indonesian, Mandarin, Pinyin, English, Latin. An LLM normalization step translates foreign-language names (German, Dutch, etc.) before fuzzy matching runs.

**Failure modes of current approach:**
- Foreign-language names not normalized by LLM will miss (rare but possible).
- Abbreviations with no lexical overlap fail (e.g., "LHG" -> "Lo Han Guo").
- Semantic queries ("obat batuk herbal") cannot resolve to a known botanical ingredient.

---

### FD-1.1: Multilingual Semantic Embeddings *(High Impact, Medium Effort)*

**Proposal:** Pre-compute vector embeddings for all ingredient name variants at database seed time. At query time, embed the normalized ingredient name and perform cosine similarity against the stored vectors.

**Recommended model:** `paraphrase-multilingual-MiniLM-L12-v2` (Sentence Transformers)
- Free, local, no external API cost.
- Handles Indonesian, Mandarin, Pinyin, English, Latin natively.
- 500MB one-time download; ~384-dimensional vectors.
- Pre-computing embeddings across 500 entries takes under 20 seconds.

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

**Why it matters long-term:**
- "Sibirischer Ginseng" (German) is correctly identified as Eleutherococcus senticosus even without LLM normalization.
- Semantic queries: "akar yang menyebabkan gagal ginjal" surfaces aristolochic acid entries.
- Cross-script matching: "龙胆" -> "Long Dan" -> "Gentiana" through semantic vector space rather than string edit distance.

---

### FD-1.2: Hybrid Confidence Display *(Low Effort, High Safety Impact)*

When fuzzy score is between 68 and 79 (borderline match), display:
> _"[Info] Kemungkinan cocok: Lo Han Guo (tingkat keyakinan medium). Ketik nama spesifik jika hasil kurang tepat."_

This prevents silent misidentification while keeping the system informative.

---

### FD-1.3: "Did You Mean?" Clarification Flow *(Medium Effort)*

When top-2 matches are close in score (within 5 points), offer disambiguation:
> _"Sistem mendeteksi dua kemungkinan: (1) Lo Han Guo atau (2) Luo Han Guo. Mana yang sesuai dengan kemasan produkmu?"_

User replies "1" or "2", and the conversation continues deterministically.

---

## 2. Database

### Current State

The database currently contains 500 TCM ingredients compiled from official BPOM public warning publications and the SymMap pharmacology database. Fields include `indonesian_name`, `mandarin_name`, `pinyin`, `latin_name`, `is_toxic`, `target_organ`, `contraindications`, and `description`.

---

### FD-2.1: Database Expansion to 1000+ Ingredients and Commercial Brands *(High Impact)*

The expansion from 100 to 500 ingredients has been completed in the current release. Future development will target:
- Ingestion of remaining WHO traditional medicine monographs.
- Automated weekly synchronizations with newly published BPOM public warnings.
- Brand product mapping (linking registered Indonesian commercial herbal products to their multi-herb formulations).

---

### FD-2.2: Richness of Safety Data Fields *(Medium Effort)*

Current safety data is binary (`is_toxic: bool`) with free-text contraindications. Planned structured expansion:

| New Field | Example | Purpose |
|---|---|---|
| `contraindicated_conditions[]` | `["diabetes", "kehamilan", "hipertensi"]` | Enable rule-based condition matching |
| `drug_class_interactions[]` | `["ACE inhibitor", "SSRI"]` | Pharmacological drug-herb interaction |
| `max_daily_dose_mg` | `500` | Dosage safety checking |
| `processing_method_risk` | `"Aconiti Radix: toksik mentah, aman setelah diproses"` | Processing-dependent safety |
| `evidence_level` | `"A" / "B" / "C" / "traditional"` | Confidence in safety claim |
| `source_doi` | `"10.1234/..."` | Citation for validated entries |

---

### FD-2.3: Structured Contraindication Engine *(High Safety Impact)*

Currently, contraindications are stored as free-text strings and referenced by the LLM in natural language replies. A structured approach would enable deterministic contraindication checking:

```python
# Instead of free text:
contraindications = "Tidak untuk ibu hamil dan penderita diabetes"

# Use structured identifiers:
contraindicated_conditions = ["kehamilan", "diabetes_tipe_1", "diabetes_tipe_2"]
```

The bot then executes an exact rule match between `contraindicated_conditions` and the user's stored health profile without relying on LLM interpretation.

---

## 3. WhatsApp Bot

### Current State

In-memory `TTLCache` for conversation history (2-hour TTL). Per-sender rate limiting. Pre-LLM safety interceptor for 119 SPGDT emergencies and BPOM BKO adulterants. Twilio WhatsApp Sandbox integration.

---

### FD-3.1: Persistent Conversation History in MongoDB *(High UX Impact)*

**Problem:** Server restarts wipe in-memory conversation history, resetting user context.

**Solution:** Persist history to MongoDB with a TTL index:

```javascript
{
  phone: "+628123456789",
  history: [{"role": "user", "content": "..."}, ...],
  last_active: ISODate("2026-03-27T12:00:00Z")
}
// TTL index: expires after 48h of inactivity
db.conversations.createIndex({"last_active": 1}, {expireAfterSeconds: 172800})
```

---

### FD-3.2: Typing Indicator Support *(Low Effort, Nice UX)*

While the backend processes the LLM response, send an asynchronous typing indicator so users know their request is actively being evaluated.

---

### FD-3.3: Direct Image Scanning via WhatsApp *(High Effort)*

Allow users to send a photo of a TCM label directly into the WhatsApp chat, execute the multimodal OCR pipeline, and return ingredient safety results inline without opening the web browser.

---

### FD-3.4: Adaptive General Chat Redirection *(Low Effort)*

Replace repetitive trailing call-to-actions with dynamic, context-aware closing remarks so extended conversations feel fluid and non-robotic.

---

## 4. OCR and Label Scanning

### Current State

Gemini 2.5 Flash Lite multimodal extraction with non-herbal food/snack boundary detection. Responsive adaptive viewfinder (widescreen 16:9 on desktop, portrait on mobile). Standalone and Bridge Mode workflows.

---

### FD-4.1: Local Image Preprocessing Pipeline *(Medium Effort)*

Apply client-side or backend image preprocessing before sending to the model:
- Auto-rotation for angled label photos.
- Contrast enhancement for faded or glossy packaging.
- Crop detection to isolate ingredient list sections.
- Glare reduction for plastic wrappers.

---

### FD-4.2: Barcode and QR Scanning Integration *(Medium Effort)*

Scan BPOM registration QR codes or barcodes directly to retrieve official registered ingredient dossiers, bypassing OCR optical distortion on damaged packaging.

---

## 5. User Health Profile

### Current State

Users manually state health conditions in messages. The bot acknowledges conditions mentioned in the conversation but does not store long-term profiles across extended time windows.

---

### FD-5.1: Persistent Health Profile per WhatsApp Number *(Very High UX and Safety Impact)*

Store user-consented health profiles in MongoDB:

```javascript
{
  phone: "+628123456789",
  conditions: ["diabetes_tipe_2", "hipertensi"],
  allergies: ["seafood"],
  medications: ["metformin", "amlodipine"],
  age_group: "dewasa",
  is_pregnant: false,
  profile_set_at: ISODate(...)
}
```

Every subsequent safety check automatically cross-references the stored profile without requiring re-entry.

---

### FD-5.2: Proactive Safety Alerts *(High Safety Impact)*

With a stored health profile, the system can proactively warn:
> _"[Peringatan Profil] Kamu tercatat memiliki riwayat hipertensi. Akar Manis (Licorice Root) berpotensi meningkatkan tekanan darah pada pemakaian berulang."_

---

## 6. Drug-Herb Interaction Checking

### Current State

The system evaluates individual ingredient safety but does not model complex interactions between TCM herbs and conventional pharmaceutical drugs.

---

### FD-6.1: Drug-Herb Interaction Database *(Very High Safety Impact, High Effort)*

Documented critical interactions in TCM include:
- Danshen (*Salvia miltiorrhiza*) with Warfarin (increased bleeding risk).
- Licorice Root with Antihypertensives and Corticosteroids (potassium loss, elevated blood pressure).
- Ginkgo Biloba with Anticoagulants and SSRIs (bleeding risk, serotonin syndrome).
- Asian Ginseng with Insulin and MAOIs (hypoglycemia risk).

Adding a dedicated interaction module enables cross-referencing between user medication lists and scanned ingredients.

---

## 7. Product-Level Recognition

### Current State

FitMate operates at the individual botanical and chemical substance level.

---

### FD-7.1: Commercial Herbal Product Database *(High UX Impact)*

Map popular registered Indonesian herbal brands (e.g., Tolak Angin, Antangin, Pil Chi Kit) to their standardized ingredient formulations. Queries like "Apakah Tolak Angin aman untuk ibu hamil?" can then be evaluated instantly without requiring physical label scanning.

---

## 8. Frontend and PWA Improvements

- **Push Notifications:** Alert users when a previously checked substance receives updated safety warnings from BPOM.
- **Offline History:** Store the last 10 scan results in IndexedDB for offline review.
- **Accessibility Enhancements:** Screen-reader ARIA optimization for toxicity cards, font size scaling for elderly users, and high-contrast styling.

---

## 9. Backend Scalability and Reliability

- **Message Queue (Redis + Celery):** Decouple incoming WhatsApp messages from FastAPI request lifecycles to guarantee zero dropped messages during traffic spikes.
- **Response Caching:** Cache common ingredient responses in Redis with 24-hour TTL, reducing LLM calls for high-frequency queries.
- **Model Fallback Chain:** Automatic failover from Gemini 2.5 Flash Lite to secondary models or deterministic templates during external API outages.

---

## 10. Analytics and Monitoring

- **Usage Analytics Dashboard:** Aggregate data on most queried herbs, frequent user health conditions, and percentage of toxic detections.
- **Automated Database Gap Detection:** Weekly reporting of top unlisted search queries to prioritize new botanical records.

---

## 11. Governance and Medical Validation

- **Clinical Pharmacist Review Panel:** Establish an ongoing review protocol with licensed pharmacists and TCM practitioners to formally audit and grade database entries.
- **Versioned Safety Database with Audit Logging:** Maintain immutable timestamps and author IDs for every change made to toxicity flags and contraindications.

---

## Priority Matrix

| Feature | Impact | Effort | Priority |
|---|---|---|---|
| FD-5.1 Persistent Health Profile | Very High | Medium | [Priority 1: Do First] |
| FD-6.1 Drug-Herb Interactions | Very High | High | [Priority 1: Do First] |
| FD-3.1 Persistent Conversation History | High | Low | [Priority 1: Do First] |
| FD-7.1 Brand Product Database | High | Medium | [Priority 2: Do Soon] |
| FD-1.1 Multilingual Embeddings | Medium | Medium | [Priority 2: Do Soon] |
| FD-10.2 DB Gap Detection | High | Low | [Priority 2: Do Soon] |
| FD-9.3 LLM Response Caching | Medium | Low | [Quick Win] |
| FD-1.2 Fuzzy Confidence Display | Medium | Low | [Quick Win] |
| FD-3.2 Typing Indicators | Low | Low | [Quick Win] |
| FD-3.3 Image via WhatsApp | High | High | [Long-term] |
| FD-9.2 Message Queue (Celery) | Medium | High | [Long-term] |
| FD-8.1 Push Notifications | Medium | High | [Long-term] |
| FD-11.3 Clinical Expert Panel | Very High | Very High | [Post-Funding] |

---

*FitMate Project Documentation. Reflects production system status with 500-ingredient database, adaptive widescreen desktop camera, and Bridge Mode.*
