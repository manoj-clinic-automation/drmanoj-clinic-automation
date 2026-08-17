@echo off
setlocal enabledelayedexpansion
REM =====================================================================
REM  push_S185_close.bat  -  commit + push the S185 close-out to GitHub
REM  (the canonical fold-in: Archive v1.33 + Fault Register v2.19 +
REM   Register v5.6 + manifest + Runbook v119 + START_HERE 186, plus the
REM   two S184 Tier-0 docs filed under F-107)
REM  Double-click to run. Safe to run more than once.
REM  Built on push_S183_close.bat + push_kit.bat v4 (F-100 guard included).
REM =====================================================================
set REPO_DIR=D:\dr-manoj-git\drmanoj-clinic-automation
set KIT_DIR=%REPO_DIR%\deploy_kits\KB_canon_all

if not exist "%REPO_DIR%\.git" (
  echo !! repo not found at %REPO_DIR%  -  edit REPO_DIR at the top of this file
  pause & exit /b 1
)

REM ---- find git.exe even if it is not on PATH -------------------------
set GIT=
where git >nul 2>&1 && set GIT=git
if not defined GIT if exist "C:\Program Files\Git\cmd\git.exe" set GIT="C:\Program Files\Git\cmd\git.exe"
if not defined GIT if exist "C:\Program Files (x86)\Git\cmd\git.exe" set GIT="C:\Program Files (x86)\Git\cmd\git.exe"
if not defined GIT for /d %%D in ("%LOCALAPPDATA%\GitHubDesktop\app-*") do if exist "%%D\resources\app\git\cmd\git.exe" set GIT="%%D\resources\app\git\cmd\git.exe"
if not defined GIT (
  echo !! git.exe not found  -  open GitHub Desktop, commit and push there instead
  pause & exit /b 1
)
echo Using git: %GIT%

cd /d "%REPO_DIR%"
if exist ".git\index.lock" del /q ".git\index.lock"

REM ---- F-100 GUARD: refuse to commit if .gitignore silently drops a kit file
echo.
echo Checking that no KB_canon_all file is excluded by .gitignore...
set EXCLUDED=0
for %%F in ("%KIT_DIR%\*.md" "%KIT_DIR%\*.txt") do (
  %GIT% check-ignore -q "%%F" && (
    echo   EXCLUDED: %%~nxF
    %GIT% check-ignore -v "%%F"
    set EXCLUDED=1
  )
)
if "!EXCLUDED!"=="1" (
  echo.
  echo !! REFUSING TO COMMIT  -  at least one kit file is excluded by .gitignore.
  echo !! A publishing step that cannot prove it published everything has not
  echo !! published anything ^(F-100^). Fix the filename, do NOT punch a hole in
  echo !! the PHI guard, then run this again.
  pause & exit /b 1
)
echo   none excluded - good.

echo.
echo Staging all changes...
%GIT% add -A || ( echo !! git add FAILED & pause & exit /b 1 )

echo.
echo These files will be committed:
%GIT% status --short
echo.

%GIT% commit -F "%REPO_DIR%\deploy_kits\KB_canon_all\COMMIT_S185.txt" || echo (nothing new to commit - continuing)

echo.
echo Pushing to GitHub...
%GIT% push || ( echo !! git push FAILED - NOT published. Check your internet / GitHub sign-in. & pause & exit /b 1 )

echo.
echo ============================================================
echo   S185 close-out pushed successfully.
echo   Verify anytime with:
echo     cd deploy_kits\KB_canon_all ^&^& md5sum -c MD5SUMS_ALL.txt
echo   Expect 63 of 63 OK.
echo ============================================================
pause
