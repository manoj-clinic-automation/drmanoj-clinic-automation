# S539_NORTIMER_OUT — NORTIMER TAB out of the 6-Sep count; the other five lines of voucher 11 re-made

**Brief:** `claude_code_briefs/S539_NORTIMER_OUT.md` (v1, session 310). **The owner's word:** 12-Oct-2026 08:42 IST — "Remove NORTIMER for now …
we will incorporate whatever surplus later with a new stock issue voucher whenever possible." **Fault:** F-185. A **data-only** kit:
no live file is edited, no service restarted, the clone is not pulled.

## What it does (`data_s539.py`, through S537's doors)

1. Finds voucher 11 by shape — count 1, round 2, ISSUE, batch 10, six lines: NIMREX P, NORTIMER TAB, NUROKIND LC, NURVION LC TAB,
   OLMETIME H 20, ONDEM MD 4; not entered. Anything else → `STOP` (exit 2, nothing written). Already done → `ALREADY DONE`.
2. One transaction: `stock_app._voucher_void` on (1, 2, ISSUE, 10) and a `stock_voucher_settle` row for NORTIMER TAB (by manoj).
3. Re-makes the five through `stock_app._voucher_pending(…, items=the five)` — which must give exactly −11, −5, −38, −45, −35 with none held by
   the guard, else STOP before making — and `stock_app._voucher_make(…, items=the five)`: one new STOCK ISSUE batch, numbered after the last
   (`_voucher_seq`: 30; the voided 29 and 11 keep their numbers unseen). It reaches Amir with a coming lot of 12.
4. Prints the state after on a scratch copy (stage, C released / held, Amir's board, the owner's Count lines).

`--dry` rolls step 2 back and runs step 3 only on a scratch copy; `--state` prints step 4 only (the installer's before / after).

## Pins (read, never edited)

`/root/finance/stock_app.py` f58e09db, `stock_watch.py` 0e6a42c4, `shelf_figure.py` 183c70fa, `loss_piles.py` 81ae481e,
`stock_statement.py` a90f3413 (S537's TOs); the clone's `DUTY_MAP.json` f499dd1f (v12). `finance.db`: rows only, `finance.db.bak_S539_<stamp>`
first; never a DELETE.

## The undo — the owner's decision, not a script

By design nothing here can be taken back by a delete: a void is never un-voided and a settle row is never removed (charter 5). If the owner
orders the reverse:
- the new batch (STOCK ISSUE 30), not yet entered, can itself be voided through `stock_app._voucher_void` (a new kit);
- NORTIMER and the five then need a fresh round from a fresh count of those items (the normal way) — voucher 11 stays void.
The database backup `finance.db.bak_S539_<stamp>` is kept and is not the undo (other rows move on after the install).

## Charter

**Retired:** nothing (no code). **Left for later:** NORTIMER's surplus — a new stock voucher from a fresh count of that item (the owner's word);
an owner door to void / settle from the hub (S537's left-for-later, still open).

## Files

`KIT_ID.txt`, `SUMS.md5`, `data_s539.py` (the data step), `walk_s539.py` (the walk), `install_S539_NORTIMER_OUT.sh` (the installer), this README.
No `.json` in the kit folder.
