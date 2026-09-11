@echo off
REM REGISTER_DOCTERZ_PICKUP.bat -- S239, rev S240. Registers the DocterzPickup task (every 5 minutes, hidden),
REM then runs the first pass at once and shows its result. Safe to run again: /F replaces the task.
REM S240 (F-430): schtasks creates every task "start only on AC power". On battery the pickup silently
REM stopped at 11:55 on 11-Sep (the F-314 shape again). The PowerShell line below clears both battery flags.
REM Undo: schtasks /Delete /TN "DocterzPickup" /F
schtasks /Create /TN "DocterzPickup" /TR "wscript.exe \"%~dp0RUN_HIDDEN.vbs\" \"%~dp0DOCTERZ_PICKUP.bat\"" /SC MINUTE /MO 5 /F
powershell -NoProfile -Command "$s=(Get-ScheduledTask -TaskName 'DocterzPickup').Settings; $s.DisallowStartIfOnBatteries=$false; $s.StopIfGoingOnBatteries=$false; $s.StartWhenAvailable=$true; Set-ScheduledTask -TaskName 'DocterzPickup' -Settings $s | Out-Null; 'battery flags cleared'"
echo.
echo First pass running now...
call "%~dp0DOCTERZ_PICKUP.bat"
echo.
type "D:\Downloads\DocterzArchive\_last_pass.txt"
echo.
echo If the line above starts with END and says ok, the pickup is live. Nothing more to do.
