# Phase 02: Backend Core - Context

**Gathered:** 2026-03-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the FastAPI backend providing an image upload endpoint that uses Google Cloud Vision API for OCR and text translation, plus matching against MongoDB for toxicity warnings and contraindications.
</domain>

<decisions>
## Implementation Decisions

### API Image Upload Format
- **D-01:** Implement `multipart/form-data` for image uploads. This is the recommended approach as it avoids the ~30% payload size overhead of Base64 encoding and is natively suited for binary file transfers, saving both bandwidth and memory.

### OCR Bounding Boxes
- **D-02:** Group OCR results into words/lines rather than returning bounding boxes for individual characters. This provides a cleaner UI overlay payload for the frontend.

### Toxicity Matching Logic
- **D-03:** Implement fuzzy matching to handle OCR imperfections when checking detected Chinese characters against the MongoDB database.

### Warning Response Structure
- **D-04:** Group detected ingredients by severity level (e.g., toxic, contraindicated, safe, unknown) in the JSON response, rather than providing a flat list.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Core Requirements
- `.planning/PROJECT.md` — Project context and core constraints
- `.planning/REQUIREMENTS.md` — Requirement IDs and specs
- `.planning/ROADMAP.md` — Phase definition and dependencies
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None specifically available yet. The `backend/` directory is primarily empty.

### Established Patterns
- Setup standard Python FastAPI structure with proper modularization (routers, services, models).
</code_context>

<specifics>
## Specific Ideas
- The system must explicitly inject a medical disclaimer advising professional consultation in every result.

</specifics>

<deferred>
## Deferred Ideas
None — discussion stayed within phase scope.
</deferred>

---

*Phase: 02-backend-core*
*Context gathered: 2026-03-25*
