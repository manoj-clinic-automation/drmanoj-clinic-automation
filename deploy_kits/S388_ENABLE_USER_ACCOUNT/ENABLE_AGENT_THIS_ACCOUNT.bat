@echo off
REM S388 -- run ONCE in a Windows account that has no administrator rights (the staff account "user").
REM Puts the medical agent's starter (D:\SendToClinic\START_AGENT.cmd, placed by S387) in THIS account's
REM start-up folder, checks this account can write where the agent works, starts it now, shows what it says.
setlocal
set "SRC=D:\SendToClinic\START_AGENT.cmd"
set "DST=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\MargAgent.cmd"
echo S388 -- the medical agent, for the account %USERNAME%
echo.
if not exist "%SRC%" goto nosrc
echo probe> "D:\SendToClinic\_write_probe_%USERNAME%.txt" 2>nul
if not exist "D:\SendToClinic\_write_probe_%USERNAME%.txt" goto nowrite
del "D:\SendToClinic\_write_probe_%USERNAME%.txt" >nul 2>&1
echo   1  this account can write in D:\SendToClinic
if exist "%DST%" copy /y "%DST%" "%DST%.replaced_S388.bak" >nul
copy /y "%SRC%" "%DST%" >nul
fc /b "%SRC%" "%DST%" >nul
if errorlevel 1 goto nocopy
echo   2  this account now starts the agent at every sign-in:
echo      %DST%
call "%SRC%"
echo   3  starting it now (20 seconds)...
timeout /t 20 /nobreak >nul
echo      What it says:
powershell -NoProfile -Command "Get-Content -Path 'D:\SendToClinic\agent_guard.log' -Tail 4"
echo.
echo   DONE for %USERNAME%. Signing either account out no longer stops the agent.
echo.
pause
exit /b 0
:nosrc
echo   STOPPED: %SRC% is missing. Nothing was changed. Tell Claude.
pause
exit /b 1
:nowrite
echo   STOPPED: this account cannot write in D:\SendToClinic, so the agent could not run here.
echo   Nothing was changed. Tell Claude.
pause
exit /b 1
:nocopy
echo   STOPPED: could not put the starter in this account's start-up folder. Tell Claude.
pause
exit /b 1
