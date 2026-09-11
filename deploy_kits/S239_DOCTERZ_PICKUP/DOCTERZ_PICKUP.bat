@echo off
REM DOCTERZ_PICKUP.bat -- S239. Task Scheduler runs this every 5 minutes, hidden, through RUN_HIDDEN.vbs.
REM One pass of docterz_pickup.py: Docterz exports in D:\Downloads are archived and fed to the tracker.
REM Its log: D:\Downloads\DocterzArchive\_pickup_log.txt   Its heartbeat: D:\Downloads\DocterzArchive\_last_pass.txt
setlocal
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
if not exist "D:\Downloads\DocterzArchive" mkdir "D:\Downloads\DocterzArchive"
python -B "%~dp0docterz_pickup.py" >> "D:\Downloads\DocterzArchive\_console.log" 2>&1
exit /b 0
