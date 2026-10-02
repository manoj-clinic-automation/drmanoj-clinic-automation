@echo off
setlocal
REM ======================================================================
REM  share_setup.cmd -- reception PC. Run ONCE, as administrator, by the
REM  owner. Lets the owner VIEW (read-only) THE WHOLE of this PC from his
REM  own devices over Tailscale, and closes what was open before:
REM    + a separate Windows account "clinicview" (the owner types its password)
REM    + one read-only share: ReceptionC -> C:\  (this PC has one disk, C:)
REM      everything is readable except the hidden AppData folder, where the
REM      browser keeps the staff's saved sign-ins
REM    + one firewall rule: file sharing from Tailscale addresses only
REM    - the Guest account switched off
REM    - the two old shares "C" (the whole C: drive) and "Users" removed
REM    - C:\ClinicAgent made writable by this PC's own user only
REM  Safe to run again. Writes C:\ClinicAgent\share_setup_log.txt.
REM ======================================================================
title Reception PC - viewing its files from the owner's devices (Tailscale only)
set "LOG=C:\ClinicAgent\share_setup_log.txt"
net session >nul 2>&1
if errorlevel 1 goto :notadmin
echo.
echo   Read-only viewing of this whole PC from your own devices, over Tailscale only.
echo.
net user clinicview >nul 2>&1
if not errorlevel 1 goto :haveuser
echo   YOUR ONE STEP: choose a NEW password for the viewing account "clinicview".
echo   Nothing shows while you type. Type it, press Enter, type it again, press Enter.
echo.
net user clinicview * /add /passwordchg:no /comment:"Read-only viewing over Tailscale - owner"
if errorlevel 1 goto :nouser
goto :userdone
:haveuser
echo   The account clinicview is already there - its password is kept as it is.
:userdone
echo.
echo   working...
call :rest > "%LOG%" 2>&1
type "%LOG%"
echo.
echo   FINISHED. You can close this window.
endlocal
exit /b 0

:notadmin
echo.
echo   This window is not running as administrator, so nothing was changed.
echo   Close it and use the line from Claude again, and click Yes when Windows asks.
exit /b 1

:nouser
echo.
echo   STOP: the account was not created (the two passwords may not have matched).
echo   Nothing else was changed. Close this window and run the same line again.
exit /b 1

:rest
echo share_setup %DATE% %TIME%
powershell -NoProfile -Command "Set-LocalUser -Name clinicview -PasswordNeverExpires $true"
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon\SpecialAccounts\UserList" /v clinicview /t REG_DWORD /d 0 /f
net user Guest /active:no
net share C /delete /y
net share Users /delete /y
net share ReceptionView /delete /y
net share ReceptionC /delete /y
net share ReceptionD /delete /y
net share ReceptionC=C:\ /GRANT:clinicview,READ /REMARK:"Read-only view of C: for the owner, over Tailscale"
icacls "C:\Users\dell" /grant clinicview:(RX) /Q
for /d %%D in ("C:\Users\dell\*") do if /i not "%%~nxD"=="AppData" icacls "%%D" /grant clinicview:(OI)(CI)(RX) /Q
icacls "C:\ClinicAgent" /inheritance:r /grant:r dell:(OI)(CI)(F) SYSTEM:(OI)(CI)(F) Administrators:(OI)(CI)(F) /Q
netsh advfirewall firewall delete rule name="Clinic - file sharing over Tailscale only"
netsh advfirewall firewall add rule name="Clinic - file sharing over Tailscale only" dir=in action=allow protocol=TCP localport=445 remoteip=100.64.0.0/10
echo.
echo --- result ---
net share ReceptionC
net share | findstr /i "Reception"
net user clinicview | findstr /i /c:"Account active" /c:"Password last set"
net user Guest | findstr /i /c:"Account active"
exit /b 0
