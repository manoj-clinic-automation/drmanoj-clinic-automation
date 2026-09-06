@echo off
REM ==========================================================================
REM  PUSH_STOCK_NIGHTLY.bat        S224 -- 04-Sep-2026  (v2: step 3 added)
REM
REM  THE ONE THING THAT RUNS EACH NIGHT. Three steps, in order:
REM
REM    1  MARG'S OWN FIGURE   push_snapshot.py -- the closing-stock export
REM                           you took after the last bill
REM    2  OUR COMPUTED FIGURE PUSH_STOCK_DAILY.bat -- baseline + purchases
REM                           - sales + credit notes
REM    3  THE PURCHASE BOOKS  push_purchases.py (S224) -- vendors + pull
REM                           heartbeat, then every archived purchase export
REM                           not yet on the server (ledger: _analysis\
REM                           purchase_push_state.json). One export per POST.
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
set PKIT=D:\dr-manoj-git\drmanoj-clinic-automation\deploy_kits\S224_MARG_PURCHASES
set PURLAST=%OUTDIR%\push_purchases_lastrun.txt
set FEEDLAST=%OUTDIR%\push_feed_lastrun.txt

if not exist "%OUTDIR%" mkdir "%OUTDIR%"
if not exist "%KIT%\push_snapshot.py" goto :no_kit

echo.>> "%LOG%"
echo ############ NIGHTLY %DATE% %TIME% >> "%LOG%"

REM ---- 1 of 3 : Marg's own closing figure ---------------------------------
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

REM ---- 2 of 3 : our computed figure ----------------------------------------
if not exist "%DAILY%" goto :no_daily
call "%DAILY%"
set DRC=%ERRORLEVEL%
echo -------- step 2  push_expected  exit %DRC% >> "%LOG%"

REM ---- 3 of 3 : the purchase books (S224) -----------------------------------
REM  3a vendors + pull heartbeat, 3b every purchase export not yet sent.
REM  push_purchases prints REFUSING when it will not send; exit 0 alone is not
REM  proof (S221 rule), so its output is kept and searched like step 1.
set PUROK=0
if not exist "%PKIT%\push_purchases.py" (
  echo -------- step 3  push_purchases  SKIPPED - kit not found at %PKIT% >> "%LOG%"
  echo   STEP 3 SKIPPED - kit not found at %PKIT%
  goto :summary
)
cd /d "%PKIT%"
python -B push_purchases.py --vendors --feed > "%FEEDLAST%" 2>&1
set FRC=%ERRORLEVEL%
echo -------- step 3a vendors+feed   exit %FRC% >> "%LOG%"
type "%FEEDLAST%" >> "%LOG%"
python -B push_purchases.py > "%PURLAST%" 2>&1
set PRC=%ERRORLEVEL%
echo -------- step 3b push_purchases exit %PRC% >> "%LOG%"
type "%PURLAST%" >> "%LOG%"
set PUROK=1
if not "%FRC%"=="0" set PUROK=0
if not "%PRC%"=="0" set PUROK=0
findstr /C:"REFUSING" "%PURLAST%" >nul 2>&1
if not errorlevel 1 set PUROK=0
if "%PUROK%"=="1" (
  echo   step 3 OK - purchase books sent
) else (
  echo   STEP 3 DID NOT SEND - see %PURLAST% and %FEEDLAST%
)

:summary
echo.
if "%SNAPOK%"=="1" if "%DRC%"=="0" if "%PUROK%"=="1" goto :all
echo  ONE OR MORE STEPS DID NOT SEND.
echo    step 1 Marg figure   : %SNAPOK%   (1 = sent)
echo    step 2 computed      : exit %DRC% (0 = sent)
echo    step 3 purchases     : %PUROK%   (1 = sent)
echo  Details: %LOG%
echo.
exit /b 2

:all
echo  All three sent. The drift page has a comparable day and the purchase
echo  books are on the server.
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
