@echo off
rem ASCII-only. Blocking uvicorn server (its own window). Close window to stop.
chcp 65001 >nul
title Science AI Lab Server
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
cd /d "%~dp0backend"
".venv\Scripts\python.exe" -m uvicorn main:app --host 127.0.0.1 --port 8000
echo.
echo Server stopped. Press any key to close.
pause >nul
