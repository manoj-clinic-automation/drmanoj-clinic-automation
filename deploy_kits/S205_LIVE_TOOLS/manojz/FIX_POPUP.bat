@echo off
setlocal
REM ===========================================================================
REM  FIX_POPUP.bat  --  S201.  Stops the console window that appears every
REM  ten minutes on THIS PC (manojz).
REM
REM  The scheduled task "Marg pull from medical" calls the pull batch directly,
REM  so Windows shows its console. This repoints the task at a tiny VBS
REM  launcher that runs the same batch hidden. Nothing else changes.
REM
REM  Right-click this file -> "Run as administrator" if it reports Access
REM  Denied. Reversible: the old command is printed before it is changed.
REM ===========================================================================
set "TASK=Marg pull from medical"
set "VBS=%~dp0PULL_HIDDEN.vbs"
echo.
echo  ==========================================================
echo   STOPPING THE 10-MINUTE POPUP
echo  ==========================================================
echo.
if not exist "%VBS%" ( echo   STOP: PULL_HIDDEN.vbs not found beside this file. & pause & exit /b 1 )

echo   the task as it is now:
schtasks /Query /TN "%TASK%" /FO LIST /V 2>nul | findstr /i "TaskName Task To Run Status" 
if errorlevel 1 (
  echo.
  echo   Could not find a task called "%TASK%".
  echo   Run this to see the real name, then tell Cowork:
  echo       schtasks /Query /FO TABLE ^| findstr /i marg
  echo.
  pause & exit /b 1
)
echo.
echo   changing it to run hidden...
schtasks /Change /TN "%TASK%" /TR "wscript.exe \"%VBS%\""
if errorlevel 1 (
  echo.
  echo   ACCESS DENIED - right-click this file and "Run as administrator".
  echo.
  pause & exit /b 1
)
echo.
echo   the task now:
schtasks /Query /TN "%TASK%" /FO LIST /V 2>nul | findstr /i "Task To Run"
echo.
echo  ==========================================================
echo   DONE. No window should appear from now on.
echo   The pull still runs every 10 minutes and still writes
echo   MargPull\_last_pull.txt - check that to prove it is alive.
echo  ==========================================================
echo.
pause
