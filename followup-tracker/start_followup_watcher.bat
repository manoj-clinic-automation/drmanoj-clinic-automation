@echo off
REM ===========================================================================
REM start_followup_watcher.bat
REM   Launches the follow-up auto-push watcher and keeps it running.
REM   Placed (via a Startup-folder shortcut) so it starts automatically at login.
REM
REM   What it does: runs watch_and_push_followups.py, which watches the tracker
REM   outputs folder and auto-pushes today's follow-ups to the dashboard the
REM   moment you process the tracker. You never type a command.
REM
REM   To STOP it: close this window (or press Ctrl+C inside it).
REM   To DISABLE auto-start: delete the shortcut from the Startup folder
REM     (see SETUP_followup_watcher_autostart.txt).
REM ===========================================================================

title Follow-up Auto-Push Watcher  (leave running - safe to minimize)

cd /d "C:\followup_tracker_local_test_kit\local_test_kit\followup_tracker"

REM Loop so that if the watcher ever exits unexpectedly, it restarts itself
REM after a short pause (so a one-off glitch can't silently leave it dead).
:loop
python watch_and_push_followups.py
echo.
echo [watcher stopped - restarting in 15 seconds; close this window to quit]
timeout /t 15 /nobreak >nul
goto loop
