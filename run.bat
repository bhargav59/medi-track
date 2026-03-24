@echo off
REM ============================================
REM  Medi-Track Nepal — Windows Launcher
REM  Double-click this file to start the app.
REM ============================================

echo Starting Medi-Track Nepal...
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

REM Install dependencies if needed
pip show flet >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Launch the application
python main.py

pause
