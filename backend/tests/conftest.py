"""
conftest.py — Shared pytest fixtures for FitMate backend tests.

Provides: client (TestClient), valid_token (JWT), auth_headers (Bearer header dict)
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """FastAPI TestClient for the main app."""
    import sys
    import os
    # Ensure backend/ is on sys.path for relative imports
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    from main import app
    return TestClient(app)


@pytest.fixture
def valid_token():
    """Generate a valid admin JWT for testing protected routes."""
    from utils.auth import create_access_token
    return create_access_token(subject="admin")


@pytest.fixture
def auth_headers(valid_token):
    """HTTP Authorization header dict with valid Bearer token."""
    return {"Authorization": f"Bearer {valid_token}"}
