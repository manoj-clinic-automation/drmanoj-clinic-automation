@echo off
setlocal
REM ===========================================================================
REM  SEND_OUTBOX.bat  (S201)  --  runs on MANOJZ.
REM
REM  Sends every VERIFIED Marg sale report sitting in MargArchive\_outbox to
REM  the clinic server, and keeps a record of what actually arrived.
REM
REM  WHY: until today nothing read _outbox. marg_router.py stamped every
REM  verified report "queued for upload" and there was no uploader. Eight
REM  reports sat there. The 24-Aug report never reached the server and the
REM  only sign was a page that stayed empty.
REM
REM  Safe to run as often as you like. A report already on the server is
REM  recognised and not sent again. A report that fails to send is NOT marked
REM  as sent, so the next run retries it.
REM ===========================================================================
set "HERE=%~dp0"

set "PY="
if exist "%HERE%pyportable\python.exe" set "PY=%HERE%pyportable\python.exe"
if not defined PY ( py -c "import sys" >nul 2>&1 && set "PY=py" )
if not defined PY ( python -c "import sys" >nul 2>&1 && set "PY=python" )
if not defined PY (
  echo.
  echo  PROBLEM: no working Python on this PC. Tell Dr. Manoj.
  echo.
  if /i not "%~1"=="AUTO" pause
  exit /b 1
)

echo.
echo  Sending any Marg reports the clinic server does not have yet...
echo.
"%PY%" "%HERE%marg_gate.py" send
set "RC=%ERRORLEVEL%"

echo.
if "%RC%"=="0" (
  echo  ==========================================================
  echo   DONE - clinic server has every verified report.
  echo  ==========================================================
) else (
  echo  ==========================================================
  echo   SOMETHING DID NOT GO. Read the lines above.
  echo   Nothing was lost - it will be retried automatically.
  echo   Details: D:\Downloads\margsync\MargArchive\_NEEDS_ATTENTION.txt
  echo  ==========================================================
)
echo.
if /i not "%~1"=="AUTO" pause
exit /b %RC%
