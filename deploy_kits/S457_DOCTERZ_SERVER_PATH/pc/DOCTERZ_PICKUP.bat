@echo off
REM DOCTERZ_PICKUP.bat -- S239; S457 puts the fetch from the clinic server in front of the pickup.
REM Task Scheduler runs this every 5 minutes, hidden, through RUN_HIDDEN.vbs.
REM 1. docterz_fetch.py (S457): reception's two Docterz exports -- the consultation report and the follow-up log --
REM    are fetched from the clinic server into D:\Downloads. It asks at most once every 10 minutes and always ends 0,
REM    so step 2 always runs. Its log: D:\Downloads\DocterzArchive\_server_fetch_log.txt
REM    Its last pass: D:\Downloads\DocterzArchive\_server_fetch_last.txt
REM    To switch only the fetch off: make a file D:\Downloads\DocterzArchive\_server_fetch_OFF.txt
REM 2. One pass of docterz_pickup.py: Docterz exports in D:\Downloads are archived and fed to the tracker.
REM    Its log: D:\Downloads\DocterzArchive\_pickup_log.txt   Its heartbeat: D:\Downloads\DocterzArchive\_last_pass.txt
setlocal
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
if not exist "D:\Downloads\DocterzArchive" mkdir "D:\Downloads\DocterzArchive"
if exist "%~dp0docterz_fetch.py" python -B "%~dp0docterz_fetch.py" >> "D:\Downloads\DocterzArchive\_console.log" 2>&1
python -B "%~dp0docterz_pickup.py" >> "D:\Downloads\DocterzArchive\_console.log" 2>&1
exit /b 0
