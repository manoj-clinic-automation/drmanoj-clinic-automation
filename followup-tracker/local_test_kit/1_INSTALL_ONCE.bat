@echo off
REM ============================================================
REM  Follow-up Tracker — ONE-TIME INSTALLER (run once per PC)
REM  Dr. Manoj Agarwal Clinic
REM ============================================================
title Follow-up Tracker - Installer
cd /d "%~dp0followup_tracker"

echo ============================================================
echo   Follow-up Tracker - One Time Setup
echo ============================================================
echo.
echo Checking for Python...
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo.
    echo  [X] Python is NOT installed or not in PATH.
    echo.
    echo  Please install Python first:
    echo    1. Go to https://www.python.org/downloads/
    echo    2. Download the latest Windows installer
    echo    3. RUN it and TICK the box "Add Python to PATH"
    echo    4. Finish install, then run this file again.
    echo.
    pause
    exit
)
echo  [OK] Python found.
echo.
echo Installing required packages (one time, needs internet)...
echo.
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo.
echo ============================================================
echo   Setup complete.
echo   You can now use  2_START_TRACKER.bat  every day.
echo ============================================================
echo.
pause
