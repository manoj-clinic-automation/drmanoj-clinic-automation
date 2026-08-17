@echo off
setlocal enabledelayedexpansion
REM ===========================================================================
REM  SEND_TO_CLINIC.bat  v1  (kit S187_M1a)  --  B5, the Marg report sender.
REM
REM  WHO RUNS THIS: reception / Shavez on the MEDICAL PC, once each morning,
REM  right after running the BILL WISE SALES report in Marg
REM  (Bill wise sales statement, With Item Deta. = Yes).
REM
REM  WHAT IT DOES: finds the report Marg just wrote
REM  (D:\MARGERP\users\<id>\report\REPORT_1.XLS -- fixed name, overwritten on
REM  every run, per the S180 recon), keeps a dated copy beside this script
REM  (Marg forgets yesterday's file; we do not), and sends it to the clinic
REM  server with a token that can do exactly one thing: hand the file over.
REM  NOTHING enters the books from here -- Dr. Manoj checks and applies it on
REM  his workbench.
REM
REM  It never writes anything inside D:\MARGERP (the S180 compliance rule).
REM  Every send is appended to send_log.txt here -- a record that outlives
REM  the run (F-113).
REM
REM  You can also DRAG a report file onto this icon to send that exact file.
REM ===========================================================================

REM ---- CONFIG (set once at install) -----------------------------------------
set "SERVER=https://followup.dr-manoj.in/finance/api/marg-push"
set "TOKEN=PUT-THE-TOKEN-HERE"
set "MARG_USERS=D:\MARGERP\users"
REM ---------------------------------------------------------------------------

set "HERE=%~dp0"
set "SENT=%HERE%Sent"
set "LOG=%HERE%send_log.txt"
set "HASHES=%HERE%sent_hashes.txt"
if not exist "%SENT%" mkdir "%SENT%"
if not exist "%HASHES%" type nul > "%HASHES%"

where curl >nul 2>&1 || (
  echo.
  echo  PROBLEM: curl is not on this PC. Windows 10/11 has it built in.
  echo  Tell Dr. Manoj this exact message.
  echo.
  pause & exit /b 1
)
if "%TOKEN%"=="PUT-THE-TOKEN-HERE" (
  echo.
  echo  This sender is not set up yet - the token is missing.
  echo  Tell Dr. Manoj: "SEND_TO_CLINIC needs its token".
  echo.
  pause & exit /b 1
)

set FOUND=0
set SENTOK=0
set REFUSED=0
set SKIPPED=0

if not "%~1"=="" (
  call :one "%~1"
) else (
  for /d %%U in ("%MARG_USERS%\*") do (
    if exist "%%U\report\REPORT_1.XLS" call :one "%%U\report\REPORT_1.XLS"
  )
)

echo.
echo  ==========================================================
if %FOUND%==0 (
  echo   NO REPORT FOUND  -  koi report nahi mili.
  echo   Pehle Marg mein BILL WISE SALES report chalayen
  echo   ^(With Item Deta. = Yes^), phir isse dobara chalayen.
) else if %SENTOK% GTR 0 (
  echo   ACCEPTED - report clinic server pahunch gayi hai.
  echo   Abhi khaate mein NAHI gayi - Dr. Manoj check karke
  echo   apply karenge. Aapka kaam ho gaya. Dhanyavaad.
) else if %SKIPPED% GTR 0 if %REFUSED%==0 (
  echo   ALREADY SENT - yeh report pehle hi bheji ja chuki hai.
  echo   Aaj ki report bhejni hai to pehle Marg mein report
  echo   dobara chalayen, phir isse chalayen.
) else (
  echo   REFUSED - report nahi gayi. Upar ka message dekhein
  echo   aur Dr. Manoj ko batayen.
)
echo  ==========================================================
echo.
pause
exit /b 0

REM ---------------------------------------------------------------------------
:one
set "SRC=%~1"
set /a FOUND+=1
echo.
echo  --- %SRC%

REM copy first (Marg may be writing; retry once), never touch the original
set "STAMP=%DATE:/=-%_%TIME::=.%"
set "STAMP=%STAMP: =0%"
set "WORK=%SENT%\REPORT_%STAMP%.XLS"
copy /y "%SRC%" "%WORK%" >nul 2>&1
if errorlevel 1 (
  echo      file busy, waiting 5 seconds...
  timeout /t 5 /nobreak >nul
  copy /y "%SRC%" "%WORK%" >nul 2>&1 || (
    echo      COULD NOT READ the report - Marg file busy. Try again in a minute.
    set /a REFUSED+=1
    goto :eof
  )
)

REM hash the copy; if source changed mid-copy the next run simply sends anew
set "HASH="
for /f "skip=1 delims=" %%H in ('certutil -hashfile "%WORK%" MD5 2^>nul') do (
  if not defined HASH set "HASH=%%H"
)
set "HASH=%HASH: =%"
if not defined HASH (
  echo      could not hash the file - certutil failed. Tell Dr. Manoj.
  set /a REFUSED+=1
  goto :eof
)

findstr /i /c:"%HASH%" "%HASHES%" >nul 2>&1
if not errorlevel 1 (
  echo      this exact report was ALREADY SENT earlier - skipping.
  del "%WORK%" >nul 2>&1
  set /a SKIPPED+=1
  goto :eof
)

echo      sending...
set "RESP=%HERE%last_response.txt"
curl -s -m 90 -o "%RESP%" -w "%%{http_code}" -H "X-Finance-Marg: %TOKEN%" ^
     -F "file=@%WORK%;filename=REPORT_1.XLS" "%SERVER%" > "%HERE%last_http.txt" 2>nul
set /p HTTP=<"%HERE%last_http.txt"

findstr /c:"ACCEPTED-FOR-REVIEW" "%RESP%" >nul 2>&1
if not errorlevel 1 (
  echo      ACCEPTED for Dr. Manoj's review.
  echo %DATE% %TIME% ^| %HASH% ^| ACCEPTED ^| %SRC%>> "%LOG%"
  echo %HASH%>> "%HASHES%"
  set /a SENTOK+=1
  goto :eof
)
findstr /c:"ALREADY-RECEIVED" "%RESP%" >nul 2>&1
if not errorlevel 1 (
  echo      the server already has this exact report.
  echo %DATE% %TIME% ^| %HASH% ^| ALREADY ^| %SRC%>> "%LOG%"
  echo %HASH%>> "%HASHES%"
  del "%WORK%" >nul 2>&1
  set /a SKIPPED+=1
  goto :eof
)
echo      REFUSED by the server ^(HTTP %HTTP%^). Server said:
type "%RESP%" 2>nul
echo.
echo %DATE% %TIME% ^| %HASH% ^| REFUSED HTTP %HTTP% ^| %SRC%>> "%LOG%"
set /a REFUSED+=1
goto :eof
