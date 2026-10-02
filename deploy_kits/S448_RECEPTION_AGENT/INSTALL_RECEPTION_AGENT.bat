@echo off
setlocal
REM ======================================================================
REM  INSTALL_RECEPTION_AGENT.bat  --  S448 kit v2.  Run ON THE RECEPTION PC.
REM
REM  Puts the reception agent into C:\ClinicAgent, proves each step, sets it
REM  to start at logon, starts it, and shows its first heartbeat.
REM  Safe to run again: it stops the running agent first, keeps the python
REM  folder if it is already there, and never touches jobs or logs.
REM  It also brings this PC's settings (config.json) and the Drive-door
REM  public keys from the kit when the PC has none, and points Chrome's
REM  download folder at Clinic Records\Docterz exports if Chrome is closed.
REM  What only a person can do is listed in README_REINSTALL.txt.
REM  Everything printed here is also saved beside this file as
REM  install_log.txt, which carries no patient data.
REM ======================================================================
title Install the reception PC agent (S448)
set "KIT=%~dp0"
set "ROOT=C:\ClinicAgent"
set "PY=%ROOT%\pyportable\python.exe"
set "PYW=%ROOT%\pyportable\pythonw.exe"
set "LOGF=%KIT%install_log.txt"
set "OKFLAG=%KIT%_install_ok.flag"
del "%OKFLAG%" >nul 2>&1

call :main > "%LOGF%" 2>&1
type "%LOGF%"
if not exist "%OKFLAG%" goto :end

REM ---- start it OUTSIDE the logged block, so the agent never inherits the
REM      log file's handle
start "" /min "%PYW%" "%ROOT%\agent_guard.py"
echo.
echo   agent started. waiting 30 seconds for its first heartbeat...
ping -n 31 127.0.0.1 >nul
call :after >> "%LOGF%" 2>&1
call :after
:end
echo.
echo   This text is saved in %LOGF%
echo   You can close this window.
endlocal
exit /b 0

REM ======================================================================
:main
echo INSTALL_RECEPTION_AGENT S448   %DATE% %TIME%
echo   kit  : %KIT%
echo   root : %ROOT%
echo   user : %USERNAME% on %COMPUTERNAME%
echo.

REM ---- 1. the kit is whole
if not exist "%KIT%reception_agent.py" set "WHY=reception_agent.py is not beside this file" & goto :stop
if not exist "%KIT%agent_guard.py" set "WHY=agent_guard.py is not beside this file" & goto :stop

REM ---- 2. the folder
if not exist "%ROOT%\" mkdir "%ROOT%"
if not exist "%ROOT%\" set "WHY=could not create %ROOT%" & goto :stop
echo   1. folder    : %ROOT% is there

REM ---- 3. stop a running agent -- only a pid that is really python
if exist "%ROOT%\_guard.pid" for /f "usebackq" %%P in ("%ROOT%\_guard.pid") do call :killpy %%P
if exist "%ROOT%\_agent.pid" for /f "usebackq" %%P in ("%ROOT%\_agent.pid") do call :killpy %%P
ping -n 3 127.0.0.1 >nul
echo   2. stopped   : any earlier agent is stopped

REM ---- 4. python
if exist "%PY%" goto :havepy
if not exist "%KIT%pyportable.zip" set "WHY=pyportable.zip is not beside this file" & goto :stop
tar -xf "%KIT%pyportable.zip" -C "%ROOT%" >nul 2>&1
if exist "%PY%" goto :havepy
powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -LiteralPath '%KIT%pyportable.zip' -DestinationPath '%ROOT%' -Force"
:havepy
if not exist "%PY%" set "WHY=python could not be unpacked into %ROOT%\pyportable" & goto :stop
if not exist "%PYW%" set "WHY=pythonw.exe is missing from %ROOT%\pyportable" & goto :stop
"%PY%" -c "import sys,json,csv,hashlib,subprocess,ctypes,msvcrt;print('  3. python    :',sys.version.split()[0],'runs')"
if errorlevel 1 set "WHY=the unpacked python does not run" & goto :stop

REM ---- 5. the two files, copied and COMPARED
del "%ROOT%\update_pending.json" >nul 2>&1
del "%ROOT%\reception_agent.py.new" >nul 2>&1
REM  an old heartbeat must never be mistaken for the new agent's first one
del "%ROOT%\heartbeat.txt" >nul 2>&1
del "%ROOT%\heartbeat.json" >nul 2>&1
if exist "%ROOT%\reception_agent.py" copy /y "%ROOT%\reception_agent.py" "%ROOT%\reception_agent.py.before_install" >nul
if exist "%ROOT%\agent_guard.py" copy /y "%ROOT%\agent_guard.py" "%ROOT%\agent_guard.py.before_install" >nul
copy /y "%KIT%reception_agent.py" "%ROOT%\reception_agent.py" >nul
copy /y "%KIT%agent_guard.py" "%ROOT%\agent_guard.py" >nul
"%PY%" -c "import hashlib,sys;h=lambda p:hashlib.md5(open(p,'rb').read()).hexdigest();sys.exit(0 if h(sys.argv[1])==h(sys.argv[2]) and h(sys.argv[3])==h(sys.argv[4]) else 1)" "%KIT%reception_agent.py" "%ROOT%\reception_agent.py" "%KIT%agent_guard.py" "%ROOT%\agent_guard.py"
if errorlevel 1 set "WHY=the installed files are not the kit's files" & goto :stop
"%PY%" -c "import hashlib,sys;[print('  4. installed :',hashlib.md5(open(p,'rb').read()).hexdigest(),p) for p in sys.argv[1:]]" "%ROOT%\reception_agent.py" "%ROOT%\agent_guard.py"
"%PY%" -c "import py_compile,sys;[py_compile.compile(p,doraise=True) for p in sys.argv[1:]]" "%ROOT%\reception_agent.py" "%ROOT%\agent_guard.py"
if errorlevel 1 set "WHY=an installed file does not compile" & goto :stop
echo   5. compiled  : both files compile on this PC

REM ---- 6. what the agent can see, before it is started
echo.
echo   ---- self-test (read-only) ----
"%PY%" "%ROOT%\reception_agent.py" --selftest
if errorlevel 1 set "WHY=the self-test failed" & goto :stop
echo   ---- end of self-test ----
echo.

REM ---- 6b. this PC's settings, the Drive-door keys, Chrome's download folder
if exist "%ROOT%\config.json" goto :havecfg
if exist "%KIT%config.json" copy /y "%KIT%config.json" "%ROOT%\config.json" >nul
:havecfg
if exist "%ROOT%\config.json" echo   .. settings  : %ROOT%\config.json is there
if not exist "%ROOT%\config.json" echo   .. settings  : none - the agent's own defaults apply
"%PY%" "%ROOT%\reception_agent.py" --install-keys "%KIT%authorized_keys.txt"
"%PY%" "%ROOT%\reception_agent.py" --set-chrome-download
echo.

REM ---- 7. the shell the .ps1 jobs will run in
powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -Command "Write-Output ('  6. job shell : powershell ' + $PSVersionTable.PSVersion.ToString())"
if errorlevel 1 echo   6. job shell : POWERSHELL DID NOT RUN -- .ps1 jobs will fail, .cmd and .py still work

REM ---- 8. start at logon
set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
if not exist "%STARTUP%\" set "WHY=the Startup folder was not found" & goto :stop
> "%STARTUP%\ClinicAgent.cmd" echo @echo off
>>"%STARTUP%\ClinicAgent.cmd" echo start "" /min "%PYW%" "%ROOT%\agent_guard.py"
if not exist "%STARTUP%\ClinicAgent.cmd" set "WHY=could not write the logon start file" & goto :stop
echo   7. autostart : %STARTUP%\ClinicAgent.cmd
echo ok> "%OKFLAG%"
exit /b 0

:killpy
tasklist /FI "PID eq %1" /FO CSV /NH 2>nul | findstr /i "python" >nul
if errorlevel 1 exit /b 0
taskkill /PID %1 /T /F >nul 2>&1
exit /b 0

:stop
echo.
echo   STOP: %WHY%
echo   Nothing was started. Tell Claude what this window says.
exit /b 1

REM ======================================================================
:after
echo.
echo   ==========================================================
findstr /b /c:"RECEPTION PC AGENT" "%ROOT%\heartbeat.txt" >nul 2>&1
if not errorlevel 1 goto :beat
echo   PROBLEM: the agent wrote no good heartbeat.
if exist "%ROOT%\heartbeat.txt" type "%ROOT%\heartbeat.txt"
if exist "%ROOT%\agent_crash.txt" type "%ROOT%\agent_crash.txt"
if exist "%ROOT%\guard_crash.txt" type "%ROOT%\guard_crash.txt"
if exist "%ROOT%\agent.log" type "%ROOT%\agent.log"
if exist "%ROOT%\guard.log" type "%ROOT%\guard.log"
goto :afterend
:beat
type "%ROOT%\heartbeat.txt"
echo.
echo   ---- guard.log, last lines ----
"%PY%" -c "import sys;print(''.join(open(sys.argv[1],encoding='utf-8',errors='replace').readlines()[-6:]))" "%ROOT%\guard.log"
echo.
echo   DONE. The agent is running and will start by itself at every logon.
:afterend
echo   ==========================================================
exit /b 0
