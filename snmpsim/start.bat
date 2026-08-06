@echo off
REM ============================================
REM Start snmpsim test environment for oxian
REM ============================================

if not exist ".venv\Scripts\activate.bat" (
    echo venv not found, creating...
    python -m venv .venv
    call .venv\Scripts\activate
    pip install snmpsim-lextudio
    echo.
) else (
    call .venv\Scripts\activate
)

echo Starting snmpsim agents...
echo.

echo   RT-CORE-01     = 127.0.0.1:1611
start /B snmpsim-command-responder --data-dir=.\data\core-router --agent-udpv4-endpoint=127.0.0.1:1611 --log-level=error

timeout /t 2 /nobreak >nul

echo   SW-ACCESS-01   = 127.0.0.1:1612
start /B snmpsim-command-responder --data-dir=.\data\switch-01 --agent-udpv4-endpoint=127.0.0.1:1612 --log-level=error

timeout /t 2 /nobreak >nul

echo   RT-BRANCH-01   = 127.0.0.1:1613
start /B snmpsim-command-responder --data-dir=.\data\branch-router --agent-udpv4-endpoint=127.0.0.1:1613 --log-level=error

timeout /t 2 /nobreak >nul

echo   MK-SW-OFFICE   = 127.0.0.1:1614
start /B snmpsim-command-responder --data-dir=.\data\mikrotik --agent-udpv4-endpoint=127.0.0.1:1614 --log-level=error

timeout /t 2 /nobreak >nul

echo   web-prod-01    = 127.0.0.1:1615
start /B snmpsim-command-responder --data-dir=.\data\linux-server --agent-udpv4-endpoint=127.0.0.1:1615 --log-level=error

echo.
echo All agents running.
echo.
echo Test with:
echo   snmpget -v2c -c public 127.0.0.1:1611 1.3.6.1.2.1.1.1.0
echo.
echo Press any key to stop all agents...
pause >nul

taskkill /F /IM snmpsim-command-responder.exe 2>nul
echo Stopped.
