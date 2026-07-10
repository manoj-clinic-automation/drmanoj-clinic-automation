# INCIDENT REPORT — FOLLOWUPS_WATCHER_NOT_RUNNING

**01 July 2026 · Session 24**

## SUMMARY
The Callback/Follow-Up dashboard showed **yesterday's (30-Jun) follow-up list** instead of today's (01-Jul). The patient list, phone numbers, and Call buttons were internally consistent — but they were the wrong day's data. Staff opening the dashboard this morning would have re-called 30-Jun's patients and missed today's genuine Due-Today patients.

## IMPACT
**Operational, not cosmetic** — but fully recovered the same morning. No patient data was lost or corrupted. Today's correct file existed the whole time; it simply had not reached the live Sheet. Detected by the owner on first use of the dashboard, morning of 01-Jul.

## TIMELINE
- **01-Jul 01:40** — the Follow-Up Tracker generated today's `Staff_Action_Today_2026-07-01.xlsx` correctly (185 worklist rows) into the outputs folder. ✅
- **Morning 01-Jul** — dashboard observed showing 30-Jun follow-ups. Live `Followups_Today` tab confirmed (via Drive connector) to contain only 30-Jun rows — zero 01-Jul due rows.
- Root cause traced by reading `watch_followups.log`: last watcher activity was **30-Jun 10:10** (a restart banner), then **nothing** — the auto-push watcher had not run since 30-Jun morning, so today's 01:40 file was never pushed.
- **Immediate fix:** owner ran the manual fallback — `python push_followups_today.py` (preview, showed correct 01-Jul file/185 rows) → `--push` → `DONE. Wrote 185 worklist rows to 'Followups_Today' and 146 to 'Followups_Settled'.` Dashboard hard-refreshed → today's list live.
- **Permanent fix:** the fragile Startup-folder shortcut was replaced with a **Windows Task Scheduler task** ("At log on" trigger → launches `start_followup_watcher.bat`). Tested via right-click → Run; watcher confirmed STARTED at 08:06:24. Old redundant Startup shortcut deleted by owner.

## DIAGNOSIS
The auto-push step is performed by a background **watcher** (`watch_and_push_followups.py`) that polls the outputs folder and runs `push_followups_today.py --push` whenever a new `Staff_Action_Today_*.xlsx` appears. That watcher was **not running** when today's file was generated. Its intended auto-start mechanism — a `.bat`-file **shortcut in the Windows Startup folder** (set up Session 19) — is unreliable: a Startup-folder shortcut to a batch file does not dependably relaunch across logoffs/restarts, and the launched window can be closed without anything bringing it back. The log gap (silent from 30-Jun 10:10) is the evidence.

So the fault was **not** in file generation (worked), **not** in the push script (worked when run), **not** in the dashboard (correctly displayed a stale tab), and **not** the earlier `2001` date bug (the date-normaliser held — dates read `01-Jul-2026`). The single point of failure was the **watcher's auto-start not surviving across days.**

## FIX APPLIED
1. **Immediate:** manual push of the already-correct 01-Jul file → today's list live (185/146 rows, replace-only, no duplication).
2. **Permanent:** auto-start moved from the Startup-folder shortcut to **Task Scheduler** —
   - Task name: `Follow-up Auto-Push Watcher`
   - Trigger: **At log on** (30-second delay to let Drive sync settle)
   - Action: `cmd.exe /c start "" "C:\followup_tracker_local_test_kit\local_test_kit\followup_tracker\start_followup_watcher.bat"`, Start-in the tracker folder
   - Runs only when user is logged on (needs the Drive-synced folder)
   - Verified launches the watcher (STARTED 08:06:24 in the log).
3. **Cleanup:** old `start_followup_watcher.bat - Shortcut` deleted from the Startup folder so only Task Scheduler launches the watcher (no duplicate windows at login).

## PREVENTION
- **New surveillance check to add to Diagnostics & Surveillance Spec (Category 1 — process liveness):** `FOLLOWUPS_WATCHER_STALE` — flag if `watch_followups.log` has no new line since the last expected file-generation window, OR if the live `Followups_Today` tab's newest Due Date is older than today. Either signal catches this class of fault the moment it recurs, before staff act on stale data.
- **Daily 5-second manual check (interim, until the above is automated):** on opening the dashboard, confirm the follow-up list shows **today's date**. If it shows yesterday, run the manual fallback: `cd` to the tracker folder → `python push_followups_today.py --push` → hard-refresh.
- The manual fallback (`push_followups_today.py --push`) remains the always-available safety net and is unchanged.

## CONTACTS IF NEEDED
None — clinic-internal fix on the clinic PC. No MyOperator / Hostinger / Sarvam involvement.
