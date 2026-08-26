@echo off
setlocal
REM ===========================================================================
REM  SETUP_CHECK.bat  (S195)  --  one-time self-check for the Marg guard.
REM  Double-click this once. It finds a WORKING Python (the bundled portable
REM  one first), then runs the guard on a bundled sample file using the vendored
REM  xlrd (no pip install needed). It writes the result to setup_check.txt.
REM  It sends NOTHING and touches no real report.
REM ===========================================================================
set "HERE=%~dp0"
set "OUT=%HERE%setup_check.txt"
echo S195 SETUP CHECK> "%OUT%"
echo.>> "%OUT%"

set "PY="
if exist "%HERE%pyportable\python.exe" set "PY=%HERE%pyportable\python.exe"
if not defined PY ( py -c "import sys" >nul 2>&1 && set "PY=py" )
if not defined PY ( python -c "import sys" >nul 2>&1 && set "PY=python" )

if not defined PY (
  echo RESULT: NO_PYTHON>> "%OUT%"
  echo   No working Python found ^(the Microsoft Store stub does not count^).>> "%OUT%"
  echo   Unzip pyportable.zip here so pyportable\python.exe exists, then run me again.>> "%OUT%"
  goto show
)

echo interpreter: %PY%>> "%OUT%"
"%PY%" --version>> "%OUT%" 2>&1
echo.>> "%OUT%"
echo --- guard dry-run on bundled _setup_sample.xls (vendored xlrd) --->> "%OUT%"
"%PY%" "%HERE%guard_and_send.py" "%HERE%_setup_sample.xls" --expect any --alert "%HERE%setup_check_alert.txt">> "%OUT%" 2>&1
echo exitcode=%errorlevel%>> "%OUT%"
echo.>> "%OUT%"
echo RESULT: PYTHON_OK>> "%OUT%"

:show
echo.>> "%OUT%"
type "%OUT%"
echo.
echo (Saved to setup_check.txt in this folder.)
pause
