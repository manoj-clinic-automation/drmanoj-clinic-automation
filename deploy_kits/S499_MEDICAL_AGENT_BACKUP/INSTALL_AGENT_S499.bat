@echo off
REM ============================================================================
REM  INSTALL_AGENT_S499.bat -- kit S499_MEDICAL_AGENT_BACKUP
REM  DOUBLE-CLICK ON THE MEDICAL PC. Safe to run twice, and again after a run
REM  that was interrupted.
REM
REM  Replaces ONE file, D:\SendToClinic\medical_agent.py, S205.1 to S499.1,
REM  and nothing else. All the work is in install_s499.py beside this file,
REM  run with this PC's own python: pins, backup, the guard's own switch
REM  D:\SendToClinic\_off\AGENT_OFF.txt on and off again at once, md5 read
REM  back, the old file put back if anything is red, and a result file in
REM  D:\SendToClinic and in Drive's FromMedical folder.
REM
REM  This file kills no process, touches no start-up entry and no scheduled
REM  task. It checks that install_s499.py is the file that was built, runs it,
REM  and keeps the window open.
REM
REM  The old ToMedical\INSTALL_AGENT.bat of 25-Aug-2026 must not be run any
REM  more: that one stops the guard too.
REM ============================================================================
setlocal
title S499 - Marg medical agent update
set "PY=D:\SendToClinic\pyportable\python.exe"
set "HERE=%~dp0"
set "WANT=4c37c400b1898d81ffaaaf0be3f88504"
echo.
echo   S499 - the Marg medical agent on this PC, S205.1 to S499.1
echo   Do this when nobody is exporting from Marg. It takes about two minutes.
echo   Do NOT click inside this window and do NOT close it
echo   until it says DONE or NOT DONE.
echo.
if not exist "%PY%" goto nopy
if not exist "%HERE%install_s499.py" goto nokit
if not exist "%HERE%medical_agent.py" goto nokit
"%PY%" -I -B -c "pass" >nul 2>nul
if errorlevel 1 goto nostart
set "GOT="
for /f "skip=1 tokens=* delims=" %%A in ('certutil -hashfile "%HERE%install_s499.py" MD5') do if not defined GOT set "GOT=%%A"
if not defined GOT goto nohash
set "GOT=%GOT: =%"
if /i not "%GOT%"=="%WANT%" goto badkit
"%PY%" -I -B "%HERE%install_s499.py"
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" goto ok
if exist "D:\SendToClinic\_off\AGENT_OFF.txt" goto stilloff
echo   NOT DONE - read the lines above. Nothing is left switched off.
echo.
pause
exit /b %RC%

:stilloff
echo   NOT DONE - and WARNING: the agent is still switched off.
echo   D:\SendToClinic\_off\AGENT_OFF.txt is there. Double-click this file again.
echo.
pause
exit /b %RC%

:ok
if exist "D:\SendToClinic\_off\AGENT_OFF.txt" goto okoff
pause
exit /b 0

:okoff
echo   WARNING: D:\SendToClinic\_off\AGENT_OFF.txt is there - the agent is switched off.
echo   If nobody switched it off on purpose, double-click this file again.
echo.
pause
exit /b 0

:nopy
echo   FAIL: python is not at %PY%
echo   Nothing was changed. Tell Claude.
echo.
pause
exit /b 1

:nostart
echo   FAIL: python at %PY% could not be started.
echo   Nothing was changed. Tell Claude.
echo.
pause
exit /b 1

:nokit
echo   FAIL: install_s499.py or medical_agent.py is not beside this file.
echo   Is Google Drive still downloading the folder? Wait a minute, run again.
echo   Nothing was changed.
echo.
pause
exit /b 1

:nohash
echo   FAIL: this PC could not work out the md5 of install_s499.py.
echo   Nothing was changed. Tell Claude.
echo.
pause
exit /b 1

:badkit
echo   FAIL: install_s499.py is not the file that was built.
echo   It reads %GOT%
echo   It should read %WANT%
echo   Is Google Drive still downloading it? Wait a minute, run again.
echo   Nothing was changed.
echo.
pause
exit /b 1
