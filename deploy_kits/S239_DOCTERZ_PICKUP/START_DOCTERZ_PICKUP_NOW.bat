@echo off
REM START_DOCTERZ_PICKUP_NOW.bat -- S239. Step 1: re-makes today's call list from the latest day and pushes it
REM to the VPS and straight into the call-list tabs. Step 2: switches on the 5-minute automatic pickup.
setlocal
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
echo.
echo 1 of 2 -- making today's call list current ...
python -B "%~dp0docterz_pickup.py" --refresh-latest
echo.
echo 2 of 2 -- switching on the automatic pickup ...
call "%~dp0REGISTER_DOCTERZ_PICKUP.bat"
