@echo off
REM PAPERS.bat  (S269)  -- rebuild the paper shelf and open it.
REM Reads only. Moves, renames and deletes nothing.
setlocal
set TOOLS=%~dp0
set ROOT=D:\Downloads\ClaudeCowork
set CANON=D:\dr-manoj-git\drmanoj-clinic-automation\deploy_kits\KB_canon_all
python "%TOOLS%build_papers_index.py" --root "%ROOT%" --canon "%CANON%" --session auto -o "%TOOLS%PAPERS.html"
if errorlevel 1 goto failed
start "" "%TOOLS%PAPERS.html"
exit /b 0

:failed
echo.
echo  The shelf could not be built. Nothing was changed.
pause
exit /b 1
