@echo off
REM ============================================================
REM  Follow-Up Tracker - ONE-TIME PC SETUP  (Local PC)
REM  Dr. Manoj Agarwal Clinic, Bareilly
REM  Run this ONCE on each PC after copying the followup_tracker
REM  folder onto it (e.g. inside the SHAVEZ synced folder).
REM ============================================================
setlocal
cd /d "%~dp0"

echo.
echo   Follow-Up Tracker - PC Setup
echo   ============================
echo.

SET TRACKER_FOLDER=%~dp0
IF "%TRACKER_FOLDER:~-1%"=="\" SET TRACKER_FOLDER=%TRACKER_FOLDER:~0,-1%
SET INPUT_FOLDER=%TRACKER_FOLDER%\Input
SET OUTPUT_FOLDER=%TRACKER_FOLDER%\Output
SET ARCHIVE_FOLDER=%TRACKER_FOLDER%\Archive

echo   Tracker folder:
echo   %TRACKER_FOLDER%
echo.

REM ---- STEP 1: CHECK PYTHON ----
echo   [1/4] Checking for Python...
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    py --version >nul 2>&1
    IF ERRORLEVEL 1 (
        echo.
        echo   Python is NOT installed on this PC.
        echo   Install it once from https://www.python.org/downloads/
        echo   IMPORTANT: on the first install screen, tick
        echo              "Add python.exe to PATH", then click Install.
        echo   After installing, run this setup again.
        echo.
        pause
        EXIT /B
    )
)
echo   Python found.
echo.

REM ---- STEP 2: INSTALL REQUIRED LIBRARIES (one time) ----
echo   [2/4] Installing required libraries (flask, pandas, openpyxl, waitress)...
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r "%TRACKER_FOLDER%\requirements.txt"
IF ERRORLEVEL 1 (
    echo   pip with 'python' failed, trying 'py'...
    py -m pip install -r "%TRACKER_FOLDER%\requirements.txt"
)
echo   Libraries ready.
echo.

REM ---- STEP 3: CREATE WORKING SUBFOLDERS ----
echo   [3/4] Creating Input / Output / Archive folders...
IF NOT EXIST "%INPUT_FOLDER%"   mkdir "%INPUT_FOLDER%"
IF NOT EXIST "%OUTPUT_FOLDER%"  mkdir "%OUTPUT_FOLDER%"
IF NOT EXIST "%ARCHIVE_FOLDER%" mkdir "%ARCHIVE_FOLDER%"
echo   Folders ready.
echo.

REM ---- STEP 4: DESKTOP SHORTCUT ----
echo   [4/4] Creating desktop shortcut "Open Followup Tracker"...
SET OPEN_BAT=%TRACKER_FOLDER%\open_tracker.bat
SET SHORTCUT=%USERPROFILE%\Desktop\Open Followup Tracker.lnk
powershell -Command "$ws=New-Object -ComObject WScript.Shell; $s=$ws.CreateShortcut('%SHORTCUT%'); $s.TargetPath='%OPEN_BAT%'; $s.WorkingDirectory='%TRACKER_FOLDER%'; $s.IconLocation='C:\Windows\System32\shell32.dll,162'; $s.Description='Open Followup Tracker'; $s.Save()"
echo   Shortcut created on the Desktop.
echo.

echo   ------------------------------------------------------------
echo   ONE MORE THING (so the Excel saves into your Output folder):
echo   Chrome will open its Download settings now. Set the download
echo   location to:
echo       %OUTPUT_FOLDER%
echo   (Click the folder next to the path, pick the Output folder, OK.)
echo   ------------------------------------------------------------
echo.
echo   Press any key to open Chrome download settings...
pause >nul
start chrome "chrome://settings/downloads"

echo.
echo   ============================================================
echo    Setup complete. Use the "Open Followup Tracker" desktop
echo    shortcut every working day.
echo   ============================================================
echo.
pause
