"""
auth.py — JWT token creation and password verification utilities for FitMate admin.

Security note (prototype): JWT stored in localStorage is XSS-vulnerable.
Post-PIMNAS: migrate to httpOnly cookies + refresh token rotation.
"""

from datetime import datetime, timedelta, timezone
import jwt
import bcrypt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from core.config import settings

http_bearer = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    """Hash a password with bcrypt (12 salt rounds)."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def create_access_token(subject: str) -> str:
    """
    Create a signed JWT with 8-hour expiry.

    Args:
        subject: The 'sub' claim value (admin username)
    Returns:
        Signed JWT string
    """
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRE_HOURS)
    payload = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
) -> str:
    """
    FastAPI dependency: validates Bearer token from Authorization header.
    Raises HTTP 401 if token is missing, invalid, or expired.
    Returns the admin username (sub claim) on success.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token tidak valid atau sudah kadaluarsa",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesi admin telah kadaluarsa. Silakan login kembali.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise credentials_exception

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2 and sys.argv[1] == "hash":
        hashed = get_password_hash(sys.argv[2])
        print(f"Bcrypt Hash: {hashed}")
    elif len(sys.argv) > 3 and sys.argv[1] == "verify":
        is_valid = verify_password(sys.argv[2], sys.argv[3])
        print(f"Valid: {is_valid}")
    else:
        print("Usage: python auth.py [hash <plain_password> | verify <plain_password> <hash>]")
