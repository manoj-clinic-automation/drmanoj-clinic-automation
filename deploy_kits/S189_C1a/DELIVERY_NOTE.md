# S189_C1a — the counted custody position, recorded where a query can reach it

**Writes to the live database. It cannot move your cash — and the gate proves
that rather than promising it.**

## What goes in

| date | from | to | amount | where it comes from |
|---|---|---|---|---|
| 6 Aug | counter | Dr Bhawna | ₹7,309 | S186 §4, itemised; proven by the drawer clearing landing exactly on ₹48,963 |
| 15 Aug | counter | Dr Bhawna | ₹3,926 | S186 §4, same proof |
| 17 Aug | counter | Dr Bhawna | ₹1,45,000 | the balance of her counted position |
| 17 Aug | drawer | Dr Manoj | ₹18,963 | S186 §4, the drawer clearing, itemised to the rupee |
| | | **total** | **₹1,75,198** | **equal to the paise to `cash_count` for 17 Aug** |

**Darpan's drawer is ₹0 and therefore has no row.** An empty drawer is the
*absence* of custody, and absence is recorded by writing nothing rather than by
inventing a row that says "nothing here".

## The one row I want you to look at

**₹1,45,000 is a balancing entry and says so in its own note.** The record
itemises only the two Vinay handovers; the individual journeys making up the
rest of Dr Bhawna's ₹1,56,235 are not written down anywhere. So it goes in as
**one row that admits it**, with its route taken from the documented custody
model (S186 §2 — the counter person hands cash direct to Dr Bhawna, bypassing
the drawer) rather than from a per-transaction record.

I could have manufactured a plausible history of daily handovers. That would
have looked more thorough and been less true. That it comes to a round
₹1,45,000 is a corroboration, not the reason: 1,56,235 − 7,309 − 3,926.

## What the gate refuses

Before writing: the marker must be absent, no S189 rows may already exist, the
17 August `cash_count` must exist **and equal ₹1,75,198 to the paise**, and both
counter-people must be in the registry. Any one of those and nothing is written.

After writing, it **restores the whole database** unless *all* of these are
byte-identical: `day_line` sum and rows · `cash_movement` rows and sum ·
`cash_adjustment` · `day_expense` · the ledger net · **cash in hand**. And it
requires exactly +4 rows, Dr Manoj +₹18,963, Dr Bhawna +₹1,56,235, and the total
entered to equal the recorded count.

It asserts **deltas, never absolute balances** (F-106) — a gate that asserts a
store state goes red the moment data is legitimately corrected, and then the
gate is what gets disabled.

## Rehearsed offline, end to end

```
PRECHECK  green   projection printed before anything measured again
APPLY     4 rows
VERIFY    cash in hand  Rs -83,750.00 -> Rs -83,750.00   UNCHANGED, as promised
          Dr Manoj      Rs 0.00 -> Rs 18,963.00
          Dr Bhawna     Rs 0.00 -> Rs 1,56,235.00
          entered total Rs 1,75,198.00  vs the 17 Aug count Rs 1,75,198.00
          verify GREEN -- location recorded, not one paisa moved
```

(The rehearsal store's own cash figure is meaningless — what matters is that it
did not move.) Then the endpoint was run against the migrated store: **Dr Manoj
₹18,963 · Dr Bhawna ₹1,56,235 · total ₹1,75,198 · as at the count of 17 Aug**,
with `drawer` and `counter` correctly absent.

## After it runs

Cash in hand stays **₹2,05,198**. It was never overstated. It becomes
₹1,75,198 when Darpan's ₹30,000 goes in through the app — the same ₹1,75,198
you counted.

**Install `S189_W1a` first.** This kit refuses otherwise.

```
bash /root/deploy/repo/deploy_kits/S189_C1a/install_c1a.sh
```
