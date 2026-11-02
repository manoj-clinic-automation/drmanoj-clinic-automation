# S700_CALLS_TAB_REPAIR3 — the tab's repair, third run (the parent, S379, 02-Nov-2026)

**Why.** S699's run (11:42 IST) wrote 3,490 rows again: copies of calls the first run had already rebuilt above the region, which the
tool's "keep what the raw log lacks" rule took for unknown rows. Its own check refused and put the rows back (nothing lost; the console
unaffected, the builder folds). v3: a region row whose call already sits above the region is dropped; the plan is pre-checked before
anything is written (the rows above must be unique; no appended key may duplicate one); this run scans the whole tab for a key seen
twice, so the first run's 15 July rows are swept up too. Simulated offline on a tab shaped like the real one after the two runs:
the region starts at the first duplicated July row, 4,648 rows remain, every key once, verified.

**What it changes — one file.** `/root/wa/call-hook/repair_call_durations_s698.py` 88d875d8 → v3; then the plan, the apply (CSV backup
first, verified, restored on a failure), call-hook restarted, console.db rebuilt once. The whole output in `/root/wa/call-hook/backups/repair_S700_<stamp>.log`.

**Install (one server line, window 04:00–23:30 IST; one to two minutes):**
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s700kit && cp -rp /root/deploy/repo/deploy_kits/S700_CALLS_TAB_REPAIR3 /tmp/s700kit && bash /tmp/s700kit/install_S700_CALLS_TAB_REPAIR3.sh
```
**Undo:** the tool's own CSV backups under `/root/wa/call-hook/backups/`; the tool's backup `repair_call_durations_s698.py.bak_S700_88d875d8`.
