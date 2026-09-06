@echo off
REM EXPECTED_ON_CAPTURE.bat -- S225: compute and push OUR stock figure the moment a new sale report
REM lands in the archive (every 15 min, scheduled). See expected_on_capture.py.
setlocal
set HERE=%~dp0
cd /d "%HERE%"
python -B "%HERE%expected_on_capture.py" >> "D:\Downloads\margsync\_analysis\expected_on_capture_console.log" 2>&1
exit /b 0
