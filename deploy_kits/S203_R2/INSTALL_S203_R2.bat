@echo off
setlocal enableextensions
title S203_R2 - the pull tells the truth, and keeps a record
color 0B
REM ===========================================================================
REM  S203_R2   --   DOUBLE-CLICK ON manojz
REM
REM  TWO FAULTS, ONE CAUSE: the pull could not tell you what it did.
REM
REM  1. "-- ok" was written UNCONDITIONALLY. Capture, routing, sending and the
REM     picture could all have failed and it still said ok. pipeline_status.py
REM     computes ended_ok as "a line starts with END and ends with ok" and
REM     posts that to the clinic server -- so the server was told the pipeline
REM     was healthy by a word that was always written. On 26-Aug the feed was
REM     dark for 8h40m and this said ok every ten minutes.
REM  2. The pull kept NO log. PULL_HIDDEN.vbs ran it hidden with nothing
REM     redirected, so every line describing what happened was destroyed.
REM
REM  WHAT CHANGES: two files, both here on manojz.
REM     PULL_FROM_MEDICAL.bat - each step's exit code is checked; the word ok
REM                             is earned; one outcome line per run is kept.
REM     PULL_HIDDEN.vbs       - the console output goes to a monthly log.
REM  Nothing on the medical PC. Nothing on the VPS. pipeline_status.py is NOT
REM  touched -- it stops reporting ok by itself, because the word is gone.
REM
REM  IT TESTS ITSELF BEFORE IT LEAVES: it runs a real pull in front of you and
REM  requires an END line, then launches the hidden path and requires the log
REM  to appear. A broken redirect in the .vbs would stop the pull silently,
REM  so it is not left installed unproven.
REM ===========================================================================
set "HERE=%~dp0"
set "DIR=D:\Downloads\margsync\MargPull"
set "OLDBAT=92f03999d0a14d00b7f552dbb4d44c05"
set "NEWBAT=cfb8b13d028a3bdc69a70701056392ec"
set "OLDVBS=9a3ba9ba3bb7376bd166f12624d282c3"
set "NEWVBS=084fc4523b0e855c8d29b54c144bb60b"

echo.
echo  ==========================================================
echo   S203_R2  -  PULL_FROM_MEDICAL.bat + PULL_HIDDEN.vbs
echo  ==========================================================
echo.

if not exist "%DIR%\PULL_FROM_MEDICAL.bat" ( echo   STOP: %DIR% not found. & pause & exit /b 1 )

REM ---- [1/7] the live files must be the ones this was built against -------
call :md5 "%DIR%\PULL_FROM_MEDICAL.bat" GOT
if /i not "%GOT%"=="%OLDBAT%" (
  echo   STOP ^[1/7^]: PULL_FROM_MEDICAL.bat on disk is not what this kit expects.
  echo      on disk : %GOT%
  echo      expected: %OLDBAT%
  echo      Nothing changed. Send me the value above.
  pause & exit /b 1
)
call :md5 "%DIR%\PULL_HIDDEN.vbs" GOT
if /i not "%GOT%"=="%OLDVBS%" (
  echo   STOP ^[1/7^]: PULL_HIDDEN.vbs on disk is not what this kit expects.
  echo      on disk : %GOT%   expected: %OLDVBS%
  pause & exit /b 1
)
echo   [1/7] both live files verified

REM ---- [2/7] the replacements must be intact ------------------------------
call :md5 "%HERE%PULL_FROM_MEDICAL.bat" GOT
if /i not "%GOT%"=="%NEWBAT%" ( echo   STOP ^[2/7^]: the .bat in this kit is damaged ^(%GOT%^). & pause & exit /b 1 )
call :md5 "%HERE%PULL_HIDDEN.vbs" GOT
if /i not "%GOT%"=="%NEWVBS%" ( echo   STOP ^[2/7^]: the .vbs in this kit is damaged ^(%GOT%^). & pause & exit /b 1 )
echo   [2/7] both replacements verified

REM ---- [3/7] back up ------------------------------------------------------
for /f "tokens=2 delims==" %%T in ('wmic os get localdatetime /value 2^>nul') do if not defined TS set "TS=%%T"
set "BB=%DIR%\PULL_FROM_MEDICAL.bat.bak_S203_R2_%TS:~0,14%"
set "BV=%DIR%\PULL_HIDDEN.vbs.bak_S203_R2_%TS:~0,14%"
copy /y "%DIR%\PULL_FROM_MEDICAL.bat" "%BB%" >nul || ( echo   STOP: no backup made. & pause & exit /b 1 )
copy /y "%DIR%\PULL_HIDDEN.vbs"       "%BV%" >nul || ( echo   STOP: no backup made. & pause & exit /b 1 )
echo   [3/7] backups taken

REM ---- [4/7] install -----------------------------------------------------
copy /y "%HERE%PULL_FROM_MEDICAL.bat" "%DIR%\PULL_FROM_MEDICAL.bat" >nul || goto :rollback
copy /y "%HERE%PULL_HIDDEN.vbs"       "%DIR%\PULL_HIDDEN.vbs"       >nul || goto :rollback
echo   [4/7] installed

REM ---- [5/7] a REAL pull, in front of you --------------------------------
REM  AUTO HIDDEN = run the body here, no hand-off, no pause at the end.
echo   [5/7] running one real pull now - about 20 seconds, please wait...
call "%DIR%\PULL_FROM_MEDICAL.bat" AUTO HIDDEN >nul 2>&1
findstr /c:"END " "%DIR%\_last_pull.txt" >nul 2>&1
if errorlevel 1 (
  echo         the pull did not write an END line. Rolling back.
  goto :rollback
)
for /f "delims=" %%L in ('findstr /c:"END " "%DIR%\_last_pull.txt"') do set "ENDLINE=%%L"
echo         %ENDLINE%

REM ---- [6/7] the hidden path, which is how it really runs ----------------
echo   [6/7] testing the hidden launcher - about 40 seconds...
set "CLOG=%DIR%\_logs\pull_console_%TS:~0,4%-%TS:~4,2%.log"
wscript.exe "%DIR%\PULL_HIDDEN.vbs"
timeout /t 40 /nobreak >nul
if not exist "%CLOG%" (
  echo         NO CONSOLE LOG APPEARED at:
  echo         %CLOG%
  echo         The hidden launcher is how the scheduled task runs, so this
  echo         must work. Rolling back.
  goto :rollback
)
for %%S in ("%CLOG%") do set "CSZ=%%~zS"
if "%CSZ%"=="0" ( echo         the console log is empty. Rolling back. & goto :rollback )
echo         console log written, %CSZ% bytes

REM ---- [7/7] prove the installed bytes ------------------------------------
call :md5 "%DIR%\PULL_FROM_MEDICAL.bat" GOT
if /i not "%GOT%"=="%NEWBAT%" ( echo   [7/7] .bat bytes do not match. & goto :rollback )
call :md5 "%DIR%\PULL_HIDDEN.vbs" GOT
if /i not "%GOT%"=="%NEWVBS%" ( echo   [7/7] .vbs bytes do not match. & goto :rollback )
echo   [7/7] installed bytes verified

echo.
echo  ==========================================================
echo   INSTALLED AND PROVEN.
echo.
echo   From now on:
echo     * "-- ok" in _last_pull.txt is EARNED. A failed step writes
echo       "-- PROBLEM: capture=1" (or send=, rescan=, picture=)
echo       and the clinic server stops being told it is healthy.
echo     * every run leaves one line in
echo       %DIR%\_logs\pull_YYYY-MM.log
echo     * the full console output is kept in
echo       %DIR%\_logs\pull_console_YYYY-MM.log
echo.
echo   Those two logs are the first history this pull has ever had.
echo   Send me pull_YYYY-MM.log if anything ever looks wrong.
echo.
echo   Backups, if you ever want them back:
echo   %BB%
echo   %BV%
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
echo   *** PUTTING BOTH ORIGINALS BACK ***
copy /y "%BB%" "%DIR%\PULL_FROM_MEDICAL.bat" >nul
copy /y "%BV%" "%DIR%\PULL_HIDDEN.vbs"       >nul
echo   restored. The pull is exactly as it was.
echo   Tell me what the step above said.
echo.
pause
exit /b 1
