@echo off
REM ===========================================================================
REM  MAKE_DESKTOP_ICON.bat  -  run ONCE on the MEDICAL PC, from D:\SendToClinic.
REM
REM  Creates a desktop shortcut named "SEND TO CLINIC" pointing at
REM  SEND_TO_CLINIC.bat, wearing SendToClinic.ico, minimized-window start.
REM  Both files must sit in the SAME folder as this script.
REM ===========================================================================
set "HERE=%~dp0"
if not exist "%HERE%SEND_TO_CLINIC.bat" ( echo !! SEND_TO_CLINIC.bat not found beside this script & pause & exit /b 1 )
if not exist "%HERE%SendToClinic.ico"   ( echo !! SendToClinic.ico not found beside this script & pause & exit /b 1 )

powershell -NoProfile -Command ^
  "$W = New-Object -ComObject WScript.Shell; " ^
  "$desk = [Environment]::GetFolderPath('Desktop'); " ^
  "$s = $W.CreateShortcut((Join-Path $desk 'SEND TO CLINIC.lnk')); " ^
  "$s.TargetPath = '%HERE%SEND_TO_CLINIC.bat'; " ^
  "$s.WorkingDirectory = '%HERE%'.TrimEnd('\'); " ^
  "$s.IconLocation = '%HERE%SendToClinic.ico'; " ^
  "$s.Description = 'Marg report clinic ko bhejein - Send the Marg report to the clinic server'; " ^
  "$s.Save()"

if exist "%USERPROFILE%\Desktop\SEND TO CLINIC.lnk" (
  echo.
  echo  DONE - desktop par "SEND TO CLINIC" icon ban gaya hai.
  echo  Roz subah: Marg mein BILL WISE report chalayen, phir is icon
  echo  ko double-click karen.
) else (
  echo  Shortcut creation could not be confirmed - check the Desktop manually.
)
echo.
pause
