@echo off
title ESP APM Platform — Server 3 Service Uninstaller
color 0E

echo ===============================================================================
echo   ESP APM PLATFORM — SERVER 3 WINDOWS SERVICE UNINSTALLER
echo ===============================================================================
echo.

:: 1. Check Administrator Privileges
net session >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    color 0C
    echo [ERROR] This uninstaller requires Administrator privileges.
    echo Please right-click 'uninstall_services.bat' and select 'Run as administrator'.
    echo.
    pause
    exit /b 1
)

cd /d "%~dp0"

echo [1/2] Stopping and uninstalling esp-frontend-service...
cd /d "%~dp0frontend_service\winsw"
esp-frontend-service.exe stop
esp-frontend-service.exe uninstall
echo       -> esp-frontend-service removed.

echo.
echo [2/2] Stopping and uninstalling esp-backend-service...
cd /d "%~dp0backend_service\winsw"
esp-backend-service.exe stop
esp-backend-service.exe uninstall
echo       -> esp-backend-service removed.

cd /d "%~dp0"
echo.
echo ===============================================================================
echo   Both services have been stopped and removed cleanly.
echo ===============================================================================
echo.
pause
