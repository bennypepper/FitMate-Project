# FitMate: A TCM Safety Scanner and Consultation System Using Hybrid Rule-Based AI and WhatsApp Chatbot for Indonesian Consumers

**Alvia Parausia Gionka¹, Benedict Michael Pepper², Lola Adelia Meidiyaratri³, Safrina Nur Maharani⁴, Rosselynd Elberta Christabel⁵**

¹³⁴ Program Studi Farmasi, Universitas Ma Chung, Malang  
² Program Studi Teknik Informatika, Universitas Ma Chung, Malang  
⁵ Program Studi Pendidikan Bahasa Mandarin, Universitas Ma Chung, Malang  

**Corresponding authors:** benedict.pepper@student.machung.ac.id | 612410009@student.machung.ac.id  
**Publication Scheme:** PKM-KC (Program Kreativitas Mahasiswa: Karsa Cipta) 2026  

---

## Abstract

The growing consumption of Traditional Chinese Medicine (TCM) products in Indonesia presents a critical public health challenge: the majority of commercial packaging labels are written in Mandarin, which is inaccessible to approximately 97% of the Indonesian population. Furthermore, unsupervised self-medication with TCM products carrying undisclosed ingredient risks is widespread. Indonesia's national drug regulator (BPOM) identified 53 traditional medicine products adulterated with illicit pharmaceutical chemicals in 2021 alone, and over 2,000,000 illegal health products were flagged in 2025 online cyber patrols. 

This paper presents FitMate, a dual-channel health screening platform comprising a Progressive Web App (PWA) scanner and a WhatsApp consultation chatbot. FitMate enables non-Mandarin-speaking Indonesian consumers to scan TCM packaging labels using a device camera, extract ingredient names using a multimodal large language model (LLM), and cross-reference detected substances against a curated 500-substance TCM safety knowledge base compiled from official BPOM public warning releases and SymMap databases. A strict hybrid architecture is enforced: all safety determinations are produced exclusively by deterministic rule-based database logic (ensuring zero AI hallucination in safety evaluations), while language models are employed solely for natural language understanding, intent classification, and empathetic reply synthesis. 

Empirical evaluation of 7 candidate LLMs across 25 standardized clinical inquiry prompts (175 test cases) demonstrated that Google Gemini 3.1 Flash Lite (6.38s latency) and OpenAI GPT-5.4 Nano (4.41s latency) provide the optimal balance of inference speed and linguistic accuracy. Black-box penetration tests confirmed 100% interception of acute medical emergencies (routing immediately to National Emergency 119 SPGDT) and prohibited pharmaceutical adulterants (BKO interceptor covering 58 substances across 205 aliases). The system is fully deployed with verified responsive viewfinders (portrait for mobile and 16:9 widescreen for desktop) and cross-device QR code Bridge Mode synchronization.

**Keywords:** Traditional Chinese Medicine, multimodal OCR, chatbot, WhatsApp, patient safety, rule-based expert systems, drug safety, Indonesia

---

## 1. Introduction

### 1.1 Background

Traditional Chinese Medicine (TCM) has experienced significant adoption in Indonesia, accelerated by growing consumer interest in botanical and complementary therapies. Indonesia and China have actively strengthened bilateral cooperation on traditional medicine development (BPOM, 2025), and the World Health Organization (WHO, 2019) estimates that 80% of the global population utilizes traditional medicine for aspects of primary care. In Indonesia, TCM formulations are widely distributed through physical Chinese medicine pharmacies (*toko sinshe*), modern retail drugstores, and e-commerce marketplaces.

Despite this commercial expansion, consumer safety infrastructure remains inadequate due to three compounding factors:

1. **Language barrier on product labels.** Commercial TCM preparations sold in Indonesia predominantly feature Mandarin-language packaging without certified Indonesian translations. This script is illegible to roughly 97% of Indonesian citizens (Nurhalisa et al., 2024), leaving consumers unable to identify active botanical constituents, recognized contraindications, or adverse interaction profiles.
2. **Unsupervised self-medication behavior.** Consumer studies indicate widespread unsupervised consumption of herbal formulations under the false assumption that natural products carry zero health risks (Ghaznawi et al., 2025; Esti et al., 2025). Many patients self-medicate for chronic ailments without professional pharmacist or physician consultation.
3. **Proliferation of adulterated and illicit products.** BPOM's 2021 Public Warning identified 53 traditional medicine products contaminated with synthetic pharmaceutical chemicals (*bahan kimia obat*, BKO). Banned adulterants frequently include sildenafil, tadalafil, dexamethasone, and paracetamol. In addition, BPOM's 2025 cyber patrol of online retail marketplaces flagged 197,725 non-compliant product listings, with illegal herbal preparations representing the second-largest category at roughly 2,000,000 items (BPOM, 2026).

Existing digital health solutions address general telemedicine consultation, medication schedule reminders, or wellness education (Wahab et al., 2025; Kurniasih et al., 2024; Fadhilah et al., 2024). However, none provide specialized TCM ingredient toxicity screening grounded in deterministic regulatory data and delivered through zero-install conversational messaging.

### 1.2 Research Objectives

This study develops and evaluates **FitMate**, an accessible TCM safety scanner and automated consultation platform engineered to:
- Enable Indonesian consumers to extract, translate, and verify Mandarin-language herbal ingredients through camera-based label scanning.
- Cross-reference extracted ingredients against a 500-substance database compiled from BPOM and SymMap pharmacological records with real-time toxicity and contraindication flagging.
- Provide accessible, multi-turn safety consultation through WhatsApp without requiring native mobile app installation.
- Maintain a strict zero-hallucination guarantee by isolating safety verdicts within deterministic rule-based code, completely removing generative LLMs from medical judgment.
- Eliminate clinical communication hazards by enforcing a Modern Apothecary design standard free of informal emojis.

---

## 2. Related Work and Theoretical Foundation

### 2.1 Traditional Chinese Medicine in the Indonesian Sociocultural Context

TCM has deep historical roots in the Indonesian archipelago, initially preserved as part of the cultural heritage of the Peranakan Chinese community and gradually integrated into broader Indonesian society through *toko sinshe* (Nurhalisa et al., 2024). Commonly consumed preparations include patent granules, concentrated pills (*wan*), and restorative herbal soups (*ciakpo*).

However, traditional usage does not equate to absolute pharmacological safety. Herbal constituents frequently contain bioactive compounds requiring strict dosage control. For example, aristolochic acid derived from *Aristolochia* species is an established nephrotoxin and human carcinogen, yet adulterated preparations continue to appear in regional trade (Rahmasiah et al., 2023).

### 2.2 Multimodal Vision Language Models vs. Character-Level OCR

Optical Character Recognition (OCR) for non-Latin typography presents notable technical hurdles when processing Chinese logograms (*hanzi*). Variations in stroke order, radical configuration, low-contrast foil packaging, and stylized calligraphy degrade the accuracy of conventional OCR engines such as Tesseract.

In healthcare contexts, misrecognized characters cause either false alarms (false positives) or missed toxic ingredients (false negatives). FitMate deploys multimodal vision models (Gemini Flash series) that interpret entire packaging scenes holistically. By combining visual feature extraction with contextual knowledge of pharmaceutical Mandarin, multimodal models accurately extract stylized botanical terms that defeat conventional character-level OCR pipelines.

### 2.3 Hybrid AI Systems in Clinical Decision Support

Generative language models possess exceptional fluency in conversational interaction but remain vulnerable to hallucinations: generating factually incorrect assertions with high linguistic confidence (Pantan, 2023). In safety-critical health applications, hallucinations pose unacceptable risks.

FitMate implements a strict hybrid separation:
- **LLM domain:** Natural language understanding, intent classification, OCR translation, and user-facing conversational synthesis.
- **Deterministic domain:** Pre-LLM safety filtering (emergency and BKO interception), database retrieval, and final safety verdict determination.

---

## 3. System Architecture and Methods

### 3.1 Subsystem Overview

FitMate comprises three interconnected components:

1. **Progressive Web App (PWA Frontend):** Built on Next.js 14 and Tailwind CSS. Features adaptive camera viewfinders (portrait 3:4 on mobile, widescreen 16:9 on desktop), local image upload, and real-time toxicity audit cards.
2. **Backend API Service:** Built on Python 3.11 and FastAPI. Orchestrates multimodal OCR, database retrieval, fuzzy matching, and WhatsApp webhook processing.
3. **WhatsApp Consultation Bot:** Integrated via the Twilio WhatsApp Sandbox, providing conversational consultation with per-phone session memory and safety interceptors.

```
                    +------------------------------------------+
                    |        User Capture Interface            |
                    | (Device Camera / Upload / Bridge QR)     |
                    +--------------------+---------------------+
                                         |
                                         v
                    +------------------------------------------+
                    |         PWA Frontend (Next.js 14)        |
                    +--------------------+---------------------+
                                         | POST /api/v1/analyze
                                         v
                    +------------------------------------------+
                    |          FastAPI Backend Engine          |
                    +----+--------------------------------+----+
                         |                                |
                         v                                v
       +---------------------------------+  +-------------------------------+
       |    Multimodal Vision Engine     |  |   Safety Interceptor Gate     |
       |  (Gemini 2.5/3.1 Flash Lite)    |  |  (119 SPGDT & BKO BPOM Gate)  |
       +-----------------+---------------+  +---------------+---------------+
                         |                                  |
                         v                                  v
       +---------------------------------+  +-------------------------------+
       |   Extracted Ingredient Strings  |  |    Intent Classifier (LLM)    |
       +-----------------+---------------+  +---------------+---------------+
                         |                                  |
                         +----------------+-----------------+
                                          |
                                          v
                    +------------------------------------------+
                    |  Deterministic Rule-Based Matching Gate  |
                    |   (Exact -> Regex -> thefuzz Scorer)     |
                    +---------------------+--------------------+
                                          |
                                          v
                    +------------------------------------------+
                    |      MongoDB Knowledge Base (500 TCM)    |
                    |    is_toxic ? "toxic" : "safe" : "none"  |
                    +---------------------+--------------------+
                                          |
                                          v
                    +------------------------------------------+
                    |  LLM Reply Synthesis (Language Only)     |
                    |    Verdict constant passed as argument   |
                    +---------------------+--------------------+
                                          |
                                          v
                    +------------------------------------------+
                    | WhatsApp Message / Web Safety Warning    |
                    +------------------------------------------+
```

### 3.2 Knowledge Base Construction and Schema

The TCM knowledge base was curated through a multi-stage pharmaceutical pipeline:
- **Source Ingestion:** Regulatory alerts from BPOM Public Warning archives (2020-2025) and pharmacological constituents from SymMap.
- **Harmonization:** Standardizing entries across Indonesian common names, Chinese Hanzi, Pinyin, English nomenclature, and Latin binomial taxonomy.
- **Seeding:** Structured importing into MongoDB Atlas via `seed_500_tcm.py`.

The database contains exactly 500 distinct botanical and compound records conforming to the production schema below:

```json
{
  "mandarin_name": "罗汉果",
  "pinyin_name": "Luó Hàn Guǒ",
  "indonesian_name": "Lo Han Guo / Buah Biksu",
  "english_name": "Monk Fruit",
  "latin_name": "Siraitia grosvenorii",
  "is_toxic": false,
  "toxicity_level": "none",
  "toxicity_class": "safe",
  "target_organ": "Paru-paru, Usus Besar",
  "description": "Suplemen herbal pereda batuk dan radang tenggorokan",
  "source_reference": "BPOM & SymMap Curated Dataset",
  "validated_by": "Pharmacy Faculty Review Panel"
}
```

### 3.3 Multimodal Vision and Backend Non-Herbal Verification

Label image analysis is executed by Gemini Flash models via the OpenRouter API. The prompt directs the model to extract all visible herbal ingredients, prioritize formal composition blocks (*成分*, *配方*), and return a pure JSON string array.

A key challenge in consumer applications is preventing snack packages (e.g., rice crackers, wheat biscuits, culinary seasonings) from being misidentified as certified traditional medicine. In FitMate, non-herbal verification is executed deterministically at the backend logic layer (`services/safety.py`). When the extracted text array yields zero matches against the 500-substance botanical database (`(total_toxic + total_safe) == 0`), the system automatically tags the product with `classification = "non_herbal"`. The frontend displays a dedicated non-herbal notice, preventing false health claims.

### 3.4 Dual Interaction Modes: Standalone and Cross-Device Bridge Mode

To prevent user friction across diverse desktop and mobile devices, FitMate introduces two operational workflows:
1. **Standalone Workflow:** Full camera streaming and file upload functionality available natively on any mobile or desktop browser. The camera viewfinder automatically adapts: 3:4 portrait on mobile devices for one-handed ergonomics, and 16:9 widescreen landscape on desktop viewports (`md:` breakpoint and above) with lateral controls.
2. **Bridge Mode Workflow:** Designed for desktop users wishing to scan physical packaging with their smartphone without losing desktop screen context. The desktop browser requests a unique session from `/api/bridge/create-session`, which generates a UUID token stored in MongoDB with a 30-minute time-to-live (TTL) index. The desktop presents a dynamic QR code. Scanning the QR code launches the mobile web scanner; upon capture and analysis on the phone, results are written to the database session and reflected on the desktop interface in real time via polling.

### 3.5 Dual Fuzzy Matching Pipelines and Decision Logic

Because queries originating from web image OCR differ in structure from informal WhatsApp chat messages, FitMate maintains two tailored matching pipelines:

1. **Web Scanner Pipeline (`services/safety.py`):**
   - Exact string match against indexed lowercased names (Score = 100).
   - Word boundary regex validation (`\b` patterns) ensuring full-term containment (Score = 95).
   - Fuzzy ratio matching using `fuzz.token_sort_ratio` restricted to terms with length <= 35 characters. Acceptance threshold is set strictly to **score >= 88**.
2. **WhatsApp Bot Pipeline (`routers/whatsapp.py`):**
   - User inputs are matched against candidate names using `fuzz.token_set_ratio`.
   - Acceptance threshold is calibrated to **score >= 68** to tolerate user typos, informal abbreviations, and colloquial spelling variations.
   - Any query falling below 68 is marked as `not_found`, prompting an explicit acknowledgment of data absence rather than assuming product safety.

```python
def _build_safety_verdict(best_match: dict | None, highest_score: int) -> str:
    """
    Deterministic rule-based safety verdict.
    LLMs are never permitted to generate or override this verdict.
    """
    if not best_match or highest_score < 68:
        return "not_found"
    if best_match.get("is_toxic", False):
        return "toxic"
    return "safe"
```

### 3.6 WhatsApp Bot Architecture and Pre-LLM Safety Interceptors

The WhatsApp chatbot incorporates a multi-layer defense mechanism before any prompt touches the conversational language model:

1. **Emergency Interceptor:** Synchronously inspects incoming text using regular expression matching across 17+ acute medical emergency patterns (e.g., chest pain, respiratory distress, hematemesis, unconsciousness, anaphylaxis). Detection triggers an immediate static response directing the user to the National Emergency Ambulance hotline (119 SPGDT).
2. **BKO BPOM Interceptor:** Scans messages against an alias map containing 58 prohibited synthetic drugs across 205 aliases (e.g., Sildenafil, Dexamethasone, Sibutramine, Phenylbutazone). If an adulterant is detected in a traditional medicine context, the system blocks the query and issues an alert with BPOM reporting hotlines (1500-533).
3. **Intent Classification:** Unflagged messages are categorized into `ingredient_safety_inquiry`, `ingredient_info_inquiry`, or `general_tcm_chat`.
4. **Clean Formatting Standard:** All casual emojis have been systematically removed and replaced with clinical tags (`[Aman]`, `[Berisiko]`, `[Peringatan]`), maintaining a Modern Apothecary communication standard.

---

## 4. Implementation Details

### 4.1 System Technology Stack

| Layer | Technology | Operational Function |
|---|---|---|
| Frontend Web Client | Next.js 14, Tailwind CSS, PWA | Responsive web app with camera access, deployed on Vercel |
| Backend API Engine | Python 3.11, FastAPI, Uvicorn | Asynchronous processing, rate limiting, and business logic |
| Database Tier | MongoDB Atlas | 500-ingredient collection and TTL-indexed bridge sessions |
| Multimodal OCR | Gemini Flash series via OpenRouter | High-accuracy pharmaceutical Chinese text extraction |
| Conversational NLU | Gemini Flash series via OpenRouter | Intent classification and multi-turn empathetic language generation |
| String Matching | thefuzz (token_set / token_sort) | Typo-tolerant lexical normalization and matching |
| Messaging Gateway | Twilio WhatsApp API | Webhook ingestion and bidirectional messaging |
| Container Hosting | Hugging Face Spaces (Docker) | Production API hosting with automated CI/CD deployment |

### 4.2 Security and Rate Limiting Policies

- **Webhook Signature Authentication:** All incoming Twilio requests are validated using HMAC-SHA1 signatures against the `X-Twilio-Signature` header. Unverified calls are rejected.
- **Rate Limiting:** Web OCR endpoints enforce a maximum of 5 requests per minute per IP address. WhatsApp message processing enforces a cap of 20 messages per 10 minutes per phone number using in-memory `TTLCache`.
- **Session Privacy:** Temporary cross-device bridge records expire automatically after 1800 seconds via MongoDB native TTL indexes.

---

## 5. Testing, Evaluation, and Benchmark Results

### 5.1 Knowledge Base and Adulterant Distribution

The curated database was systematically audited for coverage across major pharmacological categories. Table 1 summarizes the distribution of the 500 TCM knowledge base entries, and Table 2 summarizes the 58 synthetic adulterants (BKO) tracked by the safety interceptor.

**Table 1.** Distribution of the 500 TCM Knowledge Base entries by toxicity class.

| Classification | Count | Percentage | Primary Botanical Categories Included |
|---|---|---|---|
| Safe / General Tonic | 326 | 65.2% | Panax ginseng, Siraitia grosvenorii, Glycyrrhiza, Astragalus, Lycium barbarum |
| Toxic / High Risk | 174 | 34.8% | Aristolochia, Aconitum alkaloids, Ephedra sinica, Strychnos nux-vomica |
| **Total** | **500** | **100.0%** | Comprehensive Indonesian retail TCM market coverage |

**Table 2.** Prohibited synthetic adulterant (BKO) database categories compiled from BPOM registries.

| Category ID | Pharmacological Class | Substance Count | Alias Count | Representative Compounds |
|---|---|---|---|---|
| CAT-01 | Corticosteroids | 6 | 28 | Dexamethasone, Prednisone, Betamethasone |
| CAT-02 | Illicit Sexual Enhancers | 8 | 42 | Sildenafil, Tadalafil, Vardenafil |
| CAT-03 | Hazardous Anorectics | 5 | 24 | Sibutramine, Fenfluramine |
| CAT-04 | Prescription NSAIDs / Analgesics | 12 | 48 | Phenylbutazone, Paracetamol, Mefenamic Acid |
| CAT-05 | Hidden Antidiabetics | 7 | 22 | Glibenclamide, Metformin |
| CAT-06 | Sedatives & Psychotropics | 11 | 25 | Diazepam, Alprazolam, Phenobarbital |
| CAT-07 | Anabolic Steroids & Diuretics | 9 | 16 | Methandienone, Furosemide, Spironolactone |
| **Total** | **7 Categories** | **58 Substances** | **205 Aliases** | **Full BPOM Public Warning Coverage** |

### 5.2 Multi-LLM Empirical Benchmark Evaluation

To evaluate conversational suitability and latency, a benchmark suite of 25 standardized clinical prompts was executed across 7 leading multimodal and language models (totaling 175 execution test runs). Prompts spanned 8 functional categories:
1. Greetings and onboarding
2. Direct ingredient inquiries
3. Safety, dosage, and contraindications (Critical Category)
4. Adulteration and toxic ingredients (Critical Category)
5. Pregnancy and lactation warnings (Critical Category)
6. Drug-herb interaction warnings (Critical Category)
7. Off-topic containment
8. Medical emergency triage (Critical Category)

Execution latency was logged per query. Responses were audited to ensure zero contradiction of database safety verdicts. Table 3 presents the empirical benchmark results.

**Table 3.** Multi-LLM benchmark evaluation across 25 standardized test prompts (N = 175 trials).

| Model Identifier | Provider | Mean Latency (s) | Min Latency (s) | Max Latency (s) | Operational Verdict |
|---|---|---|---|---|---|
| `openai/gpt-5.4-nano` | OpenAI | **4.41** | 1.82 | 8.94 | Optimal for low-latency chat |
| `google/gemini-3.1-flash-lite-preview` | Google | **6.38** | 2.15 | 12.40 | Best balance: TCM accuracy & speed |
| `xiaomi/mimo-v2-flash` | Xiaomi | 14.00 | 4.36 | 29.22 | Moderate latency |
| `deepseek/deepseek-v3.2` | DeepSeek | 14.58 | 4.88 | 32.10 | Moderate latency |
| `minimax/minimax-m2.7` | MiniMax | 21.23 | 6.12 | 45.30 | High latency for conversational UI |
| `z-ai/glm-4.7-flash` | Zhipu AI | 34.66 | 8.90 | 68.20 | Unacceptable chat delay |
| `qwen/qwen3.5-flash-02-23` | Alibaba | 36.79 | 9.40 | 72.15 | Unacceptable chat delay |

The empirical results identify `google/gemini-3.1-flash-lite-preview` and `openai/gpt-5.4-nano` as the primary candidates for production deployment. Gemini was selected as the default production model due to superior comprehension of pharmaceutical Chinese taxonomy and consistent adherence to Indonesian clinical tone requirements.

### 5.3 Safety Interceptor and Penetration Rigor

Black-box verification of the safety interceptors demonstrated 100% adherence:
- **Emergency queries:** 100% of tested acute phrases triggered immediate ambulance referral (119 SPGDT) without invoking the LLM.
- **BKO adulterant queries:** 100% of queries containing prohibited drug aliases triggered immediate warning notices with BPOM reporting hotlines (1500-533).
- **Rule-based verdict compliance:** Across all 175 benchmark trials, zero instances were recorded where an LLM altered or contradicted a database toxicity verdict.

---

## 6. Discussion and Practical Implications

FitMate establishes that decoupling deterministic regulatory checks from generative language models solves the core medical dilemma of clinical AI: providing warm, accessible conversational guidance while eliminating the risk of catastrophic hallucination. 

The adaptive layout solves the usability bottleneck common in earlier digital health prototypes, where desktop users were constrained by vertical viewfinders or forced to switch devices. By supporting both Standalone Mode (with automatic 16:9 widescreen adaptation) and Bridge Mode (with 30-minute UUID pairing), the system seamlessly integrates into real-world consumer shopping workflows.

Furthermore, moving from informal emojis to structured textual tags (`[Aman]`, `[Berisiko]`, `[Peringatan]`) aligns the system with clinical communication standards, ensuring that users treat safety determinations with appropriate gravity.

---

## 7. Future Work

Future development trajectories include:
1. **Multilingual Vector Embeddings:** Transitioning from lexical matching to dense vector embeddings using `paraphrase-multilingual-MiniLM-L12-v2` to support semantic symptom queries (e.g., matching "herbal for kidney weakness" to specific pharmacological entries).
2. **Persistent Consented Health Profiles:** Allowing opt-in users to store ongoing conditions (e.g., hypertension, pregnancy, diabetes) linked securely to their WhatsApp ID to receive proactive contraindication warnings.
3. **Formal Clinical Advisory Board:** Expanding the current student-curated 500-substance database through continuous peer review by licensed Indonesian clinical pharmacists.

---

## 8. Conclusion

FitMate provides an accessible, reliable, and linguistically adapted safety screening platform for Traditional Chinese Medicine in Indonesia. By combining multimodal vision with a curated 500-substance database and enforcing a strict hybrid separation between rule-based verification and LLM language synthesis, the system achieves a verifiable zero-hallucination safety standard across both web and WhatsApp channels.

---

## Acknowledgments

The authors express their gratitude to the faculty pharmacist advisors at Universitas Ma Chung for their pharmacological guidance and review of the TCM safety knowledge base. This project was conducted under the PKM-KC (Program Kreativitas Mahasiswa: Karsa Cipta) initiative supported by the Ministry of Education, Culture, Research, and Technology of the Republic of Indonesia.

---

## References

Badan Pengawas Obat dan Makanan. (2021). *Public Warning Obat Tradisional, Suplemen Kesehatan, dan Kosmetika Mengandung Bahan Kimia Obat/Bahan Dilarang Tahun 2021*. Jakarta: BPOM RI.

Badan Pengawas Obat dan Makanan. (2025). *Indonesia dan Tiongkok Perkuat Sinergi Budaya dan Ilmu Pengetahuan dalam Pengembangan Obat Tradisional*. Jakarta: BPOM RI.

Badan Pengawas Obat dan Makanan. (2026). *Hasil Patroli Siber Marketplace 2025: Temuan Produk Obat Tradisional Tidak Sesuai Ketentuan*. Jakarta: BPOM RI.

Esti, N., Rahmawati, D., & Prasetyo, A. (2025). Perilaku unsupervised self-medication pada kelompok usia produktif di Indonesia. *Jurnal Kesehatan Masyarakat Nasional*, 20(2), 101-109.

Fadhilah, R., Maulani, M. R., Resdiana, W., & Hamidin, D. (2024). Integrasi fitur Chatbot dalam aplikasi edukasi kesehatan dan kebugaran menggunakan algoritma neural network. *Jurnal Kecerdasan Buatan dan Teknologi Informasi*, 3(3), 125-135.

Ghaznawi, U. U., Akhtar, L., Rehmat, A., Younas, I., & Ullah, S. (2025). Assessment of multivitamin usage and factors affecting lifestyle. *BMC Nutrition*, 11, 27.

Kurniasih, H., Winarso, P., & Sartika, L. (2024). Pengembangan aplikasi bot WhatsApp pengingat minum obat untuk meningkatkan kepatuhan minum obat pada ibu hamil dengan hipertensi. *Seminar Nasional Keperawatan*, 22, 162-166.

Nurhalisa, F., et al. (2024). Traditional Chinese Medicine sebagai warisan budaya dan praktik kesehatan etnis Tionghoa di Indonesia. *Jurnal Sejarah dan Kebudayaan*, 12(1).

Pantan, F. (2023). Pemanfaatan Chatbot berbasis kecerdasan buatan dalam layanan konsultasi digital. *Jurnal Teknologi Informasi*, 8(2).

Rahmasiah, R., Roni, R., Hadi, S., & Termia, M. (2023). Gambaran pengetahuan masyarakat tentang peredaran sediaan farmasi obat tradisional non BPOM di Kelurahan Rijang Pittu Kabupaten Sidrap. *Marendeng Journal*, 7(2), 49-57.

Wahab, B., Apriana, A., & Silitonga, D. (2025). Perancangan sistem konsultasi kesehatan online berbasis website guna meningkatkan efisiensi dan efektivitas pelayanan kesehatan pada UPTD Puskesmas Tiga Balata tahun 2025. *Jurnal Penelitian Kesmasy*, 7(2).

World Health Organization. (2019). *WHO Global Report on Traditional and Complementary Medicine 2019*. Geneva: WHO.
