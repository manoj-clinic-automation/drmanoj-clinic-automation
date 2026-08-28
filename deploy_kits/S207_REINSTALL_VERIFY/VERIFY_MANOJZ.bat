@echo off
REM ===========================================================================
REM  VERIFY_MANOJZ.bat  --  S207.1
REM
REM  Read-only rehearsal of REINSTALL_MANOJZ.md section 7, "the checks that
REM  prove it worked".  Run it on manojz, from a Command Prompt or by
REM  double-clicking.  It CHANGES NOTHING and is safe on the live machine.
REM
REM  Section 7 check 1 is "is there a Python 3" -- and that check has to happen
REM  BEFORE any python can run, so this batch does it itself, in the same order
REM  PULL_FROM_MEDICAL.bat searches:  pyportable, then py, then python.
REM  If none is found this batch reports check 1 FAILED and stops, which is the
REM  correct answer rather than a crash.
REM
REM  Exit code 0 = every automatable check passed.  1 = at least one failed.
REM ===========================================================================
setlocal EnableExtensions
set "HERE=%~dp0"
set "TARGET=%HERE%verify_manojz.py"

if not exist "%TARGET%" (
  echo FATAL: verify_manojz.py is not beside this batch file.
  echo Expected: "%TARGET%"
  goto :fail
)

set "PYEXE="
set "PYARGS="

REM  1.  the portable interpreter, if a rebuild ever ships one
set "CAND=D:\Downloads\margsync\MargPull\pyportable\python.exe"
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
  echo   CHECK 1 FAILED: no working Python on this PC.
  echo.
  echo   Nothing else in section 7 can run without it, and neither can the
  echo   10-minute pull -- it would write "FAILED: no python" to _last_pull.txt
  echo   every cycle.  Install Python 3 ^(3.8+, standard library is enough^)
  echo   and run this again.
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
REM  pause only when double-clicked, so the window does not vanish unread.
echo %cmdcmdline% | find /i "%~nx0" >nul
if not errorlevel 1 pause
endlocal & exit /b %RC%
