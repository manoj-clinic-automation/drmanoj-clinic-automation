@echo off
setlocal enableextensions
title S203_R1 - the vanishing refused file
color 0B
REM ===========================================================================
REM  S203_R1   --   DOUBLE-CLICK ON manojz
REM
REM  WHAT IT FIXES
REM    An .xls that cannot be opened was refused and then FORGOTTEN: it was
REM    never copied to _REFUSED and never written to index.csv. Because the
REM    router rebuilds what it has "seen" from index.csv on every run, the same
REM    file was picked up and refused again on the next 10-minute cycle, and
REM    the next, for ever -- and the only message went to a console window
REM    PULL_HIDDEN.vbs throws away. Nothing in the system could see it.
REM
REM  WHAT IT CHANGES
REM    ONE file: marg_router.py. The archive-and-index tail is now a function
REM    that BOTH paths call, so there is one definition of archiving and it
REM    cannot drift. No schema change. No data touched. No other file.
REM
REM  GATES  (it refuses rather than guesses)
REM    1. the file on disk must be the expected one, by md5
REM    2. the replacement must be the expected one, by md5
REM    3. the selftest must report EXACTLY 21 OK and 0 FAIL   <-- exact count,
REM       because a gate that matches the bare word "OK" matches almost anything
REM    Any gate fails -> the original is put straight back.
REM ===========================================================================
set "HERE=%~dp0"
set "LIVE=D:\Downloads\margsync\MargPull\marg_router.py"
set "OLDSUM=bbc50f9172211925755eeaa25920d1cf"
set "NEWSUM=781e5ff66d4eca6b6ed4703bf692fb46"

echo.
echo  ==========================================================
echo   S203_R1  -  marg_router.py
echo  ==========================================================
echo.

REM ---- python, the same way the pull finds it ------------------------------
set "PY="
if exist "D:\Downloads\margsync\MargPull\pyportable\python.exe" set "PY=D:\Downloads\margsync\MargPull\pyportable\python.exe"
if not defined PY ( py -c "import sys" >nul 2>&1 && set "PY=py" )
if not defined PY ( python -c "import sys" >nul 2>&1 && set "PY=python" )
if not defined PY ( echo   STOP: no python found. & pause & exit /b 1 )
echo   python    : %PY%

REM ---- [1/5] is the live file the one we built against? -------------------
if not exist "%LIVE%" ( echo   STOP: %LIVE% not found. & pause & exit /b 1 )
for /f "skip=1 tokens=1" %%H in ('certutil -hashfile "%LIVE%" MD5') do if not defined GOTOLD set "GOTOLD=%%H"
if /i not "%GOTOLD%"=="%OLDSUM%" (
  echo   STOP ^[1/5^]: the live file is not what this kit was built against.
  echo      on disk : %GOTOLD%
  echo      expected: %OLDSUM%
  echo      Nothing has been changed. Send me the value above.
  pause & exit /b 1
)
echo   [1/5] live file verified   %OLDSUM%

REM ---- [2/5] is the replacement intact? ------------------------------------
for /f "skip=1 tokens=1" %%H in ('certutil -hashfile "%HERE%marg_router.py" MD5') do if not defined GOTNEW set "GOTNEW=%%H"
if /i not "%GOTNEW%"=="%NEWSUM%" (
  echo   STOP ^[2/5^]: the replacement in this kit is damaged.
  echo      in kit  : %GOTNEW%
  echo      expected: %NEWSUM%
  pause & exit /b 1
)
echo   [2/5] replacement verified %NEWSUM%

REM ---- [3/5] back up, then install -----------------------------------------
for /f "tokens=2 delims==" %%T in ('wmic os get localdatetime /value 2^>nul') do if not defined TS set "TS=%%T"
set "BAK=%LIVE%.bak_S203_R1_%TS:~0,14%"
copy /y "%LIVE%" "%BAK%" >nul
if errorlevel 1 ( echo   STOP ^[3/5^]: could not make a backup. Nothing changed. & pause & exit /b 1 )
echo   [3/5] backup   : %BAK%
copy /y "%HERE%marg_router.py" "%LIVE%" >nul
if errorlevel 1 ( echo   STOP: copy failed. Restoring. & copy /y "%BAK%" "%LIVE%" >nul & pause & exit /b 1 )

REM ---- [4/5] the selftest, counted exactly ---------------------------------
"%PY%" "%LIVE%" --selftest > "%TEMP%\_r1.txt" 2>&1
set "NOK=0"
set "NFAIL=0"
for /f %%N in ('findstr /c:"  OK   " "%TEMP%\_r1.txt" ^| find /c /v ""') do set "NOK=%%N"
for /f %%N in ('findstr /c:"  FAIL " "%TEMP%\_r1.txt" ^| find /c /v ""') do set "NFAIL=%%N"
echo   [4/5] selftest : %NOK% OK, %NFAIL% FAIL   ^(want exactly 21 and 0^)
if not "%NFAIL%"=="0" goto :rollback
if not "%NOK%"=="21"  goto :rollback

REM ---- [5/5] prove the installed bytes are the ones we verified ------------
set "GOTFIN="
for /f "skip=1 tokens=1" %%H in ('certutil -hashfile "%LIVE%" MD5') do if not defined GOTFIN set "GOTFIN=%%H"
if /i not "%GOTFIN%"=="%NEWSUM%" (
  echo   [5/5] installed bytes do NOT match. Restoring.
  goto :rollback
)
echo   [5/5] installed : %GOTFIN%
echo.
echo  ==========================================================
echo   INSTALLED. marg_router.py is now %NEWSUM%
echo.
echo   From the next 10-minute pull, a file that cannot be read
echo   is archived into _REFUSED with a .txt saying why, and gets
echo   an index.csv row - so it is dealt with ONCE instead of
echo   being silently refused every ten minutes for ever.
echo.
echo   The backup is beside the original if you ever want it back:
echo   %BAK%
echo  ==========================================================
echo.
pause
exit /b 0

:rollback
echo.
echo   *** GATE FAILED - PUTTING THE ORIGINAL BACK ***
copy /y "%BAK%" "%LIVE%" >nul
echo   restored: %LIVE%
echo   the selftest output is at %TEMP%\_r1.txt - send it to me.
echo.
type "%TEMP%\_r1.txt" | findstr /c:"FAIL"
echo.
pause
exit /b 1
