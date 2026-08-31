@echo off
setlocal enabledelayedexpansion
REM ===========================================================================
REM  GUARD_AND_SEND.bat  (S195, v2)  --  THE ONE ICON RECEPTION USES.
REM
REM  Marg names every export by SLOT, not by content (REPORT_1.XLS,
REM  REPORT_2.XLS, even REPORT_7JJ0J0TR7.XLS) and drops stock / purchase
REM  reports into the SAME folder under the SAME names. On 21-08-2026 the old
REM  sender said "NO REPORT FOUND" while a perfectly good REPORT_2.XLS sat
REM  there. So this never trusts a filename.
REM
REM  What it does, in order:
REM    1. FIND    - looks INSIDE every REPORT*.XLS and takes the newest that is
REM                 really a BILL WISE SALES report AND is complete
REM                 (contains "GRAND TOTAL"). Stock/purchase/truncated: skipped.
REM    2. GUARD   - runs guard_and_send.py, which uses marg_report.py - the SAME
REM                 parser the clinic server ingests with - to check the business
REM                 date, the day/grand totals arithmetic, the report variant and
REM                 completeness. Only a GREEN file may be sent.
REM    3. SEND    - hands the exact file to SEND_TO_CLINIC.bat, which is left
REM                 COMPLETELY UNCHANGED (the proven v3 sender, explicit path).
REM    4. ARCHIVE - the guard files a copy named by the report's own business
REM                 date, so Sent\ is readable months later.
REM
REM  If Python is not installed, step 2 is skipped and it still sends the
REM  content-checked file -- degraded, never blocked, and it says so.
REM
REM  USAGE  double-click            -> yesterday's report, with prompts
REM         GUARD_AND_SEND.bat any  -> any recent business date
REM         GUARD_AND_SEND.bat yesterday AUTO   -> unattended (Task Scheduler)
REM         GUARD_AND_SEND.bat any AUTO "D:\full\path\to\REPORT_2.XLS"
REM ===========================================================================
set "HERE=%~dp0"
set "MARG_USERS=D:\MARGERP\users"
set "GUARD=%HERE%guard_and_send.py"
set "SENDER=%HERE%SEND_TO_CLINIC.bat"
set "ALERT=%HERE%guard_alerts.txt"

set "EXPECT=%~1"
if "%EXPECT%"=="" set "EXPECT=yesterday"
set "MODE=%~2"
set "ONEFILE=%~3"

REM ---------- 1. FIND: identify by CONTENT, never by filename ---------------
if not defined ONEFILE (
  echo.
  echo  Looking inside every Marg export for a complete SALE report...
  for /f "usebackq delims=" %%F in (`powershell -NoProfile -ExecutionPolicy Bypass -File "%HERE%find_sale_report.ps1"`) do set "ONEFILE=%%F"
)
if not defined ONEFILE (
  echo.
  echo  ==========================================================
  echo   NO COMPLETE SALE REPORT FOUND  -  koi puri SALE report nahi mili.
  echo   ^(Stock / purchase reports are ignored on purpose. An incomplete
  echo    report is also refused - adhuri report nahi bhejenge.^)
  echo   Marg mein BILL WISE SALES chalayen ^(Report Type = Detail,
  echo   With Item Deta. = Yes^), phir isse dobara chalayen.
  echo  ==========================================================
  echo.
  if /i not "%MODE%"=="AUTO" pause
  exit /b 1
)
echo    found: !ONEFILE!
for %%T in ("!ONEFILE!") do echo    written: %%~tT

REM ---------- 2. GUARD: full validation, if Python is available -------------
set "PY="
if exist "%HERE%pyportable\python.exe" set "PY=%HERE%pyportable\python.exe"
if not defined PY ( py -c "import sys" >nul 2>&1 && set "PY=py" )
if not defined PY ( python -c "import sys" >nul 2>&1 && set "PY=python" )

if not defined PY goto :nopython
if not exist "%GUARD%" goto :noguard

echo.
echo  Checking the report ^(date, totals, completeness^)...
"%PY%" "%GUARD%" "!ONEFILE!" --expect %EXPECT% --alert "%ALERT%" --archive-dir "%HERE%Sent"
if errorlevel 1 (
  echo.
  echo  ==========================================================
  echo   NOT SENT - the report did not pass the check.
  echo   Reason is above, and in guard_alerts.txt
  echo   Report BHEJI NAHI GAYI - upar ka message dekhein.
  echo  ==========================================================
  echo.
  if /i not "%MODE%"=="AUTO" pause
  exit /b 2
)
echo    GREEN - validated.
goto :send

:nopython
echo.
echo  NOTE: Python is not installed, so the full check ^(date + totals^) was
echo        skipped. The file was still confirmed to be a complete SALE report.
goto :send

:noguard
echo.
echo  NOTE: guard_and_send.py is missing, so the full check was skipped.
goto :send

REM ---------- 3. SEND: the proven sender, unchanged, explicit path ----------
:send
echo.
if /i "%MODE%"=="AUTO" (
  echo. | call "%SENDER%" "!ONEFILE!"
) else (
  call "%SENDER%" "!ONEFILE!"
)

REM ---------- 4. DID IT ACTUALLY GO? ---------------------------------------
REM  SEND_TO_CLINIC.bat always exits 0, so read what the server actually said.
REM  It writes the body to last_response.txt and the code to last_http.txt.
REM  On 21-08-2026 a token mismatch returned 401 and the report sat unsent with
REM  nobody watching. Now a failure parks the file where it can be uploaded by
REM  hand and says so loudly.
set "OK="
if exist "%HERE%last_response.txt" (
  findstr /c:"ACCEPTED-FOR-REVIEW" "%HERE%last_response.txt" >nul 2>&1 && set "OK=1"
  findstr /c:"ALREADY-RECEIVED"    "%HERE%last_response.txt" >nul 2>&1 && set "OK=1"
)
if defined OK exit /b 0

set "HTTP=?"
if exist "%HERE%last_http.txt" set /p HTTP=<"%HERE%last_http.txt"
set "PARK=%HERE%NEEDS_UPLOAD"
if not exist "%PARK%" mkdir "%PARK%"
for %%N in ("!ONEFILE!") do copy /y "!ONEFILE!" "%PARK%\%%~nxN" >nul 2>&1
echo %DATE% %TIME% ^| HTTP !HTTP! ^| !ONEFILE!>> "%PARK%\NEEDS_UPLOAD.txt"
if exist "%HERE%last_response.txt" type "%HERE%last_response.txt" >> "%PARK%\NEEDS_UPLOAD.txt"
echo.>> "%PARK%\NEEDS_UPLOAD.txt"

echo.
echo  ==========================================================
echo   THE REPORT DID NOT REACH THE CLINIC SERVER ^(HTTP !HTTP!^).
echo   Report server tak NAHI pahunchi.
echo.
echo   A copy has been parked here for manual upload:
echo     %PARK%
echo   Dr. Manoj ko batayen - woh Hub se khud upload kar denge.
echo  ==========================================================
echo.
if /i not "%MODE%"=="AUTO" pause
exit /b 3
