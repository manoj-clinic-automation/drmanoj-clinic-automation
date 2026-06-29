@echo off
REM ============================================================
REM  Follow-Up Tracker - DAILY LAUNCHER  (Local PC)
REM  Dr. Manoj Agarwal Clinic, Bareilly
REM
REM  DAILY STEPS:
REM   1. Export both CSVs from Docterz (consultation report +
REM      follow-up log) and save them where you can find them.
REM   2. Double-click the "Open Followup Tracker" desktop shortcut.
REM   3. The browser opens to the tracker. Pick the two CSVs,
REM      click Process. The Excel downloads to your Output folder.
REM   4. When done for the day, close the small black tracker window.
REM ============================================================

cd /d "%~dp0"

SET INPUT_FOLDER=%~dp0Input
SET ARCHIVE_FOLDER=%~dp0Archive

REM ---- Archive yesterday's input CSVs (optional tidiness) ----
IF EXIST "%INPUT_FOLDER%\*.csv" (
    echo Archiving previous CSV files...
    for %%f in ("%INPUT_FOLDER%\*.csv") do move /Y "%%f" "%ARCHIVE_FOLDER%\" >nul 2>&1
)

REM ---- Open the Input folder so you can drop today's exports ----
IF EXIST "%INPUT_FOLDER%" explorer "%INPUT_FOLDER%"

REM ---- Start the local tracker (opens browser automatically) ----
REM Try the Python launcher; python must be on PATH (see setup_tracker.bat)
python run_local.py
IF ERRORLEVEL 1 (
    echo.
    echo  Could not start with 'python'. Trying 'py' launcher...
    py run_local.py
)

REM If the server window closed immediately, show why:
IF ERRORLEVEL 1 (
    echo.
    echo  ERROR: Python could not run the tracker.
    echo  Run setup_tracker.bat once first, and make sure Python is installed.
    pause
)
