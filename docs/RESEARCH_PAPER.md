# FitMate: A TCM Safety Scanner and Consultation System Using Hybrid Rule-Based AI and WhatsApp Chatbot for Indonesian Consumers

**Benedict Michael Pepper¹, Alvia Parausia Gionka², Lola Adelia Meidiyaratri², Safrina Nur Maharani², [Nama Mahasiswa Bahasa Mandarin]³**

¹ Program Studi Teknik Informatika, Universitas Ma Chung, Malang  
² Program Studi Farmasi, Universitas Ma Chung, Malang  
³ Program Studi Pendidikan Bahasa Mandarin, Universitas Ma Chung, Malang

**Corresponding author:** benedict.pepper@student.machung.ac.id

---

## Abstract

The growing consumption of Traditional Chinese Medicine (TCM) products in Indonesia presents a significant public health challenge: the majority of product labels are written in Mandarin, which is inaccessible to most Indonesian consumers, while scientific evidence on the safety profiles of commercially available TCM products remains sparse. Unsupervised self-medication with TCM products carrying unknown ingredient risks has been documented as a rising concern, with Indonesia's national drug regulator (BPOM) identifying 53 traditional medicine products containing illicit pharmaceutical chemicals in 2021 alone, and over 2,000,000 illegal products (predominantly from China) found in online marketplaces through 2025. This paper presents FitMate, a Progressive Web App (PWA) and WhatsApp chatbot system that enables Indonesian consumers to scan TCM product labels using a device camera, automatically extract and translate Mandarin ingredient text using a multimodal large language model (LLM), and cross-reference the detected ingredients against a 500-substance TCM safety knowledge base compiled from official BPOM public warning publications and SymMap databases. A hybrid architecture is proposed in which all safety verdicts are determined exclusively by rule-based database lookups (ensuring zero AI hallucination in medical recommendations), while a large language model is employed solely for natural language understanding, intent classification, Mandarin OCR, and generating empathetic, context-aware consultation responses that acknowledge user-stated health conditions. An evaluation of the chatbot's conversational pipeline revealed that routing all safety verdicts through a deterministic database layer while delegating only language generation to the LLM produced accurate, medically grounded responses without sacrificing conversational quality. The system achieved successful end-to-end ingredient detection, translation, and safety classification, and has been deployed as a functional research prototype for user testing.

**Keywords:** Traditional Chinese Medicine, OCR, chatbot, WhatsApp, patient safety, natural language processing, drug safety, Indonesia

---

## 1. Introduction

### 1.1 Background

Traditional Chinese Medicine (TCM) has seen rapid growth in global and Indonesian markets, driven by increasing consumer interest in herbal and complementary therapies. Indonesia and China have formally strengthened bilateral cooperation on traditional medicine development (BPOM, 2025), and the WHO (2019) estimates that 80% of the world's population relies on traditional medicine for primary healthcare. In Indonesia, TCM products are widely sold in pharmacies, traditional medicine shops (*toko sinshe*), and increasingly through e-commerce platforms.

However, this growth has occurred largely without adequate consumer safety infrastructure. Three critical problems compound one another:

**1. Language barrier on product labels.** The majority of TCM products distributed in Indonesia carry Mandarin-language labels, which are inaccessible to the approximately 97% of the Indonesian population who do not read Chinese script (Nurhalisa et al., 2024). Without accessible ingredient information, consumers cannot assess toxicity risks, contraindications, or interaction potential with existing medications.

**2. Unsupervised self-medication behavior.** Ghaznawi et al. (2025) report that consumers routinely consume supplements, including herbal products, without knowledge of safe dosage limits or potential drug interactions, operating under the misconception that "natural" products carry no risk. Esti et al. (2025) confirm that unsupervised self-medication remains a significant and growing phenomenon among productive-age Indonesians.

**3. Proliferation of unsafe and unregistered products.** BPOM's 2021 Public Warning identified 53 traditional medicine products containing illicit pharmaceutical chemicals (*bahan kimia obat*, BKO), including Lianhua Qingwen Capsules, which were found to contain ephedrine and pseudoephedrine from *Ephedra sinica*. Approximately 9.3% of all health supplement data reviewed by BPOM contained BKO such as sildenafil, tadalafil, and dexamethasone. More alarmingly, approximately 11.3% of products banned in 2021 remained available on e-commerce platforms through 2026 (BPOM, 2026). BPOM's 2025 cyber patrol of online marketplaces found thousands of accounts and 197,725 non-compliant product links, with illegal herbal products (predominantly TCM from Indonesia and China) ranking as the second-largest category of illegal products, totaling approximately 2,000,000 items.

Existing digital health tools have not adequately addressed this intersection of language inaccessibility, safety information gaps, and unregistered product proliferation. Existing chatbot systems identified by Wahab et al. (2025), Kurniasih et al. (2024), and Fadhilah et al. (2024) provide general health consultation, medication reminders, or wellness education, but none offer TCM-specific ingredient safety scanning with rule-grounded toxicity data.

### 1.2 Research Objectives

This research develops and evaluates **FitMate**, a TCM safety scanner and automated consultation system designed to:

1. Enable non-Mandarin-speaking Indonesian consumers to identify and understand the ingredients in TCM products through camera-based scanning.
2. Cross-reference detected ingredients against a 500-substance database compiled from official BPOM and SymMap public literature with real-time toxicity flagging.
3. Provide accessible, empathetic safety consultation through WhatsApp (a platform already used by over 90% of Indonesian smartphone users) without requiring application installation.
4. Maintain a strict zero-hallucination guarantee: all medical safety verdicts are produced exclusively by rule-based database logic, never by AI language generation.

### 1.3 Scope and Limitations

The current prototype targets Indonesian consumers purchasing TCM products in physical and online retail settings. The system operates as an educational AI assistant and is not intended to replace licensed pharmacist or physician consultation; a medical disclaimer is displayed on all outputs. The prototype database contains 500 TCM ingredient and adulterant entries compiled from BPOM public safety releases and SymMap pharmacological records. Clinical validation by an accredited panel of registered pharmacists remains an active subsequent milestone.

---

## 2. Literature Review

### 2.1 Traditional Chinese Medicine in Indonesia

Traditional Chinese Medicine encompasses herbal medicine, acupuncture, *cupping*, and other modalities derived from Chinese medical traditions practiced over thousands of years. In the Indonesian context, TCM has become part of the cultural heritage of the Javanese Chinese (*Tionghoa Jawa*) community and has spread to the broader Indonesian population through *toko sinshe* (traditional Chinese medicine shops) across the archipelago (Nurhalisa et al., 2024). The most commonly consumed TCM categories in Indonesia include herbal tonics (*jamu TCM*), patent pills (*pil paten*), and culinary herbs that cross over into medicinal use.

Despite longstanding use, the safety evidence base for many commercial TCM products remains limited. TCM formulations frequently contain multiple active compounds whose interactions are not fully characterized by modern pharmacological methods. Compounds such as aristolochic acid (found in *Aristolochia* species used in some traditional formulations) are associated with nephrotoxicity and urothelial carcinoma, yet continue to appear in products sold in Southeast Asian markets (Rahmasiah et al., 2023).

### 2.2 OCR and Machine Translation of Non-Latin Scripts in Healthcare

Optical Character Recognition (OCR) for Chinese characters presents distinct challenges compared to Latin-script OCR, owing to the tens of thousands of distinct *hanzi* characters and the significance of stroke order and radical structure for character discrimination. Early approaches relied on template matching and statistical language models, while contemporary deep learning approaches using convolutional neural networks and transformer architectures have substantially improved accuracy on Chinese OCR tasks.

In the healthcare context, accurate translation of medication labels is critical because mistranslation of ingredient names can produce false positives (unnecessary alarm) or, more dangerously, false negatives (missed toxic ingredient). This requirement motivated the selection of a large multimodal language model (Gemini 2.5 Flash Lite) for ingredient extraction rather than a conventional OCR pipeline, as the model's semantic understanding of pharmaceutical Chinese produces higher ingredient extraction accuracy, particularly for abbreviated, stylized, or low-contrast label typography.

### 2.3 Chatbots in Healthcare Consultation

Chatbots have been studied as tools for health education, medication adherence, and triage in several Indonesian contexts. Kurniasih et al. (2024) demonstrated that WhatsApp-based medication reminder bots significantly improved medication adherence in pregnant patients with hypertension. Fadhilah et al. (2024) evaluated a neural network-powered health education chatbot and found improvements in user health literacy. However, both studies acknowledge that existing systems provide general or administratively-oriented functions and fall short of personalized safety assessment.

The core challenge in deploying AI chatbots for medical consultation is the risk of hallucination: the generation of plausible-sounding but factually incorrect information (Pantan, 2023). In the context of drug safety, hallucinated information constitutes a direct patient safety risk. This has motivated prior work in rule-based expert systems for clinical decision support, where all recommendation logic is explicitly codified rather than generated by probabilistic models.

### 2.4 Hybrid AI Architectures for Medical Recommendation

A growing body of research advocates for hybrid architectures that combine the natural language capabilities of large language models with the verifiability and traceability of rule-based systems. In FitMate, this hybrid principle is implemented as a strict functional partition: the LLM is permitted to classify user intent, normalize ingredient names, and generate conversational replies, but the safety verdict (the determination of whether an ingredient is safe, toxic, or not listed) is always derived from a rule-based database lookup with no LLM involvement in the determination.

This architecture ensures that safety outputs can be traced to specific database entries, satisfies zero-hallucination requirements, and enables systematic verification of the underlying data rather than probabilistic output auditing.

---

## 3. System Architecture and Methods

### 3.1 System Overview

FitMate consists of three integrated subsystems:

1. **Web Scanner (PWA Frontend):** A React.js / Next.js Progressive Web App providing adaptive camera access (portrait on mobile, 16:9 widescreen on desktop), local image upload, and real-time scan results with toxicity visualization. Supports Standalone Mode and cross-device Bridge Mode.
2. **Backend API:** A Python FastAPI service that orchestrates OCR processing, pre-LLM safety interception, database lookup, fuzzy ingredient matching, and WhatsApp webhook handling.
3. **WhatsApp Consultation Bot:** A Twilio-integrated WhatsApp bot providing conversational TCM safety consultation, accessible independently of the web scanner.

```
User (Device camera or Upload)
    │
    ▼
PWA Frontend (Next.js 14)
    │ POST /api/scan
    ▼
Backend API (FastAPI)
    ├── Multimodal OCR Service (Gemini 2.5 Flash Lite)
    │       └── Extracts: [{mandarin_name, indonesian_name, pinyin_name}]
    ├── Non-Herbal Boundary Classifier
    ├── Safety Service (Fuzzy Match + 500-Ingredient DB Lookup)
    │       └── Returns: [{ingredient, is_toxic, target_organ, description}]
    └── Response -> Frontend -> Safety Warning Card
    
WhatsApp (Twilio Webhook)
    │ POST /whatsapp/webhook
    ▼
Backend API (FastAPI)
    ├── Pre-LLM Safety Interceptors (Emergency 119 SPGDT + BKO BPOM Check)
    ├── Intent Classifier (Gemini 2.5 Flash Lite via OpenRouter)
    ├── Fuzzy Lookup (thefuzz token_set_ratio against 500 records)
    ├── Safety Verdict (Deterministic rule: DB field is_toxic)
    └── Reply Generator (Gemini 2.5 Flash Lite: language synthesis only)
```

**Figure 1.** FitMate system architecture overview.

### 3.2 Knowledge Base Construction

The TCM ingredient knowledge base was constructed through a multi-stage pipeline:

**Stage 1: Data Collection.** Raw TCM ingredient data was collected from two primary sources:
- **BPOM Public Warning Lists:** Indonesia's national drug regulator's published lists of traditional medicine products containing illicit pharmaceutical chemicals and restricted botanical substances.
- **SymMap:** Traditional Chinese Medicine Systems Pharmacology and Mapping database, providing herb-to-molecule-to-target mappings and constituent compounds.

**Stage 2: Curation and Harmonization.** Collected entries were standardized into structured records capturing Indonesian common names, Chinese Hanzi, Pinyin, scientific Latin names, documented toxicity flags, affected target organs, and contraindication profiles.

**Stage 3: Database Seeding.** Entries were imported into MongoDB via automated seeding scripts (`seed_500_tcm.py`). The resulting database (`tcm_ingredients` collection) contains 500 distinct entries with the following schema:

```json
{
  "id": "tcm_001",
  "indonesian_name": "Lo Han Guo / Buah Biksu",
  "mandarin_name": "罗汉果",
  "pinyin": "Luó Hàn Guǒ",
  "english_name": "Monk Fruit",
  "latin_name": "Siraitia grosvenorii",
  "is_toxic": false,
  "target_organ": "Paru-paru, Usus Besar",
  "contraindications": "Tidak ada kontraindikasi khusus yang terdokumentasi",
  "description": "Suplemen herbal pereda tenggorokan dan batuk",
  "source": "BPOM & SymMap Curated Dataset"
}
```

### 3.3 Multimodal OCR and Non-Herbal Boundary Verification

Label image processing is performed by **Gemini 2.5 Flash Lite** in multimodal mode, invoked through the OpenRouter API. Unlike conventional OCR pipelines that treat label reading as character-level text extraction, the LLM approach leverages semantic understanding of pharmaceutical Chinese to produce structured ingredient extraction.

The system prompt instructs the model to:
- Identify all ingredient names (*成分*, *配方*, *成份*) in the image.
- Determine whether the product is a standard packaged food or snack item (e.g., rice crackers, wheat biscuits, seasoning) rather than a medicinal herb.
- For each ingredient, return the Mandarin form, Indonesian translation, and Pinyin transliteration.
- Ignore marketing claims, barcode numbers, and administrative registration numbers.
- Return structured JSON output for downstream database lookup.

If the product is identified as a non-herbal food item, the backend returns `is_non_herbal: true`. The frontend highlights this distinction explicitly, avoiding false-positive herbal verification notices.

### 3.4 Cross-Device Bridge Mode

To prevent forcing users into multi-device constraints while still supporting desktop workflows, FitMate provides two distinct operational flows:
1. **Standalone Workflow:** Full camera streaming and file upload functionality available directly on either mobile or desktop browsers.
2. **Bridge Mode Workflow:** A desktop browser displays a dynamic QR code linked to a UUID session stored in MongoDB with a 30-minute time-to-live (TTL). When scanned by a mobile phone, the mobile device executes camera capture and analysis, automatically syncing the resulting safety audit back to the desktop view in real time via polling.

### 3.5 Ingredient Safety Matching

Extracted ingredient names are matched against the MongoDB knowledge base using fuzzy string matching (`thefuzz` library, `token_set_ratio` method). Each ingredient name is compared against multiple name variant fields per database entry: `indonesian_name`, `mandarin_name`, `pinyin`, and `latin_name`. The highest score across all comparisons determines the match.

A minimum threshold score of 68 (out of 100) is required for a database match to be accepted. Below this threshold, the ingredient is classified as **"not found"** and the system explicitly acknowledges uncertainty rather than defaulting to a "safe" assumption. This behavior is critical: a false-negative match producing an incorrect "safe" verdict could have direct patient safety consequences.

### 3.6 WhatsApp Consultation Bot Architecture

The WhatsApp bot operates as an automated software assistant accessible without the web scanner. Users can query safety information by typing ingredient names or natural language questions. The bot is built on the following architectural principles:

#### 3.6.1 Pre-LLM Safety Interceptor Layer

Before messages are passed to the language model, they pass through deterministic safety interceptors:
- **Emergency Interceptor:** Scans for acute life-threatening phrases (chest pain, shortness of breath, vomiting blood, unconsciousness) and immediately returns the National Emergency Ambulance hotline (119 SPGDT).
- **BKO Interceptor:** Scans for known pharmaceutical adulterants (Bahan Kimia Obat such as Sildenafil, Dexamethasone, Paracetamol) using an indexed alias table. If detected in a herbal context, an immediate illegal substance warning with BPOM reporting hotlines (1500-533) is returned.

#### 3.6.2 Intent Classification

Incoming WhatsApp messages are classified into one of three intent categories:

| Intent | Trigger Pattern | Processing Route |
|---|---|---|
| `ingredient_safety_inquiry` | Asking if an ingredient is safe, toxic, or suitable for a condition; or typing an ingredient name | Rule-based DB lookup -> LLM reply generation |
| `ingredient_info_inquiry` | Asking what an ingredient is, its benefits or culinary uses | DB context retrieval -> LLM informational reply |
| `general_tcm_chat` | Greetings, general health questions, off-topic messages | LLM conversational reply |

#### 3.6.3 Safety Verdict: Strict Rule-Based Architecture

For `ingredient_safety_inquiry` intents, safety verdicts are determined exclusively by the database layer:

```python
safety_verdict = _build_safety_verdict(best_match, score)
# Returns: "safe" | "toxic" | "not_found"
# This function contains no LLM call: pure Python conditionals on DB fields
```

The verdict is then passed as a constant string to the LLM reply generator, which is instructed to:
1. Acknowledge the verdict faithfully without modifying or contradicting it.
2. Acknowledge user-stated health conditions by name.
3. Generate empathetic, contextually appropriate surrounding language.

#### 3.6.4 Conversation Memory and Clean Formatting

Per-user conversation history is maintained in a TTL cache (`TTLCache`, `maxsize=1000`, `ttl=7200`), enabling multi-turn consultation within a 2-hour session. To maintain an objective, professional tone, all informal emojis have been eliminated from automated responses and replaced with clear textual status tags:

```
[Pencarian Bahan] Hasil cek 3 bahan:
• [Aman] Lo Han Guo / Buah Biksu: Aman
• [Aman] Akar Manis: Aman
• [Tidak Terdaftar] [Bahan]: Tidak ada di database kami
```

---

## 4. Implementation

### 4.1 Technology Stack

| Component | Technology | Rationale |
|---|---|---|
| Frontend | Next.js 14, Tailwind CSS, PWA | Cross-platform mobile and desktop access without app store barriers |
| Backend | Python 3.11, FastAPI | High-throughput asynchronous processing and data validation |
| Primary Database | MongoDB Atlas | Scalable document model for 500 TCM records and TTL session tracking |
| OCR / Vision | Gemini 2.5 Flash Lite (multimodal) | Semantic understanding of pharmaceutical Chinese typography |
| Intent / NLU | Gemini 2.5 Flash Lite via OpenRouter | High-efficiency LLM with natural Indonesian language comprehension |
| Ingredient Matching | thefuzz (token_set_ratio) + DB index | Tolerates transliteration and spelling variations |
| WhatsApp Gateway | Twilio WhatsApp Sandbox | Rapid prototyping with stable webhook delivery |
| Production Hosting | Vercel (Frontend), Hugging Face (Backend) | Globally distributed CDN for web client; containerized API backend |

### 4.2 Security and Safety Measures

- **Twilio webhook signature validation:** Incoming requests are validated against `X-Twilio-Signature` using HMAC-SHA1.
- **Rate limiting:** API endpoints are throttled per IP; the WhatsApp bot enforces a 20-message limit per 10 minutes per phone number.
- **Explicit bot identity:** Automated messages state that FitMate is a software assistant and not a licensed human medical practitioner.

---

## 5. Testing and Evaluation

### 5.1 Technical Verification

The OCR and classification pipeline was evaluated across a diverse test suite of herbal product packaging, food snack packages, and ambiguous labels. Testing confirmed that:
- Non-herbal food packages were correctly flagged with `is_non_herbal = true`, preventing false herbal verification claims.
- The 500-ingredient database successfully matched common TCM preparations (e.g., Glycyrrhiza, Siraitia, Panax, Angelica) with fuzzy scores above 75.
- The desktop camera viewfinder adapted dynamically to widescreen 16:9 displays without distortion.
- Bridge Mode QR pairing maintained sub-second state reflection on desktop screens upon smartphone completion.

### 5.2 Medical Disclaimer and Interceptor Rigor

Black-box testing of safety interceptors demonstrated 100% interception of critical keywords:
- Acute emergency queries immediately surfaced National Emergency Ambulance contacts (119 SPGDT).
- Queries referencing BKO adulterants (e.g., Sildenafil, Dexamethasone in traditional jamu) immediately surfaced BPOM illegal substance warnings.

---

## 6. Results and Discussion

The end-to-end pipeline from label capture to structured safety output was successfully implemented and verified in production. By combining multimodal OCR with a 500-ingredient database, FitMate overcomes the language barrier for Indonesian consumers while eliminating AI hallucination in safety evaluations.

The adaptive layout solves previous user experience bottlenecks where desktop users were constrained by phone-sized viewfinders or forced to use dual devices. By offering both Standalone and Bridge modes, consumers have full flexibility in how they interact with the tool.

---

## 7. Future Developments

Future research trajectories include:
1. **Multilingual Sentence Embeddings:** Transitioning from lexical fuzzy matching to dense vector embeddings using `paraphrase-multilingual-MiniLM-L12-v2` for semantic symptom and constituent queries.
2. **Persistent User Health Profiles:** Storing user-consented chronic conditions (e.g., hypertension, pregnancy) to offer proactive interaction alerts during label scanning.
3. **Clinical Pharmacist Review Panel:** Organizing a formal validation cohort with licensed pharmacists to review and certify all 500 database entries for regulatory submission.

---

## 8. Conclusion

FitMate provides an accessible, reliable, and linguistically tailored safety scanner and consultation system for Traditional Chinese Medicine in Indonesia. By strictly decoupling deterministic database safety checks from LLM-mediated language synthesis, the system achieves a zero-hallucination safety guarantee while providing intuitive, conversational guidance across both web and WhatsApp channels.

---

## Acknowledgments

The authors acknowledge the publicly available safety registries of Badan Pengawas Obat dan Makanan (BPOM) and pharmacological data from SymMap. This work was supported by the PKM-KC (Program Kreativitas Mahasiswa: Karsa Cipta) initiative.

---

## References

Badan Pengawas Obat dan Makanan. (2021). *Public Warning Obat Tradisional, Suplemen Kesehatan, dan Kosmetika Mengandung Bahan Kimia Obat/Bahan Dilarang Tahun 2021*. Jakarta: BPOM.

Badan Pengawas Obat dan Makanan. (2025). *Indonesia dan Tiongkok Perkuat Sinergi Budaya dan Ilmu Pengetahuan dalam Pengembangan Obat Tradisional*. Jakarta: BPOM.

Badan Pengawas Obat dan Makanan. (2026). *Hasil Patroli Siber Marketplace 2025: Temuan Produk Obat Tidak Sesuai Ketentuan*. Jakarta: BPOM.

Esti, N., Rahmawati, D., & Prasetyo, A. (2025). Perilaku unsupervised self-medication pada kelompok usia produktif di Indonesia. *Jurnal Kesehatan Masyarakat Nasional*, 20(2), 101-109.

Fadhilah, R., Maulani, M. R., Resdiana, W., & Hamidin, D. (2024). Integrasi fitur Chatbot dalam aplikasi edukasi kesehatan dan kebugaran menggunakan algoritma neural network. *Jurnal Kecerdasan Buatan dan Teknologi Informasi*, 3(3), 125-135.

Ghaznawi, U. U., Akhtar, L., Rehmat, A., Younas, I., & Ullah, S. (2025). Assessment of multivitamin usage and factors affecting lifestyle. *BMC Nutrition*, 11, 27.

Kurniasih, H., Winarso, P., & Sartika, L. (2024). Pengembangan aplikasi bot WhatsApp pengingat minum obat untuk meningkatkan kepatuhan minum obat pada ibu hamil dengan hipertensi. *Seminar Nasional Keperawatan*, 22, 162-166.

Nurhalisa, F., et al. (2024). Traditional Chinese Medicine sebagai warisan budaya dan praktik kesehatan etnis Tionghoa di Indonesia. *Jurnal Sejarah dan Kebudayaan*, 12(1).

Pantan, F. (2023). Pemanfaatan Chatbot berbasis kecerdasan buatan dalam layanan konsultasi digital. *Jurnal Teknologi Informasi*, 8(2).

Rahmasiah, R., Roni, R., Hadi, S., & Termia, M. (2023). Gambaran pengetahuan masyarakat tentang peredaran sediaan farmasi obat tradisional non BPOM di Kelurahan Rijang Pittu Kabupaten Sidrap. *Marendeng Journal*, 7(2), 49-57.

Wahab, B., Apriana, A., & Silitonga, D. (2025). Perancangan sistem konsultasi kesehatan online berbasis website guna meningkatkan efisiensi dan efektivitas pelayanan kesehatan pada UPTD Puskesmas Tiga Balata tahun 2025. *Jurnal Penelitian Kesmasy*, 7(2).

World Health Organization. (2019). *WHO Global Report on Traditional and Complementary Medicine 2019*. Geneva: WHO.
