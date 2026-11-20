@echo off
REM ============================================================================
REM  SETUP_NETWATCH_S893.bat -- kit S893_MEDICAL_NET_WATCH (session 490, 20-Nov-2026)
REM  DOUBLE-CLICK ON THE MEDICAL PC, in the owner's own (administrator) login.
REM  Copies the kit to D:\SendToClinic\_s893, asks Windows for administrator
REM  rights (press YES), checks setup_s893.py is the file that was built, runs it.
REM  Safe to run twice.
REM ============================================================================
setlocal
title S893 - medical PC internet watchdog
set "PY=D:\SendToClinic\pyportable\python.exe"
set "KIT=D:\SendToClinic\_s893"
set "WANT=2589ce8f8d03c79e4eabdde50c436e53"
set "ME=SETUP_NETWATCH_S893.bat"
if not exist "%PY%" goto nopy
if /i "%~dp0"=="%KIT%\" goto here
if not exist "%KIT%" mkdir "%KIT%"
copy /y "%~dp0setup_s893.py" "%KIT%\setup_s893.py" >nul
copy /y "%~dp0netwatch.py" "%KIT%\netwatch.py" >nul
copy /y "%~f0" "%KIT%\%ME%" >nul
if not exist "%KIT%\setup_s893.py" goto nocopy
if not exist "%KIT%\%ME%" goto nocopy
:here
fltmc >nul 2>&1
if not errorlevel 1 goto admin
if /i "%~1"=="ELEVATED" goto noadmin
goto elevate
:admin
cd /d "%KIT%"
set "GOT="
for /f "skip=1 tokens=* delims=" %%A in ('certutil -hashfile "%KIT%\setup_s893.py" MD5') do if not defined GOT set "GOT=%%A"
if not defined GOT goto badkit
set "GOT=%GOT: =%"
if /i not "%GOT%"=="%WANT%" goto badkit
"%PY%" -I -B "%KIT%\setup_s893.py" 
exit /b %ERRORLEVEL%

:elevate
echo.
echo   S893 - the internet watchdog for this PC is being set up.
echo   Windows now asks "Do you want to allow this app to make changes?" -- press YES.
echo   A second window opens and does the work (about 3 minutes). Your remote
echo   screen may blink once when the network adapters' power setting changes.
powershell -NoProfile -Command "Start-Process -FilePath '%KIT%\%ME%' -ArgumentList 'ELEVATED' -Verb RunAs"
echo.
echo   This window closes by itself.
timeout /t 20 >nul
exit /b 0

:noadmin
echo   NOT DONE: Windows did not give administrator rights. Nothing was changed.
echo   Run it from your own login and press YES when Windows asks.
pause
exit /b 1
:nopy
echo   NOT DONE: %PY% is missing on this PC. Nothing was changed. Tell Claude.
pause
exit /b 1
:nocopy
echo   NOT DONE: could not copy the kit to %KIT%. Nothing was changed. Tell Claude.
pause
exit /b 1
:badkit
echo   NOT DONE: setup_s893.py is not the file that was built. Nothing was changed. Tell Claude.
pause
exit /b 1
