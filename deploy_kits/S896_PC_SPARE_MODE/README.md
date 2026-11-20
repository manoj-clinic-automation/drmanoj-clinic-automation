# S896_PC_SPARE_MODE — the clinic PC's tracker as the spare: one flag file, the sends off (the parent, S492, 20-Nov-2026)

Plan `claude/S492_TRACKER_TO_SERVER_PLAN_FINAL.md` §5. Two PC files, built from the live bytes on manojz:
- `C:\followup_tracker_local_test_kit\local_test_kit\followup_tracker\docterz_pickup.py` ddbed001 → 9e0bf2e1 (S896, S239 rev 5):
  with `D:\Downloads\DocterzArchive\_SPARE_MODE.txt` present, a pass fetches, runs, archives and writes its list and ledgers as
  today and sends NOTHING — not the call sheet, not the patient join, not the Sheet. Without the flag: exactly ddbed001's behaviour.
- `...\watch_and_push_followups.py` 8561f3d7 → f8fb3d25: with the flag, a new workbook is noted and marked seen, never pushed
  (the watcher has not run since 01-Jul-2026; patched so it can never undo the switch if restarted).

Install: the assistant copies the two files into the live folder with `.bak_S896_<from>` beside each (the connected folder; no step
of the owner's) at session 2, dormant. The flag file is written on the switch evening (session 3) and removed for the undo.
Proof: `walk_s896.py` 10/10 (control: ddbed001 ignores the flag); S892's walk 21 green and S540's 9 green on the patched file;
`docterz_pickup.py --selftest` 0 failures.
