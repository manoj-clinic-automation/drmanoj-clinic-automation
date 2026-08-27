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
REM ---- S205 (B6): THE ADDRESS, IN ONE PLACE ------------------------------
REM  It used to be typed five times in this file and once more inside
REM  pipeline_status.py. On 26-Aug an eight-hour outage turned on this link and
REM  nobody could say what the link WAS without reading two files. One name,
REM  one place. The durable fix is the Tailscale MagicDNS name rather than a
REM  number -- pipeline_status.py now REPORTS whether the name resolves and
REM  whether it agrees with this number, so the switch can be made on evidence
REM  instead of hope. It is NOT switched here: changing how reports travel is
REM  the owner's call, and D350 build order puts every observer before it.
set "MEDHOST=100.119.151.40"
set "MEDICAL=\\%MEDHOST%\DDrive"
REM ---- S205 (B2): the facts this batch measures and used to throw away ----
REM  It already tests the share, already knows every step's exit code and
REM  already knows which route it took -- and all of it went to a console the
REM  hidden launcher discards. pipeline_status.py reads this file and carries
REM  it to the clinic server, so the half of the chain that happens here stops
REM  being invisible. Plain key=value: quoting JSON inside a batch file is how
REM  a monitor acquires a bug of its own.
set "FACTS=%HERE%_pull_facts.txt"
set "SHARE_SEEN=0"
set "TRANSPORT="
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
if not exist "%HERE%_logs" md "%HERE%_logs" >nul 2>&1
echo %DATE% %TIME%  FAILED: no python>> "%HERE%_logs\pull_early.log"
  REM S202: was an UNGUARDED pause -- under the scheduled task (AUTO) it
  REM would wait for a keypress that never comes and hold the cycle forever.
  if /i not "%~1"=="AUTO" pause
  exit /b 1
)

if not exist "%MEDICAL%\MARGERP\users" (
  echo.
  echo  Cannot reach the medical PC at %MEDICAL%
  call :diagnose
  echo.
  echo END %DATE% %TIME% -- FAILED: medical PC unreachable>> "%HB%"
if not exist "%HERE%_logs" md "%HERE%_logs" >nul 2>&1
echo %DATE% %TIME%  FAILED: medical PC unreachable>> "%HERE%_logs\pull_early.log"
  if /i not "%~1"=="AUTO" pause
  REM B2 FIX (S202): report the FAILURE too. The first wiring put this call
  REM on the SUCCESS path only, so the monitor could only ever report
  REM success -- born dead, which is AF-2's own shape.
  REM S205: and write the facts FIRST, so the reporter carries the failure it
  REM was called to report. SHARE_SEEN is still 0 here, which is the point.
  call :facts
  call :report
  exit /b 1
)

REM  S205: the gate above is a REAL reachability test, performed. Record
REM  that it passed -- on 26-Aug this exact test was failing every ten
REM  minutes and its answer went nowhere.
set "SHARE_SEEN=1"

echo  Pulling Marg reports from the medical PC...
"%PY%" "%HERE%marg_watch.py" --once --route ^
   --watch "%MEDICAL%\MARGERP\users" "%MEDICAL%\SendToClinic\Sent" "%MEDICAL%\SendToClinic\NEEDS_UPLOAD" "%MEDICAL%\SendToClinic\_captured" ^
   --spool "%SPOOL%" --archive "%ARCHIVE%" --outbox "%ARCHIVE%\_outbox"
set "RC_WATCH=%errorlevel%"
REM  S205 (D350 §1/§3): WHICH ROUTE CARRIED THIS CYCLE. There is one today.
REM  Saying so now, before the Drive fallback exists, is deliberate: a
REM  fallback whose switch is wrong fails INVISIBLY, and invisible failure is
REM  the fault the whole contract exists to end. When the reserve route is
REM  built it sets this to "drive", and the clinic server shows warn for as
REM  long as that is true -- a fallback nobody notices becomes the new normal.
set "TRANSPORT=smb"

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
set "RC_RESCAN=%errorlevel%"

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
set "RC_GATE=%errorlevel%"
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
set "RC_STATUS=%errorlevel%"

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
REM ===========================================================================
REM  S203_R2.  This line used to read "-- ok" UNCONDITIONALLY.
REM
REM  It sits on a straight-line path with no error test above it, so capture,
REM  routing, sending and the picture could all have failed and it still said
REM  ok. Worse, pipeline_status.py computes ended_ok as "a line starts with END
REM  and ends with ok" and posts that to the clinic server -- so the server was
REM  told the pipeline was healthy by a word that was always written.
REM  On 26-Aug the feed was dark for 8h40m and this said ok every ten minutes.
REM
REM  The word is now EARNED: every work step's exit code is checked and a
REM  non-zero one names itself. Nothing else had to change -- pipeline_status
REM  stops reporting ok on its own, because the word is simply not there.
REM ===========================================================================
if not defined RC_WATCH  set "RC_WATCH=0"
if not defined RC_RESCAN set "RC_RESCAN=0"
if not defined RC_GATE   set "RC_GATE=0"
if not defined RC_STATUS set "RC_STATUS=0"
set "PROBLEMS="
if not "%RC_WATCH%"=="0"  set "PROBLEMS=%PROBLEMS% capture=%RC_WATCH%"
if not "%RC_RESCAN%"=="0" set "PROBLEMS=%PROBLEMS% rescan=%RC_RESCAN%"
if not "%RC_GATE%"=="0"   set "PROBLEMS=%PROBLEMS% send=%RC_GATE%"
if not "%RC_STATUS%"=="0" set "PROBLEMS=%PROBLEMS% picture=%RC_STATUS%"

REM  A durable outcome log. Until now the pull kept NO history at all -- the
REM  hidden launcher discards every line it prints, and _last_pull.txt holds
REM  only the most recent run. One line per run, one file per month, so a
REM  month of behaviour reads at a glance and sends as one attachment.
set "LOGDIR=%HERE%_logs"
if not exist "%LOGDIR%" md "%LOGDIR%" >nul 2>&1
set "YM="
for /f "tokens=2 delims==" %%T in ('wmic os get localdatetime /value 2^>nul') do if not defined YM set "YM=%%T"
if not defined YM set "YM=000000"
set "PULLLOG=%LOGDIR%\pull_%YM:~0,4%-%YM:~4,2%.log"

if defined PROBLEMS (
  >>"%HB%" echo END %DATE% %TIME% -- PROBLEM:%PROBLEMS%
  >>"%PULLLOG%" echo %DATE% %TIME%  PROBLEM:%PROBLEMS%
  echo.
  echo   ONE OR MORE STEPS FAILED:%PROBLEMS%
  echo   This run is NOT reported as ok, here or to the clinic server.
) else (
  echo END %DATE% %TIME% -- ok>> "%HB%"
  echo %DATE% %TIME%  ok>> "%PULLLOG%"
)
REM ---- B2 (S202): tell the clinic server what only THIS machine can see.
REM      outbox drain, pull liveness, medical watcher, offsite lag.
REM      S205 adds: the link itself -- Tailscale both ends, a PERFORMED share
REM      test, which point is down in words, which transport was used, and
REM      whether a credential exists at all.
REM      It is a reporter: it can never fail this pull.
call :facts
call :report

if /i not "%~1"=="AUTO" pause
exit /b 0

REM ---- S205 (B2): WHAT THIS BATCH MEASURED, WRITTEN DOWN --------------
REM  Called from every exit path, always BEFORE :report, so the reporter
REM  carries this cycle's readings and not the last cycle's. Every line is a
REM  fact this file already had and used to discard.
REM
REM  It writes with > first and >> after, and the redirect is placed BEFORE
REM  the echo on any line ending in a variable that may end in a digit -- a
REM  digit immediately before ">" is read by cmd as a stream number, which is
REM  the same trap the START stamp above already carries a comment about.
:facts
if not defined SHARE_SEEN set "SHARE_SEEN=0"
if not defined FACTS set "FACTS=%~dp0_pull_facts.txt"
>"%FACTS%" echo share_seen=%SHARE_SEEN%
if defined TRANSPORT >>"%FACTS%" echo transport=%TRANSPORT%
>>"%FACTS%" echo fallback=0
>>"%FACTS%" echo host=%MEDHOST%
if defined RC_WATCH  >>"%FACTS%" echo rc_watch=%RC_WATCH%
if defined RC_RESCAN >>"%FACTS%" echo rc_rescan=%RC_RESCAN%
if defined RC_GATE   >>"%FACTS%" echo rc_gate=%RC_GATE%
if defined RC_STATUS >>"%FACTS%" echo rc_status=%RC_STATUS%
>>"%FACTS%" echo at=%DATE% %TIME%
exit /b 0

REM ---- B2 (S202): ONE reporter, called from every exit path ----------
REM  It posts what only this machine can see. It must never fail the pull,
REM  so it is guarded -- but its OUTPUT is NOT suppressed: a tool that
REM  refuses must be able to say so.
:report
if defined PY "%PY%" "%~dp0pipeline_status.py"
exit /b 0

REM ---- S202: SAY WHICH CAUSE, DO NOT LIST THE ONES YOU CANNOT TELL APART
REM  The old message read "Is it switched on and Tailscale connected?".
REM  On 26-Aug BOTH were true -- the PC was on, Tailscale showed it active
REM  and direct -- and the real cause was Windows blocking UNAUTHENTICATED
REM  GUEST ACCESS to the share after a policy refresh. The message named
REM  two innocent causes and not the guilty one, and cost an hour.
REM  A ping separates them: no answer = the machine or the tunnel;
REM  an answer = the machine is fine and the SHARE is refusing us.
:diagnose
ping -n 1 -w 1500 %MEDHOST% >nul 2>&1
if errorlevel 1 (
  echo   The medical PC does not answer at %MEDHOST%.
  echo   Check it is switched ON and that Tailscale is connected on BOTH PCs.
  goto :eof
)
echo   The medical PC ANSWERS - it is on and Tailscale is up.
echo   So the SHARE is refusing us, and that is almost always credentials.
echo.
echo   On THIS PC ^(manojz^), in a Command Prompt, check:
echo       cmdkey /list ^| findstr %MEDHOST%
echo   If nothing is listed, add one ^(it will ask for the password^):
echo       cmdkey /add:%MEDHOST% /user:MEDICAL\SET /pass
echo.
echo   S205: the clinic server is now told all of this by itself -- whether
echo   a credential exists, which Windows account this ran as, and whether
echo   the port answers while the share refuses. Look at the health page
echo   before walking to either machine.
echo.
echo   NOTE: credentials are stored PER WINDOWS USER. If the scheduled
echo   task runs as a different account than the one you added it under,
echo   it will still fail while a manual dir works. Check with:
echo       schtasks /query /tn "Marg pull from medical" /fo list /v ^| findstr /i "Run As User"
goto :eof
