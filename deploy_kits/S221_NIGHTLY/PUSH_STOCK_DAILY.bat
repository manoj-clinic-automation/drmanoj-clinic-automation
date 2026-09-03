@echo off
REM ==========================================================================
REM  PUSH_STOCK_DAILY.bat        v2 -- 03-Sep-2026 (S221)
REM
REM  Sends the clinic server what SHOULD be on the shelf today:
REM
REM      baseline stock + purchases - vendor returns - sales + credit notes
REM
REM  RUNS ON MANOJZ, where the archive and the token are. Not on the medical PC.
REM
REM  Sales arrive on their own every morning. Purchases arrive when Amir
REM  visits, and reach these books ONLY through his two exports, so a purchase
REM  that was not exported has not happened as far as this ledger is concerned.
REM
REM  EVERY RUN IS LOGGED, and that is the point. A run that stops working
REM  leaves evidence behind instead of one line on a console nobody reads.
REM
REM  Run it by hand, or schedule it for mid-morning, after the sale report
REM  has landed.
REM
REM  ------------------------------------------------------------------------
REM  WHAT CHANGED IN v2. Both faults showed up on the very first run,
REM  03-Sep-2026 08:54.
REM
REM  1  A PINNED BASELINE.
REM     Without --baseline, push_expected takes the NEWEST closing export in
REM     the archive as its starting point. The stock export is now near-daily,
REM     so the baseline would move to today every day -- and there is never a
REM     sale day AFTER today. It would refuse every morning, for ever, and the
REM     drift page would never fill.
REM     It would be pointless even if it worked: a figure computed FROM
REM     today's export cannot be a second opinion ON today's export.
REM     So the baseline is pinned and the computed figure walks forward from it
REM     on sales and purchases alone. MOVE THIS DATE when a fresh full closing
REM     export is taken and you want to restart from it -- monthly is the
REM     intent, not daily.
REM     IT MUST BE A DATE A CLOSING EXPORT ACTUALLY EXISTS FOR. Checked
REM     03-Sep against the archive: the available dates are ... 27-08-2026 and
REM     02-09-2026. There is NO 01-09 export, so a baseline of 01-09 would have
REM     refused every morning -- the same failure this pin exists to prevent,
REM     reintroduced by the pin itself. Caught before the first scheduled run.
REM
REM  2  A REFUSAL IS NOT A SUCCESS.
REM     push_expected exits 0 when it refuses ("REFUSING: no sale report dated
REM     after the baseline"), so v1 printed "Done" while nothing was sent.
REM     Nobody reading the window would have known. This run's own output is
REM     now kept separately and searched, and the window says what happened.
REM     (F-146's shape: a refusal that reads like a save.)
REM ==========================================================================
setlocal
set KIT=D:\dr-manoj-git\drmanoj-clinic-automation\deploy_kits\S208_STOCK_LEDGER
set OUTDIR=D:\Downloads\margsync\_analysis
set LOG=%OUTDIR%\push_stock_log.txt
set LAST=%OUTDIR%\push_stock_lastrun.txt

REM  The starting point the computed figure walks forward from. NOT today's
REM  export -- see note 1 above. Move it on a fresh full re-baseline.
set BASELINE=02-09-2026

if not exist "%OUTDIR%" mkdir "%OUTDIR%"
if not exist "%KIT%\push_expected.py" goto :no_kit

cd /d "%KIT%"
if errorlevel 1 goto :no_kit

REM  -B keeps python from writing __pycache__ inside the repository, which
REM  .gitignore blocks and which has broken a publish before.
python -B push_expected.py --baseline %BASELINE% > "%LAST%" 2>&1
set RC=%ERRORLEVEL%

echo.>> "%LOG%"
echo ======== %DATE% %TIME%   baseline %BASELINE% >> "%LOG%"
type "%LAST%" >> "%LOG%"
echo exit code %RC% >> "%LOG%"

if not "%RC%"=="0" goto :failed

REM  A clean exit code is not proof anything was sent. THIS run's own output
REM  is what gets searched -- not the whole log, which holds every past run.
findstr /C:"REFUSING" "%LAST%" >nul 2>&1
if not errorlevel 1 goto :refused
goto :ok

:refused
echo.
echo  NOTHING WAS SENT - the script refused.
echo  The reason is in:
echo     %LAST%
echo  Most often: no sale report dated after the baseline %BASELINE%,
echo  or a purchase export that cannot be dated.
echo.
exit /b 3

:failed
echo.
echo  NOT SENT - exit code %RC%
echo  The reason is in:
echo     %LAST%
echo  Nothing was recorded on the server.
echo.
exit /b %RC%

:ok
echo.
echo  Sent. Details appended to:
echo     %LOG%
echo.
exit /b 0

:no_kit
echo.
echo  Cannot find push_expected.py under:
echo     %KIT%
echo  This runs on MANOJZ, not the medical PC. Publish first, or tell Claude
echo  the folder has moved.
echo.
exit /b 1
