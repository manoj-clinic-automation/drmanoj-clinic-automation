@echo off
setlocal enabledelayedexpansion
REM ===========================================================================
REM  SEND_TO_CLINIC.bat  v4  (S205)  --  B5, the Marg report sender.
REM
REM  v3 CHANGE: the TOKEN is now read from a plain file "token.txt" that sits
REM  in THIS folder (one line, just the token). You never edit this .bat again
REM  -- create/replace token.txt with Notepad and you are done. Everything else
REM  is v2: it keeps a DATED copy of EVERY report in the Sent\ folder (even ones
REM  already sent) so you always have the full history locally, and it never
REM  writes anything inside D:\MARGERP.
REM
REM  NOTE ON THE DATED NAME: the copy is named by the DATE/TIME it was saved
REM  (when you ran this), not by the report's business date. The business date
REM  is inside the file. To re-load a specific day, open it on Dr. Manoj's
REM  workbench (Marg card -> "Load into the books").
REM
REM  You can also DRAG a report file onto this icon to send that exact file.
REM
REM  v4 CHANGE (S205) -- AF-1 / F-206. THIS SCRIPT COULD SAY "ACCEPTED" WHEN
REM  NOTHING WAS SENT, AND THEN BLOCK THAT REPORT FOR EVER.
REM
REM  v3 decided whether a report arrived by reading last_response.txt, and it
REM  never looked at the HTTP code. NEITHER response file was deleted before
REM  curl ran. So a send that failed without producing a body -- no network,
REM  a timeout -- left YESTERDAY'S body on disk, findstr found "ACCEPTED-FOR-
REM  REVIEW" in it, and the report's md5 was written into sent_hashes.txt.
REM  That file is the skip-list: the report could then never be sent again.
REM
REM  There were TWO stale files, not one. last_http.txt has the same problem,
REM  and worse: :one runs in a LOOP, so report #2 could inherit report #1's
REM  HTTP code inside a single run.
REM
REM  v4: both files are DELETED before curl; an accept needs HTTP 200 *and*
REM  the affirmative body; the md5 is written to sent_hashes.txt ONLY on a
REM  proven accept; and a run with ANY refusal now says REFUSED even if
REM  something else succeeded -- a partial failure must not read as success.
REM ===========================================================================

REM ---- CONFIG (SERVER + folder set once; token comes from token.txt) --------
set "SERVER=https://followup.dr-manoj.in/finance/api/marg-push"
set "MARG_USERS=D:\MARGERP\users"
set "TOKEN="
if exist "%~dp0token.txt" set /p TOKEN=<"%~dp0token.txt"
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
if not defined TOKEN (
  echo.
  echo  This sender is not set up yet - token.txt is missing or empty.
  echo  Make a file called  token.txt  in THIS folder, put the token on
  echo  one line, save, and run again. ^(Tell Dr. Manoj if unsure.^)
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
REM  v4: REFUSED is tested BEFORE success. A run that sent one report and
REM  failed another used to print ACCEPTED and say nothing about the failure.
if %FOUND%==0 (
  echo   NO REPORT FOUND  -  koi report nahi mili.
  echo   Pehle Marg mein BILL WISE SALES report chalayen
  echo   ^(With Item Deta. = Yes^), phir isse dobara chalayen.
) else if %REFUSED% GTR 0 (
  echo   REFUSED - %REFUSED% report^(s^) NAHI gayi. Upar ka message
  echo   dekhein aur Dr. Manoj ko batayen. Kuch bhi kho nahi gaya -
  echo   dated copy Sent\ folder mein hai.
) else if %SENTOK% GTR 0 (
  echo   ACCEPTED - report clinic server pahunch gayi hai.
  echo   Abhi khaate mein NAHI gayi - Dr. Manoj check karke
  echo   apply karenge. Aapka kaam ho gaya. Dhanyavaad.
) else if %SKIPPED% GTR 0 (
  echo   ALREADY SENT - yeh report pehle hi bheji ja chuki hai.
  echo   Ek dated copy Sent\ folder mein rakh di gayi hai.
  echo   Dobara load karni ho to Dr. Manoj ke workbench par
  echo   Sent\ folder se woh file "Load into the books" karein.
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

REM copy first (Marg may be writing; retry once), never touch the original.
REM this dated copy is KEPT no matter what happens below -- the archive.
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
echo      saved a dated copy: %WORK%

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
  echo      this exact report was ALREADY SENT earlier - not re-sending.
  echo      ^(the dated copy above is kept for re-loading on the workbench^)
  echo %DATE% %TIME% ^| %HASH% ^| SKIPPED-KEPT ^| %WORK%>> "%LOG%"
  set /a SKIPPED+=1
  goto :eof
)

echo      sending...
set "RESP=%HERE%last_response.txt"
set "HTTPF=%HERE%last_http.txt"
REM  AF-1: DELETE BOTH BEFORE ASKING. A file left from the last run is not an
REM  answer to this one. This single pair of lines is the whole fault.
del /q "%RESP%"  >nul 2>&1
del /q "%HTTPF%" >nul 2>&1
set "HTTP="
curl -s -m 90 -o "%RESP%" -w "%%{http_code}" -H "X-Finance-Marg: %TOKEN%" ^
     -F "file=@%WORK%;filename=REPORT_1.XLS" "%SERVER%" > "%HTTPF%" 2>nul
set /p HTTP=<"%HTTPF%"
REM  curl writes 000 when it never reached the server. If it wrote nothing at
REM  all, HTTP is still empty here -- and an empty HTTP must never be allowed
REM  to inherit the previous report's value on the next loop.
if not defined HTTP set "HTTP=000"

REM  AF-1: the code AND the body. Either one alone is not evidence.
set "VERDICT="
if "%HTTP%"=="200" findstr /c:"ACCEPTED-FOR-REVIEW" "%RESP%" >nul 2>&1 && set "VERDICT=ACCEPTED"
if defined VERDICT (
  echo      ACCEPTED for Dr. Manoj's review. ^(HTTP %HTTP%^)
  echo %DATE% %TIME% ^| %HASH% ^| ACCEPTED ^| %WORK%>> "%LOG%"
  echo %HASH%>> "%HASHES%"
  set /a SENTOK+=1
  goto :eof
)
set "VERDICT="
if "%HTTP%"=="200" findstr /c:"ALREADY-RECEIVED" "%RESP%" >nul 2>&1 && set "VERDICT=ALREADY"
if defined VERDICT (
  echo      the server already has this exact report ^(dated copy kept in Sent\^).
  echo %DATE% %TIME% ^| %HASH% ^| ALREADY-KEPT ^| %WORK%>> "%LOG%"
  echo %HASH%>> "%HASHES%"
  set /a SKIPPED+=1
  goto :eof
)
echo      REFUSED by the server ^(HTTP %HTTP%^). Server said:
type "%RESP%" 2>nul
echo.
echo %DATE% %TIME% ^| %HASH% ^| REFUSED HTTP %HTTP% ^| %WORK%>> "%LOG%"
set /a REFUSED+=1
goto :eof
