@echo off
setlocal enabledelayedexpansion
REM ===========================================================================
REM  PUSH.bat  -  the S186 default publish method.
REM
REM  The kit is ALREADY sitting in the repo: Claude writes it straight into
REM  deploy_kits\<KIT>\ over the device bridge. So there is no zip, no unzip,
REM  no folder to name correctly, and no xcopy step to get wrong.
REM  Paste this file's path into the Explorer address bar and press Enter.
REM
REM  It keeps the F-100 gate from push_kit.bat v4: if .gitignore silently drops
REM  any kit file, it REFUSES to commit rather than publishing an incomplete kit
REM  that would fail SUMS at the VPS console later.
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

%GIT% commit -m "deploy kit %KIT_NAME% (written direct to repo; gated installer inside)" || echo (nothing new to commit - continuing)
%GIT% push || ( echo !! git push FAILED - NOT published & pause & exit /b 1 )
echo.
echo ---- %KIT_NAME% pushed. Now on the VPS run:
echo      bash /root/deploy/vps_deploy.sh %KIT_NAME%
echo.
pause
