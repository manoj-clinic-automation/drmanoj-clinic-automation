# S794_HOUSEKEEPING — the PC set-up kits kept current (the real cause), and the S770 probe's folder removed

Runbook §2A item 7 (D899), at the owner's "do 1, 2 and then 6" (S431, 11-Nov-2026 20:09 IST).

## (a) Why the PC set-up kits still went stale — fixed on manojz (placed by the assistant at S431, 20:26 IST)
`D:\Downloads\_kbtools\pc_kits_current.py` 6c5887c5 (S723) → **af2495ef**; backup `pc_kits_current.py.bak_S794_6c5887c5` beside it.
- **The cause:** `pin_map()` skipped every pin row whose note held the word *superseded* anywhere. The medical PC's newest
  `marg_watch.py` row (S763, afcc3fd9) names a backup file `_kit\marg_watch_S722.py.superseded`, so it was skipped; the older row
  (df7736e9) was taken as the newest pin; the PC's own copy (afcc3fd9) "is not its newest pin" → left as packed — and the
  report still said **CURRENT**. The medical kit has carried df7736e9 since.
- **The fix (2 exact changes, `make_s794.py`):** only the *word* superseded marks a row, not a file name ending in `.superseded`
  (on the S430 pin list exactly one row changes: this one); a member left as packed makes the kit **BEHIND — NOT REPACKED**, never CURRENT.
- **Proven:** `walk_s794.py` 30/30 (S723's 26 + 4 new; one S723 answer changed by design); the control on 6c5887c5 red (3);
  S723's own walk 26/26 on the new file; on the real repository (`--dry`, nothing written): *medical BEHIND — marg_watch.py
  df7736e9 → afcc3fd9*. Tonight's nightly repacks the medical kit and its rehearsal re-proves it; the next publish carries it.
  No file on the medical PC changes.
- **Undo:** copy `pc_kits_current.py.bak_S794_6c5887c5` back over `pc_kits_current.py` in `D:\Downloads\_kbtools\`.

## (b) The server — `run_S794_server.sh`
Read-only first: the last lines of the 3 pm / 6 pm X-ray photo notification log and today's attendance-clock corrections
(numbers masked). Then it removes `/root/s770_probe/` (the S770 probe's report and RapidOCR venv, ~370 MB) — only after checking
that no cron line, no file under `/root`'s apps or systemd, and no running program names it. `DRY=1` removes nothing. Rehearsed on
a stand-in root: DRY · a file naming it stops it · removed · run again = already gone.
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S794_HOUSEKEEPING/run_S794_server.sh
```
