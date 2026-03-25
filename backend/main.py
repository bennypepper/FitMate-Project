from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.mongo import connect_to_mongo, close_mongo_connection
from contextlib import asynccontextmanager

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()

app = FastAPI(
    title="FitMate API",
    description="FastAPI Backend for TCM Safety Scanner",
    version="1.0.0",
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for prototype
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "FitMate API is running"}

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

