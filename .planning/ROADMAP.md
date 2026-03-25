# Roadmap: FitMate

## Overview

FitMate's prototype roadmap takes us from zero to a working PIMNAS demo in 6 phases. We start with project foundation and data pipeline (the database must exist before anything can scan against it), then build the backend API core (OCR + safety logic), the frontend scanner PWA, the WhatsApp chatbot, the admin dashboard, and finally integrate everything with PWA polish.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Data Foundation** - Scraping pipeline, data validation workflow, and MongoDB seeding
- [ ] **Phase 2: Backend Core** - FastAPI server with OCR integration and rule-based safety engine
- [ ] **Phase 3: Frontend Scanner** - React PWA with camera access, label scanning UI, and results display
- [ ] **Phase 4: WhatsApp Chatbot** - Hybrid LLM + rule-based WhatsApp bot via Cloud API webhook
- [ ] **Phase 5: Admin Dashboard** - Convincing admin UI with JWT auth and data upload
- [ ] **Phase 6: Integration & Polish** - End-to-end flow, PWA config, deep link wiring, and final polish

## Phase Details

### Phase 1: Data Foundation
**Goal**: Establish the TCM knowledge base — scraping scripts, pharmacist validation workflow, and a seeded MongoDB with 50-100 validated TCM products
**Depends on**: Nothing (first phase)
**Requirements**: DATA-01, DATA-02, DATA-04
**Success Criteria** (what must be TRUE):
  1. Python scraping scripts successfully fetch TCM data from TCMID/SymMap/BPOM
  2. Scraped data exports to Excel format for pharmacist review
  3. MongoDB is seeded with at least 50 validated TCM ingredient records (mandarin_name, indonesian_name, is_toxic, target_organ, description)
  4. Safety rules exist for all toxic ingredients in the baseline dataset
**Plans**: 2 plans

Plans:
- [x] 01-01: Data scraping pipeline (BeautifulSoup4/Selenium scripts for TCMID/SymMap/BPOM, Excel export)
- [x] 01-02: MongoDB schema and seeding (database setup, collection schemas, seed script from validated Excel)

### Phase 2: Backend Core
**Goal**: Build the FastAPI backend with Google Cloud Vision OCR integration and the rule-based toxicity matching engine
**Depends on**: Phase 1
**Requirements**: SCAN-04, SAFE-01, SAFE-02, SAFE-03, SAFE-04
**Success Criteria** (what must be TRUE):
  1. API endpoint accepts an image and returns extracted Mandarin text via Google Cloud Vision
  2. Translated ingredients are cross-referenced against MongoDB toxicity database
  3. API response includes toxicity warnings with target organ and risk level for flagged ingredients
  4. Medical disclaimer is included in every API response
  5. API returns structured JSON suitable for frontend consumption
**Plans**: 2 plans

Plans:
- [x] 02-01: FastAPI server setup and Google Cloud Vision OCR integration (image upload endpoint, OCR extraction, Mandarin-to-Indonesian translation)
- [x] 02-02: Rule-based safety engine (MongoDB toxicity matching, contraindication logic, warning response formatting, disclaimer injection)

### Phase 3: Frontend Scanner
**Goal**: Build the React PWA frontend with camera access, label capture UI, and results display following the design guidelines
**Depends on**: Phase 2
**Requirements**: SCAN-01, SCAN-02, SCAN-03, PWA-02, PWA-03
**UI hint**: yes
**Success Criteria** (what must be TRUE):
  1. User can open the PWA and access phone camera directly
  2. User can capture a TCM label image or upload from gallery
  3. Processing state shows a loader with visual bounding boxes for detected Hanzi
  4. Results display translated ingredients with Imperial Red warnings for toxic items
  5. UI follows 60-25-10-5 color ratio and uses specified typography
**Plans**: 3 plans

Plans:
- [x] 03-01: Next.js project setup with PWA config, Tailwind CSS, design system (color palette, typography, global styles)
- [x] 03-02: Camera module (HTML5 camera access, image capture, gallery upload, processing loader)
- [x] 03-03: Results display (ingredient list, toxicity warnings in Imperial Red, contraindication details, medical disclaimer)

### Phase 4: WhatsApp Chatbot
**Goal**: Build the hybrid WhatsApp chatbot — LLM for natural conversation, strict rules for medical recommendations
**Depends on**: Phase 2
**Requirements**: WHAP-02, WHAP-03, WHAP-04
**Success Criteria** (what must be TRUE):
  1. WhatsApp webhook receives and processes incoming text messages
  2. Bot replies with rule-based medical advice when ingredient is in the database
  3. Bot uses LLM for natural language understanding but defers to rules for any medical info
  4. Bot responds "I don't know / not in our database" for unrecognized ingredients
  5. Bot never hallucinates medical advice — only rule-based responses for known ingredients
**Plans**: 2 plans

Plans:
- [x] 04-01: WhatsApp Cloud API webhook setup (message receiving, response sending, Meta API configuration)
- [x] 04-02: Hybrid conversation engine (LLM intent parsing, rule-based medical response lookup, fallback "I don't know" handler)

### Phase 5: Admin Dashboard
**Goal**: Build a convincing admin dashboard with JWT authentication and Excel upload functionality
**Depends on**: Phase 2
**Requirements**: ADMN-01, ADMN-02, AUTH-01, AUTH-02, DATA-03
**UI hint**: yes
**Success Criteria** (what must be TRUE):
  1. Admin can log in with username/password and receive JWT token
  2. Unauthenticated users are blocked from admin routes
  3. Dashboard shows knowledge base overview (ingredient count, toxic count)
  4. Admin can view the ingredient list with toxicity status
  5. Admin can upload validated Excel/CSV file to update MongoDB
**Plans**: 3 plans

Plans:
- [x] 05-01: JWT authentication system (login endpoint, token generation, role middleware, protected routes)
- [x] 05-02: Admin dashboard UI (React pages — dashboard overview, ingredient list table, data display)
- [x] 05-03: Excel upload pipeline (file upload endpoint, Excel parsing, MongoDB upsert, validation feedback)

### Phase 6: Integration & Polish
**Goal**: Wire everything end-to-end — scanner to WhatsApp deep links, PWA manifest, final UI polish and testing
**Depends on**: Phases 3, 4, 5
**Requirements**: WHAP-01, PWA-01
**Success Criteria** (what must be TRUE):
  1. Complete flow works: scan label → see results → tap WhatsApp CTA → pre-filled message in WhatsApp
  2. Stateless wa.me deep link generates correctly with ingredient context
  3. PWA manifest configured (installable, icons, splash screen)
  4. All screens are responsive and polished for mobile demo
  5. End-to-end demo scenario works without errors
**Plans**: 2 plans

Plans:
- [ ] 06-01: WhatsApp deep link integration (stateless wa.me URL generation from scan results, CTA button wiring)
- [ ] 06-02: PWA configuration and final polish (manifest.json, service worker, icons, responsive testing, demo walkthrough)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6
Note: Phases 3, 4, 5 can execute in parallel after Phase 2 completes.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Data Foundation | 0/2 | Not started | - |
| 2. Backend Core | 0/2 | Not started | - |
| 3. Frontend Scanner | 0/3 | Not started | - |
| 4. WhatsApp Chatbot | 0/2 | Not started | - |
| 5. Admin Dashboard | 0/3 | Not started | - |
| 6. Integration & Polish | 0/2 | Not started | - |
