---
plan: 05-03
status: complete
completed: 2026-03-25
commits:
  - 3164583 — feat(05-03-01,02): add excel parser utility and upload router (validate+import)
  - fd6f144 — feat(05-01-06,03-03): add test infrastructure (upload tests)
  - 77c7479 — feat(05-02,03): admin dashboard UI + upload page
---

# Plan 05-03: Excel Upload Pipeline — Summary

## What was built

Two-phase Excel/CSV upload pipeline:

**Backend:**
- **`backend/utils/excel_parser.py`**: `parse_file()` (xlsx via openpyxl, csv via built-in csv with BOM handling), `validate_row()` (mandarin_name, indonesian_name, is_toxic, source_reference), `normalize_row()` (type coercion), `validate_all_rows()` (returns valid rows + error summaries)
- **`backend/routers/upload.py`**: `POST /api/v1/admin/upload/validate` (dry-run, returns summary+errors without DB writes), `POST /api/v1/admin/upload/import` (upserts valid rows to MongoDB `tcm_ingredients` using mandarin_name as natural key). Both require JWT auth, enforce 10MB limit.
- **`backend/tests/test_admin_upload.py`**: Unit tests for parser + integration tests for both endpoints

**Frontend:**
- **`/admin/upload/page.tsx`**: react-dropzone drag-and-drop (.xlsx/.csv), validates on drop → shows summary → "Konfirmasi Import" button only when error_count === 0 → import → success card with counts

## Key files created/modified

- `backend/utils/excel_parser.py` — Parser + validator + normalizer
- `backend/routers/upload.py` — Validate + import endpoints
- `backend/tests/test_admin_upload.py` — 8 test cases (unit + integration)
- `frontend/src/app/admin/upload/page.tsx` — Upload UI
- `frontend/package.json` — Added react-dropzone

## Deviations from plan

- File is uploaded twice (once for /validate, once for /import) — this was the accepted decision from Phase 5 discussion (stateless, no temp file storage needed for prototype)
- `numpy` / `pandas` NOT used — openpyxl + csv module only (smaller footprint per plan decision)

## Verification status

- [x] `backend/utils/excel_parser.py` — parse_file, validate_row, normalize_row, validate_all_rows
- [x] `backend/routers/upload.py` — /validate + /import endpoints with JWT auth + 10MB limit
- [x] `backend/tests/test_admin_upload.py` — 8 test cases
- [x] `frontend/.../upload/page.tsx` — drag-and-drop, two-phase flow, confirm button conditional
- [ ] `pytest tests/test_admin_upload.py -v` — requires pip install in venv
- [ ] Manual file upload test required
