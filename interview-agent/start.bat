@echo off
echo ================================================
echo   AI Technical Interview Agent — Quick Start
echo ================================================
echo.

REM Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    py --version >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Python not found. Install Python 3.11+ from https://python.org
        pause
        exit /b 1
    )
    set PYTHON=py
) else (
    set PYTHON=python
)

REM Check for .env
if not exist "backend\.env" (
    echo Creating .env from example...
    copy .env.example backend\.env
    echo.
    echo IMPORTANT: Edit backend\.env and set your ANTHROPIC_API_KEY before continuing!
    notepad backend\.env
    pause
)

REM Install deps
echo Installing dependencies...
cd backend
%PYTHON% -m pip install -r requirements.txt --quiet

echo.
echo Starting server at http://localhost:8000
echo Press Ctrl+C to stop.
echo.
%PYTHON% main.py
