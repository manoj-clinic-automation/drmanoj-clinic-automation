@echo off
setlocal enabledelayedexpansion
REM ===========================================================================
REM  PUBLISH_ALL.bat  v1  (S187)  -  THE default publish method.
REM
REM  One double-click publishes EVERYTHING pending in the repo: every kit
REM  folder Claude has written, the canon set, the logo folder - whatever is
REM  uncommitted. You never navigate to a kit folder again.
REM
REM  Keeps every hard-won gate:
REM   - refuses if .git\HEAD.lock exists            (the S187 lock episode)
REM   - refuses if .gitignore silently drops a file (F-100)
REM   - a failed commit is a FAILURE, never "nothing to commit" (F-124)
REM   - after pushing, VERIFIES origin HEAD == local HEAD, or refuses to
REM     print success (the projection is the check)
REM
REM  Put a shortcut to this on your desktop: right-click -> Send to ->
REM  Desktop (create shortcut), rename it PUBLISH.
REM ===========================================================================
set REPO_DIR=D:\dr-manoj-git\drmanoj-clinic-automation
if not exist "%REPO_DIR%\.git" ( echo !! repo not found at %REPO_DIR% & pause & exit /b 1 )

set GIT=
where git >nul 2>&1 && set GIT=git
if not defined GIT if exist "C:\Program Files\Git\cmd\git.exe" set GIT="C:\Program Files\Git\cmd\git.exe"
if not defined GIT if exist "C:\Program Files (x86)\Git\cmd\git.exe" set GIT="C:\Program Files (x86)\Git\cmd\git.exe"
if not defined GIT for /d %%D in ("%LOCALAPPDATA%\GitHubDesktop\app-*") do if exist "%%D\resources\app\git\cmd\git.exe" set GIT="%%D\resources\app\git\cmd\git.exe"
if not defined GIT ( echo !! git.exe not found & pause & exit /b 1 )

cd /d "%REPO_DIR%"

if exist ".git\HEAD.lock" (
  echo !! .git\HEAD.lock exists - close GitHub Desktop / editors, then rename
  echo    the lock ^(HEAD.lock.stale^) and run this again. NOTHING published.
  pause & exit /b 1
)

echo Checking what is pending...
%GIT% add -A . || ( echo !! git add FAILED & pause & exit /b 1 )

set DROPPED=
for /f "delims=" %%F in ('%GIT% ls-files --others --ignored --exclude-standard -- deploy_kits logo canonical-docs 2^>nul') do (
  echo    !! EXCLUDED BY .gitignore: %%F
  set DROPPED=1
)
if defined DROPPED (
  echo.
  echo !! REFUSING - at least one file was silently excluded by .gitignore.
  echo    Nothing committed or pushed. Tell Claude which file.
  pause & exit /b 1
)

%GIT% diff --cached --quiet
if errorlevel 1 (
  %GIT% commit -m "publish: pending kits and files (PUBLISH_ALL)" || (
    echo !! git commit FAILED - a REAL failure. NOT published.
    pause & exit /b 1
  )
) else (
  echo    nothing new to commit - will still verify the remote is current
)

%GIT% push || ( echo !! git push FAILED - NOT published & pause & exit /b 1 )

set LOCALH=
set REMOTEH=
for /f %%H in ('%GIT% rev-parse HEAD') do set LOCALH=%%H
for /f %%H in ('%GIT% ls-remote origin -q HEAD') do if not defined REMOTEH set REMOTEH=%%H
if not defined REMOTEH ( echo !! could not read origin HEAD - UNVERIFIED & pause & exit /b 1 )
if /i not "%LOCALH%"=="%REMOTEH%" (
  echo !! VERIFY FAILED: local  %LOCALH%
  echo                  origin %REMOTEH%
  echo    NOT published.
  pause & exit /b 1
)
echo.
echo  ==========================================================
echo   PUBLISHED AND VERIFIED - origin HEAD = %LOCALH:~0,10%...
echo   Now on the VPS run the deploy for whichever kit is new,
echo   e.g.:  bash /root/deploy/vps_deploy.sh S187_H1c
echo  ==========================================================
echo.
pause
