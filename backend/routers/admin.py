"""
admin.py — Admin authentication and protected admin routes.

Endpoints:
  POST /api/v1/admin/login       — Public: authenticate and receive JWT
  GET  /api/v1/admin/me          — Protected: verify token, return admin info
  GET  /api/v1/admin/stats       — Protected: dashboard overview stats
  GET  /api/v1/admin/ingredients — Protected: paginated ingredient list
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from pydantic import BaseModel

from core.config import settings
from database.mongo import get_db
from utils.auth import verify_password, create_access_token, get_current_admin

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

# Use app.state.limiter (configured in main.py) to avoid circular import
limiter = Limiter(key_func=get_remote_address)


# --- Request/Response Models ---

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class StatsResponse(BaseModel):
    total_ingredients: int
    toxic_count: int
    safe_count: int


# --- Public Endpoints ---

@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request, credentials: LoginRequest):
    """
    Admin login. Rate limited to 5 attempts per minute.
    Returns JWT on success, 401 on invalid credentials.
    """
    # Validate username
    if credentials.username != settings.ADMIN_USERNAME:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username atau password salah",
        )

    # Guard: if ADMIN_PASSWORD_HASH not configured in .env, refuse login
    if not settings.ADMIN_PASSWORD_HASH:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin auth not configured. Set ADMIN_PASSWORD_HASH in .env",
        )

    if not verify_password(credentials.password, settings.ADMIN_PASSWORD_HASH):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username atau password salah",
        )

    token = create_access_token(subject=credentials.username)
    return TokenResponse(access_token=token)


# --- Protected Endpoints ---

@router.get("/me")
async def get_me(admin: str = Depends(get_current_admin)):
    """Verify token is valid. Returns admin username."""
    return {"username": admin, "role": "admin"}


@router.get("/stats", response_model=StatsResponse)
async def get_stats(admin: str = Depends(get_current_admin)):
    """Dashboard overview: ingredient and toxicity counts from MongoDB."""
    db = get_db()
    total = await db.tcm_ingredients.count_documents({})
    toxic = await db.tcm_ingredients.count_documents({"is_toxic": True})
    return StatsResponse(
        total_ingredients=total,
        toxic_count=toxic,
        safe_count=total - toxic,
    )


@router.get("/ingredients")
async def list_ingredients(
    admin: str = Depends(get_current_admin),
    page: int = 1,
    limit: int = 20,
):
    """
    Paginated ingredient list for the admin table.
    Sorted by mandarin_name ascending.
    """
    db = get_db()
    skip = (page - 1) * limit
    total = await db.tcm_ingredients.count_documents({})

    cursor = db.tcm_ingredients.find(
        {},
        {
            "mandarin_name": 1,
            "indonesian_name": 1,
            "latin_name": 1,
            "english_name": 1,
            "is_toxic": 1,
            "toxicity_level": 1,
            "_id": 1,
        },
    ).skip(skip).limit(limit).sort("mandarin_name", 1)

    ingredients = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])  # serialize ObjectId to string
        ingredients.append(doc)

    return {
        "ingredients": ingredients,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": max(1, (total + limit - 1) // limit),
    }
