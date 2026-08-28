@echo off
REM ============================================
REM Start snmpsim test environment for oxian
REM Loopback IPs: 127.0.0.1 - 127.0.0.5 (Port 161)
REM ============================================

cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
    echo venv not found, creating...
    python -m venv .venv
    call .venv\Scripts\activate
    pip install snmpsim-lextudio
    echo.
) else (
    call .venv\Scripts\activate
)

echo Starting snmpsim agents on port 161 (Loopback aliases)...
echo.

echo   RT-CORE-01     = 127.0.0.1:161
start /B snmpsim-command-responder --data-dir=.\data\core-router --agent-udpv4-endpoint=127.0.0.1:161 --log-level=error

timeout /t 1 /nobreak >nul

echo   SW-ACCESS-01   = 127.0.0.2:161
start /B snmpsim-command-responder --data-dir=.\data\switch-01 --agent-udpv4-endpoint=127.0.0.2:161 --log-level=error

timeout /t 1 /nobreak >nul

echo   RT-BRANCH-01   = 127.0.0.3:161
start /B snmpsim-command-responder --data-dir=.\data\branch-router --agent-udpv4-endpoint=127.0.0.3:161 --log-level=error

timeout /t 1 /nobreak >nul

echo   MK-SW-OFFICE   = 127.0.0.4:161
start /B snmpsim-command-responder --data-dir=.\data\mikrotik --agent-udpv4-endpoint=127.0.0.4:161 --log-level=error

timeout /t 1 /nobreak >nul

echo   web-prod-01    = 127.0.0.5:161
start /B snmpsim-command-responder --data-dir=.\data\linux-server --agent-udpv4-endpoint=127.0.0.5:161 --log-level=error

echo.
echo All agents running on port 161.
echo.
echo Test scanning in backend API with target: 127.0.0.1 (port: 161)
echo.
echo Press any key to stop all agents...
pause >nul

taskkill /F /IM snmpsim-command-responder.exe 2>nul
echo Stopped.
