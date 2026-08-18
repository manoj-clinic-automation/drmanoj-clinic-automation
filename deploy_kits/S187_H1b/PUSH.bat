@echo off
setlocal enabledelayedexpansion
REM ===========================================================================
REM  PUSH.bat v2  -  the S186 default publish method (D324), hardened S187.
REM
REM  The kit is ALREADY sitting in the repo: Claude writes it straight into
REM  deploy_kits\<KIT>\ over the device bridge. Paste this file's path into
REM  the Explorer address bar and press Enter.
REM
REM  Keeps the F-100 gate (a .gitignore'd kit file refuses the commit).
REM
REM  v2 -- THE F-124 FIX: A FAILED COMMIT IS NOT "NOTHING TO COMMIT".
REM  v1 ran `git commit || echo (nothing new to commit - continuing)`, so a
REM  fatal error (a stale HEAD.lock, in the event) was swallowed, the push
REM  pushed nothing, and the banner said "pushed". v2 (a) distinguishes an
REM  empty commit from a failed one BEFORE committing, and (b) after pushing,
REM  VERIFIES the outcome: local HEAD must equal origin HEAD, or this refuses
REM  to print success. The projection is the check (Runbook section 1.5).
REM ===========================================================================
set REPO_DIR=D:\dr-manoj-git\drmanoj-clinic-automation
for %%I in ("%~dp0.") do set KIT_NAME=%%~nxI

if not exist "%~dp0KIT_ID.txt" ( echo !! %~dp0 has no KIT_ID.txt - not a kit & pause & exit /b 1 )
if not exist "%REPO_DIR%\.git" ( echo !! repo not found at %REPO_DIR% & pause & exit /b 1 )

set GIT=
where git >nul 2>&1 && set GIT=git
if not defined GIT if exist "C:\Program Files\Git\cmd\git.exe" set GIT="C:\Program Files\Git\cmd\git.exe"
if not defined GIT if exist "C:\Program Files (x86)\Git\cmd\git.exe" set GIT="C:\Program Files (x86)\Git\cmd\git.exe"
if not defined GIT for /d %%D in ("%LOCALAPPDATA%\GitHubDesktop\app-*") do if exist "%%D\resources\app\git\cmd\git.exe" set GIT="%%D\resources\app\git\cmd\git.exe"
if not defined GIT ( echo !! git.exe not found - commit deploy_kits\%KIT_NAME% with GitHub Desktop instead & pause & exit /b 1 )

echo Publishing kit %KIT_NAME%
cd /d "%REPO_DIR%"

if exist ".git\HEAD.lock" (
  echo !! .git\HEAD.lock exists - a git process is running, or one crashed.
  echo    Close GitHub Desktop / VS Code / any editor holding this repo,
  echo    confirm no git.exe in Task Manager, then delete or rename the lock
  echo    ^(house style: HEAD.lock.stale_S187^) and run this again.
  echo    NOTHING has been committed or pushed.
  pause & exit /b 1
)

%GIT% add deploy_kits\%KIT_NAME% || ( echo !! git add FAILED & pause & exit /b 1 )

set DROPPED=
for /f "delims=" %%F in ('%GIT% ls-files --others --ignored --exclude-standard -- deploy_kits/%KIT_NAME%') do (
  echo    !! EXCLUDED BY .gitignore: %%F
  set DROPPED=1
)
if defined DROPPED (
  echo.
  echo !! REFUSING TO COMMIT - at least one kit file was silently excluded.
  echo    Nothing has been committed or pushed. Tell Claude which file.
  echo.
  pause & exit /b 1
)
echo    all kit files tracked - OK

REM -- F-124: decide "empty" BEFORE committing, so a failure can only be real
%GIT% diff --cached --quiet
if errorlevel 1 (
  %GIT% commit -m "deploy kit %KIT_NAME% (written direct to repo; gated installer inside)" || (
    echo.
    echo !! git commit FAILED - this is a REAL failure, not an empty commit.
    echo    NOT published. Fix the message above and run this again.
    echo.
    pause & exit /b 1
  )
) else (
  echo    (nothing new to commit - continuing to push/verify)
)

%GIT% push || ( echo !! git push FAILED - NOT published & pause & exit /b 1 )

REM -- the projection is the check: local HEAD must now equal origin HEAD
set LOCALH=
set REMOTEH=
for /f %%H in ('%GIT% rev-parse HEAD') do set LOCALH=%%H
for /f %%H in ('%GIT% ls-remote origin -q HEAD') do if not defined REMOTEH set REMOTEH=%%H
if not defined REMOTEH ( echo !! could not read origin HEAD - publication UNVERIFIED & pause & exit /b 1 )
if /i not "%LOCALH%"=="%REMOTEH%" (
  echo !! VERIFY FAILED: local HEAD %LOCALH%
  echo                  origin HEAD %REMOTEH%
  echo    The push did not land. NOT published.
  pause & exit /b 1
)
echo    verified: origin HEAD = local HEAD = %LOCALH%
echo.
echo ---- %KIT_NAME% pushed AND VERIFIED. Now on the VPS run:
echo      bash /root/deploy/vps_deploy.sh %KIT_NAME%
echo.
pause
