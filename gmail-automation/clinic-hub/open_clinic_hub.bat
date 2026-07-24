@echo off
REM ===========================================================================
REM open_clinic_hub.bat  -  Dr. Manoj Agarwal Clinic  -  ONE launcher for all
REM
REM   SELF-CONTAINED: starts the tools directly with full paths.
REM   It does NOT use the old open_casepack.bat / open_vitals.bat at all,
REM   so those files cannot affect it in any way.
REM
REM   Follow-up Tracker is NOT auto-started - use open_tracker.bat daily
REM   as usual (it archives old CSVs first).
REM
REM   To stop a tool: close its minimized black window on the taskbar.
REM ===========================================================================

title Clinic Hub launcher

set CASEPACK_DIR=D:\casepack tool
set VITALS_DIR=D:\clinic_writer
set HUB=%~dp0clinic_hub.html

echo ---------------------------------------------------------------
netstat -an | findstr /C:"127.0.0.1:5058 " | findstr LISTENING >nul
if errorlevel 1 (
    if exist "%CASEPACK_DIR%\casepack_app.py" (
        echo Starting Surgical Case Pack...
        start "Surgical Case Pack tool" /D "%CASEPACK_DIR%" /MIN python casepack_app.py
    ) else (
        echo PROBLEM: casepack_app.py not found in "%CASEPACK_DIR%"
        echo Tell Claude this exact line.
        pause
    )
) else (
    echo Case Pack already running.
)

netstat -an | findstr /C:"127.0.0.1:5057 " | findstr LISTENING >nul
if errorlevel 1 (
    if exist "%VITALS_DIR%\vitals_app.py" (
        echo Starting Vitals ^& Plan...
        start "Vitals & Plan tool" /D "%VITALS_DIR%" /MIN python vitals_app.py
    ) else (
        echo PROBLEM: vitals_app.py not found in "%VITALS_DIR%"
        echo Tell Claude this exact line.
        pause
    )
) else (
    echo Vitals already running.
)


set STATEMENTS_DIR=D:\Scripts
netstat -an | findstr /C:"127.0.0.1:5059 " | findstr LISTENING >nul
if errorlevel 1 (
    if exist "%STATEMENTS_DIR%\statements_app.py" (
        echo Starting CC Statements runner...
        start "CC Statements runner" /D "%STATEMENTS_DIR%" /MIN python statements_app.py
    ) else (
        echo PROBLEM: statements_app.py not found in "%STATEMENTS_DIR%"
        echo Tell Claude this exact line.
        pause
    )
) else (
    echo Statements runner already running.
)

echo ---------------------------------------------------------------
echo Waiting 3 seconds for the tools to come up...
timeout /t 3 /nobreak >nul
start "" "%HUB%"
exit