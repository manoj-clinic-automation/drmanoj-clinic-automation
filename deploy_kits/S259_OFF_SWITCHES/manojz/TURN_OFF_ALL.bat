@echo off
REM ==========================================================================
REM  TURN_OFF_ALL.bat      S259 -- 14-Sep-2026
REM  Switches OFF everything on this PC that talks to the clinic server.
REM  It does this by putting one file in D:\Downloads\margsync\_off\.
REM  Nothing is stopped, uninstalled or unregistered. TURN_ON_ALL.bat undoes it.
REM ==========================================================================
setlocal
set OFFDIR=D:\Downloads\margsync\_off
if not exist "%OFFDIR%" mkdir "%OFFDIR%"
echo switched off %DATE% %TIME%> "%OFFDIR%\ALL_OFF.txt"
echo.
echo  SWITCHED OFF.
echo.
echo  These have stopped, from their next run:
echo     - the 15-minute check that says when the Marg pull has gone to sleep
echo     - the daily stock push
echo     - the 22:30 nightly stock push
echo.
echo  These are still running, on purpose:
echo     - the 10-minute Marg pull from the medical PC
echo     - capture on the medical PC (an export not captured is gone for ever)
echo.
echo  To switch it all back on, double-click:
echo     D:\Downloads\margsync\TURN_ON_ALL.bat
echo.
pause
exit /b 0
