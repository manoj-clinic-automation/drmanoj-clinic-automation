@echo off
REM S386 -- run ON THE MEDICAL PC, by double-click. Makes the Marg agent start for every Windows account.
setlocal
cd /d "%~dp0"
set "PY=D:\SendToClinic\pyportable\python.exe"
if not exist "%PY%" goto nopy
"%PY%" -B "%~dp0install_s386.py"
echo.
pause
exit /b 0
:nopy
echo  Python not found at %PY% - tell Claude. Nothing was changed.
pause
exit /b 1
