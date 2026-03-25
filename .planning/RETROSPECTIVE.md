# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — PIMNAS Prototype

**Shipped:** 2026-03-26
**Phases:** 6 | **Plans:** 14 | **Sessions:** 6+

### What Was Built
- Initialized Next.js 16 app with Tailwind v4 Modern Apothecary design tokens, web fonts, and basic PWA manifest.
- Implemented native HTML5 camera viewfinder, image picker fallback, and premium scanning loader.
- Wired frontend to backend FastAPI pipeline, creating the final medical results display logic using Modern Apothecary tokens.
- Full TCM knowledge base built using fuzzy search matching, seeded from 50 validated records scraped from BPOM.
- Hybrid WhatsApp chatbot handling intent via Gemini Flash but locking output securely behind rule-based guidelines.

### What Worked
- Clear boundary constraints between "Natural Conversation" (LLM) and "Medical Output" (MongoDB). Refusing to let the LLM guess herbs meant zero occurrence of hallucinations during testing.
- Relying on `wa.me` stateless URL generation offloaded massive session management from the backend, keeping the architecture exceptionally lean.

### What Was Inefficient
- Storing JWT in `localStorage` in Phase 5 caused known security tradeoffs. Moving it to `httpOnly` cookies should have ideally been prioritized but was skipped in favor of PIMNAS deadline pacing.
- Having the server inadvertently offline while building frontend features occasionally skewed `fetch` logic testing. 

### Patterns Established
- Using natural keywords in Chinese to align with `thefuzz` library was significantly more robust against OCR typos than exact string matching.

### Key Lessons
1. Hardware constraints always dictate software approaches. Running the Next.js and FastAPI servers simultaneously during development is strictly necessary for any Integration UX audits.
2. Building an "Apothecary" aesthetic drastically elevated a standard data-processing pipeline into a believable, competitive PIMNAS healthcare product.

### Cost Observations
- Model mix: 100% Gemini (Flash/Pro)
- Sessions: ~6
- Notable: Very high token usage across context switches during the UI alignment stage (reading the HTML blocks across `stitch_pkm_ki_fitme_v1/`).

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.0 | 6 | 6 | Established foundational Get-Shit-Done loop (Plan -> Audit -> Execute). |

### Cumulative Quality

| Milestone | Tests | Coverage | Zero-Dep Additions |
|-----------|-------|----------|-------------------|
| v1.0 | 15 | ~85% | 8 |

### Top Lessons (Verified Across Milestones)

1. Keep stateless designs where possible to lower backend overhead.
2. Clean separation of pure layout UI (Phase 3) vs Integration wiring (Phase 6) prevents component pollution.
