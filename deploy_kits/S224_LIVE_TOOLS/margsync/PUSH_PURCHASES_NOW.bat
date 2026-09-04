@echo off
REM ==========================================================================
REM  PUSH_PURCHASES_NOW.bat        S224 -- 04-Sep-2026
REM
REM  ONE DOUBLE-CLICK for the owner: prove the server accepts this machine's
REM  token (nothing written), then send every archived purchase export the
REM  server does not have yet, plus the vendor pairs and the pull heartbeat.
REM
REM  RUNS ON MANOJZ, where the archive and the token are.
REM  Everything it prints is also appended to _analysis\push_stock_log.txt.
REM ==========================================================================
setlocal
set PKIT=D:\dr-manoj-git\drmanoj-clinic-automation\deploy_kits\S224_MARG_PURCHASES
set OUTDIR=D:\Downloads\margsync\_analysis
set LOG=%OUTDIR%\push_stock_log.txt
set LAST=%OUTDIR%\push_purchases_lastrun.txt
if not exist "%OUTDIR%" mkdir "%OUTDIR%"
if not exist "%PKIT%\push_purchases.py" goto :no_kit
cd /d "%PKIT%"
echo.>> "%LOG%"
echo ############ PURCHASES NOW %DATE% %TIME% >> "%LOG%"
echo.
echo  Step 1 of 3 - checking the server accepts this machine's token ...
python -B push_purchases.py --verify > "%LAST%" 2>&1
set VRC=%ERRORLEVEL%
type "%LAST%"
echo -------- verify  exit %VRC% >> "%LOG%"
type "%LAST%" >> "%LOG%"
if not "%VRC%"=="0" goto :verify_failed
echo.
echo  Step 2 of 3 - vendor pairs and the pull heartbeat ...
python -B push_purchases.py --vendors --feed > "%LAST%" 2>&1
set FRC=%ERRORLEVEL%
type "%LAST%"
echo -------- vendors+feed  exit %FRC% >> "%LOG%"
type "%LAST%" >> "%LOG%"
echo.
echo  Step 3 of 3 - every purchase export not yet on the server ...
python -B push_purchases.py > "%LAST%" 2>&1
set PRC=%ERRORLEVEL%
type "%LAST%"
echo -------- push_purchases  exit %PRC% >> "%LOG%"
type "%LAST%" >> "%LOG%"
set OK=1
if not "%FRC%"=="0" set OK=0
if not "%PRC%"=="0" set OK=0
findstr /C:"REFUSING" "%LAST%" >nul 2>&1
if not errorlevel 1 set OK=0
echo.
if "%OK%"=="1" goto :done
echo  ============================================================
echo   NOT EVERYTHING WENT. Read the lines above: a line starting
echo   REFUSING or FAILED says what stopped and why. Nothing is lost -
echo   run this again after the cause is fixed; sent files are not resent.
echo   Full record: %LOG%
echo  ============================================================
echo.
pause
exit /b 2
:done
echo  ============================================================
echo   DONE. The purchase books on the server are up to date with
echo   the archive. Open the purchases page on the portal to see them.
echo  ============================================================
echo.
pause
exit /b 0
:verify_failed
echo.
echo  ============================================================
echo   STOPPED before sending anything. The server did not accept
echo   this machine's token (or is not reachable / not installed yet).
echo   The line above says which. Nothing was written anywhere.
echo  ============================================================
echo.
pause
exit /b 1
:no_kit
echo.
echo  Cannot find push_purchases.py under:
echo     %PKIT%
echo  Pull the repository on this PC first (PUBLISH_ALL / git pull).
echo.
pause
exit /b 1
