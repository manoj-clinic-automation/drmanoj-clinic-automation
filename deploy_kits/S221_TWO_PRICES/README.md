# S221_TWO_PRICES — the mislabelled money column, corrected; and the drift log

**Three files:** `stock_app.py` (`ed2f76ef` → **`c627e440`**), `stock_finding.html` **replaced**,
`stock_drift.html` **new**. The base was reproduced offline and md5-proven first:
S213 `83b0a1b0` + this morning's finding patcher = `ed2f76ef`, which is what is live.

## Why this exists: I mislabelled a money column

`S221_STOCK_FINDING`, installed this morning, heads a column **"at MRP"**. It is not MRP.
`stock_rate.rate_p` is built by `push_snapshot.py` from the `PURCHASE_ITEMWISE` exports, and its
own docstring says what it is:

> *"the last purchase rate in paise **so a shortage can be priced**"*

**The figure on the live document is the owner's cost.** I read where the number sat instead of
what produced it — the F-135 / F-284 family — and told the owner the opposite: that cost was not
computable and MRP was. Both wrong, and the wrong way round. **No count exists, so nothing has
printed. This corrects it before the first one does.**

## And MRP turns out to be real

The first derivation I tried priced one item anywhere from ₹2 to ₹61 a unit, and put a third of
items below cost. That is how it announced itself. So I read the raw rows:

```
2026-08-31   0:15 units   amount 61.60
2026-08-27   0:10 units   amount 61.60
2026-08-18   0:1  unit    amount 61.60      ← the same figure, whatever the quantity
```

**`sale_line_item.amount_p` is not an amount. It is the printed rate of a full strip**, repeated on
every line. A column named *amount* holding a rate. And `returns_desk._per_unit_p()` already says
so — *"a strip-form line's printed rate is the strip's"* — and divides by the pack. **The live
module knew before I did.** The rule here is not new; it is that module's rule, applied.

> **MRP per unit = the printed strip rate ÷ the pack size**

Measured across the 147 items that have both prices:

| MRP ÷ cost | p10 | p25 | median | p75 | below cost |
|---|---|---|---|---|---|
| | 1.25 | 1.30 | **1.40** | 1.62 | **2 of 147** |

A coherent pharmacy margin. The broken derivation had 34 of 147 below cost.

## What changes on the document

- the existing figure is **relabelled at cost**, and the page says it is the last purchase rate
- a real **at MRP** column arrives, and the page says where it comes from
- **a recovery is valued at MRP** — the owner's D-a, now actually executable — falling back to cost
  only when the item has never sold, and **the answer says which basis was used**
- a **coverage line**: how many differences could be priced both ways, one way, or **not at all**
- the no-price block now says *why*: never bought in an export we hold, never sold

**Coverage across the 376-item snapshot: cost 187 · MRP 180 · either 220 · neither 156.**
Those 156 need a rate report out of Marg; nothing here invents a price for them.

## The drift log — and the collision it prevents

`push_expected.py` (what *should* be on the shelf, computed) and `push_snapshot.py` (what *Marg*
says) **post to the same endpoint**, and `stock_snapshot` is keyed `(as_on, item)` with last-write
wins. Two different numbers for one shelf: **if both carry the same `as_on`, the second silently
overwrites the first**, and `reconcile()` then closes differences against whichever landed last.

It has never bitten because the computed push has never run. **It would go live the first morning
both ran.** The walk proves it: after both feeds, `stock_snapshot` holds **one** figure for the day
and `stock_feed` holds **both**.

`stock_feed` is append-only — every pushed figure, its source, and when it arrived. `/api/drift`
then reports, per item, how many runs agreed and how many did not, and distinguishes in words:

- **the same gap on every run** → *look at the arithmetic* (a bug)
- **agreement, then a gap** → *look at the shelf* (an event)

A printed comparison thrown away each morning can never tell those apart. A series tells them
apart at a glance. **That is what makes the owner's month-or-two cross-check mean something**, and
what has to be true before the spot-count bridge can be armed.

`/page/drift` renders it, and says plainly when it has nothing to compare rather than showing an
empty table.

## Proof

| | |
|---|---|
| **walk** | **63/63** — everything the finding walk proved, plus the two prices, the MRP-based recovery, and the feed collision demonstrated and survived |
| **render** | **35/35** — chromium as the owner, as the counter, and on the drift page |

## Before un-parking the daily push

`PUSH_STOCK_DAILY.bat` on the medical PC has **never run** — its own log file does not exist.
**Install this kit first.** Until `stock_feed` is in place, running both feeds risks them
overwriting each other with nothing kept to show it happened.

## Files

| file | what |
|---|---|
| `patch_stock_prices_s221.py` | stock_app.py — the two prices, the MRP recovery, the feed log, the drift API (7 anchors) |
| `stock_finding.html` | the document, corrected — replaces this morning's |
| `stock_drift.html` | the drift page — new |
| `walk_stock_prices_s221.py` | the live-shape walk, 63 checks, runs on the box |
| `RENDER_TEST_prices_s221.py` | the browser gate, 35 checks, offline |
