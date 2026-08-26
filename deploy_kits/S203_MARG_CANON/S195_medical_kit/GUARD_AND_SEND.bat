@echo off
setlocal enabledelayedexpansion
REM ===========================================================================
REM  GUARD_AND_SEND.bat  (S195)  --  validate BEFORE sending.
REM
REM  For each  D:\MARGERP\users\*\report\REPORT_1.XLS  it runs guard_and_send.py
REM  (the SAME checker the clinic server uses) and calls SEND_TO_CLINIC.bat ONLY
REM  for files that pass:  single-day Detail export, ends with GRAND TOTAL (not a
REM  truncated partial), arithmetic balances, and a sane business date. A bad or
REM  stale file is NEVER sent -- the reason is shown and written to guard_alerts.txt.
REM
REM  It does NOT change SEND_TO_CLINIC.bat and does NOT touch D:\MARGERP. The
REM  maker/checker split is unchanged: the sender only STAGES for review; Dr Manoj
REM  alone applies.
REM
REM  Put this file in the SAME folder as SEND_TO_CLINIC.bat, guard_and_send.py and
REM  marg_report.py (i.e. D:\SendToClinic).
REM
REM  USAGE (reception, interactive):   just double-click this file.
REM  USAGE (with a date rule):         GUARD_AND_SEND.bat today
REM                                    GUARD_AND_SEND.bat yesterday
REM                                    GUARD_AND_SEND.bat 2026-08-19
REM                                    GUARD_AND_SEND.bat any        (default)
REM  USAGE (unattended / Task Scheduler, no prompts): add AUTO as 2nd word:
REM                                    GUARD_AND_SEND.bat any AUTO
REM ===========================================================================
set "HERE=%~dp0"
set "MARG_USERS=D:\MARGERP\users"
set "GUARD=%HERE%guard_and_send.py"
set "SENDER=%HERE%SEND_TO_CLINIC.bat"
set "ALERT=%HERE%guard_alerts.txt"

set "EXPECT=%~1"
if "%EXPECT%"=="" set "EXPECT=any"
set "MODE=%~2"

REM --- find a WORKING Python: bundled portable first, then py, then python ---
REM     (the Microsoft Store stub answers 'where python' but fails to run, so we
REM      test each candidate by actually running it.)
set "PY="
if exist "%HERE%pyportable\python.exe" set "PY=%HERE%pyportable\python.exe"
if not defined PY ( py -c "import sys" >nul 2>&1 && set "PY=py" )
if not defined PY ( python -c "import sys" >nul 2>&1 && set "PY=python" )

if not defined PY (
  echo.
  echo  PROBLEM: no working Python on this PC. The guard needs it.
  echo  Fix: unzip pyportable.zip here so pyportable\python.exe exists
  echo  ^(or install Python^). See SETUP_S195_MARG.md.  xlrd is already bundled.
  echo.
  if /i not "%MODE%"=="AUTO" pause
  exit /b 1
)

set /a FOUND=0
set /a GREEN=0
set /a BLOCKED=0

for /d %%U in ("%MARG_USERS%\*") do (
  if exist "%%U\report\REPORT_1.XLS" (
    set /a FOUND+=1
    echo.
    echo  --- checking %%U\report\REPORT_1.XLS   ^(expect=%EXPECT%^)
    "%PY%" "%GUARD%" "%%U\report\REPORT_1.XLS" --expect %EXPECT% --alert "%ALERT%" --archive-dir "%HERE%Sent"
    if !errorlevel! EQU 0 (
      echo      GREEN - validated. Sending...
      if /i "%MODE%"=="AUTO" (
        echo. | call "%SENDER%" "%%U\report\REPORT_1.XLS"
      ) else (
        call "%SENDER%" "%%U\report\REPORT_1.XLS"
      )
      set /a GREEN+=1
    ) else (
      echo      BLOCKED - NOT sent. Reason is above and in guard_alerts.txt
      set /a BLOCKED+=1
    )
  )
)

echo.
echo  ==========================================================
if !FOUND! EQU 0 (
  echo   NO REPORT FOUND - koi REPORT_1.XLS nahi mili.
  echo   Pehle Marg mein BILL WISE SALES report chalayen
  echo   ^(Report Type = Detail, With Item Deta. = Yes^), phir dobara.
) else if !GREEN! GTR 0 (
  echo   !GREEN! report^(s^) check hokar bheji gayi. !BLOCKED! blocked.
  echo   Ab Dr. Manoj check karke apply karenge. Dhanyavaad.
) else (
  echo   Koi report nahi bheji - !BLOCKED! file check mein fail hui.
  echo   guard_alerts.txt dekhein aur Dr. Manoj ko batayen.
)
echo  ==========================================================
echo.
if /i not "%MODE%"=="AUTO" pause
exit /b 0
