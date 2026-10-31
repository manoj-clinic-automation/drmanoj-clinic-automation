# S686_INGEST_SELFTEST_F1051 — the ingest self-test reports, never crashes

*The parent, session 372 · 31-Oct-2026 · on the owner's "F-1051 FIX FIRST" (13:55 IST).*

## For the owner
The finance import's own self-test (`/root/finance/finance_ingest.py`) stopped half way with an error. Nothing you see changes.
What changes is that the check now runs to the end and reports a score. Found with it: each time it stopped, it left a full
copy of the finance database (with patients) behind in the server's temp folder. The installer removes any left there.

## Why it stopped (F-1051)
Its test of "a return with no patient name goes to the review queue" was written before the rule of S186 (F-114):
a cleanly read line with no name or ID goes to WALK-IN, not review. The line went to WALK-IN, the test looked for a review row,
found none, and crashed. Two more checks could never pass on the live database: the test's made-up patients used plain numeric
clinic IDs, which can already be in use there.

## What changes — one file, the self-test section only
`/root/finance/finance_ingest.py` **ce01a9e1 → 029f5c20** (`make_s686.py`, one counted edit: the selftest section replaced whole).
- The no-name return is tested **both ways** on the throwaway copy: setting on (as live) → accepted onto WALK-IN as a pharmacy
  return of 77.00; setting off → review, kept signed (−77.00). The copy's setting is put back after.
- Every lookup that can find no row is a failed check, not a crash; any other error is ONE failed check naming it.
- The throwaway copy (and any `-journal`/`-wal`/`-shm`) is removed in a `finally`.
- The made-up patients are `ZZ9471` and `ZZ5120` (the clinic never issues a ZZ ID), checked unused first.
- **Nothing above the self-test changes:** `ingest_day`, the adapters, the ladder — byte-identical (walk M2, and M4 by syntax tree).

## Proof (device VM, a copy of the 31-Oct database — never the cloud workspace, D656)
- New file: `INGEST 56/56 passed`, exit 0, nothing left in its temp folder. Live file: TypeError, one copy left behind.
- `walk_s686.py`: **24 of 24 green** (behaviour B1–B9, builder M1–M7, mutants X1–X6). Control on the live file: **5 red · 2 green**.
- Mutants caught: the setting ignored either way, a parked return unsigned, WALK-IN renamed, a return served as a sale, the clean-up removed.

## Install
No restart: the running finance app keeps its import step, which is unchanged byte for byte.
Undo: `\cp -p /root/finance/finance_ingest.py.bak_S686_ce01a9e1 /root/finance/finance_ingest.py`
