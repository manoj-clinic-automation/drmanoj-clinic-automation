@echo off
REM ── One-time revenue-ledger rebuild ───────────────────────────────────────
REM HOW TO USE: drag your wide Docterz consultation report (1 Apr -> today) onto
REM this file. OR place it in this folder named  consultation_report_full.csv
REM and just double-click. It backs up data\ first, then rebuilds.
cd /d "%~dp0"
if "%~1"=="" (
  python backfill_revenue.py
) else (
  python backfill_revenue.py "%~1"
)
echo.
pause
