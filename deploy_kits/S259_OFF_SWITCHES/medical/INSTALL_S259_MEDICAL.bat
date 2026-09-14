@echo off
REM ==========================================================================
REM  INSTALL_S259_MEDICAL.bat       S259 -- 14-Sep-2026
REM
REM  RUN THIS ON MANOJZ. It sends the OFF switches to the MEDICAL PC over the
REM  Tailscale share the Marg pull already uses. Nothing goes near Drive and
REM  nothing has to be typed at the shop's machine.
REM
REM  It checks the two files over there are exactly what this kit was built
REM  from, backs them up, copies the new ones across, proves them by running
REM  their own tests and really throwing the switch, and puts the old files
REM  back by itself if any of that fails. It leaves everything switched ON.
REM
REM  The medical PC must be on, with Tailscale up. Safe to run twice.
REM ==========================================================================
setlocal
cd /d "%~dp0"
python -B install_s259_medical.py
echo.
pause
exit /b 0
