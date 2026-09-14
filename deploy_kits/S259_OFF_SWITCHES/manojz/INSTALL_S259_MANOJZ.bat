@echo off
REM ==========================================================================
REM  INSTALL_S259_MANOJZ.bat       S259 -- 14-Sep-2026
REM
REM  ONE DOUBLE-CLICK. It checks the three live files are exactly what this
REM  kit was built from, backs them up, installs the new ones, makes the
REM  _off folder, then WALKS IT FOR REAL -- switches everything off, proves
REM  each job did nothing and said so, and switches it back on.
REM
REM  If any part of that walk fails it puts the old files back by itself.
REM  It leaves the system SWITCHED ON. Safe to run twice.
REM ==========================================================================
setlocal
cd /d "%~dp0"
python -B install_s259.py
echo.
pause
exit /b 0
