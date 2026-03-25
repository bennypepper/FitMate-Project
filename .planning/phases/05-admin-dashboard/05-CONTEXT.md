# Phase 5: Admin Dashboard - Context

**Gathered:** 2026-03-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Build a JWT-authenticated admin dashboard: FastAPI login endpoint + protected routes, a `/admin` route group in the existing Next.js frontend (login page, dashboard overview, ingredient list table, Excel upload page), and a backend Excel/CSV upload-and-parse pipeline that upserts records into MongoDB. The admin UI matches the Modern Apothecary editorial design system established in Phase 3 — specifically pixel-for-pixel targeting the Stitch reference designs in `stitch_pkm_ki_fitme_v1/`.

Scope is **prototype-grade**: convincing UI and working data flow. Full CRUD (add/edit/delete individual ingredients via form) is explicitly deferred to post-funding (v2).

</domain>

<decisions>
## Implementation Decisions

### JWT Storage & Session Handling
- **D-01:** Store JWT in `localStorage` (not httpOnly cookie) for prototype simplicity.
- **D-02:** Access token expiry: **8 hours** (`exp = now + 8h` set on backend during token generation).
- **D-03:** Token expiry UX — frontend intercepts HTTP 401 responses → clears `localStorage` → redirects to `/admin/login`. No silent refresh, no refresh tokens.
- **D-04:** No server-side session state. The JWT is the entire auth mechanism — stateless.

> ⚠️ **Security Note (Post-Prototype):** `localStorage` is vulnerable to XSS attacks. For production, migrate to `httpOnly` cookies with `SameSite=Strict`, add CSRF protection, and implement token rotation with refresh tokens. This is a known accepted trade-off for the PIMNAS prototype timeline.

### Admin UI Placement
- **D-05:** Admin pages live as a **route group inside the existing `frontend/` Next.js app** at `/admin/*`. No separate admin app.
- **D-06:** Route structure:
  ```
  frontend/src/app/
    admin/
      layout.tsx          ← admin shell (sidebar nav + auth guard)
      login/page.tsx      ← login form (unauthenticated access)
      page.tsx            ← dashboard / overview redirect
      ingredients/page.tsx ← ingredient list table
      upload/page.tsx     ← Excel/CSV upload pipeline
  ```
- **D-07:** `admin/layout.tsx` wraps all `/admin/*` routes with an `AuthGuard` component that reads the JWT from `localStorage` on mount — missing or expired token redirects to `/admin/login`.

### Dashboard Aesthetic & UI Reference
- **D-08:** Admin dashboard UI **must match the Stitch reference designs** in `stitch_pkm_ki_fitme_v1/` — these are the canonical visual spec.
  - `stitch_pkm_ki_fitme_v1/dashboard_admin/code.html` — Admin console layout (sidebar, stat cards, ingredient table, bento insight cards)
  - `stitch_pkm_ki_fitme_v1/beranda_scanner/code.html` — Public scanner homepage
  - `stitch_pkm_ki_fitme_v1/hasil_peringatan_scanner/code.html` — Scan results page
- **D-09:** Key UI elements from the admin reference to replicate in React/Tailwind:
  - Sidebar: sticky, 18rem wide, Merriweather "Admin Console" header, active item as `rounded-r-full` pill in primary color
  - Stat cards: `rounded-3xl`, Imperial Red card for total count, surface-container tinted cards for secondary stats
  - Ingredient table: `divide-y divide-surface-container` row separation (no explicit borders), hover-reveal action buttons (opacity-0 → opacity-100)
  - Bento insights: 2-column grid at bottom of overview page
  - Mobile: bottom nav bar with backdrop blur (replaces sidebar on small screens)
- **D-10:** Design tokens from `globals.css` already align with the Stitch reference — use existing Tailwind theme variables (`bg-primary`, `bg-surface-container`, etc.), do not hardcode hex values.
- **D-11:** Dark mode is **not required** for the prototype (consistent with Phase 3 decision D-04).

### Excel Upload UX
- **D-12:** Upload UI: **drag-and-drop file zone** (with click-to-browse fallback). No simple `<input type="file">` button alone.
- **D-13:** Validation flow: **Option B — summary with row-level detail underneath** (two-phase):
  1. User drops file → backend parses and validates without importing → returns `{ valid_count, error_count, errors: [{ row, field, message }] }`
  2. If `error_count === 0`: show "✓ {N} bahan siap diimpor" + **"Konfirmasi Import"** button
  3. If `error_count > 0`: show summary ("✗ {N} baris bermasalah") + scrollable row-level error list + **no import button** (fix and re-upload)
- **D-14:** Backend uses a single `/api/v1/admin/upload` endpoint: `?action=validate` for dry-run, `?action=import` for confirmed import (or two separate endpoints — planner decides).
- **D-15:** Accepted file types: `.xlsx` and `.csv`. Max file size: 10MB (reasonable for pharmacist-prepared datasets).
- **D-16:** Excel column mapping aligns with `TCMIngredient` schema in `database/schemas.py` — columns: `mandarin_name`, `pinyin_name`, `latin_name`, `indonesian_name`, `english_name`, `is_toxic`, `target_organ`, `toxicity_level`, `description`, `source_reference`.

### the Agent's Discretion
- Login page visual treatment (form card style, whether to include FitMate logo/branding)
- Exact animation for drag-and-drop hover state
- Pagination vs. infinite scroll for the ingredient table (pagination is simpler and matches the reference design)
- Python Excel parsing library choice (`openpyxl` vs `pandas` — whichever is already in `requirements.txt` or cleanest to add)
- Error message copy (Indonesian)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### UI Design Reference (Visual Spec — Highest Priority)
- `stitch_pkm_ki_fitme_v1/dashboard_admin/code.html` — Admin console full HTML reference: sidebar, stat cards, ingredient table, bento insight cards, mobile bottom nav
- `stitch_pkm_ki_fitme_v1/dashboard_admin/screen.png` — Rendered screenshot of admin dashboard
- `stitch_pkm_ki_fitme_v1/beranda_scanner/code.html` — Scanner homepage reference (shared design language)
- `stitch_pkm_ki_fitme_v1/hasil_peringatan_scanner/code.html` — Scan results reference (shared design language)
- `stitch_pkm_ki_fitme_v1/modern_apothecary/DESIGN.md` — Full design system spec: color tokens, typography, no-line rule, surface hierarchy, component guidelines

### Backend Patterns (Follow Existing Architecture)
- `backend/main.py` — FastAPI app entry point; add admin router here following the existing pattern
- `backend/core/config.py` — Settings via pydantic_settings; add `ADMIN_USERNAME`, `ADMIN_PASSWORD_HASH`, `JWT_SECRET_KEY` here
- `backend/database/mongo.py` — MongoDB connection; use `get_db()` for all database access
- `backend/database/schemas.py` — `TCMIngredient` Pydantic schema; Excel upload must map to this exactly
- `backend/routers/analyze.py` — Example of existing router pattern to replicate for admin router

### Frontend Patterns (Follow Existing Architecture)
- `frontend/src/app/layout.tsx` — Root layout; admin layout follows same font/provider pattern
- `frontend/src/app/globals.css` — Tailwind theme tokens (color variables, font variables); use these, don't hardcode hex
- `frontend/src/app/page.tsx` — Example of existing page pattern

### Project Constraints
- `.planning/REQUIREMENTS.md` — ADMN-01, ADMN-02, AUTH-01, AUTH-02, DATA-03 are the requirement IDs this phase must satisfy
- `.planning/PROJECT.md` — Prototype scope constraints; full CRUD is out of scope

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/database/mongo.py` → `get_db()` function: use for all MongoDB access in admin routes
- `backend/database/schemas.py` → `TCMIngredient` Pydantic model: the exact schema for Excel row validation
- `backend/core/config.py` → `Settings` class: extend with JWT/admin credentials, follow same pattern
- `frontend/src/app/globals.css` → All color and font tokens already defined as CSS variables; Tailwind theme is wired up

### Established Patterns
- FastAPI: modular routers in `backend/routers/`, services in `backend/services/`, all registered in `backend/main.py`
- Rate limiting via `slowapi` already configured in `main.py` — apply to login endpoint to prevent brute force
- Frontend: Next.js App Router, Tailwind CSS v4, `use client` directive for interactive components
- No auth library in use yet — implement JWT from scratch using `python-jose` or `PyJWT` on backend

### Integration Points
- New admin router (`backend/routers/admin.py`) registered in `backend/main.py` alongside existing OCR/analyze/whatsapp routers
- Admin frontend pages at `frontend/src/app/admin/*` — completely separate from public scanner at `frontend/src/app/page.tsx`; no shared state needed
- `AuthGuard` in `admin/layout.tsx` is the sole enforcement point for frontend route protection

</code_context>

<specifics>
## Specific Ideas

- The admin Stitch reference (code.html) already uses the exact Tailwind tokens and Merriweather/Inter typography — treat it as the design contract, not just inspiration.
- The stat card showing "TOTAL SCAN" in Imperial Red with a large bold number is the centerpiece of the overview — must be implemented as shown.
- The ingredient table shows Mandarin character avatar (square with first Hanzi character), name + Latin name stacked, English translation column, toxicity status badge (pill-shaped, color-coded), and hover-reveal edit/delete buttons — replicate all of these columns.
- Sidebar "Secure Logout" button at the bottom matches the reference — clicking it clears localStorage and redirects to `/admin/login`.

</specifics>

<deferred>
## Deferred Ideas

- **Full CRUD (add/edit/delete ingredients via forms)** — Explicitly out of scope. `PROJECT.md` lists this as post-funding v2. The ingredient table in this phase shows data + view only; edit/delete buttons in the reference are visual only (not wired up).
- **httpOnly cookie auth** — Deferred. localStorage is used for prototype. Post-PIMNAS security hardening should migrate to httpOnly cookies + refresh token rotation. Noted in D-04 security warning.
- **Real-time analytics / scan volume charts** — The bento chart in the reference is decorative/static for the prototype. No real-time data fetching needed.

</deferred>

---

*Phase: 05-admin-dashboard*
*Context gathered: 2026-03-25*
