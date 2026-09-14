@echo off
REM INSTALL_KBTOOLS.bat  (S268)  -- one run does all four things:
REM   1. checks python is there        2. runs the 27 selftests
REM   3. registers the nightly task    4. rebuilds MANIFEST.md5 now
REM Nothing is deleted. Nothing on the VPS is touched.
setlocal
set TOOLS=%~dp0
echo ============================================================
echo  S268 - KB manifest tool
echo ============================================================
echo.

echo [1/4] python
python --version
if errorlevel 1 goto nopython
echo.

echo [2/4] selftests
python "%TOOLS%selftest_rebuild_manifest_s268.py"
if errorlevel 1 goto badtests
echo.

echo [3/4] nightly task - KB Manifest Rebuild, daily 03:10
schtasks /create /tn "KB Manifest Rebuild" /tr "%TOOLS%REBUILD_MANIFEST.bat" /sc daily /st 03:10 /f
if errorlevel 1 echo    NOTE: the task could not be registered. The rebuild below still runs.
echo.

echo [4/4] rebuilding MANIFEST.md5 - this walks about 2,700 files, give it a minute
call "%TOOLS%REBUILD_MANIFEST.bat"
echo.
echo ============================================================
echo  DONE. Report: %TOOLS%REBUILD_REPORT_LATEST.txt
echo ============================================================
pause
exit /b 0

:nopython
echo.
echo  STOPPED: "python" was not found on the PATH of this window.
echo  Nothing was changed.
pause
exit /b 1

:badtests
echo.
echo  STOPPED: the selftests did not all pass, so nothing was rebuilt.
echo  Nothing was changed.
pause
exit /b 1
