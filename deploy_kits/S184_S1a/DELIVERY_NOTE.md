# Kit S184_S1a — read-only survey of the medical cash chain

**Session 184 · 16 Aug 2026 · installs nothing · writes nothing**

## What it is

One Python script, run against `/root/finance/finance.db` opened **read-only**, that
prints fourteen short sections describing the Sanjeevni (medical) cash chain as the
machine actually holds it. It then re-hashes `finance.db` and refuses to report success
unless the file is byte-identical to before the run.

## Why it exists before the deposit booking

The S183 reconciliation concluded the drawer is whole and that the impossible
**−₹30,056** closing is 16 unrecorded Yes Bank deposits. The arithmetic in that document
is sound, but it does not survive contact with how `v_cash_ledger` computes the balance:

```
closing = cash_in − noncash − expenses − cash_out + cash_back + adjustments
```

Cash collected over the period is ₹17,98,033 and recorded expenses are ₹84,442. If the
16 deposits were simply *absent* from the books, then `cash_out` would be zero and the
computed closing today would be roughly **+₹17.1 lakh**, not −₹30,056.

So something is already subtracting about ₹18.3 lakh, and no canonical document says
what. The three candidates:

1. **`cash_adjustment` rows** written by the S179 legacy import, carrying the old
   sheet's carry-forward breaks. If so, booking deposits as `cash_movement` on top of
   them would **double-count** and drive the drawer ₹16 lakh further negative.
2. **`cash_movement` out rows** already present from the legacy sheet's hand-over
   column — in which case the deposits are recorded, just not reconciled, and the
   S184 task is a reconciliation, not a booking.
3. Something else entirely.

Each of the three needs a *different* migration. Section 3 of the survey answers which,
in one line. That is the whole point of running it first.

## What it prints

| § | Question it answers |
|---|---|
| 1 | how many days, what statuses, what span |
| 2 | the last 20 days of the ledger, opening → closing |
| 3 | **the composition of today's balance, one line per component** |
| 4 | cash movements already recorded, and on the 16 deposit dates specifically |
| 5 | adjustments, their source and status, the 10 largest with reasons |
| 6 | whether a `day_entry` exists for each of the 16 deposit dates |
| 7 | the 3 salary-advance dates and any expenses already on them |
| 7b | every `salary_advance` expense ever recorded (double-count check) |
| 8 | `staff_ref` ids, so an advance can be attached to the right person |
| 9 | open exceptions by kind, and the **uncapped** unfiled-day list |
| 10 | every day where the computed drawer is negative |
| 11 | August 2026 in full |
| 12 | home / procedure medicine bills already captured |
| 13 | whether the drawer has ever been physically counted |
| 14 | which migrations are already marked applied |

## Safety

- The connection is `sqlite3.connect("file:...?mode=ro", uri=True)`. **A write is
  refused by the driver, not by the script's intentions** — and the script proves it at
  startup by attempting one and printing the refusal.
- `finance.db` is hashed before and after; a difference is an alarm, not a warning.
- **No PHI is printed.** Dates, money, statuses, counts and staff first names only.
  No patient name, no phone number, no clinic id.

## Offline proof before shipping

Built and run here against a throwaway database created from the live
`finance_schema.sql` + `finance_returns.sql` (31 tables, 8 views) and seeded to the
shape of the real store — 121 filed days 1 Apr → 13 Aug, 17 unfiled days, legacy
adjustments driving the balance. `py_compile` clean; the survey ran end to end; the
seeded database's md5 was **identical before and after** the run; the read-only guard
was confirmed firing (`attempt to write a readonly database`).

## To run

On the PC: double-click `deploy/push_kit.bat`.

Then on the VPS, one command:

```
bash /root/deploy/vps_deploy.sh S184_S1a
```

Copy the whole output back into the session.

---
*S184 · survey only · the migration is built after this returns*
