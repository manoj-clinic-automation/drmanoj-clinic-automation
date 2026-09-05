@echo off
REM REGISTER_EXPECTED_ON_CAPTURE.bat -- S225: double-click me. Registers the MargExpectedOnCapture task and fixes the
REM nightly's time limit, through register_expected_on_capture.ps1 beside me. The window STAYS OPEN with the result.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0register_expected_on_capture.ps1"
echo.
echo Read the two tables above: both should say Ready. Close this window when done.
pause
