@echo off
echo =========================================
echo FitMate Local Development Environment
echo =========================================

echo [1/3] Starting Docker containers (MongoDB & PostgreSQL)...
docker-compose up -d

echo.
echo [2/3] Starting FastAPI Backend...
echo The backend will run on http://localhost:8000
start "FitMate Backend (FastAPI)" cmd /k "cd backend && call venv\Scripts\activate && uvicorn main:app --reload"

echo.
echo [3/3] Starting Next.js Frontend...
echo The frontend will run on http://localhost:3000
start "FitMate Frontend (Next.js)" cmd /k "cd frontend && npm run dev"

echo.
echo =========================================
echo Both servers are launching in separate windows!
echo - Backend swagger UI: http://localhost:8000/docs
echo - Frontend app: http://localhost:3000
echo =========================================
echo You can close this window at any time. The servers will continue running in their respective windows.
pause
