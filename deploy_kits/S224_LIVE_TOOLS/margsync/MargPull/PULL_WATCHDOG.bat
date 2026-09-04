@echo off
REM ==========================================================================
REM  PULL_WATCHDOG.bat        S224 -- 04-Sep-2026   (A3: the pull-asleep shout)
REM
REM  Runs every 15 minutes from Task Scheduler. Reads _last_pull.txt; if the
REM  last END is older than 35 minutes AND this watchdog itself has been
REM  running (so the PC was awake), it prepends a red PULL ASLEEP line to
REM  MARG_PICTURE.txt, writes _pull_alarm.txt, and tells the server through
REM  push_purchases.py --feed. When the pull wakes, it clears both.
REM
REM  Nothing here messages anyone directly: manojz has no outbound shout
REM  channel. The server tile is the shout.
REM
REM  Register (one line, run as the logged-in user):
REM  schtasks /Create /TN "MargPullWatchdog" /TR "\"D:\Downloads\margsync\MargPull\PULL_WATCHDOG.bat\"" /SC MINUTE /MO 15 /F
REM ==========================================================================
setlocal
set HERE=%~dp0
if not exist "%HERE%_logs" mkdir "%HERE%_logs"
cd /d "%HERE%"
python -B "%HERE%pull_watchdog.py" >> "%HERE%_logs\watchdog_console.log" 2>&1
exit /b 0
