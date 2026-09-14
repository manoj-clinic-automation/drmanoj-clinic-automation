@echo off
REM ==========================================================================
REM  probe_conf_s260.bat -- proves cmd.exe reads machine.conf the same way the
REM  two real jobs do. It carries the SAME six lines as PULL_FROM_MEDICAL.bat
REM  and PUSH_STOCK_DAILY.bat and does nothing else: no pull, no push, no
REM  network. Run by the installer; safe to double-click any time.
REM ==========================================================================
setlocal
set "MEDHOST=FALLBACK_HOST"
set "MEDSHARE=FALLBACK_SHARE"
set "BASELINE=FALLBACK_DATE"
set "S260CONF=%~1"
if "%S260CONF%"=="" set "S260CONF=D:\Downloads\margsync\_config\machine.conf"
if exist "%S260CONF%" for /f "usebackq eol=# tokens=1,* delims==" %%A in ("%S260CONF%") do (
  if /i "%%~A"=="MEDICAL_HOST" if not "%%~B"=="" set "MEDHOST=%%~B"
  if /i "%%~A"=="MEDICAL_SHARE" if not "%%~B"=="" set "MEDSHARE=%%~B"
  if /i "%%~A"=="STOCK_BASELINE" if not "%%~B"=="" set "BASELINE=%%~B"
)
echo MEDHOST=%MEDHOST%
echo MEDSHARE=%MEDSHARE%
echo BASELINE=%BASELINE%
echo SHARE=\\%MEDHOST%\%MEDSHARE%
exit /b 0
