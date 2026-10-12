# REPORT S539_NORTIMER_OUT — ran 12-Oct-2026 08:50 IST, green (data only: no code, no restart)

**For the owner**
1. Voucher 11 is voided and NORTIMER TAB is out of the 6-Sep count. It is marked settled, so the count will never raise it again.
2. The other five lines of voucher 11 are a new voucher: **STOCK ISSUE voucher 30**, with NIMREX P −11, NUROKIND LC −5, NURVION LC TAB −38, OLMETIME H 20 −45 and ONDEM MD 4 −35. All five are the same quantities as on 6-Sep. None of them takes Marg below zero on the 10-10 closing. No other voucher changed its number.
3. Amir's card still says "Dawa ke voucher: 12 — board kholiye". Voucher 30 reaches him with a coming lot of 12. Your Needs-you no longer carries a NORTIMER line, and nothing is held any more, so the count can finish once all medicine vouchers are entered and proven.

---

## For the chat

### Pins (read at the gate and again after the data step; never edited)
| file | pin |
|---|---|
| `/root/finance/stock_app.py` | f58e09dbb273e8b1470aa7220da70015 |
| `/root/finance/stock_watch.py` | 0e6a42c4c7ae51eb8f8a0869fce2d101 |
| `/root/finance/shelf_figure.py` | 183c70fabb64ed1e5a43c645a225c560 |
| `/root/finance/loss_piles.py` | 81ae481e4480a12fead3016515037214 |
| `/root/finance/stock_statement.py` | a90f3413427841b7daea76b7730b2896 |
| `/root/deploy/repo/claude_code_briefs/DUTY_MAP.json` (v12) | f499dd1fb53cb9b23422154aac41596e |

All six matched at 08:46 IST (probe) and at the installer's gate. After the data step they were unmoved, and so was the crontab.
- **No live file is FROM → TO**: this kit edited none.
- **No service was restarted and the clone was not pulled.**
- `clinic-finance` reads `ActiveEnterTimestamp=08:38:12`. That restart was **not this kit's**; it came after S537's 08:08:09 and before this run.

### The data step (live, `DATA_S539:` lines; times read from the rows)
- **1, by shape:** count #1, round 2, ISSUE, batch 10 is STOCK ISSUE voucher 11. It holds six lines (NIMREX P −11, NORTIMER TAB −10, NUROKIND LC −5, NURVION LC TAB −38, OLMETIME H 20 −45, ONDEM MD 4 −35) and was not entered, voided, settled or re-made.
- **2, one transaction:** voided through `stock_app._voucher_void`, giving `stock_voucher_void` row (1, 2, ISSUE, 10, manoj, at 2026-10-12T08:50:20). Then `stock_voucher_settle` row (1, NORTIMER TAB, manoj, 08:50:20). Committed.
- **3, the five re-made:** `_voucher_pending(…, items=the five)` gave exactly −11, −5, −38, −45, −35, with none held by the guard. `_voucher_make` then made **round 7, ISSUE, batch 1, five lines**, made_by manoj at 08:50:24. Its counted-day Marg readings are 178→167, 14→9, 354→316, 102→57, 100→65. `_voucher_seq` gives it **STOCK ISSUE voucher 30**.
- **Rows:** void 1 → 2, settle 1 → 2, voucher lines 202 → 207.
- **Backup:** `/root/finance/finance.db.bak_S539_20261012_084946` (35,938,304 bytes, backup API).

### The state (scratch copies of the live database; the installer printed both)

**BEFORE**
- stage C; released 12 of 30; held = NORTIMER TAB (voucher 11)
- voucher 11 is a batch
- Amir's board: STOCK ISSUE 1–10, 12, 13
- his line: "Dawa ke voucher: 12 — board kholiye"
- Needs-you: "Count #1: Stage C: 0 of 30 entered · 12 released · 0 verified" and "Count #1: NORTIMER TAB (STOCK ISSUE voucher 11) — … not given to Amir"

**AFTER**
- stage C; released 12 of 30; unreleased 18; **held none**
- voucher 11 is not a batch; NORTIMER is settled; the five are re-made as STOCK ISSUE voucher 30
- Amir's board unchanged (12 vouchers), same line
- Needs-you: only "Count #1: Stage C: 0 of 30 entered · 12 released · 0 verified" — no NORTIMER line

### The walk (`walk_s539.py`, in the installer, on backup-API copies of the live finance.db and spine.db): **WALK_S539 GREEN (15 checks)**
The first DRY was green; the real run's walk was green too.

**Controls, RED on the untouched copy:**
- voucher 11 is held in `C["held"]`
- NORTIMER is on the owner's Needs-you ("Count #1: NORTIMER TAB (STOCK ISSUE voucher 11) — …")
- voucher 11 is a batch on the owner's board

**After the data step on a copy:**
- voucher 11 is gone from `_s446_batches` and from the board as amir and as the owner
- NORTIMER TAB is in `stock_voucher_settle`
- there is exactly one new ISSUE batch, (7, ISSUE, 1), holding exactly the five lines and their changes
- `_voucher_seq` is unchanged for every pre-existing batch, and the new batch is voucher 30
- `C["held"]` is empty and NORTIMER is absent from Needs-you
- the new batch is on the owner's board, not yet on Amir's
- a second run says `ALREADY DONE` and writes no row
- `amir.count_vouchers` (v12 SQL) reads 12 → 12. Voucher 11 was never released, so it was never counted there, and now it can never become due.

**The other two cases:**
- `--dry` writes nothing (void, settle, line and entered counts the same), and its own scratch copy shows the outcome
- a copy where voucher 11 carries an entry → `STOP`, exit 2, nothing written

### The build lock
Taken 08:49:46 and held until this report; removed after it.

### Calls made inside the brief
- **Half-done states finish instead of stopping.** Re-running after a partial state (void and settle done, the five not yet made, e.g. after a step-3 STOP) skips step 2 and goes on to step 3. Only the fully done state answers `ALREADY DONE`; any other shape STOPs.
- **`--dry` runs `_voucher_make` only on a scratch copy.** `_voucher_make` commits by itself, so it cannot be rolled back. `--dry` therefore rolls step 2 back on the database and runs steps 2–3 on a scratch copy for the printout (S537's `--dry` shape).
- **Step 4 reads stock_app instead of importing amir_day.** It builds the owner's Count lines from `stock_app._s521_stage_words` (the source of amir_day's Count lines) and Amir's board from `_amir_board_light`. This keeps the data step from loading the whole app.
- **The undo is written as the owner's decision.** The README says how: the new batch can itself be voided by a later kit, and NORTIMER and the five then go on a fresh round from a fresh count. Voucher 11 stays void, because a void and a settle are never deleted (charter 5).

### Charter
- **Retired:** nothing (no code).
- **Left for later:**
  - NORTIMER's surplus: a new stock voucher from a fresh count of that item (the owner's word)
  - the owner door to void or settle from the hub (S537's, still open)
- **Left out:** nothing.
- **Seen, not touched:** the 08:38:12 restart of `clinic-finance` (not this kit's; it is another build's to report).
- **The dependency's state:** the spine passed 13/13 (last success 08:40:45).

### Not done
Nothing in the brief is left undone. No command was refused.
