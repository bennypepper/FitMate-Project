"""
test_admin_auth.py — Tests for JWT admin authentication (Plan 05-01).

Requirements covered: AUTH-01, AUTH-02
"""

import pytest
from unittest.mock import patch
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
TEST_PASSWORD = "testpassword123"
TEST_HASH = pwd_context.hash(TEST_PASSWORD)


def test_login_returns_token(client):
    """AUTH-01: Valid credentials return a JWT access token."""
    with patch("core.config.settings.ADMIN_USERNAME", "testadmin"), \
         patch("core.config.settings.ADMIN_PASSWORD_HASH", TEST_HASH):
        response = client.post(
            "/api/v1/admin/login",
            json={"username": "testadmin", "password": TEST_PASSWORD},
        )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 10


def test_login_wrong_password_returns_401(client):
    """AUTH-01: Wrong password returns HTTP 401."""
    with patch("core.config.settings.ADMIN_USERNAME", "testadmin"), \
         patch("core.config.settings.ADMIN_PASSWORD_HASH", TEST_HASH):
        response = client.post(
            "/api/v1/admin/login",
            json={"username": "testadmin", "password": "wrongpassword"},
        )
    assert response.status_code == 401


def test_login_wrong_username_returns_401(client):
    """AUTH-01: Wrong username returns HTTP 401."""
    with patch("core.config.settings.ADMIN_USERNAME", "testadmin"), \
         patch("core.config.settings.ADMIN_PASSWORD_HASH", TEST_HASH):
        response = client.post(
            "/api/v1/admin/login",
            json={"username": "hacker", "password": TEST_PASSWORD},
        )
    assert response.status_code == 401


def test_protected_route_without_token_returns_403(client):
    """AUTH-02: No Authorization header → HTTP 403 (FastAPI HTTPBearer default)."""
    response = client.get("/api/v1/admin/me")
    # HTTPBearer returns 403 when Authorization header is absent
    assert response.status_code in (401, 403)


def test_protected_route_with_valid_token(client, auth_headers):
    """AUTH-02: Valid Bearer token → protected route returns 200."""
    response = client.get("/api/v1/admin/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["username"] == "admin"


def test_protected_route_with_invalid_token(client):
    """AUTH-02: Malformed/tampered token → HTTP 401."""
    response = client.get(
        "/api/v1/admin/me",
        headers={"Authorization": "Bearer notavalidtoken"},
    )
    assert response.status_code == 401


def test_expired_token_returns_401(client):
    """AUTH-01: Token past its exp claim → HTTP 401."""
    import jwt
    from datetime import datetime, timezone, timedelta
    from core.config import settings

    expired_payload = {
        "sub": "admin",
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),  # already expired
    }
    expired_token = jwt.encode(
        expired_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )

    response = client.get(
        "/api/v1/admin/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
