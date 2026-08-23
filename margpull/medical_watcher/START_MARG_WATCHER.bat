@echo off
REM ============================================================================
REM  START_MARG_WATCHER.bat  (S195)  -- runs ON THE MEDICAL PC.
REM
REM  Starts marg_watch.py RESIDENT: event-driven capture of every Marg export
REM  the moment it is written, into D:\SendToClinic\_captured -- BEFORE Marg
REM  can overwrite the slot (REPORT_1.XLS etc.) with the next report.
REM  Capture only; classification/naming stays on manojz, which sweeps the
REM  _captured folder every 10 minutes.
REM
REM  Safe: reads D:\MARGERP only, never writes inside it. Dedup by content.
REM ============================================================================
setlocal
cd /d "%~dp0"
set "PY="
where pythonw >nul 2>&1 && set "PY=pythonw"
if not defined PY where python >nul 2>&1 && set "PY=python"
if not defined PY ( py -3 -c "1" >nul 2>&1 && set "PY=py -3" )
if not defined PY ( echo Python not found - tell Cowork. & pause & exit /b 1 )

if not exist "D:\SendToClinic\_captured" mkdir "D:\SendToClinic\_captured"
start "MargWatcher" /min %PY% "%~dp0marg_watch.py" ^
  --watch "D:\MARGERP\users" --spool "D:\SendToClinic\_captured"
echo  Marg watcher started (minimised). Exports are now captured the moment
echo  Marg writes them - overwriting a slot can no longer lose a report.
exit /b 0
