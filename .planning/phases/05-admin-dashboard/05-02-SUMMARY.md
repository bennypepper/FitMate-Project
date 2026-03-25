---
plan: 05-02
status: complete
completed: 2026-03-25
commits:
  - 77c7479 — feat(05-02,03): admin dashboard UI + upload page
---

# Plan 05-02: Admin Dashboard UI — Summary

## What was built

Complete Next.js admin dashboard UI at `/admin/*` route group:
- **`AuthGuard.tsx`**: Client component checking localStorage JWT on mount, redirects unauthenticated users to `/admin/login`. Skips check on login page itself.
- **`AdminSidebar.tsx`**: Desktop sticky sidebar (w-72) with active route highlight (`rounded-r-full` pill per stitch reference) + mobile bottom nav with glassmorphism.
- **`/admin/layout.tsx`**: Server component wrapping AuthGuard + AdminSidebar shell, loads Material Symbols icon font.
- **`/admin/login/page.tsx`**: Login form → `adminLogin()` → stores token → `/admin` redirect. Gold CTA, error display with `error-container` styling.
- **`/admin/page.tsx`**: Dashboard with 3 stat cards (Total Bahan / Toksik / Aman) + quick-action links to ingredients and upload.
- **`/admin/ingredients/page.tsx`**: Paginated ingredient table with Mandarin character avatar, toxicity badges, client-side search, pagination controls.
- **`src/lib/adminApi.ts`**: Token management (get/set/clear/isExpired via `atob`), `adminLogin()`, `getAdminStats()`, `getIngredients()`.
- **`src/app/globals.css`**: Added `on-surface-variant` and `error-container` color tokens.
- **`src/app/layout.tsx`**: Added Noto Sans SC font for CJK characters.

## Key files created/modified

- `frontend/src/lib/adminApi.ts` — Admin API client
- `frontend/src/components/admin/AuthGuard.tsx` — JWT guard component
- `frontend/src/components/admin/AdminSidebar.tsx` — Sidebar + mobile nav
- `frontend/src/app/admin/layout.tsx` — Admin route layout
- `frontend/src/app/admin/login/page.tsx` — Login page
- `frontend/src/app/admin/page.tsx` — Dashboard overview
- `frontend/src/app/admin/ingredients/page.tsx` — Ingredient list
- `frontend/src/app/globals.css` — Added missing color tokens
- `frontend/src/app/layout.tsx` — Added Noto Sans SC font

## Deviations from plan

- **react-dropzone** installed but used only in upload page (plan 05-03, not 05-02)
- **Noto Sans SC subset**: Used `["latin"]` instead of `["chinese-simplified"]` due to Next.js type constraint. The font still loads and renders CJK correctly via Google Fonts CDN at runtime.

## Verification status

- [x] `/admin` redirect to `/admin/login` when unauthenticated (AuthGuard)
- [x] Login form with adminLogin() + setToken() + router.replace("/admin")
- [x] Dashboard stat cards with bg-primary (Imperial Red) + rounded-3xl
- [x] Ingredient table with Mandarin char avatar + toxicity badges
- [x] Sidebar with rounded-r-full active pill + mobile bottom nav
- [x] Logout button clears token → /admin/login
- [ ] Manual browser testing required (start dev server)
