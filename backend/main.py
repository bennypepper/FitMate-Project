import os
import sys
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from core.config import settings
from core.limiter import limiter
from database.mongo import db, connect_to_mongo, close_mongo_connection


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds standard security headers to all responses."""
    async def dispatch(self, request: StarletteRequest, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Permissions-Policy"] = "camera=(self), microphone=(), geolocation=()"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()


_is_prod = settings.APP_ENV.lower() == "production"

app = FastAPI(
    title="FitMate API",
    description="FastAPI Backend for TCM Safety Scanner",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None if _is_prod else "/api/docs",
    redoc_url=None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(SecurityHeadersMiddleware)

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://fitmate-project.vercel.app",
    "https://fitmate-tcm.vercel.app",
    "https://fitmate-scanner.vercel.app",
]

for extra_origin in (
    [settings.FRONTEND_URL, os.environ.get("FRONTEND_URL", "")]
    + [o.strip() for o in (settings.ALLOWED_ORIGINS or "").split(",")]
):
    cleaned = (extra_origin or "").strip().rstrip("/")
    if cleaned and cleaned not in ALLOWED_ORIGINS:
        ALLOWED_ORIGINS.append(cleaned)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Bridge-Token"],
)


@app.get("/")
async def root():
    return {"message": "FitMate API is running", "version": "1.0.0"}


@app.get("/health")
@app.get("/api/v1/health")
async def health():
    """Health check endpoint for uptime monitoring."""
    return {
        "status": "healthy",
        "database": "fallback" if db.is_fallback else "mongodb",
    }

from routers.ocr import router as ocr_router
from routers.analyze import router as analyze_router
from routers.whatsapp import router as whatsapp_router
from routers.admin import router as admin_router
from routers.upload import router as upload_router
from routers.bridge import router as bridge_router

app.include_router(ocr_router)
app.include_router(analyze_router)
app.include_router(whatsapp_router)
app.include_router(whatsapp_router, prefix="/api/v1")
app.include_router(admin_router)
app.include_router(upload_router)
app.include_router(bridge_router)
