@echo off
setlocal enabledelayedexpansion
REM ===========================================================================
REM  PUBLISH_CLOSE.bat  v2  -  publishes the SESSION CLOSE-OUT.
REM
REM  F-115: PUSH.bat stages only its own kit folder, so it can never publish
REM  deploy_kits\KB_canon_all (the canonical set) - that folder is not a kit
REM  and has no PUSH.bat of its own.
REM
REM  v2 fix: the .gitignore gate now scans ONLY the folders that actually have
REM  staged changes. v1 scanned the whole deploy_kits tree and tripped on
REM  deliberate historical ignores (.pyc residue in S182 kits, a stray .tsv in
REM  S183) that have nothing to do with the publish. A gate that cries wolf on
REM  old junk is a gate that gets waved through - D316.
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

cd /d "%REPO_DIR%"

if exist ".git\index.lock" (
  echo !! .git\index.lock is present - another git is running, or a run died.
  echo    Close GitHub Desktop, delete that file, then run this again.
  pause & exit /b 1
)

echo Staging deploy_kits ...
%GIT% add deploy_kits >nul 2>&1 || ( echo !! git add FAILED & pause & exit /b 1 )

%GIT% diff --cached --quiet && (
  echo.
  echo Nothing is staged - there is nothing new to publish.
  echo.
  %GIT% status -sb
  pause & exit /b 0
)

echo.
echo ---- what will be published ----
%GIT% diff --cached --name-status
echo --------------------------------
echo.

echo Checking .gitignore did not silently drop anything from THESE folders ...
set DROPPED=
for /f "tokens=1,2 delims=/" %%A in ('%GIT% diff --cached --name-only -- deploy_kits') do (
  if not defined SEEN_%%B (
    set SEEN_%%B=1
    echo    scanning deploy_kits/%%B
    for /f "delims=" %%F in ('%GIT% ls-files --others --ignored --exclude-standard -- deploy_kits/%%B') do (
      echo    !! EXCLUDED BY .gitignore: %%F
      set DROPPED=1
    )
  )
)
if defined DROPPED (
  echo.
  echo !! REFUSING TO COMMIT - a file inside the payload was silently excluded.
  echo    Nothing committed, nothing pushed. Tell Claude which file.
  pause & exit /b 1
)
echo    payload complete - nothing dropped - OK
echo.

%GIT% commit -m "session close-out: canonical set + pending kits" || echo (nothing new to commit - continuing)
%GIT% push || ( echo !! git push FAILED - NOT published & pause & exit /b 1 )

for /f "delims=" %%A in ('%GIT% rev-parse HEAD') do set L=%%A
for /f "delims=" %%B in ('%GIT% rev-parse origin/main') do set R=%%B
echo.
if "!L!"=="!R!" (
  echo ---- GREEN: your PC and GitHub are the same commit
  echo      !L!
) else (
  echo ---- RED: PC !L!
  echo          GitHub !R!   - NOT published
)
echo.
%GIT% log --oneline -2
%GIT% status -sb
echo.
pause
