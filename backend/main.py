from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response

from database.mongo import connect_to_mongo, close_mongo_connection
from contextlib import asynccontextmanager

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds standard security headers to all responses."""
    async def dispatch(self, request: StarletteRequest, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Allow camera/microphone for PWA scanning feature
        response.headers["Permissions-Policy"] = "camera=(*), microphone=()"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()


app = FastAPI(
    title="FitMate API",
    description="FastAPI Backend for TCM Safety Scanner",
    version="1.0.0",
    lifespan=lifespan,
    # Hide detailed error info in production
    docs_url="/api/docs",
    redoc_url=None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security headers on all responses
app.add_middleware(SecurityHeadersMiddleware)

# CORS — explicit origin allowlist only
# localhost:3000 for local dev, Vercel for production
# ngrok URLs are dynamic; add yours to .env ALLOWED_ORIGINS if needed
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://fitmate-tcm.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # Removed PUT/DELETE from public CORS (admin only)
    allow_headers=["Content-Type", "Authorization"],
)


@app.get("/")
async def root():
    return {"message": "FitMate API is running", "version": "1.0.0"}


@app.get("/health")
async def health():
    """Health check endpoint for uptime monitoring."""
    return {"status": "healthy"}


from routers.ocr import router as ocr_router
from routers.analyze import router as analyze_router
from routers.whatsapp import router as whatsapp_router
from routers.admin import router as admin_router
from routers.upload import router as upload_router

app.include_router(ocr_router)
app.include_router(analyze_router)
app.include_router(whatsapp_router)
app.include_router(admin_router)
app.include_router(upload_router)
