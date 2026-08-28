@echo off
REM VERIFY_KB_CANON.bat -- double-clickable wrapper for VERIFY_KB_CANON.ps1
REM Phase 0 Lite step 1 on Windows. `md5sum` is NOT a Windows command; this is.
REM Read-only. Verifies deploy_kits\KB_canon_all\MD5SUMS_ALL.txt.
REM Expect 238/238 as at 28-Aug-2026. This line said 229/229, which was right
REM when it was written and went stale at the S206 close when rows were added.
REM The SCRIPT never hard-codes a count -- it reads however many rows the sums
REM file has -- so a stale number here misleads a reader and breaks nothing.
REM Do not treat this comment as the expectation: RESULT: PASS is.
setlocal
set "HERE=%~dp0"
set "SUMS=%HERE%..\KB_canon_all\MD5SUMS_ALL.txt"
if not exist "%SUMS%" (
  echo FATAL: cannot find "%SUMS%"
  echo Run this from deploy_kits\S206_F216_DISPOSITION\ inside the repo.
  exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%HERE%VERIFY_KB_CANON.ps1" -SumsFile "%SUMS%"
set "RC=%ERRORLEVEL%"
echo.
echo exit code %RC%   (0 = pass, 1 = fail)

REM  S207: pause ONLY when double-clicked, so the window does not vanish
REM  before the answer can be read. It did exactly that on 28-Aug-2026 and
REM  the run told the owner nothing. This is a DISASTER-RECOVERY tool -- the
REM  person running it is standing at a rebuilt machine, and a check whose
REM  result nobody sees is not a check. Same idiom as the S207 wrappers.
echo %cmdcmdline% | find /i "%~nx0" >nul
if not errorlevel 1 pause

endlocal & exit /b %RC%
