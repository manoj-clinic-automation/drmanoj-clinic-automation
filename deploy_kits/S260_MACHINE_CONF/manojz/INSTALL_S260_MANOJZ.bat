@echo off
REM ==========================================================================
REM  INSTALL_S260_MANOJZ.bat       S260 -- 14-Sep-2026
REM
REM  ONE DOUBLE-CLICK. It checks the four live files are exactly what this kit
REM  was built from, reads TODAY'S settings out of those very files and writes
REM  them into D:\Downloads\margsync\_config\machine.conf, backs the files up,
REM  installs the new ones, then WALKS IT FOR REAL -- including taking the
REM  settings file away to prove everything falls back to what it always was.
REM
REM  If any part of that walk fails it puts the old files back by itself.
REM  Safe to run twice.
REM ==========================================================================
setlocal
cd /d "%~dp0"
python -B install_s260.py
echo.
pause
exit /b 0
