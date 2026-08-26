# S202_DARPAN20K — the Rs 20,000 that left the drawer and was never recorded

**Session 202 · F-187 · one INSERT, one marker, nothing else.**

## What was wrong

On 17-Aug-2026 Darpan's drawer was cleared. `cash_count.explanation` and the S186 close
both record the itemisation **in words**:

> 48,963 = 10,000 July-salary advance + **20,000 August-salary advance** + 18,963 handed to the owner

The 18,963 became `cash_custody_event` #4. The 10,000 became `day_expense` #56.
**The 20,000 became nothing.** It has existed only as prose inside an explanation column —
**F-137's exact shape**: a custody fact written where no query can reach it.

So every drawer figure from 17-Aug onward has carried 20,000 the drawer did not hold.

## How it was established — counted, not argued

| | |
|---|---|
| books said the drawer held | **63,903** |
| the drawer physically held | **43,903** |
| difference | **20,000**, exactly |

The owner counted it on 25-Aug-2026. An earlier theory — that the gap was "20,003 with 3 written
off" — was **disproved first**: 20,003 turned out to be the 20-Aug running balance
(66,994 + 7,939 in − 51,930 handed out − 3,000 non-cash = 20,003), and it reconciles on every
row of the table. The "3" was arithmetic, not a write-off. **The count is the only reason this
kit exists; without it the entry would have been a guess.**

A second reading was reconciled too. The ledger entry describes itself as *"Rs 15,000 drawer +
Rs 5,000 via Dr Manoj"*, which would make this kit 5,000 too big. If 5,000 had come from the
owner's own held cash the drawer would be short 15,000 and the count would have read 48,903.
It read 43,903. **The 5,000 came out of the drawer and merely passed through his hands** —
routing, not source. Custody (18,963) is unaffected.

## What it does

One row in `day_expense` on the medical 17-Aug day: **Rs 20,000, salary_advance, Darpan.**
`v_cash_ledger` computes `closing = cash_in − noncash − EXPENSE − cash_out + cash_back + adjust`,
so this moves every closing from 17-Aug forward down by exactly 20,000 and lands the drawer on
the counted figure.

## The one thing that makes it safe

**`ledger_posted` is set to 1 at insert, carrying Staff Ledger reference `0cc0b26b38c5`.**

`finance_app.py`'s approval path selects salary-advance expenses `WHERE ledger_posted = 0` and
posts each into the Staff Ledger. A row left at 0 would push **a second Rs 20,000** in the next
time that day is approved, and Darpan would appear to owe 40,000. Stamping it posted uses the
system's own idempotency guard for exactly what it was built for, and **links** the two books
instead of duplicating them. The ledger side was already correct; only the drawer side was missing.

The gate fails the install if that stamp is missing.

## What it cannot touch

`day_line` (the money — D313), `cash_movement`, `cash_adjustment`, `cash_count`,
`cash_custody_event`, `sale_item`, `sale_item_review`, `day_noncash_bill`, `day_entry`, and the
Staff Ledger. The gate proves every one unchanged by row count **and** sum, and the installer
**restores the whole database** on any red.

## Rehearsed offline before delivery

Applied to a throwaway copy of the 24-Aug database backup: **23 checks, 0 failed.** Closing fell
by exactly 20,000. Re-running the migration a second time left **exactly one** row — the
`NOT EXISTS` guard holds, so a double-install is harmless.

## Install

```
cd /root/deploy/repo && git pull && cd deploy_kits/S202_DARPAN20K && bash install_s202.sh
```

Expected: `23 checks, 0 failed` and **the drawer reading Rs 43,903** — the figure counted by hand.
Darpan's ledger stays at Rs 20,000 owing, and the August close still collects Rs 8,000 of it.

## Reverse

```
sqlite3 /root/finance/finance.db "DELETE FROM day_expense WHERE expense_uid='exS202darpan20k17aug'; DELETE FROM setting WHERE key='migration.S202_darpan20k';"
```

or restore the `.bak_S202_DARPAN20K_*` the installer writes before touching anything.

## Not in this kit, deliberately

- **Expense #56** (Rs 10,000, 31-Jul) is tagged `salary_advance` with `ledger_posted = 0` — it is
  **armed**. Its ledger entry was made at S190 and reversed at S192; a re-approval of that day
  would post it a third time. Its own kit.
- **Expenses #53/#54/#55** (Rs 40,000 total) carry no `category_fixed`, so the bridge can never
  see them. **Leave them so** — S189's §4a verification established that money was already
  recovered in the workbook era; tagging them would charge Darpan twice.
- **The `/ledger/statement` quota-lane display bug** — it announces full recovery for any
  scheduled advance because its `is_quota` test omits the schedule check the close applies first.
  A display fault, not a money fault. Belongs with **D349**, one rule in one place.
