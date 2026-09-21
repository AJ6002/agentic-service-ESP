@echo off
title ESP APM - Local CUDA GPU LLM Server (RTX 3050 - Context 8192)
color 0B

echo ===============================================================================
echo   ESP APM AGENT SERVICE - LOCAL CUDA GPU LLM SERVER (llama.cpp)
echo ===============================================================================
echo   - Model   : Qwen2.5-Coder-3B-Instruct-Q4_K_M.gguf
echo   - Context : 8192 (-c 8192 matching prod architecture)
echo   - Port    : http://127.0.0.1:8080/v1
echo   - GPU     : -ngl 99 (Full layer offloading)
echo ===============================================================================
echo.

cd /d "%~dp0"

call "%~dp0llm_service\start_gpu_llm_8192.bat"
