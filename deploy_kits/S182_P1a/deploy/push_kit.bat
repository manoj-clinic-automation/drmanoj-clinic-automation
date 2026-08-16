@echo off
setlocal enabledelayedexpansion
REM push_kit.bat v3 - finds git even off PATH; never claims success unless the push succeeded.
set REPO_DIR=D:\dr-manoj-git\drmanoj-clinic-automation

for %%I in ("%~dp0..") do set KIT_DIR=%%~fI
for %%I in ("%KIT_DIR%") do set KIT_NAME=%%~nxI
if not exist "%KIT_DIR%\KIT_ID.txt" ( echo !! %KIT_DIR% has no KIT_ID.txt - not a kit & pause & exit /b 1 )
if not exist "%REPO_DIR%\.git" ( echo !! repo not found at %REPO_DIR% - edit REPO_DIR & pause & exit /b 1 )

set GIT=
where git >nul 2>&1 && set GIT=git
if not defined GIT if exist "C:\Program Files\Git\cmd\git.exe" set GIT="C:\Program Files\Git\cmd\git.exe"
if not defined GIT if exist "C:\Program Files (x86)\Git\cmd\git.exe" set GIT="C:\Program Files (x86)\Git\cmd\git.exe"
if not defined GIT for /d %%D in ("%LOCALAPPDATA%\GitHubDesktop\app-*") do if exist "%%D\resources\app\git\cmd\git.exe" set GIT="%%D\resources\app\git\cmd\git.exe"
if not defined GIT ( echo !! git.exe not found - commit %REPO_DIR%\deploy_kits\%KIT_NAME% with GitHub Desktop instead & pause & exit /b 1 )

echo Publishing kit %KIT_NAME% using %GIT%
xcopy /e /i /y "%KIT_DIR%" "%REPO_DIR%\deploy_kits\%KIT_NAME%\" >nul
cd /d "%REPO_DIR%"
%GIT% add deploy_kits\%KIT_NAME% || ( echo !! git add FAILED & pause & exit /b 1 )
%GIT% commit -m "deploy kit %KIT_NAME% (code-only, gated installer inside)" || echo (nothing new to commit - continuing)
%GIT% push || ( echo !! git push FAILED - NOT published & pause & exit /b 1 )
echo.
echo ---- kit %KIT_NAME% pushed successfully. Now on the VPS run:
echo      bash /root/deploy/vps_deploy.sh %KIT_NAME%
pause
