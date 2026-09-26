@echo off
REM APPLY_S415.bat -- kit S415_NIGHTLY_SELFHEAL (F-630). OPTIONAL: the nightly applies this by itself at its next run.
REM Double-click only to apply it NOW and to read at once why the 23-Sep and 25-Sep runs were missed.
REM It creates the 07:30 / log-on morning task, sets wake-to-run on the 03:10 task, and writes
REM   D:\Downloads\_kbtools\reports\TASK_HISTORY_LATEST.txt
setlocal
set TOOLS=%~dp0
powershell -NoProfile -ExecutionPolicy Bypass -File "%TOOLS%task_selfheal.ps1"
echo.
echo ============================================================
echo  S415 applied. The history is in %TOOLS%reports\TASK_HISTORY_LATEST.txt
echo ============================================================
pause
