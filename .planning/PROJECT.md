# FitMate

## What This Is

FitMate is a TCM (Traditional Chinese Medicine) Safety Scanner and Consultant built as a Progressive Web App with a WhatsApp chatbot companion. It lets Indonesian consumers scan TCM product labels using their phone camera, instantly translates the Mandarin ingredient text, and cross-references ingredients against a validated toxicity database to flag dangerous compounds and contraindications. When warnings are detected, users are seamlessly bridged to a WhatsApp chatbot for rule-based medical guidance — no account required.

## Core Value

Users can scan any TCM label and instantly know if it contains ingredients that are toxic or contraindicated for their specific health conditions — with zero AI hallucination in medical recommendations.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

- [x] OCR-based TCM label scanning with Mandarin-to-Indonesian translation (Phase 02)
- [x] Rule-based toxicity warning system with contraindication flagging (Phase 02)
- [x] Medical disclaimer system (always recommend professional consultation) (Phase 02)

### Active

<!-- Current scope. Building toward these. -->

- [ ] Stateless WhatsApp deep link generation with pre-filled ingredient context
- [ ] Hybrid WhatsApp chatbot (LLM for natural conversation, strict rules for medical info)
- [ ] Admin dashboard with convincing UI for knowledge base management
- [ ] Data pipeline: scrape TCMID/SymMap/BPOM → Excel → pharmacist validation → MongoDB import
- [ ] Curated baseline dataset of 50-100 most common TCM products in Indonesia
- [ ] PWA configuration for native-like mobile experience
- [ ] JWT-based admin authentication

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- Full admin CRUD dashboard — convincing UI sufficient for prototype; full functionality deferred to post-funding
- Image processing via WhatsApp Bot — avoided to prevent Meta API timeout complexity; bot is text-only
- User accounts/registration — users access scanner statelessly to lower barrier to entry
- Multilingual support beyond Indonesian — targeting Indonesian market for PIMNAS
- Mobile native app — PWA-first approach, no app store deployment needed

## Context

**Competition context:** FitMate is being built as a working prototype for PIMNAS (Program Kreativitas Mahasiswa Nasional), Indonesia's national university innovation competition. The proposal is due April 2-4, 2026 via Simbelmawa. If funded, development continues through further selection rounds.

**Team composition:**
- 3 Pharmacy students (data validation, medical knowledge, toxicity rules)
- 1 Chinese Language Education student (Mandarin translation accuracy)
- 1 Computer Science student (development — the builder)
- Faculty advisor available for advanced medical consultation

**The problem:** Most Indonesian TCM consumers cannot read Mandarin characters on product labels and are unaware of nephrotoxic or cardiotoxic side effects. Self-medication with unknown compounds is a real public health risk.

**The approach:** Combine Google Cloud Vision OCR with a pharmacist-validated rule-based database. The bot uses LLM for natural conversation understanding but strictly defers to rules for any medical recommendation. If an ingredient isn't in the database, the system says "I don't know" rather than guessing.

**UI guidelines:** Existing design concept and brand guidelines folder available. 60-25-10-5 color ratio rule with Imperial Red (#930014) for critical warnings. Typography: Playfair Display for headings, Inter/Poppins for body, Noto Sans SC for Chinese characters.

**Data strategy:** Start with manually curated 50-100 most common TCM products in Indonesia. Pharmacy team validates each entry for toxicity flags and contraindications. Expandable via scraping pipeline targeting TCMID, SymMap, and BPOM databases.

## Constraints

- **Timeline**: Proposal submission April 2-4, 2026 — working prototype needed by then
- **Team size**: Solo developer (CS student) — all code built by one person
- **Medical accuracy**: Zero hallucination mandate — rule-based only for medical info, medical disclaimer required
- **Budget**: University student budget — leveraging free tiers where possible
- **Tech stack (decided)**: React/Next.js + Tailwind CSS (PWA), Python/FastAPI, MongoDB + PostgreSQL, Google Cloud Vision API, WhatsApp Cloud API
- **Deployment**: Vercel (frontend), AWS EC2 or VPS Hostinger (backend)

## Key Decisions

<!-- Decisions that constrain future work. Add throughout project lifecycle. -->

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Hybrid LLM + Rules for WhatsApp bot | LLM handles natural conversation/intent; rules handle medical recommendations — balances usability with zero-hallucination safety | — Pending |
| Stateless wa.me deep links (no session management) | Eliminates server-side session overhead; Frontend generates WhatsApp URLs directly with ingredient context | — Pending |
| MongoDB for knowledge base, PostgreSQL for admin/logs | MongoDB's flexible schema suits evolving TCM data structure; PostgreSQL for structured admin data | — Pending |
| 50-100 TCM products for prototype baseline | Sufficient for PIMNAS demo; quality over quantity; pharmacy team can validate thoroughly | — Pending |
| Medical disclaimer on all outputs | Team are students, not licensed practitioners; always recommend professional consultation | — Pending |
| Push to GitHub for backups | Remote: https://github.com/bennypepper/FitMate-PKM-KI | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-25 after Phase 02 backend-core*
