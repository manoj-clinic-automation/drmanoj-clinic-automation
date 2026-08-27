@echo off
setlocal
REM ===========================================================================
REM  MEDICAL_INVENTORY.bat  (S201)  --  runs on MANOJZ. READ-ONLY.
REM
REM  Lists every Marg export sitting on the medical PC and says, for each one,
REM  whether manojz has captured it. Anything marked NOT CAPTURED is a report
REM  the pipeline missed.
REM
REM  Writes nothing on the medical PC. Writes one file here:
REM     D:\Downloads\margsync\MEDICAL_INVENTORY.txt
REM
REM  Takes a minute or two - it hashes every file across the network.
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

echo.
echo  Looking at every Marg export on the medical PC. Please wait...
echo.
"%PY%" "%HERE%medical_inventory.py"
echo.
if /i not "%~1"=="AUTO" pause
exit /b 0
