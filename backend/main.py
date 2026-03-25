from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.mongo import connect_to_mongo, close_mongo_connection
from contextlib import asynccontextmanager

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
app.include_router(ocr_router)
app.include_router(analyze_router)

