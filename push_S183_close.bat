@echo off
setlocal enabledelayedexpansion
REM =====================================================================
REM  push_S183_close.bat  -  commit + push the S183 close-out to GitHub
REM  (the KB canonical set v5.5 + the S183 Marg-feed and pin-verifier kits)
REM  Double-click to run. Safe to run more than once.
REM =====================================================================
set REPO_DIR=D:\dr-manoj-git\drmanoj-clinic-automation

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

REM ---- clear a stale index lock if one is lying around (harmless) -----
if exist ".git\index.lock" del /q ".git\index.lock"

echo.
echo Staging all changes...
%GIT% add -A || ( echo !! git add FAILED & pause & exit /b 1 )

echo.
echo These files will be committed:
%GIT% status --short
echo.

%GIT% commit -m "S183 close: KB canonical set v5.5 (Register/Runbook/START_HERE/manifest) + Marg feed kit S183_M2a + pin verifier S183_V1a-c" || echo (nothing new to commit - continuing)

echo.
echo Pushing to GitHub...
%GIT% push || ( echo !! git push FAILED - NOT published. Check your internet / GitHub sign-in. & pause & exit /b 1 )

echo.
echo ============================================================
echo   S183 close-out pushed successfully.
echo ============================================================
pause
