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

REM ---- S201: do not sit on screen for 15 seconds every 10 minutes ----------
REM  Task Scheduler launches this batch with a console. Nothing here needs to
REM  be seen. So on an AUTO run we hand the work to a hidden copy of ourselves
REM  and exit immediately -- the console still appears, but for a blink rather
REM  than the whole run.
REM
REM  We also try ONCE to repoint the scheduled task straight at the hidden
REM  launcher, which removes even the blink. That can fail (the task may store
REM  credentials, and schtasks then wants the password) -- so stdin is closed
REM  with "< nul", which makes it fail instantly instead of hanging a hidden
REM  process forever waiting for input nobody can see. It is attempted once and
REM  never again, success or not.
if /i "%~1"=="AUTO" if /i not "%~2"=="HIDDEN" (
  if not exist "%HERE%_task_repoint_tried.txt" (
    echo %DATE% %TIME%> "%HERE%_task_repoint_tried.txt"
    schtasks /Change /TN "Marg pull from medical" /TR "wscript.exe \"%HERE%PULL_HIDDEN.vbs\"" < nul >> "%HERE%_task_repoint_tried.txt" 2>&1
  )
  start "" wscript.exe "%HERE%PULL_HIDDEN.vbs"
  exit /b 0
)

REM  S201 heartbeat. Without this a dead scheduler and a quiet one look
REM  identical -- which is how the 24-Aug report sat unsent for a day.
set "HB=%HERE%_last_pull.txt"
REM  Redirect written FIRST: %TIME% ends in a digit, and a digit
REM  immediately before ">" is read by cmd as a stream number.
>"%HB%" echo START %DATE% %TIME%
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
  echo END %DATE% %TIME% -- FAILED: no python>> "%HB%"
  REM S202: was an UNGUARDED pause -- under the scheduled task (AUTO) it
  REM would wait for a keypress that never comes and hold the cycle forever.
  if /i not "%~1"=="AUTO" pause
  exit /b 1
)

if not exist "%MEDICAL%\MARGERP\users" (
  echo.
  echo  Cannot reach the medical PC at %MEDICAL%
  echo  Is it switched on and Tailscale connected?
  echo.
  echo END %DATE% %TIME% -- FAILED: medical PC unreachable>> "%HB%"
  if /i not "%~1"=="AUTO" pause
  REM B2 FIX (S202): report the FAILURE too. The first wiring put this call
  REM on the SUCCESS path only, so the monitor could only ever report
  REM success -- born dead, which is AF-2's own shape.
  call :report
  exit /b 1
)

echo  Pulling Marg reports from the medical PC...
"%PY%" "%HERE%marg_watch.py" --once --route ^
   --watch "%MEDICAL%\MARGERP\users" "%MEDICAL%\SendToClinic\Sent" "%MEDICAL%\SendToClinic\NEEDS_UPLOAD" "%MEDICAL%\SendToClinic\_captured" ^
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

echo.
echo  Mirroring the medical D:\MARG REPORTS folder ^(your manual saves^)...
REM  S195: where Dr Manoj saves Marg reports by hand. Read-only mirror to
REM  margsync (reading medical is allowed); the resident watcher on the
REM  medical PC also captures this folder into the classify/archive pipeline.
if exist "%MEDICAL%\MARG REPORTS" (
  robocopy "%MEDICAL%\MARG REPORTS" "D:\Downloads\margsync\marg_reports_mirror" /E /R:1 /W:2 /NP /NDL /NJH /NJS /NC /NS
  if errorlevel 8 (echo    MARG REPORTS mirror had a problem) else (echo    mirrored MARG REPORTS)
) else ( echo    ^(no D:\MARG REPORTS folder on the medical PC^) )

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

REM ---- S201: if the signature registry changed, re-judge quarantine -------
REM  Adding a signature used to rescue nothing: marg_router blacklists a file
REM  by md5 the moment it is indexed, so every already-quarantined example of
REM  a newly-taught report type stayed frozen until a human remembered to
REM  re-run the rescue. Two purchase reports and eight stock exports sat that
REM  way. This does nothing at all unless signatures.json has actually
REM  changed since the last run.
"%PY%" "%HERE%marg_rescan.py" --if-signatures-changed --apply

REM ---- S201: send anything the clinic server does not have yet -----------
REM  marg_router stamps every VERIFIED sale report "queued for upload" and
REM  copies it to _outbox. Until 25-Aug NOTHING read that folder -- eight
REM  reports sat there and the 24-Aug day never reached the server. This is
REM  the missing consumer. Safe every cycle: a business date already
REM  delivered is skipped, and a send that fails is retried next cycle
REM  rather than being recorded as done.
echo.
echo  Sending any Marg reports the clinic server does not have yet...
"%PY%" "%HERE%marg_gate.py" send
if errorlevel 1 (
  echo.
  echo   NOTE: one or more reports did NOT reach the clinic server.
  echo   They stay queued and will be retried on the next run.
  echo   Details: %ARCHIVE%\_NEEDS_ATTENTION.txt
)

REM ---- S201: refresh the picture and the manual-upload folder --------------
REM  Until now MARG_PICTURE.txt and _UPLOAD_NOW were only refreshed when a
REM  human ran MARG_STATUS.bat. So the surface that says "someone must upload
REM  this by hand" stayed stale exactly when it mattered -- a report that
REM  failed to send was retried silently, but nothing told anyone to step in.
"%PY%" "%HERE%marg_gate.py" status >nul 2>&1

REM ---- S195: ToMedical (Drive -> medical). Drop a file in the Drive folder
REM      "Clinic Data Archive\ToMedical" and it lands on the medical PC at
REM      D:\SendToClinic\FROM_CLINIC within one 10-minute cycle. Copies only;
REM      the README is not carried. Failure here never blocks the pull above.
REM  ToMedical delivery leg DISABLED (S195, 23-Aug): the medical share is
REM  READ-ONLY from manojz -- robocopy to FROM_CLINIC returns ERROR 5
REM  (confirmed by probe 06:50). Delivery TO medical must be a medical-side
REM  PULL, not a manojz push. Left out until that puller exists.

echo.
if exist "%MEDICAL%\SendToClinic\NEEDS_UPLOAD\NEEDS_UPLOAD.txt" (
  echo  ==========================================================
  echo   ATTENTION: the medical PC has report^(s^) that FAILED to send.
  echo   They are now copied here and listed in:
  echo     %MEDICAL%\SendToClinic\NEEDS_UPLOAD\NEEDS_UPLOAD.txt
  echo   Upload them from the Hub in your browser.
  echo  ==========================================================
)
echo END %DATE% %TIME% -- ok>> "%HB%"
REM ---- B2 (S202): tell the clinic server what only THIS machine can see.
REM      outbox drain, pull liveness, medical watcher, offsite lag.
REM      It is a reporter: it can never fail this pull.
call :report

if /i not "%~1"=="AUTO" pause
exit /b 0

REM ---- B2 (S202): ONE reporter, called from every exit path ----------
REM  It posts what only this machine can see. It must never fail the pull,
REM  so it is guarded -- but its OUTPUT is NOT suppressed: a tool that
REM  refuses must be able to say so.
:report
if defined PY "%PY%" "%~dp0pipeline_status.py"
exit /b 0
