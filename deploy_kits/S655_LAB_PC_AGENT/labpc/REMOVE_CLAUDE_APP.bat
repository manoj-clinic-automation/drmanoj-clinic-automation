@echo off
setlocal
REM ======================================================================
REM  REMOVE_CLAUDE_APP.bat  --  S655.  Run ON THE LAB PC, ONLY AFTER the lab
REM  agent has reported to the server (the owner says so).  Removes the Claude
REM  desktop app for this Windows user. The agent does not need it: Claude
REM  reaches this PC through signed jobs (the Drive door and the server door).
REM  It does NOT sign Chrome out -- that is two clicks for the owner: Chrome >
REM  the profile picture (top right) > "Sign out".
REM ======================================================================
title Remove the Claude app from the lab PC (S655)
echo REMOVE_CLAUDE_APP S655   %DATE% %TIME%   user %USERNAME% on %COMPUTERNAME%
echo.
if not exist "C:\ClinicLabAgent\heartbeat.txt" (
  echo   STOP: C:\ClinicLabAgent\heartbeat.txt is not there - the lab agent is not installed yet.
  echo   Install the agent first ^(INSTALL_LAB_AGENT.bat^). Nothing removed.
  goto :end
)
findstr /c:"direct upload on | last accepted 20" "C:\ClinicLabAgent\heartbeat.txt" >nul 2>&1
if errorlevel 1 (
  echo   STOP: the agent's heartbeat does not yet say the server accepted it.
  echo   Wait for the owner's word that the server side is installed. Nothing removed.
  goto :end
)
echo   the agent reports to the server - the Claude app may go.
taskkill /IM claude.exe /F >nul 2>&1
echo   1. Claude closed ^(if it was open^)
powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -Command "$p = Get-AppxPackage -Name '*Claude*' -ErrorAction SilentlyContinue; if ($p) { $p | Remove-AppxPackage -ErrorAction SilentlyContinue; Write-Output '  2. Store app removed: ' + ($p.Name -join ', ') } else { Write-Output '  2. no Store app named Claude for this user' }"
set "UN="
for /f "tokens=2,*" %%A in ('reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall" /s /v UninstallString 2^>nul ^| findstr /i "claude"') do set "UN=%%B"
if defined UN (
  echo   3. desktop installer found - removing quietly
  %UN% /S >nul 2>&1
) else echo   3. no per-user desktop installer entry named Claude
tasklist /FI "IMAGENAME eq claude.exe" 2>nul | findstr /i "claude.exe" >nul && echo   NOTE: claude.exe is still running - restart the PC once. || echo   4. claude.exe is not running
echo.
echo   DONE. Now sign Chrome out: Chrome ^> profile picture ^(top right^) ^> Sign out.
echo   The agent keeps running by itself at every logon ^(C:\ClinicLabAgent^).
:end
echo.
pause
endlocal
