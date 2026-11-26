"""
admin.py — Admin authentication and protected admin routes.

Endpoints:
  POST /api/v1/admin/login       — Public: authenticate and receive JWT
  GET  /api/v1/admin/me          — Protected: verify token, return admin info
  GET  /api/v1/admin/stats       — Protected: dashboard overview stats
  GET  /api/v1/admin/ingredients — Protected: paginated ingredient list
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status, Request
from pydantic import BaseModel

from core.config import settings
from core.limiter import limiter
from database.mongo import get_db
from datetime import datetime, timezone
from utils.auth import verify_password, get_password_hash, create_access_token, get_current_admin

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

# Precomputed dummy bcrypt hash to equalize timing on unknown usernames
_DUMMY_BCRYPT_HASH = get_password_hash("dummy-timing-equalization-password")

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class StatsResponse(BaseModel):
    total_ingredients: int
    toxic_count: int
    safe_count: int

@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request, credentials: LoginRequest, db = Depends(get_db)):
    """
    Admin login. Rate limited to 5 attempts per minute.
    Returns JWT on success, 401 on invalid credentials.
    Checks admin_users collection with fallback to .env configuration.
    """
    # 1. Check database for admin user first
    user_doc = await db.admin_users.find_one({"username": credentials.username})
    expected_hash = None

    if user_doc:
        expected_hash = user_doc.get("hashed_password")
    elif credentials.username == settings.ADMIN_USERNAME:
        expected_hash = settings.ADMIN_PASSWORD_HASH

    if not expected_hash:
        # Equalize response timing and status code to prevent username enumeration
        verify_password(credentials.password, _DUMMY_BCRYPT_HASH)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username atau password salah",
        )

    if not verify_password(credentials.password, expected_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username atau password salah",
        )

    token = create_access_token(subject=credentials.username)
    return TokenResponse(access_token=token)

@router.post("/change-password")
@limiter.limit("5/minute")
async def change_password(
    request: Request,
    req: ChangePasswordRequest,
    admin: str = Depends(get_current_admin),
    db = Depends(get_db),
):
    """
    Change password for authenticated admin.
    Requires current password verification and at least 8 characters for new password.
    """
    if len(req.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password baru minimal 8 karakter",
        )

    user_doc = await db.admin_users.find_one({"username": admin})
    current_hash = user_doc.get("hashed_password") if user_doc else settings.ADMIN_PASSWORD_HASH

    if not current_hash or not verify_password(req.old_password, current_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password saat ini tidak sesuai",
        )

    new_hash = get_password_hash(req.new_password)
    settings.ADMIN_PASSWORD_HASH = new_hash

    await db.admin_users.update_one(
        {"username": admin},
        {
            "$set": {
                "username": admin,
                "hashed_password": new_hash,
                "updated_at": datetime.now(timezone.utc),
            }
        },
        upsert=True,
    )

    return {"status": "success", "message": "Password berhasil diperbarui dengan enkripsi bcrypt"}

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
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    q: str = "",
    db = Depends(get_db),
):
    """
    Paginated ingredient list for the admin table.
    Supports catalog-wide search across all ingredients via 'q'.
    """
    from database.ingredient_repository import ingredient_repository
    ingredients, total, pages = await ingredient_repository.admin_list(
        db=db,
        page=page,
        limit=limit,
        search_query=q,
    )

    return {
        "ingredients": ingredients,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
    }
