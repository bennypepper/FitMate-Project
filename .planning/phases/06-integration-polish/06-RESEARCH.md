# Phase 06: Integration & Polish - Research

**Date:** 2026-03-26

<understanding>
## Phase Goal
Wire the complete end-to-end user journey: WhatsApp deep link CTA from scan results to the chatbot, PWA installability (manifest icons + service worker registration), an inline "no internet" error state replacing the current `alert()`, and a final mobile responsiveness pass across all screens.

## Project Context
FitMate is a progressive web app (Next.js) relying on a FastAPI backend. Time to delivery is short (prototype needed by early April 2026), meaning simple, robust approaches are best. No time for complex architectures (e.g., real offline caching for PWA)—simplification to registration-only service worker is correct.
</understanding>

<investigation>
## Implementation Analysis

### 1. WhatsApp Deep Link Generation (WHAP-01)
- The URL format `https://wa.me/6285161618852?text=<encoded>` is perfectly supported across devices.
- Need to construct the `<encoded>` string natively in JS. Standard Web API `encodeURIComponent` operates correctly.
- Pre-filled text: `Halo FitMate! Saya baru scan produk TCM dan ditemukan bahan berbahaya: [nama bahan 1], [nama bahan 2]. Bisa bantu jelaskan risikonya?`
- In `ToxicityWarning.tsx`, we have an array of `toxicItems`. Creating the comma-separated string `toxicItems.map(item => item.indonesian_name || item.mandarin_name).join(', ')` is trivial.
- The button should logically appear at the bottom of the `ToxicityWarning` component so it is contextually relevant.
- Action should open in a new tab `target="_blank" rel="noopener noreferrer"`.

### 2. PWA Manifest & Installability (PWA-01)
To meet basic PWA install criteria (in Chrome and others):
1. Serve over HTTPS (Vercel provides this) or `localhost`
2. Include a Web App Manifest
    - Must include `name` or `short_name`, `icons` (at least 192px and 512px), `start_url` (`/`), and `display` (`standalone`).
3. Have a registered Service Worker with a `fetch` event handler (even if it does nothing).

#### Service Worker
A minimal valid service worker in `frontend/public/sw.js`:
```javascript
self.addEventListener('fetch', function(event) {
  // Required to pass PWA installability criteria,
  // but we aren't caching anything yet.
});
```
Registration in `layout.tsx`:
```javascript
if (typeof window !== 'undefined' && 'serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js');
}
```

#### Icons
The existing `icon.png` is 1080x1080. It needs resizing. A short canvas-based browser script or an external node script like `sharp` can do this. Actually, the easiest approach for the developer inside the project might just be to drop a `generate-icons.js` using `sharp` (already standard in Next.js for Image optimization) to generate `192` and `512` images at build time, or just manually run it once.
Given `D-07` specifies "generate PNG icons ... from icon.png", creating a tiny node script `frontend/scripts/generate-icons.js` that uses `npm i sharp` saves time.

### 3. Error Handling Redesign
- `try/catch` in `app/page.tsx`'s `handleImageReady` currently uses `alert()`.
- The new design involves setting state: `setError(message)`.
- If `!navigator.onLine`, `message = "Tidak ada ..."` else `message = "Server tidak ..."`
- Needs an ErrorCard component inside the scanner view (or overlaid).

### 4. API URL Configuration
Next.js `NEXT_PUBLIC_API_URL` environment variable support is out-of-the-box. We just need to replace instances of `http://localhost:8000` with `process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'`.

</investigation>

<validation_architecture>
## Validation Architecture

### 1. WhatsApp Button Verification
- Ensure the button only renders when `toxicItems.length > 0`.
- Verify the `href` matches `wa.me` spec with properly encoded text.
- Verify visual styling matches `ToxicityWarning` constraints.

### 2. PWA Verification
- Check if `manifest.json` exists with correct properties.
- Check if icons (192, 512) are generated and referenceable.
- Verify `sw.js` is served at the root and registered in browser.

### 3. Error State Verification
- Turn off network (Chrome DevTools offline mode), trigger scan → see visually correct offline message, not an `alert()`.
- Return a 500 from the local backend, trigger scan → see server error message.

</validation_architecture>

## RESEARCH COMPLETE
