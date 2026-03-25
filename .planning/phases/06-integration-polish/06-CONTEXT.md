# Phase 6: Integration & Polish - Context

**Gathered:** 2026-03-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Wire the complete end-to-end user journey: WhatsApp deep link CTA from scan results to the chatbot, PWA installability (manifest icons + service worker registration), an inline "no internet" error state replacing the current `alert()`, and a final mobile responsiveness pass across all screens.

**Not in scope:** New features, CRUD, advanced analytics, real offline caching.
</domain>

<decisions>
## Implementation Decisions

### WhatsApp Deep Link CTA
- **D-01:** Show the "Tanya di WhatsApp" CTA button **only when toxic or contraindicated ingredients are detected** in scan results. Clean results (safe/unknown only) get no CTA.
- **D-02:** CTA button placement: inside `ToxicityWarning.tsx`, appended **below the ingredient warning list** within the Imperial Red card. It should feel like a natural escalation action after seeing the danger.
- **D-03:** WhatsApp phone number: `6285161618852` (Indonesian mobile, no `+`). Deep link format: `https://wa.me/6285161618852?text=<encoded_message>`
- **D-04:** Pre-filled message template (URL-encoded):
  ```
  Halo FitMate! Saya baru scan produk TCM dan ditemukan bahan berbahaya: [nama bahan 1], [nama bahan 2]. Bisa bantu jelaskan risikonya?
  ```
  Ingredient names are dynamically injected from the `toxicItems` array (use `indonesian_name` if available, fallback to `mandarin_name`). List is comma-separated.
- **D-05:** CTA button styling: full-width, white background with Imperial Red text and WhatsApp icon, `rounded-xl`, shadow to lift it above the dark card. Opens in new tab (`target="_blank", rel="noopener noreferrer"`).

### PWA Installability
- **D-06:** App icon source: `C:\Users\Benny Pepper\OneDrive - Ma Chung University\College Docs\PKM\assets\logo2.png` (Imperial Red gradient rounded-square with leaf/scanner mark). Already copied to `frontend/public/icon.png`.
- **D-07:** Generate PNG icons at **192×192** and **512×512** from `icon.png` (use `sharp` npm package or Next.js Image optimization in a build script). Output to `frontend/public/icons/icon-192.png` and `frontend/public/icons/icon-512.png`.
- **D-08:** Update `manifest.json` to include:
  - `icons` array with both 192 and 512 entries (type: `image/png`, purpose: `any maskable`)
  - `scope: "/"`
  - `description: "Scanner keamanan TCM berbasis AI untuk konsumen Indonesia"`
  - `orientation: "portrait"`
  - Keep existing `theme_color: "#69000B"` and `background_color: "#FFF8F7"`
- **D-09:** Splash screen is **automatically generated** by the browser from `background_color` + `theme_color` + 512px icon — no extra code needed. Manifest update in D-08 is sufficient.
- **D-10:** Register a **minimal service worker** (`frontend/public/sw.js`) for the installability badge. It does NO caching. Registration happens in `layout.tsx` via an inline effect script.

### Offline / Network Error Handling
- **D-11:** Remove the current `alert()` in `page.tsx` `handleImageReady` catch block.
- **D-12:** Replace with an **inline error state** rendered in the results area: show a styled card with an offline icon, message *"Tidak ada koneksi internet atau server tidak dapat dijangkau. Pastikan Anda terhubung ke internet untuk menggunakan fitur scanning."*, and a "Coba Lagi" button that resets to the scanner.
- **D-13:** Detect offline specifically via `navigator.onLine` in the catch block. If `navigator.onLine === false`, show the offline-specific message. If `navigator.onLine === true` but fetch still fails, show a generic server error: *"Server tidak dapat dijangkau. Coba lagi dalam beberapa saat."*

### Mobile Responsiveness
- **D-14:** Run a responsive audit pass on all public-facing screens (scanner homepage, results card, ToxicityWarning card with new CTA button) at 375px (iPhone SE) and 393px (Pixel 7) viewport widths using Chrome DevTools.
- **D-15:** Admin dashboard mobile (bottom nav from Stitch reference Phase 5 D-09) — verify it functions correctly; no new mobile admin design is needed beyond what Phase 5 implemented.
- **D-16:** The WhatsApp CTA button must be large enough for thumb tap (min 48px height, full width).

### Demo Preparation
- **D-17:** End-to-end demo scenario must work without errors: land on scanner → capture/upload image → see results → tap WhatsApp CTA (if toxic) → WhatsApp opens with pre-filled message.
- **D-18:** API base URL in `page.tsx` is currently hardcoded to `http://localhost:8000`. For the demo, leave it configurable via `NEXT_PUBLIC_API_URL` env variable with `http://localhost:8000` as fallback, so it can be pointed at production without a rebuild.

### the Agent's Discretion
- Icon resize implementation approach (sharp script, canvas, or Next.js API route)
- WhatsApp icon SVG to use in the CTA button (WhatsApp official brand green icon or simple chat bubble)
- Exact animation for the offline error card fade-in
- Whether to show a snackbar-style toast or inline card for network errors

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Frontend Code to Modify
- `frontend/src/components/results/ToxicityWarning.tsx` — Add WhatsApp CTA button here (D-02)
- `frontend/src/app/page.tsx` — Replace alert() with inline error state (D-11), add env-based API URL (D-18)
- `frontend/public/manifest.json` — Update with full icon entries and metadata (D-08)
- `frontend/src/app/layout.tsx` — Register service worker here (D-10)
- `frontend/public/icon.png` — Source icon (already copied, 1080×1080px)

### Design System
- `stitch_pkm_ki_fitme_v1/modern_apothecary/DESIGN.md` — Color tokens, typography, surface hierarchy
- `frontend/src/app/globals.css` — Tailwind token definitions (use these, never hardcode hex)

### Prior Decisions
- `.planning/phases/03-frontend-scanner/03-CONTEXT.md` — Design system decisions (D-01 to D-04)
- `.planning/phases/05-admin-dashboard/05-CONTEXT.md` — Admin UI decisions including D-09 mobile bottom nav

### Project Constraints
- `.planning/REQUIREMENTS.md` — WHAP-01 (wa.me deep link) and PWA-01 (installable PWA) are the requirement IDs this phase must satisfy
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ToxicityWarning.tsx` — Already has `toxicItems` array filtered from `ingredients`. The WhatsApp CTA only needs the `toxicItems` names — no new data needed.
- `ResultsCard.tsx` — Orchestrates ToxicityWarning + IngredientList. The `onReset` button pattern (full-width, `rounded-md`, `active:scale-95`) is the visual reference for the CTA button style.
- `manifest.json` — Already has correct `theme_color` and `background_color`. Needs icon entries added.
- `layout.tsx` — Has `manifest: "/manifest.json"` in metadata. Service worker registration goes here.

### Established Patterns
- Frontend: next.js App Router, Tailwind CSS v4, `use client` for interactive components
- Error handling currently: `try/catch` with `alert()` — replace with `setError(...)` state + conditional render
- API calls: direct `fetch()` in `page.tsx` — keep but make URL configurable via `NEXT_PUBLIC_API_URL`

### Integration Points
- `ToxicityWarning.tsx` receives `ingredients: any[]` from `ResultsCard.tsx` → WA deep link can be built inline from the already-filtered `toxicItems`
- `page.tsx` `handleImageReady` is the single catch point for all API failures — D-11/D-13 fix happens here

</code_context>

<specifics>
## Specific Ideas

- WhatsApp number: `6285161618852` — hardcode with a `// TODO: update for production` comment
- Icon path: `public/icon.png` (1080×1080 Imperial Red gradient rounded-square with leaf/scanner mark + golden bracket corners) — resize to 192 and 512 for manifest
- The CTA button should visually escape the Imperial Red card slightly — white background with green WhatsApp color on the icon signals "safe action" contrast against the danger card
- Pre-filled WA message: `Halo FitMate! Saya baru scan produk TCM dan ditemukan bahan berbahaya: {names}. Bisa bantu jelaskan risikonya?`
</specifics>

<deferred>
## Deferred Ideas

- Real offline caching / shell cache — explicitly decided against. Service worker is registration-only for installability.
- PWA screenshots in manifest (for richer install dialog) — nice-to-have, skip for prototype
- Push notifications — out of scope for v1
</deferred>

---

*Phase: 06-integration-polish*
*Context gathered: 2026-03-26*
