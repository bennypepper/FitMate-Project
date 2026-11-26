"""
test_security_hardening.py — Security & reliability regression tests (TDD).

Covers:
  - P0-1: Twilio webhook fail-closed signature validation & canonical URL
  - P0-2: /whatsapp/test-chat feature flag gating & model allowlist
  - P0-3: Fail-closed JWT_SECRET_KEY in production
  - P0-4: Strict CORS allowlist (no wildcard regex) & /health db status
  - P0-6: Deterministic OCR BKO detection & Indonesian BPOM aliases
  - P1-1: Proxy-safe client IP extraction
  - P1-2: Bridge mode 404/409/403 token & concurrency hardening
  - P1-3/P1-4: Unicode/zero-width normalization & LLM prompt hardening
  - P1-5: Chunked upload size limit (413) & image magic-byte check (400)
  - P1-7 & P2: Excel max-rows, generic upload error messages, pagination bounds
"""

import io
from unittest.mock import AsyncMock, MagicMock, patch

import openpyxl
import pytest
from starlette.requests import Request as StarletteRequest

# Minimal valid 1x1 PNG bytes
VALID_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
    b"\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0\x00\x00\x03\x01\x01\x00\x18\xdd\x8d\xb0"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


# ---------------------------------------------------------------------------
# P0-1: Twilio Webhook Fail-Closed
# ---------------------------------------------------------------------------
def test_twilio_webhook_fails_closed_without_signature(client):
    """P0-1: Missing X-Twilio-Signature must return 403 even if token is unset."""
    with patch("core.config.settings.TWILIO_AUTH_TOKEN", ""):
        res = client.post(
            "/whatsapp/webhook",
            data={"Body": "halo", "From": "whatsapp:+628123456789"},
        )
    assert res.status_code == 403


def test_twilio_webhook_rejects_invalid_signature(client):
    """P0-1: Invalid X-Twilio-Signature must return 403."""
    with patch("core.config.settings.TWILIO_AUTH_TOKEN", "super-secret-token"):
        res = client.post(
            "/whatsapp/webhook",
            headers={
                "X-Twilio-Signature": "invalid-signature",
                "X-Forwarded-Host": "evil.example.com",
            },
            data={"Body": "halo", "From": "whatsapp:+628123456789"},
        )
    assert res.status_code == 403


# ---------------------------------------------------------------------------
# P0-2: Gate /whatsapp/test-chat
# ---------------------------------------------------------------------------
def test_whatsapp_test_chat_disabled_by_default(client):
    """P0-2: /whatsapp/test-chat returns 403 when ENABLE_TEST_ENDPOINTS is False."""
    with patch("core.config.settings.ENABLE_TEST_ENDPOINTS", False):
        res = client.post(
            "/whatsapp/test-chat",
            json={"sender": "tester", "message": "halo"},
        )
    assert res.status_code == 403


def test_whatsapp_test_chat_rejects_disallowed_model(client):
    """P0-2: /whatsapp/test-chat rejects arbitrary expensive models when enabled."""
    with patch("core.config.settings.ENABLE_TEST_ENDPOINTS", True):
        res = client.post(
            "/whatsapp/test-chat",
            json={
                "sender": "tester",
                "message": "halo",
                "model": "anthropic/claude-opus-4-expensive",
            },
        )
    assert res.status_code == 400


# ---------------------------------------------------------------------------
# P0-3: Fail-Closed JWT_SECRET_KEY in Production
# ---------------------------------------------------------------------------
def test_production_weak_jwt_secret_raises_runtime_error():
    """P0-3: APP_ENV=production with default or short JWT secret must raise RuntimeError."""
    from core.config import Settings

    prod_default = Settings(
        APP_ENV="production",
        JWT_SECRET_KEY="change-me-in-production-min-32-chars",
    )
    with pytest.raises(RuntimeError):
        prod_default.validate_security()

    prod_short = Settings(
        APP_ENV="production",
        JWT_SECRET_KEY="short-secret",
    )
    with pytest.raises(RuntimeError):
        prod_short.validate_security()

    prod_strong = Settings(
        APP_ENV="production",
        JWT_SECRET_KEY="a-very-strong-random-production-secret-key-at-least-32-chars",
    )
    prod_strong.validate_security()  # Should not raise


# ---------------------------------------------------------------------------
# P0-4: Strict CORS & /health DB status
# ---------------------------------------------------------------------------
def test_cors_rejects_wildcard_evil_vercel_origin(client):
    """P0-4: CORS must NOT allow arbitrary fitmate-*.vercel.app subdomains."""
    res = client.options(
        "/health",
        headers={
            "Origin": "https://fitmate-evil.vercel.app",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert res.headers.get("access-control-allow-origin") != "https://fitmate-evil.vercel.app"


def test_health_reports_database_mode(client):
    """P0-4: /health returns database mode ('mongodb' or 'fallback')."""
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "healthy"
    assert body["database"] in ("mongodb", "fallback")


# ---------------------------------------------------------------------------
# P0-6: OCR BKO Detection + Indonesian Aliases
# ---------------------------------------------------------------------------
def test_ocr_analyze_detects_bko_dexamethasone_and_fenilbutason(client):
    """P0-6: OCR /analyze flags Dexamethasone and Fenilbutason as high-risk toxic BKO."""
    mock_blocks = [
        {"text": "Dexamethasone 0.5mg", "bounding_box": []},
        {"text": "Fenilbutason", "bounding_box": []},
    ]
    with patch("routers.analyze.extract_and_translate_text", new=AsyncMock(return_value=mock_blocks)):
        res = client.post(
            "/api/v1/analyze/",
            files={"file": ("label.png", VALID_PNG_BYTES, "image/png")},
        )
    assert res.status_code == 200
    analysis = res.json()["safety_analysis"]
    assert analysis["meta"]["classification"] == "toxic"
    assert analysis["meta"]["is_herbal_product"] is True
    assert analysis["meta"]["total_toxic"] >= 2
    toxic_names = {item["indonesian_name"].lower() for item in analysis["toxic"]}
    assert "deksametason" in toxic_names
    assert "fenilbutazon" in toxic_names
    assert all(
        item["source_reference"] == "BPOM-BKO-Dilarang"
        for item in analysis["toxic"]
        if item["indonesian_name"].lower() in ("deksametason", "fenilbutazon")
    )


def test_bko_indonesian_aliases_loaded():
    """P0-6: Indonesian BPOM aliases are matched deterministically."""
    from services.safety_interceptor import check_bko_deterministic

    for alias in ("fenilbutason", "parasetamol", "antalgin", "metampiron", "yohimbin", "alopurinol", "allupurinol"):
        hits = check_bko_deterministic(f"Komposisi jamu mengandung {alias}")
        assert len(hits) >= 1, f"Expected BKO match for alias '{alias}'"


# ---------------------------------------------------------------------------
# P1-1: Proxy-Safe Rate Limiting
# ---------------------------------------------------------------------------
def test_limiter_ignores_spoofed_xff_from_untrusted_client():
    """P1-1: Untrusted direct clients cannot spoof X-Forwarded-For."""
    from core.limiter import get_client_ip

    scope = {
        "type": "http",
        "headers": [(b"x-forwarded-for", b"1.2.3.4"), (b"cf-connecting-ip", b"5.6.7.8")],
        "client": ("198.51.100.99", 12345),
    }
    req = StarletteRequest(scope)
    assert get_client_ip(req) == "198.51.100.99"


def test_limiter_picks_rightmost_untrusted_ip_from_trusted_proxy():
    """P1-1: Trusted proxy extracts rightmost non-trusted IP from X-Forwarded-For."""
    from core.limiter import get_client_ip

    with patch("core.config.settings.TRUSTED_PROXIES", "10.0.0.0/8"):
        scope = {
            "type": "http",
            "headers": [(b"x-forwarded-for", b"9.9.9.9, 203.0.113.50, 10.0.0.2")],
            "client": ("10.0.0.1", 12345),
        }
        req = StarletteRequest(scope)
        assert get_client_ip(req) == "203.0.113.50"


# ---------------------------------------------------------------------------
# P1-2: Bridge Mode Hardening
# ---------------------------------------------------------------------------
def test_bridge_unknown_session_returns_404(client):
    """P1-2: Polling an unknown session must return 404 (no auto-provisioning)."""
    res = client.get("/api/v1/bridge/nonexistent_session_xyz/status")
    assert res.status_code == 404


def test_bridge_custom_id_collision_returns_409(client):
    """P1-2: Creating a session with an existing custom_id returns 409."""
    res1 = client.post("/api/v1/bridge/session?custom_id=collision_test_1")
    assert res1.status_code == 200
    body1 = res1.json()
    assert "upload_token" in body1 and len(body1["upload_token"]) >= 16

    # Status must never expose upload_token
    st = client.get("/api/v1/bridge/collision_test_1/status")
    assert st.status_code == 200
    assert "upload_token" not in st.json()

    res2 = client.post("/api/v1/bridge/session?custom_id=collision_test_1")
    assert res2.status_code == 409


def test_bridge_upload_requires_valid_token(client):
    """P1-2: Uploading to a bridge session without valid X-Bridge-Token returns 403."""
    create_res = client.post("/api/v1/bridge/session")
    assert create_res.status_code == 200
    session_id = create_res.json()["session_id"]

    res_missing = client.post(
        f"/api/v1/bridge/{session_id}/upload",
        files={"file": ("label.png", VALID_PNG_BYTES, "image/png")},
    )
    assert res_missing.status_code == 403

    res_wrong = client.post(
        f"/api/v1/bridge/{session_id}/upload",
        headers={"X-Bridge-Token": "wrong-token"},
        files={"file": ("label.png", VALID_PNG_BYTES, "image/png")},
    )
    assert res_wrong.status_code == 403


# ---------------------------------------------------------------------------
# P1-3 & P1-4: Safety Interceptor Normalization & Deterministic Herbal BKO Block
# ---------------------------------------------------------------------------
def test_safety_interceptor_normalizes_newlines_and_zero_width():
    """P1-3: Emergency and BKO regexes catch newline/zero-width obfuscation."""
    from services.safety_interceptor import check_bko_deterministic, check_emergency

    assert check_emergency("saya mengalami nyeri\n\tdada hebat") is not None
    assert check_emergency("sesak\u200b napas sekarang") is not None
    hits = check_bko_deterministic("deksa\u200bmetason dalam jamu")
    assert len(hits) >= 1


@pytest.mark.anyio
async def test_check_bko_blocks_herbal_context_without_llm_downgrade():
    """P1-3: Herbal/jamu + BKO deterministically blocks without trusting LLM."""
    from services.safety_interceptor import check_bko

    with patch("services.safety_interceptor._bko_context_llm_check", new=AsyncMock(return_value="NO")) as mock_llm:
        res = await check_bko("Jamu pegal linu saya mengandung deksametason, aman?")
    assert res["action"] == "block"
    mock_llm.assert_not_called()


# ---------------------------------------------------------------------------
# P1-5: Chunked Upload Limiter (413) & Image Magic-Byte Check (400)
# ---------------------------------------------------------------------------
def test_analyze_rejects_fake_image_magic_bytes_with_400(client):
    """P1-5: Spoofed Content-Type image/jpeg with non-image bytes must return 400."""
    with patch("routers.analyze.extract_and_translate_text", new=AsyncMock()) as mock_ocr:
        res = client.post(
            "/api/v1/analyze/",
            files={"file": ("fake.jpg", b"<html>not an image</html>", "image/jpeg")},
        )
    assert res.status_code == 400
    mock_ocr.assert_not_called()


def test_ocr_rejects_oversized_upload_with_413(client):
    """P1-5: Upload exceeding 10MB returns 413 immediately via chunked reader."""
    oversized = b"\x89PNG\r\n\x1a\n" + (b"\x00" * (10 * 1024 * 1024 + 1024))
    res = client.post(
        "/api/v1/ocr/upload",
        files={"file": ("huge.png", oversized, "image/png")},
    )
    assert res.status_code == 413


# ---------------------------------------------------------------------------
# P1-7 & P2: Excel MAX_ROWS, Generic Upload Error, Pagination Bounds
# ---------------------------------------------------------------------------
def test_excel_parser_enforces_max_rows():
    """P1-7: Excel/CSV parser rejects files exceeding MAX_ROWS."""
    from utils.excel_parser import MAX_ROWS, parse_file

    csv_lines = ["mandarin_name,indonesian_name,is_toxic,source_reference"]
    csv_lines.extend([f"草{i},Herba {i},false,BPOM-{i}" for i in range(MAX_ROWS + 5)])
    csv_bytes = "\n".join(csv_lines).encode("utf-8")

    with pytest.raises(ValueError):
        parse_file(csv_bytes, "too_many.csv")


def test_upload_import_hides_raw_db_exception(client, auth_headers):
    """P1-7: /import must not leak raw exception strings in failed_rows."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["mandarin_name", "indonesian_name", "is_toxic", "source_reference"])
    ws.append(["人参", "Ginseng", "false", "SymMap-1"])
    buf = io.BytesIO()
    wb.save(buf)

    with patch("routers.upload.get_db") as mock_get_db:
        mock_db = MagicMock()
        mock_db.tcm_ingredients.update_one = AsyncMock(
            side_effect=RuntimeError("mongodb+srv://secret-host:27017 connection error")
        )
        mock_get_db.return_value = mock_db

        res = client.post(
            "/api/v1/admin/upload/import",
            headers={k: v for k, v in auth_headers.items() if k != "Content-Type"},
            files={
                "file": (
                    "test.xlsx",
                    buf.getvalue(),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )
    assert res.status_code == 200
    body = res.json()
    assert body["failed"] == 1
    reason = body["failed_rows"][0]["reason"]
    assert "mongodb+srv" not in reason
    assert "secret-host" not in reason


def test_admin_ingredients_rejects_limit_zero_with_422(client, auth_headers):
    """P2: /api/v1/admin/ingredients?limit=0 must return 422."""
    res = client.get("/api/v1/admin/ingredients?limit=0", headers=auth_headers)
    assert res.status_code == 422


def test_analyze_search_rejects_excessive_limit_with_422(client):
    """P2: /api/v1/analyze/search?limit=500 must return 422."""
    res = client.get("/api/v1/analyze/search?q=ginseng&limit=500")
    assert res.status_code == 422
