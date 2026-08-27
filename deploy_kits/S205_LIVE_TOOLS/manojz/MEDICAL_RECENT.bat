@echo off
setlocal
REM ===========================================================================
REM  MEDICAL_RECENT.bat  (S201)  --  runs on MANOJZ. READ-ONLY.
REM
REM  Lists EVERY file written on the medical PC's D: drive in the last 3 days,
REM  of ANY type - xls, xlsx, pdf, csv, anything - anywhere on the drive.
REM
REM  WHY: the watcher only takes .xls/.xlsx from two folders. A report saved
REM  as PDF, or saved to a different folder, is invisible to the whole
REM  pipeline and no other tool would ever show it to you. This one does.
REM
REM  Writes: D:\Downloads\margsync\MEDICAL_RECENT.txt
REM ===========================================================================
set "HERE=%~dp0"

set "PY="
if exist "%HERE%pyportable\python.exe" set "PY=%HERE%pyportable\python.exe"
if not defined PY ( py -c "import sys" >nul 2>&1 && set "PY=py" )
if not defined PY ( python -c "import sys" >nul 2>&1 && set "PY=python" )
if not defined PY (
  echo  PROBLEM: no working Python on this PC. Tell Dr. Manoj.
  pause & exit /b 1
)

set "DAYS=%~1"
if "%DAYS%"=="" set "DAYS=3"

echo.
echo  Looking at everything written on the medical PC in the last %DAYS% day(s)...
echo.
"%PY%" "%HERE%medical_inventory.py" recent %DAYS%
echo.
pause
exit /b 0
