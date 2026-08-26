@echo off
setlocal enableextensions
title Tidy the medical PC  -  MOVES, never deletes
color 0B
REM ===========================================================================
REM  TIDY_MEDICAL_PC.bat   --   DOUBLE-CLICK ON THE MEDICAL PC
REM
REM  Two setup leftovers sit in D:\SendToClinic taking 15 MB:
REM     pyportable.zip              11.9 MB  - the installer for the bundled
REM                                            python, which is already unpacked
REM     SCREEN REC 21 8 2026.zip     3.4 MB  - a screen recording from setup
REM
REM  Neither is used by anything. Both are excluded from the mirror by /XF *.zip,
REM  which is why they were invisible from Dr Manoj's PC until this session.
REM
REM  IT MOVES THEM INTO  D:\SendToClinic\_old\  AND DELETES NOTHING.
REM  This project has lost documents permanently before (F-89); retirement here
REM  is always a move. _old is excluded from the mirror by design, so they stop
REM  being carried around but stay exactly where you can find them.
REM
REM  It touches nothing else. It does not stop the agent or the watcher.
REM ===========================================================================
set "SRC=D:\SendToClinic"
set "OLD=D:\SendToClinic\_old"

echo.
echo  ==========================================================
echo   Tidying %SRC%   ^(moving, not deleting^)
echo  ==========================================================
echo.
if not exist "%SRC%\" ( echo   STOP: %SRC% not found. & pause & exit /b 1 )
if not exist "%OLD%\" md "%OLD%"

set "MOVED=0"
call :shift "pyportable.zip"
call :shift "SCREEN REC 21 8 2026.zip"

echo.
echo   %MOVED% file(s) moved into %OLD%
echo.
echo   Free space on D: now:
for /f "tokens=3" %%F in ('dir /-c "D:\" ^| findstr /c:"bytes free"') do echo      %%F bytes
echo.
echo   Nothing was deleted. If you ever want one back, it is in _old.
echo.
pause
exit /b 0

:shift
if not exist "%SRC%\%~1" ( echo   already gone : %~1 & goto :eof )
for %%S in ("%SRC%\%~1") do echo   moving       : %~1  ^(%%~zS bytes^)
move /y "%SRC%\%~1" "%OLD%\" >nul
if errorlevel 1 (
  echo   COULD NOT MOVE %~1 - it may be open. Nothing lost; try again later.
) else (
  set /a MOVED+=1
  echo   moved        : %~1
)
goto :eof
