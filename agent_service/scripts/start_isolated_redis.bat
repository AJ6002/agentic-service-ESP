@echo off
title ESP APM Agent Service - Isolated Redis (Port 6380)
echo ===============================================================================
echo   ESP APM AGENT SERVICE - DEDICATED ISOLATED REDIS INSTANCE
echo ===============================================================================
echo   Port     : 6380 (completely isolated from default 6379)
echo   Data dir : %~dp0data\redis
echo   DB file  : dump-v3.rdb
echo ===============================================================================

cd /d "%~dp0"
if not exist "data\redis" mkdir "data\redis"

"C:\Program Files\Redis\redis-server.exe" --port 6380 --dir "%~dp0data\redis" --dbfilename dump-v3.rdb --save 60 1
