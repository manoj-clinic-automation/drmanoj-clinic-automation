@echo off
setlocal
REM ===========================================================================
REM  PULL_FROM_MEDICAL.bat  (S195)  --  runs on MANOJZ.
REM
REM  Copies every Marg report off the medical PC onto THIS machine, identifies
REM  each one BY CONTENT, renames it by the business date inside it, and files
REM  it in D:\MargArchive. Also picks up anything the medical PC parked in
REM  NEEDS_UPLOAD (a report whose send to the clinic server failed).
REM
REM  WHY: on 21-08-2026 a report sat unsent on the medical PC and nobody could
REM  see it from here. With this running, every export exists on manojz within
REM  minutes -- a second copy, and one that can actually be looked at.
REM
REM  Uses UNC paths, so it does NOT depend on the Z: drive mapping (which only
REM  exists inside the normal login session). Read-only on the medical PC.
REM
REM  ARCHIVE lives under margsync for now so Cowork can read it directly while
REM  we settle in. Move it into the Drive-synced folder whenever you like --
REM  change the one ARCHIVE line below.
REM
REM  Task Scheduler: run every 10 minutes. "Run whether user is logged on or
REM  not" works, because UNC needs no mapped drive -- but the stored credential
REM  for the medical share must be available to that account.
REM ===========================================================================
set "HERE=%~dp0"
set "MEDICAL=\\100.119.151.40\DDrive"
set "ARCHIVE=D:\Downloads\margsync\MargArchive"
set "SPOOL=%ARCHIVE%\_spool"
set "MIRROR=D:\Downloads\margsync\medical_SendToClinic"
set "DRIVE=H:\My Drive\Clinic Data Archive"

set "PY="
if exist "%HERE%pyportable\python.exe" set "PY=%HERE%pyportable\python.exe"
if not defined PY ( py -c "import sys" >nul 2>&1 && set "PY=py" )
if not defined PY ( python -c "import sys" >nul 2>&1 && set "PY=python" )
if not defined PY (
  echo  PROBLEM: no working Python on this PC. Install Python 3, then re-run.
  pause & exit /b 1
)

if not exist "%MEDICAL%\MARGERP\users" (
  echo.
  echo  Cannot reach the medical PC at %MEDICAL%
  echo  Is it switched on and Tailscale connected?
  echo.
  if /i not "%~1"=="AUTO" pause
  exit /b 1
)

echo  Pulling Marg reports from the medical PC...
"%PY%" "%HERE%marg_watch.py" --once --route ^
   --watch "%MEDICAL%\MARGERP\users" "%MEDICAL%\SendToClinic\Sent" "%MEDICAL%\SendToClinic\NEEDS_UPLOAD" ^
   --spool "%SPOOL%" --archive "%ARCHIVE%" --outbox "%ARCHIVE%\_outbox"

REM ---- mirror the medical PC's working folder, so its LOGS are readable ----
REM  On 21-08-2026 a send failed with HTTP 401 and the only record of why was
REM  last_response.txt sitting on the medical PC, where nobody could read it
REM  without walking to the machine. This mirrors the operational files -- the
REM  logs, the alerts, the scripts, NEEDS_UPLOAD -- so the evidence is always
REM  on this machine too.
REM  NOT mirrored: token.txt (a secret stays on one machine), Sent\ and the
REM  reports (already archived by content above), pyportable and .zip bulk.
echo.
echo  Mirroring the medical SendToClinic folder ^(logs, alerts, config^)...
robocopy "%MEDICAL%\SendToClinic" "%MIRROR%" /E /R:1 /W:2 /NP /NDL /NJH /NJS /NC /NS ^
   /XD Sent pyportable __pycache__ _old 01_MEDICAL_PC ^
   /XF token.txt *.zip
if errorlevel 8 (echo    mirror had a problem ^(code %errorlevel%^)) else (echo    mirrored to %MIRROR%)

REM ---- offsite: mirror the archive to Google Drive -------------------------
REM  Third copy, failing differently from the other two: medical PC is the
REM  origin, margsync is the working copy, Drive survives losing both machines.
REM  H: is the clinic account (drmka.ortho). Skipped silently if Drive for
REM  Desktop is not running, so a laptop with no Drive never breaks the pull.
REM  _spool and _outbox are deliberately NOT synced -- transient, not records.
echo.
if exist "H:\My Drive\" (
  echo  Mirroring the archive to Google Drive ^(offsite^)...
  robocopy "%ARCHIVE%" "%DRIVE%\MargArchive" /E /R:1 /W:2 /NP /NDL /NJH /NJS /NC /NS /XD _spool _outbox
  if errorlevel 8 (echo    Drive mirror had a problem ^(code %errorlevel%^)) else (echo    offsite copy up to date: %DRIVE%\MargArchive)
) else (
  echo  NOTE: Google Drive ^(H:^) not available - offsite copy skipped this run.
)

REM ---- S195: ToMedical (Drive -> medical). Drop a file in the Drive folder
REM      "Clinic Data Archive\ToMedical" and it lands on the medical PC at
REM      D:\SendToClinic\FROM_CLINIC within one 10-minute cycle. Copies only;
REM      the README is not carried. Failure here never blocks the pull above.
if exist "%DRIVE%\ToMedical\" (
  robocopy "%DRIVE%\ToMedical" "%MEDICAL%\SendToClinic\FROM_CLINIC" /E /R:1 /W:2 /NP /NDL /NJH /NJS /NC /NS /XF "READ ME*"
  if errorlevel 8 (echo    ToMedical delivery had a problem) else (echo    ToMedical: delivered to the medical PC)
)

echo.
if exist "%MEDICAL%\SendToClinic\NEEDS_UPLOAD\NEEDS_UPLOAD.txt" (
  echo  ==========================================================
  echo   ATTENTION: the medical PC has report^(s^) that FAILED to send.
  echo   They are now copied here and listed in:
  echo     %MEDICAL%\SendToClinic\NEEDS_UPLOAD\NEEDS_UPLOAD.txt
  echo   Upload them from the Hub in your browser.
  echo  ==========================================================
)
if /i not "%~1"=="AUTO" pause
exit /b 0
