@echo off
REM ============================================
REM  Medi-Track Nepal — Windows .exe Builder
REM  
REM  HOW TO USE:
REM  1. Copy this entire "pms" folder to a Windows PC
REM  2. Make sure Python 3.10+ is installed
REM  3. Double-click this file (or run in CMD)
REM  4. The .exe will appear in dist\MediTrackNepal\
REM ============================================

echo ============================================
echo   Building Medi-Track Nepal .exe
echo ============================================
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed.
    echo Install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

REM Create virtual environment
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate and install
call .venv\Scripts\activate.bat
pip install flet pyinstaller

REM Build the exe
echo.
echo Building executable...
pyinstaller --name "MediTrackNepal" ^
    --onedir ^
    --windowed ^
    --add-data "views;views" ^
    --hidden-import flet ^
    --hidden-import flet_desktop ^
    --hidden-import views.dashboard ^
    --hidden-import views.inventory ^
    --hidden-import views.pos ^
    --hidden-import views.reports ^
    --hidden-import views.suppliers ^
    --clean ^
    main.py

echo.
if exist "dist\MediTrackNepal" (
    echo ============================================
    echo   BUILD SUCCESSFUL!
    echo   Your .exe is at: dist\MediTrackNepal\MediTrackNepal.exe
    echo ============================================
) else (
    echo BUILD FAILED. Check errors above.
)

pause
