@echo off
REM RUN_AGENT.bat -- the manojz pipeline heartbeat. Read-only; writes one file.
REM Exit code 0 = healthy, 1 = needs a look. Schedule this every 15 minutes.
setlocal
set "MARGSYNC=D:\Downloads\margsync"
python "%~dp0manojz_agent.py"
set "RC=%ERRORLEVEL%"
echo.
echo exit code %RC%   (0 = healthy, 1 = needs a look)
endlocal & exit /b %RC%
