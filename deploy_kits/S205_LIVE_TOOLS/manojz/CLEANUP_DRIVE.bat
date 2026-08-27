@echo off
setlocal
REM ===========================================================================
REM  CLEANUP_DRIVE.bat  --  S201.  DOUBLE-CLICK on MANOJZ.
REM
REM  Tidies the clinic Drive delivery folder (ToMedical), which still holds the
REM  first attempt at getting the watcher onto the medical PC -- superseded by
REM  the agent and the _kit folder. Moves, never deletes.
REM
REM  Amir's NEFT advices and the vendor reconciliation are LEFT ALONE: they are
REM  real deliveries to the medical counter, not pipeline clutter.
REM ===========================================================================
title Tidy the clinic Drive delivery folder
set "T=H:\My Drive\Clinic Data Archive\ToMedical"
set "BIN=H:\My Drive\Clinic Data Archive\_to_delete_S201"
if not exist "%T%" ( echo   STOP: %T% not found. Is Google Drive running? & pause & exit /b 1 )
mkdir "%BIN%" 2>nul
echo.
echo  ==========================================================
echo   TIDYING THE DRIVE DELIVERY FOLDER   (nothing is deleted)
echo  ==========================================================
echo.
for %%F in ("marg_watch.py" "INSTALL_WATCHER.bat" "START_MARG_WATCHER.bat" "SETUP_WATCHER.txt" "ADD_MARG_REPORTS_to_watcher.txt" "ADD_MARG_REPORTS_to_watcher.gdoc" "DELIVERY_TEST_S195.txt" "_S201_channel_probe.txt") do (
  if exist "%T%\%%~F" ( move /y "%T%\%%~F" "%BIN%\" >nul && echo       moved %%~F )
)
echo.
echo  ==========================================================
echo   KEPT:
echo       INSTALL_AGENT.bat    the one installer you run
echo       medical_agent.py     what it installs
echo       _kit\                what the agent picks up by itself
echo       SURVEY_MEDICAL.txt   the read-only survey
echo       CLEANUP_MEDICAL.bat  the medical-side tidy
echo       NEFT advices, vendor reconciliation  - real deliveries
echo.
echo   Parked in: %BIN%
echo  ==========================================================
echo.
pause
