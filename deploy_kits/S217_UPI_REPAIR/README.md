# S217_UPI_REPAIR — restore the real bank transactions, flag the silent day

**What happened (measured from the 01-Sep 01:40 nightly backup, never guessed):**
at 2026-08-30T00:25:16 nine synthetic MPR statements (rrn `RRN1`, Rs 999,
txn_time 20:00:00, nine distinct fake shas) were ingested against the LIVE
`finance.db`. `store_txns()` deletes per (merchant, day) before inserting, so
the REAL bank transaction detail was wiped for nine medical days:
**14, 16, 19, 20, 21, 23, 25, 26, 28 Aug 2026.** The `upi_statement` day
totals were untouched — they are the reference this kit verifies against.

**The money effect:** 28-Aug was filed with UPI Rs 999 (exactly the fixture
row) while the bank settled **Rs 6,687** — the drawer position is inflated by
**Rs 5,688** on that day, and no mismatch flag ever opened, because the
statement had landed BEFORE the day was filed and nothing re-compared after.

**What the script does (dry-run by default; `--apply` to write):**
1. timestamped verified backup of `finance.db`
2. `finance_upi.backfill_txns()` over the raw statement store (every real MPR
   is kept on the box since the GAS push began) — real rows restored, June's
   two older AF-7 artefacts included
3. deletes any surviving `RRN1` fixture rows
4. re-runs `finance_upi.reconcile_upi()` for every statement day since
   2026-08-01 — the 28-Aug mismatch finally opens and shouts
5. prints a per-day verdict table: statement vs txn-store, `ok` / `STILL SHORT`

**Rehearsed** on a copy of the real backup: see `EVIDENCE_rehearsal_01Sep.txt`.
Exactly one new flag opened (28-Aug, bank 6687 vs entered 999). Verdicts are
honest: with no real files present the damaged days report STILL SHORT.

**Rollback:** restore the printed pre-repair backup from
`/root/backups/finance/finance_pre_S217_repair_<stamp>.db` — one file, nothing
else is touched.

**Root cause — FOUND (read from the code, not guessed):** the app's smoke
suite posts fixture statements ('mpr.xlsx', rrn RRN1, Rs 999) through the
upi-statement route. The route runs against the smoke's throwaway DB copy —
but it STORES the posted file into the LIVE raw-statement store. Nine smoke
runs left nine fixture files there. At 00:25 on 30-Aug a backfill replayed
the whole store into upi_txn, and each fixture's delete-then-insert wiped the
real rows for the day it named. Hence step 2a: fixture files (no 15-digit MID
in the stored name) are QUARANTINED before the backfill, so this cannot
recur on the next backfill. A follow-up patch should stop the route storing
smoke files at all (or point the smoke at a temp store).
