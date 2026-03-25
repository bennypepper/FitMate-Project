---
status: Ready for planning
phase: 03-frontend-scanner
started: 2026-03-25T20:25:00Z
updated: 2026-03-25T20:25:00Z
---

# Phase 03: Frontend Scanner - Context

**Gathered:** 2026-03-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the React PWA frontend with HTML5 camera access, custom label capture UX, loader state, and results display following the Modern Apothecary Editorial design guidelines.
</domain>

<decisions>
## Implementation Decisions

### Camera & Capture UX
- **D-01:** Implement a custom in-app viewfinder camera using HTML5 APIs rather than triggering the native device camera. This allows for immersive PWA experience and potential overlay guides.

### Processing State
- **D-02:** Use a generalized loading animation instead of attempting to draw boundary box overlays onto the captured photo via canvas.

### Results Layout
- **D-03:** Display the extraction and safety results using a card carousel grouped by severity, ensuring critical (Imperial Red) warnings are highlighted prominently.

### Design System Mapping
- **D-04:** Dark mode is explicitly not required for the prototype. Implementation must strictly follow the "Modern Apothecary" guidelines.

### the agent's Discretion
- Approach to requesting camera permissions gracefully (managing denied states).
- Specific animation sequence for the generic loading state.
- Fallback UI if the user's device lacks a back-facing camera.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Design System
- `../../stitch_pkm_ki_fitme_v1/modern_apothecary/DESIGN.md` — Detailed Modern Apothecary brand guidelines, color tokens, and surface philosophy.

</canonical_refs>
