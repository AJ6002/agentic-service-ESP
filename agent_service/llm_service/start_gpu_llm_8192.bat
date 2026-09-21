@echo off
title ESP APM - Local CUDA GPU LLM Server (RTX 3050 - Context 8192)
color 0B

echo ===============================================================================
echo   ESP APM AGENT SERVICE - LOCAL CUDA GPU LLM SERVER (llama.cpp)
echo ===============================================================================
echo   - Model   : Qwen2.5-Coder-3B-Instruct-Q4_K_M.gguf
echo   - Context : 8192 (-c 8192 matching prod architecture)
echo   - Port    : http://127.0.0.1:8080/v1
echo   - GPU     : -ngl 99 (Full layer offloading to CUDA)
echo ===============================================================================
echo.

cd /d "%~dp0"

set LLAMA_BIN=%~dp0bin\llama-cpp\llama-server.exe
set LLAMA_MODEL=%~dp0models\Qwen2.5-Coder-3B-Instruct-Q4_K_M.gguf

if not exist "%LLAMA_BIN%" (
    echo [ERROR] %LLAMA_BIN% not found!
    pause
    exit /b 1
)

if not exist "%LLAMA_MODEL%" (
    echo [ERROR] %LLAMA_MODEL% not found!
    pause
    exit /b 1
)

echo Starting GPU llama-server with 100%% layer offloading (-ngl 99) and -c 8192...
"%LLAMA_BIN%" -m "%LLAMA_MODEL%" -ngl 99 -c 8192 --host 0.0.0.0 --port 8080
