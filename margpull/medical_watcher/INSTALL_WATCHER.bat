@echo off
REM ============================================================================
REM  INSTALL_WATCHER.bat  (S195)  -- run ONCE on the MEDICAL PC (double-click).
REM  Installs the resident Marg watcher to start at every logon, and starts it
REM  now. No admin needed (current-user task).
REM ============================================================================
setlocal
cd /d "%~dp0"
schtasks /create /f /tn "Marg export watcher" /sc onlogon ^
  /tr "\"%~dp0START_MARG_WATCHER.bat\"" >nul 2>&1 ^
  && echo  logon task installed: "Marg export watcher" ^
  || echo  !! could not install the logon task - tell Cowork (watcher still starts now)
call "%~dp0START_MARG_WATCHER.bat"
echo.
echo  CONFIRM it works: generate any Marg report, then within ~10 seconds a
echo  copy appears in  D:\SendToClinic\_captured  - that copy is the safe one.
pause
