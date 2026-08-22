@echo off
setlocal enabledelayedexpansion
REM ===========================================================================
REM  PUBLISH_CLOSE.bat  v4  -  publishes the SESSION CLOSE-OUT.
REM
REM  F-115: PUSH.bat stages only its own kit folder, so it can never publish
REM  deploy_kits\KB_canon_all -- that folder is not a kit and has no PUSH.bat.
REM
REM  THE GATE (v3, F-121 properly fixed). v1 and v2 both asked a PROXIMITY
REM  question -- "is anything .gitignore'd sitting near what I staged?" -- and
REM  both refused over junk that was never payload. The real question is a
REM  CONTENT one:
REM      does git track every file the payload's own checksum list names?
REM  SUMS.md5 (kits) and MD5SUMS_ALL.txt (the canon set) ARE that list. A
REM  folder counts as payload only if it carries KIT_ID.txt.
REM
REM  v4: publishes correctly when the commit ALREADY EXISTS but was never
REM  pushed. Claude can commit over the device bridge but cannot reach GitHub
REM  from there (403 from proxy), so that state is normal now -- and v3 would
REM  have said "nothing to publish" and left the commit stranded on this PC.
REM
REM  Paste this file's full path into the Explorer address bar, press Enter.
REM ===========================================================================
set REPO_DIR=D:\dr-manoj-git\drmanoj-clinic-automation
if not exist "%REPO_DIR%\.git" ( echo !! repo not found at %REPO_DIR% & pause & exit /b 1 )

set GIT=
where git >nul 2>&1 && set GIT=git
if not defined GIT if exist "C:\Program Files\Git\cmd\git.exe" set GIT="C:\Program Files\Git\cmd\git.exe"
if not defined GIT if exist "C:\Program Files (x86)\Git\cmd\git.exe" set GIT="C:\Program Files (x86)\Git\cmd\git.exe"
if not defined GIT for /d %%D in ("%LOCALAPPDATA%\GitHubDesktop\app-*") do if exist "%%D\resources\app\git\cmd\git.exe" set GIT="%%D\resources\app\git\cmd\git.exe"
if not defined GIT ( echo !! git.exe not found - use GitHub Desktop instead & pause & exit /b 1 )
set GITNP=%GIT% --no-pager

cd /d "%REPO_DIR%"

REM ---- stale git lock sweep (S195) -----------------------------------------
REM  A lock only means something while a git process is actually running. Left
REM  behind by a crash -- or by a sandbox that cannot delete files -- it killed
REM  every later publish and needed a hand fix each time. No git running + a
REM  lock present = stale, cleared here and said out loud. Git running = real.
set LOCKFOUND=
if exist ".git\index.lock" set LOCKFOUND=1
if exist ".git\HEAD.lock" set LOCKFOUND=1
if exist ".git\config.lock" set LOCKFOUND=1
if not defined LOCKFOUND goto :locks_clear

tasklist /fi "IMAGENAME eq git.exe" 2>nul | find /i "git.exe" >nul
if not errorlevel 1 goto :git_running

echo    stale git lock found, and no git process is running - clearing it.
if exist ".git\index.lock" del /f /q ".git\index.lock"
if exist ".git\HEAD.lock" del /f /q ".git\HEAD.lock"
if exist ".git\config.lock" del /f /q ".git\config.lock"
set LOCKFOUND=
if exist ".git\index.lock" set LOCKFOUND=1
if exist ".git\HEAD.lock" set LOCKFOUND=1
if defined LOCKFOUND goto :lock_stuck
goto :locks_clear

:lock_stuck
echo !! the lock could not be removed - something still holds it.
echo    Close GitHub Desktop / editors and run this again. NOTHING published.
pause & exit /b 1

:git_running
echo !! a git lock exists AND a git process is running.
echo    Close GitHub Desktop / any editor doing git, wait, then run this again.
echo    NOTHING published.
pause & exit /b 1

:locks_clear

echo Staging deploy_kits ...
%GITNP% add deploy_kits >nul 2>&1 || ( echo !! git add FAILED & pause & exit /b 1 )

set STAGED=1
%GITNP% diff --cached --quiet && set STAGED=0
if "%STAGED%"=="0" (
  echo    nothing new staged - checking for a commit that was made but never pushed
  goto PUSHSTEP
)

echo.
echo ---- what will be published ----
%GITNP% diff --cached --name-status
echo --------------------------------
echo.

set TRACKED=%TEMP%\pc_tracked.txt
%GITNP% ls-files > "%TRACKED%"

echo Payload check: every name in a payload folder's own checksum list must be tracked by git.
set DROPPED=
for /f "tokens=1,2 delims=/" %%A in ('%GITNP% diff --cached --name-only -- deploy_kits') do (
  if not defined SEEN_%%B (
    set SEEN_%%B=1
    set LIST=
    if exist "deploy_kits\%%B\KIT_ID.txt" (
      if exist "deploy_kits\%%B\SUMS.md5"        set LIST=deploy_kits\%%B\SUMS.md5
      if exist "deploy_kits\%%B\MD5SUMS_ALL.txt" set LIST=deploy_kits\%%B\MD5SUMS_ALL.txt
    )
    if defined LIST (
      set COUNT=0
      for /f "usebackq tokens=1,2" %%H in ("!LIST!") do (
        set /a COUNT+=1
        findstr /x /c:"deploy_kits/%%B/%%I" "%TRACKED%" >nul || (
          echo    !! NOT TRACKED BY GIT, but listed in !LIST!: %%I
          set DROPPED=1
        )
      )
      echo    deploy_kits/%%B  -  !COUNT! listed files, all tracked
    ) else (
      echo    deploy_kits/%%B  -  not a payload folder ^(no KIT_ID.txt^), skipped
    )
  )
)
if defined DROPPED (
  echo.
  echo !! REFUSING TO COMMIT - a file the payload's own checksum list names is
  echo    not tracked by git. That is the F-100 fault: the kit would fail SUMS
  echo    at the VPS console later. Nothing committed, nothing pushed.
  pause & exit /b 1
)
echo    payload complete - OK
echo.

echo INFO only - files .gitignore excludes under the staged folders ^(these do NOT block^):
for /f "tokens=1,2 delims=/" %%A in ('%GITNP% diff --cached --name-only -- deploy_kits') do (
  if not defined INFO_%%B (
    set INFO_%%B=1
    for /f "delims=" %%F in ('%GITNP% ls-files --others --ignored --exclude-standard -- deploy_kits/%%B') do echo      ignored: %%F
  )
)
echo.

%GITNP% commit -m "session close-out: canonical set + pending kits" || echo (nothing new to commit - continuing)

:PUSHSTEP
%GITNP% fetch -q origin >nul 2>&1
set AHEAD=0
for /f %%A in ('%GITNP% rev-list --count origin/main..HEAD 2^>nul') do set AHEAD=%%A
echo.
if "!AHEAD!"=="0" (
  echo Nothing to push - this PC and GitHub are already the same commit.
  %GITNP% log --oneline -1
  %GITNP% status -sb
  echo.
  pause & exit /b 0
)
echo Pushing !AHEAD! commit^(s^) ...
%GITNP% push || ( echo !! git push FAILED - NOT published & pause & exit /b 1 )

for /f "delims=" %%A in ('%GITNP% rev-parse HEAD') do set L=%%A
for /f "delims=" %%B in ('%GITNP% rev-parse origin/main') do set R=%%B
echo.
if "!L!"=="!R!" (
  echo ---- GREEN: your PC and GitHub are the same commit
  echo      !L!
) else (
  echo ---- RED: PC     !L!
  echo          GitHub !R!   - NOT published
)
echo.
%GITNP% log --oneline -2
%GITNP% status -sb
echo.
pause
