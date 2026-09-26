@echo off
REM NIGHTLY.bat  (S272, + S275, + S278, + S415)  -- what the 03:10 task runs, and the morning task (argument: morning).
REM   0. unattended_pull.py   (S278, new)        -- the 02:05 cloud run's reports, from Drive into ClaudeCowork
REM   1. REBUILD_MANIFEST.bat   (S268, unchanged)  -- the manifest and the paper shelf
REM   2. MAINTENANCE.bat        (S272, unchanged)  -- VPS code in reach, SSD mirror, counts
REM   3. CANON_SUMS.bat         (S275, new)        -- the canon gate covers every canon file
REM The manifest is rebuilt FIRST so that the mirror taken in step 2 contains it.
REM Step 3 is last because it may rewrite MD5SUMS_ALL.txt, and that change should
REM ride the next PUBLISH_ALL rather than a mirror taken the same minute.
setlocal
set TOOLS=%~dp0
set WORST=0

REM  --- S415 (F-630): started by the MORNING task (07:30 or at log-on)?  Then run only if the
REM  03:10 run did not happen today.  nightly_guard.py answers: exit 3 = already ran, stop here.
if /I "%~1"=="morning" (
  python "%TOOLS%nightly_guard.py"
  if errorlevel 3 exit /b 0
)

REM  --- S278: step 0 -- copy the unattended run's reports from Drive, so that
REM  step 1 gives them MANIFEST.md5 rows and step 2 mirrors them to the SSD.
REM  Copies only; never deletes or overwrites.  A WARN here never stops the rest.
python "%TOOLS%unattended_pull.py" --tools "%TOOLS:~0,-1%"
set RC0=%ERRORLEVEL%
if %RC0% GTR %WORST% set WORST=%RC0%

call "%TOOLS%REBUILD_MANIFEST.bat"
set RC1=%ERRORLEVEL%
if %RC1% GTR %WORST% set WORST=%RC1%

call "%TOOLS%MAINTENANCE.bat"
set RC2=%ERRORLEVEL%
if %RC2% GTR %WORST% set WORST=%RC2%

call "%TOOLS%CANON_SUMS.bat"
set RC3=%ERRORLEVEL%
if %RC3% GTR %WORST% set WORST=%RC3%

REM  --- S415 (F-630): the task self-heal.  Keeps the catch-up flags (S258), adds wake-to-run, keeps the
REM  07:30 / log-on morning task in place, and writes reports\TASK_HISTORY_LATEST.txt (the tasks' own
REM  history and the PC's sleep / wake / boot events) so a missed night can be explained, not guessed.
REM  Failure here never fails the nightly.
powershell -NoProfile -ExecutionPolicy Bypass -File "%TOOLS%task_selfheal.ps1" 2>&1

echo.
echo ============================================================
echo  NIGHTLY done.  unattended rc=%RC0%   manifest rc=%RC1%   maintenance rc=%RC2%   canon rc=%RC3%
echo  %TOOLS%UNATTENDED_PULL_LATEST.txt
echo  %TOOLS%REBUILD_REPORT_LATEST.txt
echo  %TOOLS%MAINTENANCE_REPORT_LATEST.txt
echo  %TOOLS%CANON_SUMS_LATEST.txt
echo ============================================================
exit /b %WORST%
