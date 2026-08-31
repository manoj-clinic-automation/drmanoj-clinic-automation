@echo off
REM  Double-click me. One-time setup for the patient fingerprint salt.
REM  Nothing secret is ever shown on screen.
cd /d "%~dp0"
python setup_salt.py
if errorlevel 1 (
  echo.
  echo Something went wrong above. Nothing was changed.
)
echo.
pause
