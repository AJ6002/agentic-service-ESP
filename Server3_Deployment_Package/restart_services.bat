@echo off
title ESP APM Platform — Restart Services
color 0E

echo ===============================================================================
echo   ESP APM PLATFORM — SERVER 3 SERVICE RESTARTER
echo ===============================================================================
echo.

:: 1. Check Administrator Privileges
net session >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    color 0C
    echo [ERROR] This restarter requires Administrator privileges.
    echo Please right-click 'restart_services.bat' and select 'Run as administrator'.
    echo.
    pause
    exit /b 1
)

cd /d "%~dp0"

echo [1/3] Indexing SQLite telemetry databases for high performance...
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" index_databases.py
) else (
    python index_databases.py
)

echo.
echo [2/3] Restarting Backend ML Service (esp-backend-service)...
cd /d "%~dp0backend_service\winsw"
esp-backend-service.exe stop >nul 2>&1
timeout /t 2 /nobreak >nul
esp-backend-service.exe start
echo       -> esp-backend-service restarted.

echo.
echo [3/3] Restarting Frontend Dashboard Service (esp-frontend-service)...
cd /d "%~dp0frontend_service\winsw"
esp-frontend-service.exe stop >nul 2>&1
timeout /t 2 /nobreak >nul
esp-frontend-service.exe start
echo       -> esp-frontend-service restarted.

cd /d "%~dp0"
echo.
echo ===============================================================================
echo   SERVICES RESTARTED SUCCESSFULLY!
echo   - Operations Dashboard : http://localhost:3000
echo   - Backend Swagger Docs : http://localhost:8090/docs
echo ===============================================================================
echo.
pause
