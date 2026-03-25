# Phase 04: WhatsApp Chatbot - Context

**Gathered:** 2026-03-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the hybrid WhatsApp chatbot — LLM for natural conversation parsing, strict rules for medical recommendations via FastAPI webhook and Meta API configuration.
</domain>

<decisions>
## Implementation Decisions

### LLM Engine
- **D-01:** Use Gemini Flash via API for the intent parsing LLM engine to align with the student budget constraint while remaining highly performant.

### Session Memory 
- **D-02:** The bot will be strictly single-turn and stateless (ping-pong). No conversational memory (e.g., Redis context) will be implemented.

### Unknown Handling UX
- **D-03:** When an ingredient is not found in the database, the bot must reply with a simple, polite "I don't know / Not in database" message. It will not actively suggest or support user-submitted ingredient images.

### API Rate Limiting
- **D-04:** Implement strict rate limiting on EVERY API route in the project. For the WhatsApp webhook, rate limiting must be enforced per WhatsApp number to comprehensively protect the LLM API and the backend from abuse/spam.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Core Requirements
- `.planning/PROJECT.md` — Project context and core constraints
- `.planning/REQUIREMENTS.md` — Requirement IDs and specs
- `.planning/ROADMAP.md` — Phase definition and dependencies
</canonical_refs>

<deferred>
## Deferred Ideas
None — discussion stayed within phase scope.
</deferred>
