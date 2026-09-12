@echo off
setlocal
title MEDICAL PC - START AT POWER ON
net session >nul 2>&1
if errorlevel 1 (
  echo Asking for administrator rights...
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)
cls
echo ================================================================
echo    MEDICAL PC  --  MAKE THE CLINIC AGENT START AT POWER ON
echo ================================================================
echo.
echo    Today the clinic agent starts only when somebody logs in.
echo    After this, the PC logs itself in when it is switched on,
echo    so exports are captured and pushed even if nobody touches it.
echo.
echo    STEP 1 of 2  --  doing it now, automatically.
echo.
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\PasswordLess\Device" /v DevicePasswordLessBuildVersion /t REG_DWORD /d 0 /f >nul 2>&1
if errorlevel 1 (
  echo    [FAILED] Could not change the sign-in setting.
  echo    Stop here and tell Claude. Nothing has been changed.
  echo.
  pause
  exit /b 1
)
echo    [OK] Done.
echo.
echo ================================================================
echo    STEP 2 of 2  --  a small window will open when you press a key
echo ================================================================
echo.
echo      1.  Click the account this PC normally uses.
echo      2.  UNTICK the box that says:
echo            "Users must enter a user name and password
echo             to use this computer"
echo      3.  Click OK.
echo      4.  Type that account's Windows password twice, click OK.
echo.
echo    The password is typed by you into Windows itself.
echo    It is not stored by us and it never leaves this PC.
echo.
echo    Nothing else to do. Then restart the PC once to prove it.
echo.
pause
start "" netplwiz
echo.
echo    The sign-in window is open. Close this black window when done.
echo.
pause
exit /b
