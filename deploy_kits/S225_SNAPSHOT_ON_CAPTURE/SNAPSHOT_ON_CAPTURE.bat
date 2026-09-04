@echo off
REM SNAPSHOT_ON_CAPTURE.bat -- S225: push the Marg stock snapshot the moment a new whole-store
REM closing export lands in the archive (every 15 min, scheduled). See snapshot_on_capture.py.
setlocal
set HERE=%~dp0
cd /d "%HERE%"
python -B "%HERE%snapshot_on_capture.py" >> "D:\Downloads\margsync\_analysis\snapshot_on_capture_console.log" 2>&1
exit /b 0
