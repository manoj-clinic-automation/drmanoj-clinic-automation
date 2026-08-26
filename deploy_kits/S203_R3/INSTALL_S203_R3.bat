@echo off
setlocal enableextensions
title S203_R3 - the clinic server learns about the backup
color 0B
REM ===========================================================================
REM  S203_R3   --   DOUBLE-CLICK ON manojz.   ONE file: pipeline_status.py
REM
REM  WHAT IT ADDS
REM    Every pull posts a status to the clinic server: the outbox, the pull,
REM    the watcher, the offsite lag. It has never said anything about whether
REM    the pharmacy's DATABASE has been backed up -- the one loss that cannot
REM    be undone. The agent has reported that in its heartbeat since this
REM    morning; this carries it the last hop, to the server.
REM
REM  IT REPORTS THE RIGHT NUMBER
REM    The age posted is the BACKUP STICK's. Marg's own serverbackup is newer
REM    but sits on the SAME DISK as the data, so reporting that would be a
REM    reassuring lie -- it is sent beside the stick's age, never instead.
REM
REM  GATES: live md5 · replacement md5 · selftest EXACTLY 21 OK, 0 FAIL ·
REM         a real parse of the CURRENT heartbeat on this PC · installed md5.
REM  Any gate fails -> the original goes straight back.
REM ===========================================================================
set "HERE=%~dp0"
set "LIVE=D:\Downloads\margsync\MargPull\pipeline_status.py"
set "OLDSUM=51cf10c9f2543fcd48a61ee7f8faf51a"
set "NEWSUM=0b3dd968f31cdb48a910539a087206c6"

echo.
echo  ==========================================================
echo   S203_R3  -  pipeline_status.py
echo  ==========================================================
echo.
set "PY="
if exist "D:\Downloads\margsync\MargPull\pyportable\python.exe" set "PY=D:\Downloads\margsync\MargPull\pyportable\python.exe"
if not defined PY ( py -c "import sys" >nul 2>&1 && set "PY=py" )
if not defined PY ( python -c "import sys" >nul 2>&1 && set "PY=python" )
if not defined PY ( echo   STOP: no python found. & pause & exit /b 1 )
echo   python : %PY%

call :md5 "%LIVE%" GOT
if /i not "%GOT%"=="%OLDSUM%" (
  echo   STOP ^[1/5^]: the live file is not what this kit expects.
  echo      on disk : %GOT%
  echo      expected: %OLDSUM%
  echo      Nothing changed.
  pause & exit /b 1
)
echo   [1/5] live file verified

call :md5 "%HERE%pipeline_status.py" GOT
if /i not "%GOT%"=="%NEWSUM%" ( echo   STOP ^[2/5^]: the kit file is damaged ^(%GOT%^). & pause & exit /b 1 )
echo   [2/5] replacement verified

for /f "tokens=2 delims==" %%T in ('wmic os get localdatetime /value 2^>nul') do if not defined TS set "TS=%%T"
set "BAK=%LIVE%.bak_S203_R3_%TS:~0,14%"
copy /y "%LIVE%" "%BAK%" >nul || ( echo   STOP: no backup made. & pause & exit /b 1 )
copy /y "%HERE%pipeline_status.py" "%LIVE%" >nul || goto :rollback
echo   [3/5] backup + installed

"%PY%" "%LIVE%" --selftest > "%TEMP%\_r3.txt" 2>&1
set "NOK=0"
set "NFAIL=0"
for /f %%N in ('findstr /c:"checks OK" "%TEMP%\_r3.txt" ^| find /c /v ""') do set "NPASS=%%N"
for /f "tokens=4" %%N in ('findstr /c:"checks OK" "%TEMP%\_r3.txt"') do set "NOK=%%N"
findstr /c:"FAILED" "%TEMP%\_r3.txt" >nul 2>&1 && set "NFAIL=1"
echo   [4/5] selftest : %NOK% checks, FAIL=%NFAIL%   ^(want exactly 21 and 0^)
if not "%NFAIL%"=="0" goto :rollback
if not "%NOK%"=="21"  goto :rollback

REM  Proven against the REAL heartbeat on this PC, not a fixture. S202's rule:
REM  a monitor is proven against the thing it monitors, in its real state.
"%PY%" "%LIVE%" --dry-run > "%TEMP%\_r3dry.txt" 2>&1
findstr /c:"\"reported\": true" "%TEMP%\_r3dry.txt" >nul 2>&1
if errorlevel 1 (
  echo         it did not read a BACKUP block from the live heartbeat.
  echo         ^(If the medical PC is off, that is expected - tell me and
  echo          we will re-check when it is on. Rolling back for now.^)
  goto :rollback
)
for /f "tokens=2 delims=:," %%A in ('findstr /c:"stick_age_days" "%TEMP%\_r3dry.txt"') do set "AGE=%%A"
echo         live heartbeat read: backup is%AGE% day(s) old

call :md5 "%LIVE%" GOT
if /i not "%GOT%"=="%NEWSUM%" ( echo   [5/5] installed bytes differ. & goto :rollback )
echo   [5/5] installed bytes verified

echo.
echo  ==========================================================
echo   INSTALLED AND PROVEN.
echo   From the next pull, the clinic server is told how old the
echo   pharmacy backup is - the stick's age, not Marg's same-disk
echo   copy. Backup: %BAK%
echo  ==========================================================
echo.
pause
exit /b 0

:md5
set "%~2="
for /f "skip=1 tokens=1" %%H in ('certutil -hashfile "%~1" MD5') do if not defined %~2 set "%~2=%%H"
goto :eof

:rollback
echo.
echo   *** GATE FAILED - PUTTING THE ORIGINAL BACK ***
copy /y "%BAK%" "%LIVE%" >nul
echo   restored. Send me %TEMP%\_r3.txt
echo.
pause
exit /b 1
