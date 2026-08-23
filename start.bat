@echo off
echo ============================================
echo  ClauseGuard — Starting Backend
echo ============================================
echo.
echo Starting backend on http://localhost:8000
echo Migrations will run automatically on startup.
echo.
start "ClauseGuard Backend" cmd /k "cd /d %~dp0backend && uvicorn app.main:app --reload --port 8000"

timeout /t 3 /nobreak >nul

echo Starting frontend on http://localhost:5173
start "ClauseGuard Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ============================================
echo  Both servers are starting...
echo  Backend:  http://localhost:8000
echo  Frontend: http://localhost:5173
echo  API Docs: http://localhost:8000/docs
echo ============================================
echo.
echo Open http://localhost:5173 in your browser.
pause
