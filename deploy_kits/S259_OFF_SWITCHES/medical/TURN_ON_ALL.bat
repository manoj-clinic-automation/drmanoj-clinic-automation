@echo off
REM ==========================================================================
REM  TURN_ON_ALL.bat       S259 -- 14-Sep-2026   RUNS ON THE MEDICAL PC
REM  Removes every OFF marker in D:\SendToClinic\_off\, including the one
REM  that stops capture. Nothing is restarted - the jobs read the folder as
REM  they come round, and the pusher comes round every 60 seconds.
REM ==========================================================================
setlocal
set OFFDIR=D:\SendToClinic\_off
if exist "%OFFDIR%\ALL_OFF.txt" del /q "%OFFDIR%\ALL_OFF.txt"
if exist "%OFFDIR%\MARG_PUSH_OFF.txt" del /q "%OFFDIR%\MARG_PUSH_OFF.txt"
if exist "%OFFDIR%\MARG_WATCH_OFF.txt" del /q "%OFFDIR%\MARG_WATCH_OFF.txt"
echo.
echo  SWITCHED ON. Sending resumes within about a minute, and everything
echo  waiting in _captured goes then - nothing was lost.
echo.
pause
exit /b 0
