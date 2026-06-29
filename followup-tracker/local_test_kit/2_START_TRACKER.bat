@echo off
REM ============================================================
REM  Follow-up Tracker — DAILY LAUNCHER (local testing)
REM  Dr. Manoj Agarwal Clinic
REM ============================================================
title Follow-up Tracker - RUNNING (keep this window open)
cd /d "%~dp0followup_tracker"

echo ============================================================
echo   Follow-up Tracker is starting...
echo ============================================================
echo.
echo   KEEP THIS BLACK WINDOW OPEN while you use the tracker.
echo   Your browser will open automatically in a few seconds.
echo.
echo   If it does not, open your browser and go to:
echo       http://localhost:5000
echo.
echo   Login password:  clinic2026
echo.
echo   When finished for the day: close the browser tab,
echo   then close this black window (or press Ctrl+C).
echo ============================================================
echo.

REM open browser after a short delay
start "" /b cmd /c "timeout /t 3 >nul & start "" http://localhost:5000"

REM start the local server (this keeps running)
python app.py

pause
