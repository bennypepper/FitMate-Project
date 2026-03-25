# Phase 02: Backend Core - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-25
**Phase:** 02-backend-core
**Areas discussed:** API Image Upload Format, OCR Bounding Boxes, Toxicity Matching Logic, Warning Response Structure

---

## API Image Upload Format

| Option | Description | Selected |
|--------|-------------|----------|
| Multipart Form-Data | Raw file upload, binary transfer | ✓ |
| Base64 JSON | Encode image to string inside JSON | |

**User's choice:** Requested recommendation.
**Notes:** The agent recommended `multipart/form-data` to avoid Base64 size overhead; user tacitly accepted via requesting the recommendation.

---

## OCR Bounding Boxes

| Option | Description | Selected |
|--------|-------------|----------|
| Words/Lines | Group characters into lines with boxes | ✓ |
| Individual Chars | Box for every single character | |

**User's choice:** group into words/lines
**Notes:** Provides a cleaner payload for frontend UI.

---

## Toxicity Matching Logic

| Option | Description | Selected |
|--------|-------------|----------|
| Fuzzy Matching | Handle slight text variations | ✓ |
| Exact Matching | Strict character checking | |

**User's choice:** fuzzy matching handle ocr imperfections
**Notes:** Imperative for accuracy given the nature of cloud vision on sometimes blurry medical labels.

---

## Warning Response Structure

| Option | Description | Selected |
|--------|-------------|----------|
| Group by Severity | Group ingredients under warning categories | ✓ |
| Flat List | Array of ingredients with flag booleans | |

**User's choice:** group by severity level is good
**Notes:** Makes it easier for the frontend to parse and render warnings immediately.
