# S911_CALL_CAP_LINE — the 120-call cap's count on the owner's console (the parent, S495, 20-Nov-2026; D1027)

**His word 21:33 IST:** build the console's overflow line now. The cap itself stays at 120 (his 20:14 question, D1027).

## What it does
1. **The engine says it.** `processor.py` caps the day's follow-up calls at 120 — the winnable first, the room left filled with the most
   overdue probable dropouts; whoever does not fit waits for the next run, and the engine never said how many. `call_cap_s911.py` inserts
   ONE print line right after the cap decides: `CALL CAP: kept 120 of 143 due for a call -- 23 wait for tomorrow`. It lands in the run's
   log (the server runner's `logs/runner.log`; the PC's console log). Nothing else changes — workbook, data files, the cap — and the installer
   proves it: Replay 2 for run #7 under the 3.11 venv must give the live report's content hash, or the engine goes back.
   **Both machines get the same line:** the server's `/root/followup_tracker/processor.py` 6929fc15 → **64824680** by this kit; the clinic PC's
   `C:\followup_tracker_local_test_kit\local_test_kit\followup_tracker\processor.py` 6929fc15 → 64824680 by the assistant (connected folder,
   `.bak_S911_6929fc15` beside it). A-D103 (S908) stands: the engine's bytes equal on both machines.
2. **The console reads it.** `owner_console.py` (S897's 500534f7 → `make_s911.py` → cf7f8b09): `_s911_call_cap_lines()` reads the last 64 KB
   of `/root/followup_tracker/logs/runner.log`, takes the newest CALL CAP line and the nearest preceding `[date time]` stamp, and adds one line
   to the work section's exports: green *"Call list: all 88 due calls are on the sheet (the server's run of 23-Nov 21:05)"* or a note
   *"Call list: 120 of 143 due calls on the sheet -- 23 wait for tomorrow (the 120-call cap)"* with a Patients link. Before the switch
   (no SWITCHED_AT, no line) it says the clinic PC makes the list until the switch; after the switch with no line yet, that the server has not
   reported yet. Read only; wrapped so a failure never breaks the console.

## Proof before the install
- `walk_s911.py` 17/17: the engine patch (check/apply/idempotent/compiles/5 lines/control without the anchor refused) + the lifted reader
  (no folder; no log before/after the switch; newest line wins with its stamp; wait 0 green; a 200 KB log; a garbled line).
- `rehearse_s911.sh` 14/14 on a made-up root: green install · again · undo · run #7's hash differs → engine back, console untouched, no
  restart · forced red at [4/5] → both back, restarted · healthz not 200 before → nothing · tampered kit · an undo after a later change refuses · lock held → nothing.
- Cold review (a reviewer that had not seen the build): no MUST; 4 SHOULD built in (the live hash captured before the replay; the OFF file keys the console wording and the log is never read while OFF stands; an undo refuses when a later kit has moved a file; run #7 must have printed the line) + 2 LOW.
- Number gate clean. Second look: see the close report.

## His part
The publish (`D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`) and one server line:
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s911kit && cp -rp /root/deploy/repo/deploy_kits/S911_CALL_CAP_LINE /tmp/s911kit && bash /tmp/s911kit/install_S911_CALL_CAP_LINE.sh
```
Undo: `bash /tmp/s911kit/install_S911_CALL_CAP_LINE.sh --undo`
