# Requirements: FitMate

**Defined:** 2026-03-25
**Core Value:** Users can scan any TCM label and instantly know if it contains ingredients that are toxic or contraindicated for their specific health conditions — with zero AI hallucination in medical recommendations.

## v1 Requirements

Requirements for PIMNAS prototype. Each maps to roadmap phases.

### Scanner

- [ ] **SCAN-01**: User can access phone camera directly from the PWA
- [ ] **SCAN-02**: User can capture TCM label image or upload from gallery
- [ ] **SCAN-03**: System displays real-time processing loader with visual bounding boxes for detected Hanzi text
- [ ] **SCAN-04**: System extracts and translates Mandarin characters to Indonesian via Google Cloud Vision API

### Safety

- [ ] **SAFE-01**: System cross-references translated ingredients against the MongoDB toxicity knowledge base
- [ ] **SAFE-02**: System displays Imperial Red warning when toxic/dangerous ingredients are detected
- [ ] **SAFE-03**: System shows contraindication details (target organ, risk level) for flagged ingredients
- [ ] **SAFE-04**: System displays medical disclaimer recommending professional consultation on every result

### WhatsApp Integration

- [ ] **WHAP-01**: Frontend generates stateless wa.me deep link with pre-filled ingredient context
- [ ] **WHAP-02**: WhatsApp chatbot replies with rule-based medical advice for known ingredients
- [ ] **WHAP-03**: Chatbot uses LLM for natural conversation understanding but strictly defers to rules for medical recommendations
- [ ] **WHAP-04**: Chatbot responds "I don't know" for ingredients not in the database (no guessing)

### Data Pipeline

- [x] **DATA-01**: Python scraping scripts fetch raw TCM data from TCMID/SymMap/BPOM
- [x] **DATA-02**: Scraped data exported to Excel for pharmacist review
- [ ] **DATA-03**: Admin can upload validated Excel/CSV files to update MongoDB knowledge base
- [x] **DATA-04**: Curated baseline dataset of 50-100 most common TCM products loaded

### Admin Dashboard

- [ ] **ADMN-01**: Admin dashboard with convincing UI for knowledge base overview
- [ ] **ADMN-02**: Admin can view ingredient list and toxicity status

### Authentication

- [ ] **AUTH-01**: Admin can log in with JWT-based secure authentication
- [ ] **AUTH-02**: Role-based middleware protects admin routes from unauthorized access

### PWA & UI

- [ ] **PWA-01**: App configured as Progressive Web App for native-like mobile experience
- [ ] **PWA-02**: UI follows 60-25-10-5 color ratio with Imperial Red (#930014) for warnings
- [ ] **PWA-03**: Typography uses Playfair Display/Merriweather for headings, Inter/Poppins for body, Noto Sans SC for Chinese characters

## v2 Requirements

Deferred to post-funding. Tracked but not in current roadmap.

### Admin Dashboard (Extended)

- **ADMN-03**: Admin can add/edit/delete TCM ingredients via dashboard forms
- **ADMN-04**: Admin can manage safety rules (condition logic, warning messages, medical advice)
- **ADMN-05**: Admin can view analytics (scan counts, most detected toxic ingredients)

### Data & Scale

- **DATA-05**: Expanded database to 500-1000+ TCM products
- **DATA-06**: Automated scheduled scraping pipeline (cron-based)

### Localization

- **LOCL-01**: Multi-language support beyond Indonesian

### Logging

- **LOG-01**: Admin can view scan history/logs with filters

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Image processing via WhatsApp Bot | Meta API timeout risk; bot is strictly text-based |
| User accounts/registration | Stateless access lowers barrier to entry for general public |
| Mobile native app (iOS/Android) | PWA-first approach; no app store needed |
| AI-generated medical advice | Zero hallucination mandate — rule-based only for medical info |
| Real-time collaborative editing | Single admin workflow sufficient for prototype |
| Payment/subscription system | Free public health tool; no monetization in v1 |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| SCAN-01 | Phase 3 | Pending |
| SCAN-02 | Phase 3 | Pending |
| SCAN-03 | Phase 3 | Pending |
| SCAN-04 | Phase 2 | Pending |
| SAFE-01 | Phase 2 | Pending |
| SAFE-02 | Phase 2 | Pending |
| SAFE-03 | Phase 2 | Pending |
| SAFE-04 | Phase 2 | Pending |
| WHAP-01 | Phase 6 | Pending |
| WHAP-02 | Phase 4 | Pending |
| WHAP-03 | Phase 4 | Pending |
| WHAP-04 | Phase 4 | Pending |
| DATA-01 | Phase 1 | Complete |
| DATA-02 | Phase 1 | Complete |
| DATA-03 | Phase 5 | Pending |
| DATA-04 | Phase 1 | Complete |
| ADMN-01 | Phase 5 | Pending |
| ADMN-02 | Phase 5 | Pending |
| AUTH-01 | Phase 5 | Pending |
| AUTH-02 | Phase 5 | Pending |
| PWA-01 | Phase 6 | Pending |
| PWA-02 | Phase 3 | Pending |
| PWA-03 | Phase 3 | Pending |

**Coverage:**
- v1 requirements: 23 total
- Mapped to phases: 23
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-25*
*Last updated: 2026-03-25 after initial definition*
