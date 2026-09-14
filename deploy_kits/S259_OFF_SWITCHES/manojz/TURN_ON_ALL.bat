@echo off
REM ==========================================================================
REM  TURN_ON_ALL.bat       S259 -- 14-Sep-2026
REM  Removes every OFF marker in D:\Downloads\margsync\_off\, so every job
REM  runs again from its next turn. Nothing is started or re-registered --
REM  the jobs were never stopped, only told to do nothing.
REM ==========================================================================
setlocal
set OFFDIR=D:\Downloads\margsync\_off
if exist "%OFFDIR%\ALL_OFF.txt" del /q "%OFFDIR%\ALL_OFF.txt"
if exist "%OFFDIR%\PULL_WATCHDOG_OFF.txt" del /q "%OFFDIR%\PULL_WATCHDOG_OFF.txt"
if exist "%OFFDIR%\PUSH_STOCK_OFF.txt" del /q "%OFFDIR%\PUSH_STOCK_OFF.txt"
echo.
echo  SWITCHED ON.
echo.
echo  Everything runs again from its next turn:
echo     - the pull-asleep check, within 15 minutes
echo     - the stock push, at its next run (the nightly one at 22:30)
echo.
echo  Anything they missed while switched off is sent then - nothing was lost.
echo.
pause
exit /b 0
