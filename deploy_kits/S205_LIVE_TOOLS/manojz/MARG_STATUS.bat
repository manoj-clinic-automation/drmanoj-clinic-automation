@echo off
setlocal
REM ===========================================================================
REM  MARG_STATUS.bat  (S201)  --  runs on MANOJZ. Read-only, no network.
REM
REM  Answers, in one screen: which trading days have a Marg sale report, which
REM  of those actually reached the clinic server, and which days have no
REM  report at all. Sundays are excluded - they are not trading days.
REM
REM  Also refreshes D:\Downloads\margsync\_UPLOAD_NOW, which holds exactly the
REM  reports that still need uploading by hand through the portal. When the
REM  automatic sender is working that folder is empty, and an empty folder is
REM  itself the answer.
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

"%PY%" "%HERE%marg_gate.py" status
echo.
if /i not "%~1"=="AUTO" pause
exit /b 0
