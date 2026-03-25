---
phase: 06
slug: integration-polish
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-26
---

# Phase 06 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | manual / next.js dev |
| **Config file** | none |
| **Quick run command** | `npm run dev` |
| **Full suite command** | `npm run build && npm start` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run basic check in `npm run dev`
- **After every plan wave:** Run `npm run build && npm start`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | WHAP-01 | manual | none | ✅ | ⬜ pending |
| 06-02-01 | 02 | 1 | PWA-01 | manual | none | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*Existing infrastructure covers all phase requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| WA Deep Link | WHAP-01 | External intent | Scan unsafe product, click WhatsApp CTA, check if WA opens with correct text |
| PWA Install | PWA-01 | Browser UI | Open app in browser, click Install, check if installed correctly and icon present |
| Offline mode | N/A | Network Level | Disconnect from network or use DevTools offline mode, check error display |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
