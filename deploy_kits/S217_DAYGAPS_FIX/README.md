# S217_DAYGAPS_FIX — the CounterGaps card 500

**Fault (from journalctl + reproduced offline):** `/finance/api/day-gaps` dies with
`sqlite3.OperationalError: no such column: mobile` at `finance_daily_gaps.py:217`.
The module expected the D356 patient-master push to add a `mobile` column to
`patient_ref`; that push never ran — the table has `phone_last4`, never `mobile`.
The line runs only for a day carrying an UNMATCHED bill, so the card worked until
the first such day was filed (01-Sep), then killed the whole card. A green test
proves only the path it walked — all four offline test days were fully matched.

**Fix:** `patch_daily_gaps_mobile.py` — byte-anchored (exactly-once or abort),
timestamped backup, in-process compile with restore on failure. The SELECT takes
only `name, phone_last4`, and the row shows `xxxxxx<last4>` — which is also the
masking rule. Matched days are byte-for-byte unaffected.

**Rehearsed on a copy of the real backup** (EVIDENCE_rehearsal_01Sep.txt):
unpatched module crashes exactly as on the box; patched module returns
`unmatched: 1, mobile: xxxxxx1234`. Idempotent (second run: "already patched").

**Rollback:** restore the printed `.bak_S217_mobile_<stamp>` file — one file.

**Owed after this stabilizes:** the D356 patient-master re-push (which also
fills the collision `kind`), still on the backlog from the S211 close.
