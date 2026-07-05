@echo off
echo.
echo  *  Aetherial AI Interior Architect
echo  *  Starting Backend + Frontend...
echo.

:: Check if .env has been configured
findstr /C:"PASTE_YOUR_KEY_HERE" backend\.env >nul 2>&1
if not errorlevel 1 (
    echo  WARNING: You haven't set your GEMINI_API_KEY yet!
    echo  Open backend\.env and replace PASTE_YOUR_KEY_HERE with your actual key.
    echo  Get your key at: https://aistudio.google.com/app/apikey
    echo.
    pause
)

:: Start Backend
echo  Starting FastAPI backend on http://localhost:8000 ...
start "Aetherial Backend" cmd /k "cd backend && uvicorn main:app --reload --port 8000"

:: Wait a moment
timeout /t 2 /nobreak >nul

:: Start Frontend
echo  Starting Next.js frontend on http://localhost:3000 ...
start "Aetherial Frontend" cmd /k "cd frontend && npm run dev"

:: Wait then open browser
timeout /t 5 /nobreak >nul
echo.
echo  Opening http://localhost:3000 ...
start http://localhost:3000

echo.
echo  Both servers are running in separate windows.
echo  Close those windows to stop the servers.
echo.
pause
