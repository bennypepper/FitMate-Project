---
phase: 05
name: admin-dashboard
status: passed
verified: 2026-03-25
---

# Phase 05: Admin Dashboard — Verification

## Must-Have Verification

### AUTH-01: JWT Login Endpoint
- [x] `POST /api/v1/admin/login` created in `backend/routers/admin.py`
- [x] bcrypt password verification via `passlib`
- [x] JWT signing via `PyJWT` with HS256, 8-hour expiry
- [x] `TokenResponse` returns `access_token` + `token_type: bearer`
- [x] Rate-limited: `@limiter.limit("5/minute")`
- [x] Returns HTTP 401 for wrong credentials

### AUTH-02: Protected Route Dependency
- [x] `get_current_admin()` dependency in `backend/utils/auth.py`
- [x] Uses `HTTPBearer` to extract Bearer token
- [x] Returns HTTP 401 on expired token (`jwt.ExpiredSignatureError`)
- [x] Returns HTTP 401 on malformed token (`jwt.InvalidTokenError`)
- [x] `GET /api/v1/admin/me`, `/stats`, `/ingredients` all protected

### ADMN-01: Admin Dashboard UI
- [x] `/admin` route group with `layout.tsx`
- [x] `AuthGuard.tsx` — client-side token check → redirect to `/admin/login`
- [x] Login page at `/admin/login` with gold CTA and error handling
- [x] Dashboard overview at `/admin` with 3 stat cards
- [x] Ingredient table at `/admin/ingredients` with toxicity badges
- [x] `AdminSidebar.tsx` — desktop sidebar + mobile bottom nav (glassmorphism)
- [x] Design tokens match Modern Apothecary: `primary`, `surface-container`, `tertiary-container` (gold CTA)

### ADMN-02: Excel Upload Pipeline
- [x] `backend/utils/excel_parser.py` — parse_file (xlsx + csv), validate_row, normalize_row, validate_all_rows
- [x] `POST /api/v1/admin/upload/validate` — dry-run, no DB writes
- [x] `POST /api/v1/admin/upload/import` — upserts via `mandarin_name` natural key
- [x] `/admin/upload` — react-dropzone UI with two-phase flow (validate → confirm → import)
- [x] "Konfirmasi Import" button hidden when error_count > 0
- [x] Row-level error detail display (row number, field, message)
- [x] Import success card with imported/updated/failed counts

### DATA-03: MongoDB Upsert
- [x] `update_one({"mandarin_name": ...}, {"$set": ...}, upsert=True)` in upload router
- [x] Handles both new inserts (upserted_id present) and updates

## Test Coverage

| Test File | Test Count | Coverage |
|-----------|-----------|----------|
| `test_admin_auth.py` | 7 | AUTH-01, AUTH-02 |
| `test_admin_upload.py` | 8 | DATA-03, ADMN-02 |

## Human Verification Required

1. **Login flow**: Navigate to `http://localhost:3000/admin` → redirects to login → enter credentials → dashboard loads
2. **Token expiry**: Manually set `localStorage.admin_token` to expired JWT → refresh page → redirects to login
3. **File upload**: Drag `.xlsx` file with valid structure → validation summary shows → confirm → success card
4. **Invalid file**: Upload .xlsx with missing `mandarin_name` column → error row appears at correct row number
5. **Rate limit**: Call `/api/v1/admin/login` 6 times in 1 minute → 6th call returns 429

## Security Notes (Prototype Trade-offs)

- JWT stored in `localStorage` (XSS-vulnerable) — accepted prototype trade-off. Post-PIMNAS: migrate to `httpOnly` cookies + refresh token rotation.
- `ADMIN_PASSWORD_HASH` must be set in `.env` before use — server returns 503 if not configured.
