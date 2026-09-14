@echo off
REM CHECK_MANIFEST.bat  (S268)  -- verify the tree against MANIFEST.md5. Writes nothing.
setlocal
set TOOLS=%~dp0
set ROOT=D:\Downloads\ClaudeCowork
python "%TOOLS%rebuild_manifest.py" --root "%ROOT%" --report "%TOOLS%CHECK_REPORT_LATEST.txt"
set RC=%ERRORLEVEL%
echo.
echo Report: %TOOLS%CHECK_REPORT_LATEST.txt
echo Exit code %RC%   (0 = tree matches the manifest exactly)
exit /b %RC%
