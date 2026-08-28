@echo off
REM ===========================================================================
REM  VERIFY_MEDICAL.bat  --  S207.1
REM
REM  Read-only rehearsal of REINSTALL_MEDICAL.md section 7.  Run it ON THE
REM  MEDICAL PC.  It CHANGES NOTHING -- it reads D:\SendToClinic\heartbeat.txt
REM  and the capture spool and judges them.  Safe on the live machine.
REM
REM  Section 7 check 1 is the bundled interpreter, so this batch looks for it
REM  first and by its full documented path.  Falling back to a system python is
REM  allowed but is reported as a WARN by the script: the agent itself runs on
REM  pyportable and nothing else, so a missing pyportable is a real finding.
REM
REM  Checks 4, 5 and 6 of section 7 run on MANOJZ, not here.  Run
REM  VERIFY_MANOJZ.bat over there.  This script prints them as CROSS rows so
REM  the table matches the document one to one.
REM
REM  Exit code 0 = every check readable here passed.  1 = at least one failed.
REM ===========================================================================
setlocal EnableExtensions
set "HERE=%~dp0"
set "TARGET=%HERE%verify_medical.py"

if not exist "%TARGET%" (
  echo FATAL: verify_medical.py is not beside this batch file.
  echo Expected: "%TARGET%"
  goto :fail
)

set "PYEXE="
set "PYARGS="

REM  1.  the bundled interpreter the agent itself runs on
set "CAND=D:\SendToClinic\pyportable\python.exe"
if exist "%CAND%" set "PYEXE=%CAND%"

REM  2.  the Windows launcher
if not defined PYEXE (
  py -3 -c "pass" >nul 2>&1
  if not errorlevel 1 (
    set "PYEXE=py"
    set "PYARGS=-3"
  )
)

REM  3.  python on PATH
if not defined PYEXE (
  python -c "pass" >nul 2>&1
  if not errorlevel 1 set "PYEXE=python"
)

if not defined PYEXE (
  echo.
  echo   CHECK 1 FAILED: no Python at all on this PC.
  echo.
  echo   Expected the bundled interpreter at
  echo     D:\SendToClinic\pyportable\python.exe
  echo   If that is missing, medical_agent.py cannot start either -- it logs
  echo   "FATAL: bundled python missing" and exits.  Nothing on this machine
  echo   captures anything until it is back.
  goto :fail
)

"%PYEXE%" %PYARGS% "%TARGET%" %*
set "RC=%ERRORLEVEL%"
echo.
echo exit code %RC%   ^(0 = pass, 1 = at least one check failed^)
goto :done

:fail
set "RC=1"
echo.
echo exit code 1

:done
echo %cmdcmdline% | find /i "%~nx0" >nul
if not errorlevel 1 pause
endlocal & exit /b %RC%
