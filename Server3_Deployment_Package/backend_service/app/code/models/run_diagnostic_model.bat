@echo off
title CCED VFD 13-Fault Diagnostic & Anomaly Engine
echo ======================================================
echo    CCED VFD 13-Fault Diagnostic & Anomaly Engine
echo ======================================================
echo.
echo Running 13-Fault Validation Suite and Live Testing...
echo.
python "%~dp0test_fault_scenarios.py" %*
echo.
pause
