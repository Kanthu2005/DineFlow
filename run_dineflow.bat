@echo off
title DineFlow - Restaurant Management System
echo ========================================================
echo   Starting DineFlow Backend and Frontend Web App
echo ========================================================
echo.
echo [1/2] Launching DineFlow in your default browser...
start http://localhost:8000/
echo.
echo [2/2] Starting FastAPI Server on port 8000 with auto-reload...
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause
