@echo off
REM VERIFY_KB_CANON.bat -- double-clickable wrapper for VERIFY_KB_CANON.ps1
REM Phase 0 Lite step 1 on Windows. `md5sum` is NOT a Windows command; this is.
REM Read-only. Verifies deploy_kits\KB_canon_all\MD5SUMS_ALL.txt (expect 229/229).
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
endlocal & exit /b %RC%
