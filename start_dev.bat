@echo off
echo =========================================
echo  FitMate Local Development Environment
echo =========================================

echo.
echo [1/4] Starting Docker containers (MongoDB ^& PostgreSQL)...
docker-compose up -d

echo.
echo [2/4] Starting FastAPI Backend...
echo     ^> http://localhost:8000
start "FitMate Backend" cmd /k "cd backend && call venv\Scripts\activate.bat && python -m uvicorn main:app --reload --port 8000"

echo.
echo [3/4] Starting Next.js Frontend...
echo     ^> http://localhost:3000
start "FitMate Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo [4/4] Starting Localtunnel (WhatsApp webhook)...
echo     Waiting 5s for backend to boot first...
timeout /t 5 /nobreak >nul
start "FitMate Tunnel" cmd /k "npx -y localtunnel --port 8000"

echo.
echo =========================================
echo  All services are launching!
echo.
echo  Backend:   http://localhost:8000
echo  Docs:      http://localhost:8000/docs
echo  Frontend:  http://localhost:3000
echo  Tunnel:    check the Tunnel window for the public URL
echo.
echo  REMINDER: After the tunnel window shows its URL,
echo  update it in Twilio Console ^> Sandbox settings:
echo  https://console.twilio.com
echo =========================================
echo.
pause
