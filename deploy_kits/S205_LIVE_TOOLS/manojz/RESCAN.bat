@echo off
setlocal
REM ===========================================================================
REM  RESCAN.bat  (S201 Part 0)  --  runs on MANOJZ.
REM
REM  Re-judges every report sitting in MargArchive\_UNKNOWN and \_REFUSED
REM  against the CURRENT signature registry, and corrects its index row.
REM
REM  WHY: marg_router blacklists a file by content hash the moment it is
REM  indexed, and index.csv is append-only. So a report filed as UNKNOWN before
REM  its signature existed could never be re-examined, and its row could never
REM  be corrected. Every signature added stranded whatever it should have
REM  rescued. Ten real reports were stuck this way.
REM
REM  A VERIFIED report is NEVER touched. Quarantine only.
REM
REM  Run with no argument for a DRY RUN. Run as  RESCAN.bat APPLY  to do it.
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
"%PY%" -c "import sys;print('  python here is', sys.version.split()[0])"
echo.
if /i "%~1"=="APPLY" (
  echo  APPLYING - files will be re-filed and index rows corrected.
  "%PY%" "%HERE%marg_rescan.py" --apply
) else if /i "%~1"=="TIDY" (
  echo  TIDYING - rescued reports move out of quarantine into _rescued\.
  "%PY%" "%HERE%marg_rescan.py" --tidy --apply
) else (
  echo  DRY RUN - nothing will be written. Use  RESCAN.bat APPLY  to do it.
  "%PY%" "%HERE%marg_rescan.py"
)
echo.
pause
exit /b 0
