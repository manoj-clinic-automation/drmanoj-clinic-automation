@echo off
REM ===========================================================================
REM  PUBLISH_ALL_.bat  --  NOT THE PUBLISH. It just calls the real one.
REM
REM  This file was a stray second copy of PUBLISH_ALL.bat, and an OLDER one:
REM  it checked staged files for phone numbers only. The real PUBLISH_ALL.bat
REM  checks for phone numbers AND for credentials -- a token, a private key, a
REM  password left in a file -- which matters because this repository is
REM  PUBLIC (F-365). Anything published through this file was going out past
REM  the weaker of the two gates.
REM
REM  It is emptied rather than deleted so that a desktop shortcut pointing here
REM  keeps working, with the full gate, until the shortcut is moved. It is
REM  deleted once that is done.
REM
REM  THE REAL ONE, and the only one to make a shortcut to:
REM      D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat
REM ===========================================================================
echo.
echo  This is not the publish - it is the old spare copy, with the weaker check.
echo  Handing over to the real one now. Nothing is lost; carry on as normal.
echo.
echo  Make your desktop shortcut point here instead:
echo     D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat
echo.
call "D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat" %*
exit /b %ERRORLEVEL%
