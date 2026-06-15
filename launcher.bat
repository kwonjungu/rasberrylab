@echo off
rem ASCII-only full launcher (no Windows Script Host dependency).
chcp 65001 >nul
title Science AI Lab
cd /d "%~dp0"

rem 1) Already running? open browser.
curl -s -o nul --max-time 2 http://127.0.0.1:8000/health && goto open

rem 2) Start server in its own minimized window (keeps running).
rem    Absolute path + /D so the spawned cmd uses the right working dir.
start "Science AI Lab Server" /min /D "%~dp0" cmd /c "%~dp0run_server.bat"

rem 3) Poll health up to ~60s, then open browser.
for /l %%i in (1,1,60) do (
  curl -s -o nul --max-time 2 http://127.0.0.1:8000/health && goto open
  ping -n 2 127.0.0.1 >nul
)
echo [ERROR] Server did not start. Run run_server.bat to see the error.
pause
exit /b 1

:open
start "" http://127.0.0.1:8000/
exit /b 0
