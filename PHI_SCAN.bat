@echo off
REM ===================================================================
REM  PHI_SCAN.bat  --  double-click me BEFORE PUBLISH_ALL.bat
REM  Checks that no patient data or secret is about to be published.
REM  It never prints a phone number or a token.
REM ===================================================================
cd /d "%~dp0"
python tools\phi_scan.py
echo.
if errorlevel 1 (
  echo ############################################################
  echo #  SOMETHING NEEDS A LOOK -- do not publish until checked  #
  echo ############################################################
) else (
  echo ============================================================
  echo   CLEAN -- safe to run PUBLISH_ALL.bat
  echo ============================================================
)
echo.
pause
