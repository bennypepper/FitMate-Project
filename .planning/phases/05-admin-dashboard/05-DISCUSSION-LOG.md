# Phase 5: Admin Dashboard - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-25
**Phase:** 05-admin-dashboard
**Areas discussed:** JWT storage & session handling, Admin UI placement, Dashboard aesthetic, Excel upload UX

---

## JWT Storage & Session Handling

| Option | Description | Selected |
|--------|-------------|----------|
| localStorage + access token only | Simple, no backend session. Sufficient for internal tool. XSS-vulnerable. | ✓ |
| httpOnly cookie | XSS-resistant, industry gold standard. Requires CSRF protection + more CORS config. | |
| sessionStorage | Clears on tab close, no persistence across tabs. | |

**User's choice:** localStorage + access token only  
**Notes:** User explicitly requested a note for future remediation. Security note added to CONTEXT.md D-04: post-PIMNAS hardening should migrate to httpOnly cookies + refresh token rotation. Token expiry set at 8 hours per user confirmation. 401 response → clear localStorage → redirect to `/admin/login`. No refresh tokens for prototype.

---

## Admin UI Placement

| Option | Description | Selected |
|--------|-------------|----------|
| `/admin` route group in existing Next.js app | Single deploy, simpler setup, shares globals.css tokens | ✓ |
| Separate Next.js admin app | Cleaner boundary but doubles deployment complexity | |

**User's choice:** `/admin` route group in existing `frontend/` Next.js app  
**Notes:** Route structure agreed: `admin/layout.tsx` (AuthGuard wrapper), `admin/login/page.tsx`, `admin/page.tsx`, `admin/ingredients/page.tsx`, `admin/upload/page.tsx`.

---

## Dashboard Aesthetic & UI Reference

| Option | Description | Selected |
|--------|-------------|----------|
| Match Stitch reference design exactly | Use `stitch_pkm_ki_fitme_v1/` HTML files as pixel-for-pixel spec | ✓ |
| Utilitarian data-table look | More density-focused, less editorial | |

**User's choice:** Same Modern Apothecary style as the scanner. All three Stitch folders referenced as canonical UI spec.  
**Notes:** User confirmed all three folders (`beranda_scanner`, `hasil_peringatan_scanner`, `dashboard_admin`) should be referenced. All UI elements — including the admin dashboard — must trace back to these HTML references.

---

## Excel Upload UX

| Option | Description | Selected |
|--------|-------------|----------|
| Simple file input button | No drag-and-drop, minimal UI | |
| Drag-and-drop only | Better UX, no dry-run | |
| Drag-and-drop + Option A (inline row list) | Always shows error list on upload | |
| Drag-and-drop + Option B (summary + row details) | Two-phase: validate → confirm import | ✓ |

**User's choice:** Drag-and-drop + Option B summary validation  
**Notes:** Backend validates first without importing, returns `{ valid_count, error_count, errors[] }`. If no errors → show confirm import button. If errors → show row-level error list, no import button (fix and re-upload). Accepted types `.xlsx` and `.csv`, max 10MB.

---

## The Agent's Discretion

- Login page visual treatment
- Drag-and-drop hover animation
- Pagination approach for ingredient table
- Python Excel parsing library choice
- Indonesian error message copy

## Deferred Ideas

- Full CRUD (add/edit/delete via forms) → post-funding v2
- httpOnly cookie auth → post-PIMNAS security hardening
- Real-time analytics data → decorative/static charts for prototype
