@echo off
REM REGISTER_DOCTERZ_PICKUP.bat -- S239. Registers the DocterzPickup task (every 5 minutes, hidden),
REM then runs the first pass at once and shows its result. Safe to run again: /F replaces the task.
REM Undo: schtasks /Delete /TN "DocterzPickup" /F
schtasks /Create /TN "DocterzPickup" /TR "wscript.exe \"%~dp0RUN_HIDDEN.vbs\" \"%~dp0DOCTERZ_PICKUP.bat\"" /SC MINUTE /MO 5 /F
echo.
echo First pass running now...
call "%~dp0DOCTERZ_PICKUP.bat"
echo.
type "D:\Downloads\DocterzArchive\_last_pass.txt"
echo.
echo If the line above starts with END and says ok, the pickup is live. Nothing more to do.
