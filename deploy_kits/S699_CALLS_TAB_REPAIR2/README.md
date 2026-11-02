# S699_CALLS_TAB_REPAIR2 — the tab's repair, second run (the parent, S379, 02-Nov-2026)

**Why.** S698's repair (11:13 IST) rebuilt the affected region of the `Call_Durations` tab from the raw log and then its own check found
15 keys twice: calls of 12-July the raw log holds AND that already sat in the rows above the region. It put the original rows back
(nothing lost), so the tab now carries the rebuilt rows and the originals. The console is unaffected (the builder folds them).

**What it changes — one file.** `/root/wa/call-hook/repair_call_durations_s698.py` 27609eb5 → v2: a raw-log call whose key already sits
above the region is kept there and never appended again; the verify counts those keys as present. Then the tool runs: the plan (dry run),
the apply (CSV backup first, verified, restored on a failure), call-hook restarted, console.db rebuilt once. The whole output is kept in
`/root/wa/call-hook/backups/repair_S699_<stamp>.log`.

**Install (one server line, window 04:00–23:30 IST; one to two minutes):**
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s699kit && cp -rp /root/deploy/repo/deploy_kits/S699_CALLS_TAB_REPAIR2 /tmp/s699kit && bash /tmp/s699kit/install_S699_CALLS_TAB_REPAIR2.sh
```
**Undo:** the tool's own CSV backups under `/root/wa/call-hook/backups/`; the tool's backup `repair_call_durations_s698.py.bak_S699_27609eb5`.
