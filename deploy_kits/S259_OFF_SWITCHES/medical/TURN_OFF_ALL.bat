@echo off
REM ==========================================================================
REM  TURN_OFF_ALL.bat      S259 -- 14-Sep-2026   RUNS ON THE MEDICAL PC
REM  Switches OFF the SENDING of captured Marg exports to the clinic server.
REM  CAPTURE KEEPS RUNNING - see D:\SendToClinic\_off\READ_ME.txt for why.
REM ==========================================================================
setlocal
set OFFDIR=D:\SendToClinic\_off
if not exist "%OFFDIR%" mkdir "%OFFDIR%"
echo switched off %DATE% %TIME%> "%OFFDIR%\ALL_OFF.txt"
echo.
echo  SENDING SWITCHED OFF - within about a minute.
echo.
echo  Capture is STILL RUNNING. Every Marg export is still copied out of
echo  Marg's way the instant it appears, and waits in _captured. When you
echo  switch sending back on, everything waiting goes at once.
echo.
echo  To stop capture as well - only if you mean to - put a file called
echo     MARG_WATCH_OFF.txt
echo  in %OFFDIR%
echo.
echo  To switch sending back on, double-click:
echo     D:\SendToClinic\TURN_ON_ALL.bat
echo.
pause
exit /b 0
