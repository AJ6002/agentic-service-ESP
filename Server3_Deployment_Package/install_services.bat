@echo off
title ESP APM Platform — Server 3 Service Installer
color 0A

echo ===============================================================================
echo   ESP APM PLATFORM — SERVER 3 DUAL WINDOWS SERVICE INSTALLER
echo ===============================================================================
echo.

:: 1. Check Administrator Privileges
net session >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    color 0C
    echo [ERROR] This installer requires Administrator privileges.
    echo Please right-click 'install_services.bat' and select 'Run as administrator'.
    echo.
    pause
    exit /b 1
)

cd /d "%~dp0"

echo [1/4] Configuring Windows Firewall rules...
netsh advfirewall firewall add rule name="ESP APM Backend (8090)" dir=in action=allow protocol=TCP localport=8090 >nul 2>&1
netsh advfirewall firewall add rule name="ESP APM Frontend (3000)" dir=in action=allow protocol=TCP localport=3000 >nul 2>&1
echo       -> Allowed incoming TCP traffic on ports 8090 and 3000.

echo.
echo [2/4] Installing and starting Backend ML Service (esp-backend-service)...
cd /d "%~dp0backend_service\winsw"
esp-backend-service.exe stop >nul 2>&1
esp-backend-service.exe uninstall >nul 2>&1
esp-backend-service.exe install
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install esp-backend-service.
    pause
    exit /b 1
)
esp-backend-service.exe start
echo       -> esp-backend-service started successfully.

echo.
echo [3/4] Installing and starting Frontend Dashboard Service (esp-frontend-service)...
cd /d "%~dp0frontend_service\winsw"
esp-frontend-service.exe stop >nul 2>&1
esp-frontend-service.exe uninstall >nul 2>&1
esp-frontend-service.exe install
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install esp-frontend-service.
    pause
    exit /b 1
)
esp-frontend-service.exe start
echo       -> esp-frontend-service started successfully.

cd /d "%~dp0"
echo.
echo ===============================================================================
echo   SERVICES SUCCESSFULLY INSTALLED AND RUNNING:
echo.
echo   - Operations Dashboard : http://localhost:3000  (or http://<SERVER_3_IP>:3000)
echo   - Backend REST & WS    : http://localhost:8090  (Swagger: /docs, WS: /ws/live)
echo.
echo   - Configuration File   : %~dp0config\config.env
echo   - Backend Logs         : %~dp0backend_service\logs\
echo   - Frontend Logs        : %~dp0frontend_service\logs\
echo ===============================================================================
echo.
pause
