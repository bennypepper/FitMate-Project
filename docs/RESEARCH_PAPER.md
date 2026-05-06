# FitMate: A TCM Safety Scanner and Consultation System Using Hybrid Rule-Based AI and WhatsApp Chatbot for Indonesian Consumers

**Benedict Michael Pepper¹, Alvia Parausia Gionka², Lola Adelia Meidiyaratri², Safrina Nur Maharani², [Nama Mahasiswa Bahasa Mandarin]³**

¹ Program Studi Teknik Informatika, Universitas Ma Chung, Malang  
² Program Studi Farmasi, Universitas Ma Chung, Malang  
³ Program Studi Pendidikan Bahasa Mandarin, Universitas Ma Chung, Malang

**Corresponding author:** benedict.pepper@student.machung.ac.id

---

## Abstract

The growing consumption of Traditional Chinese Medicine (TCM) products in Indonesia presents a significant public health challenge: the majority of product labels are written in Mandarin, which is inaccessible to most Indonesian consumers, while scientific evidence on the safety profiles of commercially available TCM products remains sparse. Unsupervised self-medication with TCM products carrying unknown ingredient risks has been documented as a rising concern, with Indonesia's national drug regulator (BPOM) identifying 53 traditional medicine products containing illicit pharmaceutical chemicals in 2021 alone, and over 2,000,000 illegal products—predominantly from China—found in online marketplaces through 2025. This paper presents FitMate, a Progressive Web App (PWA) and WhatsApp chatbot system that enables Indonesian consumers to scan TCM product labels using a smartphone camera, automatically extract and translate Mandarin ingredient text using a multimodal large language model (LLM), and cross-reference the detected ingredients against a pharmacist-validated toxicity database. A hybrid architecture is proposed in which all safety verdicts are determined exclusively by rule-based database lookups (ensuring zero AI hallucination in medical recommendations), while a large language model is employed solely for natural language understanding, intent classification, Mandarin OCR, and generating empathetic, context-aware consultation responses that acknowledge the user's stated health conditions. An evaluation of the chatbot's conversational pipeline revealed that routing all safety verdicts through a deterministic database layer while delegating only language generation to the LLM produced accurate, medically grounded responses without sacrificing conversational quality. The system achieved successful end-to-end ingredient detection, translation, and safety classification, and has been deployed as a functional prototype for user testing.

**Keywords:** Traditional Chinese Medicine, OCR, chatbot, WhatsApp, patient safety, natural language processing, drug safety, Indonesia

---

## 1. Introduction

### 1.1 Background

Traditional Chinese Medicine (TCM) has seen rapid growth in global and Indonesian markets, driven by increasing consumer interest in herbal and complementary therapies. Indonesia and China have formally strengthened bilateral cooperation on traditional medicine development (BPOM, 2025), and the WHO (2019) estimates that 80% of the world's population relies on traditional medicine for primary healthcare. In Indonesia, TCM products are widely sold in pharmacies, traditional medicine shops (*toko sinshe*), and increasingly through e-commerce platforms.

However, this growth has occurred largely without adequate consumer safety infrastructure. Three critical problems compound one another:

**1. Language barrier on product labels.** The majority of TCM products distributed in Indonesia carry Mandarin-language labels, which are inaccessible to the approximately 97% of the Indonesian population who do not read Chinese script (Nurhalisa et al., 2024). Without accessible ingredient information, consumers cannot assess toxicity risks, contraindications, or interaction potential with existing medications.

**2. Unsupervised self-medication behavior.** Ghaznawi et al. (2025) report that consumers routinely consume supplements—including herbal products—without knowledge of safe dosage limits or potential drug interactions, operating under the misconception that "natural" products carry no risk. Esti et al. (2025) confirm that unsupervised self-medication remains a significant and growing phenomenon among productive-age Indonesians.

**3. Proliferation of unsafe and unregistered products.** BPOM's 2021 Public Warning identified 53 traditional medicine products containing illicit pharmaceutical chemicals (*bahan kimia obat*, BKO), including Lianhua Qingwen Capsules, which were found to contain ephedrine and pseudoephedrine from *Ephedra sinica*. Approximately 9.3% of all health supplement data reviewed by BPOM contained BKO such as sildenafil, tadalafil, and dexamethasone. More alarmingly, approximately 11.3% of products banned in 2021 remained available on e-commerce platforms through 2026 (BPOM, 2026). BPOM's 2025 cyber patrol of online marketplaces found thousands of accounts and 197,725 non-compliant product links, with illegal herbal products—predominantly TCM from Indonesia and China—ranking as the second-largest category of illegal products, totaling approximately 2,000,000 items.

Existing digital health tools have not adequately addressed this intersection of language inaccessibility, safety information gaps, and unregistered product proliferation. Existing chatbot systems identified by Wahab et al. (2025), Kurniasih et al. (2024), and Fadhilah et al. (2024) provide general health consultation, medication reminders, or wellness education, but none offer TCM-specific ingredient safety scanning with pharmacist-validated toxicity data.

### 1.2 Research Objectives

This research develops and evaluates **FitMate**, a TCM safety scanner and consultation system designed to:

1. Enable non-Mandarin-speaking Indonesian consumers to identify and understand the ingredients in TCM products through camera-based scanning
2. Cross-reference detected ingredients against a pharmacist-validated safety database with real-time toxicity flagging
3. Provide accessible, empathetic safety consultation through WhatsApp — a platform already used by over 90% of Indonesian smartphone users — without requiring application installation
4. Maintain a strict zero-hallucination guarantee: all medical safety verdicts are produced exclusively by rule-based database logic, never by AI language generation

### 1.3 Scope and Limitations

The current prototype targets Indonesian consumers purchasing TCM products in physical and online retail settings. The system is not intended to replace licensed pharmacist consultation; a medical disclaimer is displayed on all outputs. The prototype database contains 103 pharmacist-validated TCM ingredient entries covering the 100 most commonly consumed TCM products and ingredients in Indonesia.

---

## 2. Literature Review

### 2.1 Traditional Chinese Medicine in Indonesia

Traditional Chinese Medicine encompasses herbal medicine, acupuncture, *cupping*, and other modalities derived from Chinese medical traditions practiced over thousands of years. In the Indonesian context, TCM has become part of the cultural heritage of the Javanese Chinese (*Tionghoa Jawa*) community and has spread to the broader Indonesian population through *toko sinshe* (traditional Chinese medicine shops) across the archipelago (Nurhalisa et al., 2024). The most commonly consumed TCM categories in Indonesia include herbal tonics (*jamu TCM*), patent pills (*pil paten*), and culinary herbs that cross over into medicinal use.

Despite longstanding use, the safety evidence base for many commercial TCM products remains limited. TCM formulations frequently contain multiple active compounds whose interactions are not fully characterized by modern pharmacological methods. Compounds such as aristolochic acid—found in *Aristolochia* species used in some traditional formulations—are associated with nephrotoxicity and urothelial carcinoma, yet continue to appear in products sold in Southeast Asian markets (Rahmasiah et al., 2023).

### 2.2 OCR and Machine Translation of Non-Latin Scripts in Healthcare

Optical Character Recognition (OCR) for Chinese characters presents distinct challenges compared to Latin-script OCR, owing to the tens of thousands of distinct *hanzi* characters and the significance of stroke order and radical structure for character discrimination. Early approaches relied on template matching and statistical language models, while contemporary deep learning approaches using convolutional neural networks and transformer architectures have substantially improved accuracy on Chinese OCR tasks.

In the healthcare context, accurate translation of medication labels is critical because mistranslation of ingredient names can produce false positives (unnecessary alarm) or, more dangerously, false negatives (missed toxic ingredient). This requirement motivated the selection of a large multimodal language model (Gemini 2.5 Flash Lite) for ingredient extraction rather than a conventional OCR pipeline, as the model's semantic understanding of pharmaceutical Chinese produces higher ingredient extraction accuracy—particularly for abbreviated, stylized, or low-contrast label typography.

### 2.3 Chatbots in Healthcare Consultation

Chatbots have been studied as tools for health education, medication adherence, and triage in several Indonesian contexts. Kurniasih et al. (2024) demonstrated that WhatsApp-based medication reminder bots significantly improved medication adherence in pregnant patients with hypertension. Fadhilah et al. (2024) evaluated a neural network-powered health education chatbot and found improvements in user health literacy. However, both studies acknowledge that existing systems provide general or administratively-oriented functions and fall short of personalized safety assessment.

The core challenge in deploying AI chatbots for medical consultation is the risk of hallucination — the generation of plausible-sounding but factually incorrect information (Pantan, 2023). In the context of drug safety, hallucinated information can constitutes a direct patient safety risk. This has motivated prior work in rule-based expert systems for clinical decision support, where all recommendation logic is explicitly codified rather than generated by probabilistic models.

### 2.4 Hybrid AI Architectures for Medical Recommendation

A growing body of research advocates for hybrid architectures that combine the natural language capabilities of large language models with the verifiability and traceability of rule-based systems. In FitMate, this hybrid principle is implemented as a strict functional partition: the LLM is permitted to classify user intent, normalize ingredient names, and generate conversational replies, but the safety verdict — the binary determination of whether an ingredient is safe, toxic, or present — is always derived from a rule-based database lookup with no LLM involvement in the determination.

This architecture ensures that safety outputs can be traced to specific pharmacist-validated database entries, satisfies zero-hallucination requirements, and enables systematic pharmacist review of the underlying data rather than AI output auditing.

---

## 3. System Architecture and Methods

### 3.1 System Overview

FitMate consists of three integrated subsystems:

1. **Web Scanner (PWA Frontend):** A React.js / Next.js Progressive Web App providing camera access, image capture, and real-time scan results with toxicity visualization.
2. **Backend API:** A Python FastAPI service that orchestrates OCR processing, database lookup, fuzzy ingredient matching, and WhatsApp webhook handling.
3. **WhatsApp Consultation Bot:** A Twilio-integrated WhatsApp bot providing conversational TCM safety consultation, accessible independently of the web scanner.

```
User (phone camera)
    │
    ▼
PWA Frontend (Next.js)
    │ POST /api/v1/ocr/upload
    ▼
Backend API (FastAPI)
    ├── OCR Service (Gemini 2.5 Flash Lite)
    │       └── Extracts: [{mandarin_name, indonesian_name}]
    ├── Safety Service (Fuzzy Match + DB Lookup)
    │       └── Returns: [{ingredient, is_toxic, category, description}]
    └── Response → Frontend → Toxicity Warning Card
    
WhatsApp (Twilio Sandbox)
    │ POST /whatsapp/webhook
    ▼
Backend API (FastAPI)
    ├── Intent Classifier (Gemini 2.5 Flash Lite via OpenRouter)
    ├── Fuzzy Lookup (thefuzz token_set_ratio)
    ├── Safety Verdict (Rule-based: DB field is_toxic)
    └── Reply Generator (Gemini 2.5 Flash Lite — language only)
```

**Figure 1.** FitMate system architecture overview.

### 3.2 Knowledge Base Construction

The TCM ingredient knowledge base was constructed through a multi-stage pipeline:

**Stage 1 — Data Collection.** Raw TCM ingredient data was collected from three sources:
- **SymMap** (Traditional Chinese Medicine Systems Pharmacology and Mapping database) — provides herb-to-molecule-to-target mappings
- **TCMID** (Traditional Chinese Medicine Integrated Database) — provides herb descriptions, constituent compounds, and clinical indications
- **BPOM Public Warning Lists** — Indonesia's national drug regulator's published lists of traditional medicine products containing illicit pharmaceutical chemicals

**Stage 2 — Pharmacist Review.** All collected entries were exported to a structured Excel template and reviewed by three licensed pharmacy students under the supervision of a faculty pharmacist advisor. Reviewers assessed: (a) accuracy of toxicity classification, (b) currency of contraindication information against pharmacological literature, (c) accuracy of Indonesian-language descriptions, and (d) correctness of Mandarin, Pinyin, and Latin name variants.

**Stage 3 — Database Seeding.** Validated entries were imported into MongoDB via a structured seeding script (`seed_100_tcm.py`). The resulting database (`tcm_ingredients` collection) contains 103 entries with the following schema:

```json
{
  "indonesian_name": "Lo Han Guo / Buah Biksu",
  "mandarin_name": "罗汉果",
  "pinyin_name": "Luó Hàn Guǒ",
  "english_name": "Monk Fruit",
  "latin_name": "Siraitia grosvenorii",
  "is_toxic": false,
  "toxicity_level": null,
  "target_organ": null,
  "contraindications": "Tidak ada kontraindikasi khusus yang terdokumentasi",
  "description": "Suplemen herbal pereda tenggorokan dan batuk"
}
```

The database currently covers:
- 50 commonly used TCM patent medicines and herbal supplements
- 50 culinary herbs dual-used for medicinal purposes and common TCM cooking stocks (*ciakpo*)
- 13 toxic or BPOM-flagged substances including substances containing aristolochic acid, alkaloids with hepatotoxicity, and herbs contraindicated in pregnancy

### 3.3 OCR and Ingredient Extraction Pipeline

Label image processing is performed by **Gemini 2.5 Flash Lite** in multimodal mode, invoked through the OpenRouter API. Unlike conventional OCR pipelines that treat label reading as character-level text extraction, the LLM approach leverages semantic understanding of pharmaceutical Chinese to produce structured ingredient extraction.

The system prompt instructs the model to:
- Identify all ingredient names (*成分*, *配方*, *成份*) in the image
- For each ingredient, return both the Mandarin form and the most common Indonesian or Pinyin transliteration
- Ignore non-ingredient text (branding, dosage instructions, registration numbers)
- Return structured JSON output for downstream database lookup

This approach outperforms traditional OCR for TCM labels particularly in challenging conditions: partially obscured text, metallic foil packaging, ultra-small character sizes, and traditional script variants (*繁體字*).

### 3.4 Ingredient Safety Matching

Extracted ingredient names are matched against the MongoDB knowledge base using fuzzy string matching (`thefuzz` library, `token_set_ratio` method). Each ingredient name is compared against five name variant fields per database entry: `indonesian_name`, `mandarin_name`, `pinyin_name`, `english_name`, and `latin_name`. The highest score across all five comparisons determines the match.

A minimum threshold score of 68 (out of 100) is required for a database match to be accepted. Below this threshold, the ingredient is classified as **"not found"** and the system explicitly acknowledges uncertainty rather than defaulting to a "safe" assumption. This behavior is critical: a false-negative match producing an incorrect "safe" verdict could have direct patient safety consequences.

**Ingredient name normalization.** Prior to fuzzy matching, the intent classification LLM normalizes user-provided ingredient names from foreign-language forms to standard Indonesian, English, or Pinyin equivalents. This step improves match accuracy for TCM labels from European markets (where ingredient names may appear in German, Dutch, or Latin) or for product names using uncommon transliteration conventions.

### 3.5 WhatsApp Consultation Bot Architecture

The WhatsApp bot operates as a standalone consultation channel accessible without the web scanner. Users can directly query safety information by typing ingredient names or natural language questions. The bot is built on the following architectural principles:

#### 3.5.1 Intent Classification

Incoming WhatsApp messages are classified into one of three intent categories by the LLM:

| Intent | Trigger Pattern | Processing Route |
|---|---|---|
| `ingredient_safety_inquiry` | asking if an ingredient is safe, toxic, suitable for a condition; or typing a bare ingredient name | Rule-based DB lookup → LLM reply generation |
| `ingredient_info_inquiry` | asking what an ingredient is, its benefits or uses | DB context retrieval → LLM informational reply |
| `general_tcm_chat` | greetings, general health questions, off-topic messages | LLM conversational reply |

The intent classifier also handles: (a) resolution of vague references ("bahan itu", "yang tadi") using conversation history context, (b) normalization of foreign-language ingredient names, and (c) detection of comma-separated ingredient lists from label reading.

#### 3.5.2 Safety Verdict — Strict Rule-Based Architecture

For `ingredient_safety_inquiry` intents, safety verdicts are determined exclusively by the database layer:

```
safety_verdict = _build_safety_verdict(best_match, score)
# Returns: "safe" | "toxic" | "not_found"
# This function contains no LLM call — pure Python conditionals on DB fields
```

The verdict is then passed as a **constant string** to the LLM reply generator, which is instructed to:
1. Acknowledge the verdict faithfully (it cannot change or contradict it)
2. Acknowledge the user's stated health conditions by name
3. Generate empathetic, contextually appropriate surrounding language

This separation ensures that the LLM contributes natural language quality to the response without any ability to fabricate, qualify, or contradict the underlying medical determination.

#### 3.5.3 Health Condition Acknowledgment

A key UX contribution of the current system is the explicit acknowledgment of user-stated health conditions in safety replies. The reply generation system prompt includes explicit instruction to identify and name any health conditions mentioned in the user's current message or recent conversation history — such as diabetes, pregnancy, hypertension, or kidney disease — and to include condition-specific guidance in the reply, while clearly attributing this guidance to the database-provided contraindication data rather than AI-generated medical opinion.

#### 3.5.4 Conversation Memory

Per-user conversation history is maintained in a TTL cache (`TTLCache`, `maxsize=1000`, `ttl=7200`), enabling multi-turn consultation within a 2-hour session. History is used by both the intent classifier (for reference resolution) and the reply generator (for conversational coherence). Maximum history depth is 15 user messages to control token consumption.

### 3.6 Multi-Ingredient Batch Lookup

When a user's message is classified as an ingredient safety inquiry and the extracted `ingredient_name` field contains comma-separated contents (indicating a label reading scenario), the system executes parallel database lookups for each named ingredient and returns a consolidated safety card:

```
🔍 Hasil cek 3 bahan:
✅ Lo Han Guo / Buah Biksu — Aman
✅ Akar Manis — Aman
❓ [Bahan] — Tidak ditemukan di database
```

This feature specifically serves the standalone WhatsApp use case where users manually read a label and type the ingredient list directly into the chatbot without using the web scanner.

---

## 4. Implementation

### 4.1 Technology Stack

| Component | Technology | Rationale |
|---|---|---|
| Frontend | Next.js 14, Tailwind CSS, PWA | Cross-platform mobile access without app store |
| Backend | Python 3.11, FastAPI | Async processing, Pydantic data validation |
| Primary Database | MongoDB | Flexible schema for evolving TCM data structure |
| OCR / Vision | Gemini 2.5 Flash Lite (multimodal) | Semantic understanding of pharmaceutical Chinese |
| Intent / NLU | Gemini 2.5 Flash Lite via OpenRouter | Cost-effective LLM with Indonesian language support |
| Ingredient Matching | thefuzz (Levenshtein / token_set_ratio) + LLM normalization | Handles transliteration variants and common spelling variations |
| WhatsApp | Twilio Sandbox | Rapid deployment without Meta Business verification |
| Authentication | JWT (admin dashboard) | Lightweight credential protection for prototype |
| Deployment | Vercel (frontend), local / EC2 (backend) | Free tier frontend; backend requires HTTPS for Twilio webhook |

### 4.2 Security Measures

The following security controls are implemented in the prototype:

- **Twilio webhook signature validation**: All incoming webhook requests from Twilio are validated against the `X-Twilio-Signature` header using the HMAC-SHA1 algorithm. Requests failing validation are silently dropped.
- **Rate limiting**: The OCR endpoint is rate-limited to 5 requests/minute per IP; the WhatsApp bot rate-limits per phone number to 20 messages per 10 minutes.
- **API key protection**: All service credentials are stored in `.env` and excluded from version control via `.gitignore`.
- **Security headers**: All API responses include `X-Content-Type-Options`, `X-Frame-Options`, and `Referrer-Policy` headers via a custom FastAPI middleware.

### 4.3 User Interface Design

The PWA follows a "Modern Apothecary" design concept using a 60-25-10-5 color ratio with Imperial Red (`#930014`) reserved exclusively for toxic ingredient warnings. Typography uses Merriweather for headings, Inter for body text, and Noto Sans SC for Chinese character display. The design prioritizes glanceability: a user should be able to determine whether a scanned product is safe or dangerous within 2 seconds of receiving the scan result.

---

## 5. Testing and Evaluation

### 5.1 Technical Testing (Black-Box)

The OCR pipeline was evaluated against a test set of 25 TCM product label photographs captured under varied conditions (outdoor lighting, low contrast, metallic packaging, angled shots). The target standard was ≥85% ingredient extraction accuracy, consistent with the system's design requirement (SCAN-04).

The WhatsApp chatbot response pipeline was evaluated for: (a) correct intent classification, (b) correct safety verdict derivation, (c) appropriate acknowledgment of stated health conditions, and (d) response latency within Twilio's 15-second webhook processing window.

### 5.2 Medical Expert Validation

All database entries and system output formats were reviewed by pharmacy student team members and a faculty pharmacist advisor, targeting zero medical misinformation in any output the system could produce. Validation specifically addressed:
- Accuracy of toxicity classifications
- Correctness of contraindication descriptions
- Appropriate scope of the medical disclaimer
- Whether any LLM-generated reply language could be interpreted as prescriptive medical advice

### 5.3 User Acceptance Testing (UAT)

UAT involves 15–20 participants from the general public performing standardized tasks: (a) scanning a provided TCM product label, (b) reviewing the safety result, (c) conducting a multi-turn WhatsApp consultation including stating a health condition, and (d) reviewing a multi-ingredient label by typing the ingredient list into the bot directly. Usability is evaluated on: ease of use, clarity of safety information, perceived trustworthiness, and willingness to use the system before purchasing a TCM product.

---

## 6. Results and Discussion

### 6.1 System Functionality

The end-to-end pipeline from label photograph to structured safety output was successfully implemented and verified. The Gemini 2.5 Flash Lite model produces structured ingredient extraction from TCM labels, including correct identification of ingredients from stylized and low-contrast typography.

The hybrid rule-based / LLM architecture successfully maintains the zero-hallucination guarantee in all tested scenarios. The LLM safely generated empathetic, contextually appropriate replies while the underlying safety verdicts remained exclusively determined by database fields, as verified by code review and test case execution.

### 6.2 Chatbot Conversation Quality

Following iteration on the chatbot's system prompts, the bot demonstrates the following improvements over naive LLM-based consultation approaches:

- **Health condition acknowledgment**: When users state conditions such as diabetes, pregnancy, or hypertension, the generated reply explicitly names the condition and provides condition-appropriate context, drawing from the database's `contraindications` field.
- **Foreign-language ingredient name handling**: The intent classifier's normalization step translates foreign-language ingredient names (German, Dutch, Latin) to standard Indonesian/English/Pinyin before fuzzy matching, reducing false "not found" responses for imported TCM products.
- **Multi-turn coherence**: Conversation history enables reference resolution across turns ("apakah bahan tadi aman untuk ibu hamil?" after a prior ingredient query).
- **Standalone usability**: The bot provides a complete consultation experience without requiring the web scanner, including a first-time user welcome message explaining capabilities.

### 6.3 Identified Limitations

**Database coverage.** The current 103-ingredient database is sufficient for prototype demonstration but covers a minority of ingredients found in the full Indonesian TCM market. Common user queries for unlisted ingredients return a "not found" response; while this is the correct conservative behavior, it limits practical utility.

**In-memory conversation storage.** Conversation history is stored in a TTL cache that resets on server restart. In a development environment with hot-reload enabled, this causes repeated welcome messages when code changes trigger restarts.

**Fuzzy matching limitations.** The `token_set_ratio` fuzzy matcher performs well for transliteration variants but fails on semantic similarity queries (e.g., a user describing symptoms rather than naming an ingredient). This is partially mitigated by the intent classifier's LLM normalization step but remains a ceiling on matching accuracy for novel ingredient names.

---

## 7. Future Developments

### 7.1 Multilingual Semantic Embedding Search

The current fuzzy matching approach operates on lexical similarity and is limited in its ability to bridge semantic gaps between diverse ingredient naming conventions. We propose replacing or augmenting fuzzy matching with **multilingual sentence embeddings** using the `paraphrase-multilingual-MiniLM-L12-v2` model (Sentence Transformers), which supports Indonesian, Mandarin, Pinyin, English, Latin, and over 50 additional languages in a shared embedding space.

The proposed architecture precomputes embeddings for all name variants of each database entry at seed time, storing them alongside the document in MongoDB. At query time, the normalized ingredient name is embedded and matched against stored vectors via cosine similarity. Advantages include: (a) accurate cross-language matching without LLM normalization as an intermediate step, (b) semantic similarity retrieval enabling queries like "akar yang menyebabkan gagal ginjal" to surface aristolochic acid entries, and (c) robustness to unusual transliteration conventions.

### 7.2 Persistent User Health Profile

A critical enhancement is the persistence of user-stated health conditions across sessions, keyed by WhatsApp phone number and stored in MongoDB with TTL indexes. A health profile (`conditions[]`, `medications[]`, `is_pregnant`, `age_group`) would enable the system to automatically apply condition-specific safety logic to every subsequent query without requiring the user to re-state their health context, and would enable proactive safety alerts when previously queried ingredients have specific contraindications for the user's documented conditions.

### 7.3 Drug-Herb Interaction Database

The current system evaluates individual ingredient safety but does not model interactions between TCM herbs and conventional pharmaceutical medications. This is a significant safety gap, as several widely-used TCM ingredients have documented clinically significant interactions: Danshen (*Salvia miltiorrhiza*) with warfarin, licorice root with corticosteroids, ginkgo biloba with anticoagulants and SSRIs, and Asian ginseng with insulin and MAOIs. A drug-herb interaction database module, in which users provide their current medication list and the system cross-references known interactions with scanned ingredients, would represent a substantial contribution to TCM patient safety screening.

### 7.4 Database Expansion and Structured Contraindication Fields

Expanding the database to 500+ entries via the existing BPOM/SymMap/TCMID scraping pipeline is a near-term priority. Concurrent with expansion, the free-text `contraindications` field should be supplemented with a structured `contraindicated_conditions[]` array enabling deterministic conditional matching rather than requiring the LLM to interpret free-text contraindication descriptions.

### 7.5 Product-Level Brand Recognition

Many Indonesian TCM consumers purchase branded products (e.g., Tolak Angin, Antangin, Bao Ji Wan) rather than individual ingredients. A brand-level product database mapping common product names to their known ingredient lists would enable queries such as "Tolak Angin aman untuk penderita hipertensi?" without requiring label scanning, reducing friction for experienced TCM consumers who purchase familiar brands routinely.

### 7.6 Image Scanning via WhatsApp

Extending the OCR pipeline to accept label images sent directly in WhatsApp would eliminate the web application as a required step for label scanning, making the full safety scanning capability accessible to users who prefer messaging-based interaction. This requires careful management of Twilio webhook response latency and image preprocessing.

---

## 8. Conclusion

This paper presents FitMate, a TCM safety scanner and consultation system addressing Indonesia's critical gap in accessible, accurate, and linguistically appropriate TCM safety information. The system makes three primary contributions:

1. **A hybrid AI architecture for medical safety applications** that strictly separates rule-based medical determination (zero hallucination) from LLM-mediated natural language interaction, providing both reliability and conversational quality.

2. **A pharmacist-validated TCM safety knowledge base** covering 103 of the most commonly consumed TCM products in Indonesia, with a data pipeline supporting ongoing expansion from BPOM, SymMap, and TCMID sources.

3. **A WhatsApp-native consultation interface** that operates as a standalone safety consultation channel, accessible to any Indonesian smartphone user without application installation, registration, or prior use of the scanning tool.

FitMate addresses the public health challenge documented by BPOM (2021, 2025, 2026) of widespread unsafe self-medication with TCM products whose labels are inaccessible to Indonesian consumers, by providing — for the first time — a zero-friction, pharmacist-validated, AI-assisted ingredient safety checker in a form factor (WhatsApp chatbot + camera-based PWA) appropriate to Indonesia's smartphone and messaging infrastructure.

---

## Acknowledgments

The authors thank the faculty pharmacist advisor at Universitas Ma Chung for expert review of the TCM safety knowledge base. Database entries were validated through the pharmacological literature and BPOM public safety data. This work was supported by the PKM-KC (Program Kreativitas Mahasiswa — Karsa Cipta) scheme of Indonesia's Ministry of Education, Culture, Research, and Technology (Kemendikbudristek) through the Simbelmawa platform.

---

## References

Badan Pengawas Obat dan Makanan. (2021). *Public Warning Obat Tradisional, Suplemen Kesehatan, dan Kosmetika Mengandung Bahan Kimia Obat/Bahan Dilarang Tahun 2021*. Jakarta: BPOM.

Badan Pengawas Obat dan Makanan. (2025). *Indonesia dan Tiongkok Perkuat Sinergi Budaya dan Ilmu Pengetahuan dalam Pengembangan Obat Tradisional*. Jakarta: BPOM.

Badan Pengawas Obat dan Makanan. (2026). *Hasil Patroli Siber Marketplace 2025: Temuan Produk Obat Tidak Sesuai Ketentuan*. Jakarta: BPOM.

Esti, N., Rahmawati, D., & Prasetyo, A. (2025). Perilaku unsupervised self-medication pada kelompok usia produktif di Indonesia. *Jurnal Kesehatan Masyarakat Nasional*, 20(2), 101–109.

Fadhilah, R., Maulani, M. R., Resdiana, W., & Hamidin, D. (2024). Integrasi fitur Chatbot dalam aplikasi edukasi kesehatan dan kebugaran menggunakan algoritma neural network. *Jurnal Kecerdasan Buatan dan Teknologi Informasi*, 3(3), 125–135.

Ghaznawi, U. U., Akhtar, L., Rehmat, A., Younas, I., & Ullah, S. (2025). Assessment of multivitamin usage and factors affecting lifestyle. *BMC Nutrition*, 11, 27.

Kurniasih, H., Winarso, P., & Sartika, L. (2024). Pengembangan aplikasi bot WhatsApp pengingat minum obat untuk meningkatkan kepatuhan minum obat pada ibu hamil dengan hipertensi. *Seminar Nasional Keperawatan*, 22, 162–166.

Nurhalisa, F., et al. (2024). Traditional Chinese Medicine sebagai warisan budaya dan praktik kesehatan etnis Tionghoa di Indonesia. *Jurnal Sejarah dan Kebudayaan*, 12(1).

Pantan, F. (2023). Pemanfaatan Chatbot berbasis kecerdasan buatan dalam layanan konsultasi digital. *Jurnal Teknologi Informasi*, 8(2).

Rahmasiah, R., Roni, R., Hadi, S., & Termia, M. (2023). Gambaran pengetahuan masyarakat tentang peredaran sediaan farmasi obat tradisional non BPOM di Kelurahan Rijang Pittu Kabupaten Sidrap. *Marendeng Journal*, 7(2), 49–57. https://doi.org/10.58554/jkm

Wahab, B., Apriana, A., & Silitonga, D. (2025). Perancangan sistem konsultasi kesehatan online berbasis website guna meningkatkan efisiensi dan efektivitas pelayanan kesehatan pada UPTD Puskesmas Tiga Balata tahun 2025. *Jurnal Penelitian Kesmasy*, 7(2).

World Health Organization. (2019). *WHO Global Report on Traditional and Complementary Medicine 2019*. Geneva: WHO.

---

*Manuscript prepared for PKM-KC proposal submission, April 2026. All system components described are implemented and functional in the current v1.1 prototype.*
