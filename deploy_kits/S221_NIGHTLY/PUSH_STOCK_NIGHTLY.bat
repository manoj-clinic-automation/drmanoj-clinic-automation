@echo off
REM ==========================================================================
REM  PUSH_STOCK_NIGHTLY.bat        S221 -- 03-Sep-2026
REM
REM  THE ONE THING THAT RUNS EACH NIGHT. Two steps, in order:
REM
REM    1  MARG'S OWN FIGURE   push_snapshot.py -- the closing-stock export
REM                           you took after the last bill
REM    2  OUR COMPUTED FIGURE PUSH_STOCK_DAILY.bat -- baseline + purchases
REM                           - sales + credit notes
REM
REM  Both land on the server against the SAME as-on date, which is the whole
REM  point: only a day that has both figures can be compared, and that
REM  comparison is what the drift page exists for.
REM
REM  RUNS ON MANOJZ, where the archive and the token are. Not the medical PC.
REM
REM  Step 2 is not duplicated here -- it calls PUSH_STOCK_DAILY.bat, so the
REM  pinned baseline and the refusal check live in exactly one place.
REM
REM  IT DOES NOT EXPORT ANYTHING FROM MARG. Both reports still have to be
REM  taken by hand, after closing. This sends what is already in the archive.
REM ==========================================================================
setlocal
set KIT=D:\dr-manoj-git\drmanoj-clinic-automation\deploy_kits\S208_STOCK_LEDGER
set OUTDIR=D:\Downloads\margsync\_analysis
set LOG=%OUTDIR%\push_stock_log.txt
set SNAPLAST=%OUTDIR%\push_snapshot_lastrun.txt
set DAILY=D:\Downloads\margsync\PUSH_STOCK_DAILY.bat

if not exist "%OUTDIR%" mkdir "%OUTDIR%"
if not exist "%KIT%\push_snapshot.py" goto :no_kit

echo.>> "%LOG%"
echo ############ NIGHTLY %DATE% %TIME% >> "%LOG%"

REM ---- 1 of 2 : Marg's own closing figure ---------------------------------
cd /d "%KIT%"
python -B push_snapshot.py > "%SNAPLAST%" 2>&1
set SRC=%ERRORLEVEL%
echo -------- step 1  push_snapshot  exit %SRC% >> "%LOG%"
type "%SNAPLAST%" >> "%LOG%"

REM  A clean exit code is not proof anything was sent (the lesson of v1 of the
REM  daily bat). push_snapshot REFUSES a category-filtered export rather than
REM  sending 81 rows as if they were the shop -- and that refusal must read as
REM  a refusal.
set SNAPOK=1
if not "%SRC%"=="0" set SNAPOK=0
findstr /C:"REFUSING" "%SNAPLAST%" >nul 2>&1
if not errorlevel 1 set SNAPOK=0

if "%SNAPOK%"=="1" (
  echo   step 1 OK - Marg's figure sent
) else (
  echo   STEP 1 DID NOT SEND - see %SNAPLAST%
)

REM ---- 2 of 2 : our computed figure ----------------------------------------
if not exist "%DAILY%" goto :no_daily
call "%DAILY%"
set DRC=%ERRORLEVEL%
echo -------- step 2  push_expected  exit %DRC% >> "%LOG%"

echo.
if "%SNAPOK%"=="1" if "%DRC%"=="0" goto :both
echo  ONE OR BOTH STEPS DID NOT SEND.
echo    step 1 Marg figure   : %SNAPOK%   (1 = sent)
echo    step 2 computed      : exit %DRC% (0 = sent)
echo  Details: %LOG%
echo.
exit /b 2

:both
echo  Both sent. The drift page has a comparable day.
echo  Details: %LOG%
echo.
exit /b 0

:no_daily
echo.
echo  Cannot find %DAILY%
echo.
exit /b 1

:no_kit
echo.
echo  Cannot find push_snapshot.py under:
echo     %KIT%
echo  This runs on MANOJZ, not the medical PC.
echo.
exit /b 1
