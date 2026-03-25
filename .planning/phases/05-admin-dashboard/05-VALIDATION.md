---
phase: 5
slug: admin-dashboard
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-25
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (backend) — Wave 0 installs if not present |
| **Config file** | `backend/pytest.ini` or inline `pyproject.toml` — Wave 0 creates |
| **Quick run command** | `cd backend && pytest tests/test_admin.py -v` |
| **Full suite command** | `cd backend && pytest tests/ -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && pytest tests/test_admin.py -v`
- **After every plan wave:** Run `cd backend && pytest tests/ -v`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | Status |
|---------|------|------|-------------|-----------|-------------------|--------|
| 05-01-01 | 01 | 1 | AUTH-01 | unit | `pytest tests/test_admin.py::test_login_returns_token -v` | ⬜ pending |
| 05-01-02 | 01 | 1 | AUTH-01 | unit | `pytest tests/test_admin.py::test_login_wrong_password_returns_401 -v` | ⬜ pending |
| 05-01-03 | 01 | 1 | AUTH-02 | unit | `pytest tests/test_admin.py::test_protected_route_without_token_returns_401 -v` | ⬜ pending |
| 05-01-04 | 01 | 1 | AUTH-02 | unit | `pytest tests/test_admin.py::test_protected_route_with_expired_token_returns_401 -v` | ⬜ pending |
| 05-02-01 | 02 | 2 | ADMN-01 | manual | Navigate to /admin — verify stat cards render | ⬜ pending |
| 05-02-02 | 02 | 2 | ADMN-02 | manual | Navigate to /admin/ingredients — verify ingredient table with toxicity badges | ⬜ pending |
| 05-02-03 | 02 | 2 | AUTH-02 | manual | Open /admin while logged out — verify redirect to /admin/login | ⬜ pending |
| 05-03-01 | 03 | 3 | DATA-03 | unit | `pytest tests/test_admin.py::test_validate_endpoint_valid_file -v` | ⬜ pending |
| 05-03-02 | 03 | 3 | DATA-03 | unit | `pytest tests/test_admin.py::test_validate_endpoint_missing_required_fields -v` | ⬜ pending |
| 05-03-03 | 03 | 3 | DATA-03 | unit | `pytest tests/test_admin.py::test_import_upserts_mongodb -v` | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_admin.py` — stubs for AUTH-01, AUTH-02, DATA-03
- [ ] `backend/tests/conftest.py` — shared fixtures (test client, mock MongoDB, test JWT)
- [ ] `pytest` and `httpx` installed (`pip install pytest httpx pytest-asyncio`)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| AuthGuard redirects unauthenticated user | AUTH-02 | Browser localStorage behavior, not testable via pytest | Open /admin/ingredients, verify redirect to /admin/login |
| Dashboard stat cards show correct counts | ADMN-01 | Requires live MongoDB with seeded data | Seed DB, open /admin, check ingredient count and toxic count match |
| Ingredient table renders with Mandarin avatar + toxicity badges | ADMN-02 | Visual regression — no automated visual test | Open /admin/ingredients, check table rows match stitch_pkm_ki_fitme_v1/dashboard_admin/screen.png |
| Drag-and-drop zone accepts .xlsx file | DATA-03 | Browser file API interaction | Drag test .xlsx onto upload zone, verify validation response appears |
| Confirm Import button disabled when errors exist | DATA-03 | UI state conditional | Upload file with intentional errors, verify confirm button is absent/disabled |

---

## Validation Sign-Off

- [ ] All tasks have automated verify or Manual entry
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
