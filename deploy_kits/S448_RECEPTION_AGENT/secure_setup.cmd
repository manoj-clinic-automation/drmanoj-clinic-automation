@echo off
setlocal
title Clinic - security setup for the Reception PC (once, as administrator)
REM  secure_setup.cmd -- session 290, 02-Oct-2026 (F-688). Run ELEVATED, once. Safe to run again.
REM    + Windows Firewall ON for all three profiles (it was found OFF)
REM    + file sharing reachable from Tailscale addresses only; Windows' own file-and-printer-sharing rules off
REM    + the Sentinel licence server's ports left open to the clinic's own network
REM    - the share "G" (the whole Google Drive letter) and a stale printer share removed
REM    Windows Security's exclusions are READ into the log, nothing about them is changed, and no scan is started.
REM    AnyDesk, UltraViewer, Tailscale, Google Drive and the agent work outwards and are not touched.
set "ROOT=C:\ClinicAgent"
set "LOG=%ROOT%\secure_setup_log.txt"
net session >nul 2>&1
if errorlevel 1 goto :notadmin
call :main > "%LOG%" 2>&1
type "%LOG%"
echo.
echo   Done. This window closes by itself.
timeout /t 15 >nul
exit /b 0

:notadmin
echo NOT ELEVATED %DATE% %TIME% - nothing was changed> "%LOG%"
echo   This must run as administrator. Nothing was changed.
timeout /t 15 >nul
exit /b 1

:main
echo secure_setup.cmd S290 -- %DATE% %TIME% -- computer %COMPUTERNAME%
echo.
echo ==== BEFORE ====
netsh advfirewall show allprofiles state
net share
echo ---- Windows Security exclusions (read only) ----
powershell -NoProfile -Command "$p=Get-MpPreference; 'paths: ' + (@($p.ExclusionPath) -join ' ; '); 'processes: ' + (@($p.ExclusionProcess) -join ' ; '); 'extensions: ' + (@($p.ExclusionExtension) -join ' ; '); 'real-time protection off: ' + $p.DisableRealtimeMonitoring"
echo.
echo ==== 1. the rules first, so nothing wanted is cut off when the firewall comes on ====
netsh advfirewall firewall delete rule name="Clinic - file sharing over Tailscale only" >nul 2>&1
netsh advfirewall firewall add rule name="Clinic - file sharing over Tailscale only" dir=in action=allow protocol=TCP localport=445 remoteip=100.64.0.0/10
netsh advfirewall firewall delete rule name="Clinic - licence server for the clinic network" >nul 2>&1
netsh advfirewall firewall add rule name="Clinic - licence server for the clinic network" dir=in action=allow protocol=TCP localport=6002,7001,7002 remoteip=LocalSubnet
netsh advfirewall firewall add rule name="Clinic - licence server for the clinic network" dir=in action=allow protocol=UDP localport=6001,6002,7001,7002 remoteip=LocalSubnet
echo ---- Windows' own file-and-printer-sharing rules off (the share is for Tailscale only) ----
netsh advfirewall firewall set rule group="File and Printer Sharing" new enable=No
echo.
echo ==== 2. the firewall ON, all three profiles: inbound blocked unless a rule allows it ====
netsh advfirewall set allprofiles firewallpolicy blockinbound,allowoutbound
netsh advfirewall set allprofiles state on
echo.
echo ==== 3. shares that should not be there ====
net share G /delete /y
reg delete "HKLM\SYSTEM\CurrentControlSet\Services\LanmanServer\Shares" /v "HP Laser 1003-1008" /f
reg delete "HKLM\SYSTEM\CurrentControlSet\Services\LanmanServer\Shares\Security" /v "HP Laser 1003-1008" /f
echo.
echo ==== AFTER ====
netsh advfirewall show allprofiles state
netsh advfirewall firewall show rule name="Clinic - file sharing over Tailscale only"
netsh advfirewall firewall show rule name="Clinic - licence server for the clinic network"
net share
net user Guest | findstr /i /c:"Account active"
echo.
echo DONE %DATE% %TIME%
exit /b 0
