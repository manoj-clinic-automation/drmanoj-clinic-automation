# S398_SLIP_DEAD_CODE — the drift read of slip_log.py, acted on

The S282 open read `/root/finance/slip_log.py` whole (five anchored patches since the last whole read: S379, S382, S384,
S391, S392). It found no contradiction and no bug — and **three blocks of dead code**, all left by S379 when the owner
retired the "X-rays not yet uploaded to Docterz" screen: the panel in the day report behind `n_emr = 0`, and the old
bodies of the two retired doors behind their `return redirect(...)`. Three helpers only that code called
(`emr_items`, `emr_pending_count`, `_emr_html`) and the flag `_BLOOD_ASKING` went with them. Three dead blocks in one
file is over the v10 line, so the consolidation came first.

**What changes for anyone: nothing.** Both old doors still answer with the same redirect; every page is byte-identical.
The `emr_upload` table and `emr_ensure` stay (the blood list still reads the table).

**Proof.** `walk_s398.py` mounts the kit file and the live S392 file side by side, each over its own scratch copy of
the live finance.db, clock pinned, and fetches every page a person can open (26 addresses × 4 roles, plus the retired
POST door) from both: **119/119, 112 answers identical byte for byte**, and the tables end identical. Negative control:
one changed word on a page turns the walk red. pyflakes 0. `slip_log.py` ffb629c1 → d208f57a (2,493 → 2,337 lines).
Restarts clinic-finance only (about 5 seconds).
