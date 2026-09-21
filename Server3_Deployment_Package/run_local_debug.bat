@echo off
title ESP APM Platform — Server 3 Local Debug Launcher
color 0B

echo ===============================================================================
echo   ESP APM PLATFORM — LOCAL DEBUG RUNNER (STANDALONE CONSOLE MODE)
echo ===============================================================================
echo   Runs Backend and Frontend in separate visible console windows.
echo   Does NOT require Administrator privileges or Windows Service installation.
echo ===============================================================================
echo.

cd /d "%~dp0"

:: Set Python Executable
if exist ".venv\Scripts\python.exe" (
    set "PY_EXEC=%~dp0.venv\Scripts\python.exe"
) else (
    set "PY_EXEC=python"
)

echo [1/2] Launching Backend ML Service on Port 8090...
start "ESP Server 3 — Backend ML (:8090)" cmd /k "cd /d "%~dp0backend_service" && "%PY_EXEC%" run_backend.py"

echo [2/2] Launching Frontend Dashboard on Port 3000...
start "ESP Server 3 — Frontend Dashboard (:3000)" cmd /k "cd /d "%~dp0frontend_service" && "%PY_EXEC%" serve_frontend.py"

echo.
echo ===============================================================================
echo   LOCAL SERVERS LAUNCHED:
echo   - Operations Dashboard : http://localhost:3000
echo   - Backend Swagger Docs : http://localhost:8090/docs
echo   - Live WebSockets      : ws://localhost:8090/ws/live
echo ===============================================================================
echo.
pause
