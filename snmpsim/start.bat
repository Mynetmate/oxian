@echo off
REM ============================================
REM Start snmpsim test environment for oxian
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

python start.py
