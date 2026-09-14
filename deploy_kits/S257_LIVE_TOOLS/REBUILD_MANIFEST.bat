@echo off
REM REBUILD_MANIFEST.bat  (S268)  -- rebuild D:\Downloads\ClaudeCowork\MANIFEST.md5
REM Replaces the shell-only rebuild that has been OWED since 08-Sep-2026.
REM Safe to run any time: it never deletes anything, it backs the old manifest up
REM outside the measured tree, and it refuses a rebuild that would lose rows.
setlocal
set TOOLS=%~dp0
set ROOT=D:\Downloads\ClaudeCowork
for /f %%d in ('powershell -nop -c "Get-Date -Format yyyyMMdd_HHmmss"') do set STAMP=%%d
if not exist "%TOOLS%reports" mkdir "%TOOLS%reports"
python "%TOOLS%rebuild_manifest.py" --root "%ROOT%" --rebuild --label %STAMP% --backup-dir "%TOOLS%manifest_backups" --report "%TOOLS%reports\REBUILD_%STAMP%.txt"
set RC=%ERRORLEVEL%
copy /y "%TOOLS%reports\REBUILD_%STAMP%.txt" "%TOOLS%REBUILD_REPORT_LATEST.txt" >nul
python "%TOOLS%build_papers_index.py" --root "%ROOT%" --canon "D:\dr-manoj-git\drmanoj-clinic-automation\deploy_kits\KB_canon_all" --session auto -o "%TOOLS%PAPERS.html"
echo.
echo Report: %TOOLS%REBUILD_REPORT_LATEST.txt
echo Exit code %RC%
exit /b %RC%
