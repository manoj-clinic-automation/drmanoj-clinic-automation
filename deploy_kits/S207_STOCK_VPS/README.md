# S207_STOCK_VPS — closing the loop on the clinic server

**Staged, not installed. The VPS was not touched.** No credential for it exists in the session that
built this, deliberately — that is the owner's own rule and it is the right one.

```
expected (Marg)  ->  counted (staff)  ->  difference  ->  cause  ->  closed
```

## Why this is worth having

Stock leaves the shop by several doors. It is **sold**, or **returned to a vendor** — Marg records
those two well. It is also **issued** for clinic use, thrown away **expired**, **broken**,
**received and never entered**, or **sold and never billed**.

Those leave no trace at all until a physical count finds the hole, and by then nobody remembers
which door. So: capture the difference **the day it is found**, name the door while the memory is
fresh, and keep it open until Marg's own numbers agree again. After a few counts that becomes the
only honest answer to *"where does the stock go"* — by cause, by item, by month, in rupees.

## It goes INSIDE the finance app, not beside it

Same Flask process, same `finance.db`, same `unit_role` table, same fail-closed gate, same backup.
A second service would mean a second set of users, a second backup nobody takes, and a second thing
to notice has died.

**Install — two lines in `finance_app.py`, after the app and `require` exist:**

```python
import stock_app
stock_app.init(app, db, require, unit=UNIT)
```

Then copy `stock_app.py` and `stock_schema.sql` beside `finance_app.py`, run the gate, and restart:

```
cd /root/finance && python3 selftest_stock_app.py && systemctl restart clinic-finance
```

The schema is created on first touch and is idempotent — safe on every boot, safe twice.

## The five tables

| | |
|---|---|
| `stock_count` | one counting session, **pinned to a sale bill** so a mid-day count still reconciles |
| `stock_count_item` | what was found, per item — with the expected figure **copied in**, not looked up later |
| `stock_diff` | the ledger this is all for: one row per difference, open until Marg agrees |
| `stock_snapshot` | every Marg closing export we have seen, item by item — this is what closes differences |
| `stock_rate` | last purchase rate per item, so a loss can be priced |

**The expected quantity is copied into the count, never re-read.** A difference measured against a
number the counter never saw is not a difference, it is an argument.

## The rules that matter

**A count with no bill number is refused.** Not a warning — refused. A count that is not pinned
cannot be reconciled later, so recording one would be recording something useless.

**Naming the cause is the checker's job.** A maker may count and may load stock; only a checker may
say *why* it went. The default is `UNEXPLAINED` and it is **meant to be used** — a cause guessed to
tidy the list becomes a number in a report later.

**A difference closes only on an exact match.** Not "moved in the right direction", not "close
enough". Anything else is a second, smaller difference and it stays open under its own number.

**Nobody has to remember to tick anything off.** When the next export shows the quantity the counter
found, the difference closes itself and records *which* export agreed. A manual "mark as done" step
is the step that stops being done in week three.

**A surplus is never netted off a shortage.** Five found here and ninety-four missing there is two
errors, not one small one. Losses and surpluses are reported separately.

## `push_snapshot.py` — the link that makes it self-closing

Runs on **manojz**, where the archive and the token already are. Without it, differences sit open
forever because nothing ever tells the server that Marg's numbers changed.

```
python3 push_snapshot.py --dry-run     # see what would go, send nothing
python3 push_snapshot.py               # send it
```

Sends item, quantity, packing, pack size and last purchase rate in paise. **No patient data, no bill
numbers, nothing that is not already a stock figure.** The token is read the way `marg_gate.py`
reads it — live copy off the medical share, local cache as fallback — and is never passed on the
command line, never printed, never put in an error message.

Schedule it after the daily stock export and the loop runs itself.

## Two bugs the first real run found

**`31-03-2026` sorted after `27-08-2026`.** Marg writes `dd-mm-yyyy`, and comparing that as text puts
March ahead of August because `"31" > "27"`. The first dry run against the real archive picked the
**year-opening** export and would have posted 974 items of April's opening stock as if it were
today's shelf. Both this kit and `S207_STOCK_CHECK` now use a real date key; the count-sheet builder
had the same latent bug and had only escaped it by scanning two month folders.

**A log line that was wrong.** Deciding and reporting in one pass made it call a March export *"a
smaller export for the same date"* — it was neither. Gather, then choose, then report. A wrong log
line is worse than none, because the next person believes it.

## Proven — 37 checks, first run, against the real routes

`selftest_stock_app.py` builds its own temp database, drives every endpoint through Flask's test
client and deletes it. It covers: schema idempotence · a count refused without a bill · both people
recorded on every entry · batch detail surviving the round trip · pricing from the last purchase
rate · an unpriced item still recorded · a **maker refused** the cause and a **checker allowed** ·
an invented cause refused · **auto-reconcile closing a fixed item and NOT closing a partly fixed
one** · the surplus reported separately · the date window · and a repeat offender emerging across
two counts.

## What is not here yet

**The count page still lives as an artifact.** Once this is installed, the natural next step is to
serve the same page from `/stock/count` so a staff phone posts straight into this database instead
of the count being copied across. The page is already written to a state shape that ports over.

*S207_STOCK_VPS · staged 28-Aug-2026 · the VPS was not touched.*
