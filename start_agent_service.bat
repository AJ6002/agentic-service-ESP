@echo off
setlocal EnableDelayedExpansion
title ESP Agent Service Launcher

REM ===== Config =====
set "ROOT=%~dp0"
set "AGENT_PORT=8091"
set "AGENT_HOST=127.0.0.1"
set "VENV_UVICORN=%ROOT%.venv\Scripts\uvicorn.exe"
set "ENV_FILE=%ROOT%agent_service\.env"

REM ===== 1. Self-elevate to Administrator =====
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator privileges...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs -WorkingDirectory '%ROOT%'"
    exit /b
)
cd /d "%ROOT%"

echo ================================================================
echo  ESP Agent Service Launcher (Administrator)
echo ================================================================

REM ===== 2. Kill stale processes on the agent port =====
echo.
echo [1/4] Checking for stale processes on port %AGENT_PORT%...
set "FOUND=0"
for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:":%AGENT_PORT% .*LISTENING"') do (
    if not "%%P"=="0" (
        set "FOUND=1"
        echo   Killing PID %%P ^(and child tree^) holding port %AGENT_PORT%
        taskkill /F /T /PID %%P >nul 2>&1
    )
)
if "!FOUND!"=="0" echo   Port %AGENT_PORT% is free.
REM Wait until the port is actually released (max ~10s)
set "TRIES=0"
:waitfree
netstat -ano | findstr /R /C:":%AGENT_PORT% .*LISTENING" >nul 2>&1
if %errorlevel%==0 (
    set /a TRIES+=1
    if !TRIES! geq 10 (
        echo   ERROR: Port %AGENT_PORT% still in use after kill attempts.
        pause
        exit /b 1
    )
    timeout /t 1 /nobreak >nul
    goto waitfree
)
echo   Port %AGENT_PORT% is clear.

REM ===== 3. Ping LLM server =====
echo.
echo [2/4] Pinging LLM server...
set "LLM_URL="
if exist "%ENV_FILE%" (
    for /f "usebackq tokens=1,* delims==" %%A in ("%ENV_FILE%") do (
        if /i "%%A"=="LLM_GATEWAY_URL" set "LLM_URL=%%B"
    )
)
if not defined LLM_URL (
    echo   WARNING: LLM_GATEWAY_URL not found in %ENV_FILE%
) else (
    set "LLM_URL=!LLM_URL:"=!"
    echo   Target: !LLM_URL!/models
    powershell -NoProfile -Command "try { $r = Invoke-WebRequest -UseBasicParsing -TimeoutSec 8 -Uri '!LLM_URL!/models'; Write-Host ('  LLM ONLINE - HTTP ' + $r.StatusCode) -ForegroundColor Green } catch { Write-Host ('  LLM UNREACHABLE: ' + $_.Exception.Message) -ForegroundColor Red }"
)

REM ===== 4. Start agent service fresh =====
echo.
echo [3/4] Starting Agent Service on %AGENT_HOST%:%AGENT_PORT%...
if not exist "%VENV_UVICORN%" (
    echo   ERROR: %VENV_UVICORN% not found.
    pause
    exit /b 1
)
start "ESP Agent Service :%AGENT_PORT%" /D "%ROOT%" "%VENV_UVICORN%" app.main:app --app-dir "%ROOT%agent_service" --host %AGENT_HOST% --port %AGENT_PORT%

REM ===== 5. Health check =====
echo.
echo [4/4] Waiting for health endpoint...
set "TRIES=0"
:waithealth
timeout /t 2 /nobreak >nul
powershell -NoProfile -Command "try { (Invoke-WebRequest -UseBasicParsing -TimeoutSec 3 -Uri 'http://%AGENT_HOST%:%AGENT_PORT%/health').StatusCode | Out-Null; exit 0 } catch { exit 1 }"
if %errorlevel%==0 (
    echo   Agent Service HEALTHY at http://%AGENT_HOST%:%AGENT_PORT%
    goto done
)
set /a TRIES+=1
if !TRIES! lss 15 goto waithealth
echo   WARNING: Health check timed out. Check the "ESP Agent Service" window for errors.

:done
echo.
echo Launcher finished. The service runs in its own window; close that window to stop it.
pause
endlocal
