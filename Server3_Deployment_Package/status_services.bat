@echo off
title ESP APM Platform — Service Status Checker
color 0B

echo ===============================================================================
echo   ESP APM PLATFORM — SERVER 3 SERVICE STATUS CHECKER
echo ===============================================================================
echo.

echo [1/2] Checking Windows Service Control Manager status:
echo.
sc query esp-backend-service | findstr "STATE"
sc query esp-frontend-service | findstr "STATE"

echo.
echo [2/2] Checking Local Network Ports:
echo.
powershell -Command "try { (New-Object Net.Sockets.TcpClient('127.0.0.1', 8090)).Close(); Write-Host ' [ONLINE] Backend ML Service is responding on port 8090.' -ForegroundColor Green } catch { Write-Host ' [OFFLINE] Backend ML Service is not responding on port 8090.' -ForegroundColor Red }"
powershell -Command "try { (New-Object Net.Sockets.TcpClient('127.0.0.1', 3000)).Close(); Write-Host ' [ONLINE] Frontend Dashboard Service is responding on port 3000.' -ForegroundColor Green } catch { Write-Host ' [OFFLINE] Frontend Dashboard Service is not responding on port 3000.' -ForegroundColor Red }"

echo.
echo ===============================================================================
pause
