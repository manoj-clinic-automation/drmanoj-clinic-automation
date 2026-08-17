@echo off
setlocal enabledelayedexpansion
REM push_kit.bat v4 - finds git even off PATH; never claims success unless the push succeeded.
REM
REM v4 (S183, F-100): a kit file that .gitignore excludes used to vanish SILENTLY.
REM   `git add <folder>` does not complain about ignored files inside it, so v3
REM   printed "pushed successfully" while the kit in the repo was incomplete, and
REM   the fault only surfaced as a SUMS failure at the VPS console. That is the
REM   same shape as F-97 one layer up: the record claimed a file that was not
REM   there. v4 checks every file in the kit is actually TRACKED after the add,
REM   and refuses to commit if any was dropped.
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

REM ---- v4 GATE: did git actually take EVERY file in the kit? ------------------
REM A file excluded by .gitignore is skipped without a word. Catch it HERE, on
REM the PC, in daylight - not as a SUMS red at the VPS console at night.
set DROPPED=
for /f "delims=" %%F in ('%GIT% ls-files --others --ignored --exclude-standard -- deploy_kits/%KIT_NAME%') do (
  echo    !! EXCLUDED BY .gitignore: %%F
  set DROPPED=1
)
if defined DROPPED (
  echo.
  echo !! REFUSING TO COMMIT - at least one kit file was silently excluded.
  echo    Nothing has been committed or pushed.
  echo    The kit in the repo would have been INCOMPLETE and the VPS installer
  echo    would have refused it on SUMS. Rename the file to an extension the
  echo    repo does not exclude - do NOT punch a hole in .gitignore, those rules
  echo    are the guard that keeps patient data out of a public repo ^(F-31/F-49, D320^).
  echo.
  pause & exit /b 1
)
echo    all kit files tracked - OK
REM ---------------------------------------------------------------------------

%GIT% commit -m "deploy kit %KIT_NAME% (code-only, gated installer inside)" || echo (nothing new to commit - continuing)
%GIT% push || ( echo !! git push FAILED - NOT published & pause & exit /b 1 )
echo.
echo ---- kit %KIT_NAME% pushed successfully. Now on the VPS run:
echo      bash /root/deploy/vps_deploy.sh %KIT_NAME%
pause
