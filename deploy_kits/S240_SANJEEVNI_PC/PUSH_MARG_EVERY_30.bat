@echo off
REM PUSH_MARG_EVERY_30.bat -- S240. Task MargPushEvery30 runs this every 30 minutes (at :15 and :45),
REM hidden through RUN_HIDDEN.vbs, allowed on battery. It only SENDS what is already archived:
REM   1. push_purchases.py  -- purchase exports the server has not had yet (was only at 22:30)
REM   2. push_sale_bills.py -- the sale bills' money rows the server has not had yet
REM Both keep a ledger and the server is idempotent, so a run with nothing new costs a second.
REM Log: D:\Downloads\margsync\_analysis\push_every30_log.txt
setlocal
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set "LOG=D:\Downloads\margsync\_analysis\push_every30_log.txt"
echo ==== %DATE% %TIME% >> "%LOG%"
python -B "D:\dr-manoj-git\drmanoj-clinic-automation\deploy_kits\S224_MARG_PURCHASES\push_purchases.py" >> "%LOG%" 2>&1
python -B "%~dp0push_sale_bills.py" >> "%LOG%" 2>&1
exit /b 0
