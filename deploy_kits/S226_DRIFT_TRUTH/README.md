# S226_DRIFT_TRUTH — what the first live look found

The owner opened `/finance/stock/page/drift` minutes after `S226_READINESS`
went live. Four things came back. Three were defects; one was a question that
had no page to answer it.

## 1 · "746 items" and "1,492 items" for a 373-item shop

The readiness header counted **rows in `stock_feed`, not items.** That table is
append-only and every push writes a whole set of rows, so a day with two Marg
pushes reads as 746 and four of ours as 1,492. Now it counts the items of the
**newest push**, which is the only figure that means anything.

## 2 · A re-export changed nothing on the screen

The bigger one. `api_drift` grouped `stock_feed` by `(as_on, source, item)` and
then wrote each feed's figure into a dictionary in **whatever order the rows
came back**. With three pushes of the same day under three different `source`
strings, the winner was arbitrary — so after LACTOVAX was merged in Marg and the
merged export was pushed *and marked*, the page could still be showing the
figure from the push before it. The owner's words: *"I merged lactovax and
re-exported the stock report, but the table is the same."*

`_feed_latest()` now applies **the owner's own rule, already on the wall card:
the server keeps the newer export of a day.** One push per day per feed — the
newest — wins. An item the newer push no longer carries (a merged duplicate)
correctly stops on the day it was merged, and its history is not rewritten.

## 3 · "look at the shelf" after one single day

A day compared **once** was being read as *"gap on some runs — look at the
shelf"*. One day is not a series; the whole page exists to tell a bug from an
event, and it cannot on day one. It now says *"first day compared — too early
to say which."*

## 4 · The headers, and the column that did not line up

`Runs`, `Last gap`, `Recent` → **Days compared · Days agreed · Days differed ·
Gap on the last day · Day by day (oldest → newest)**, with one line above the
table saying what a gap is: *our figure minus Marg's, in units; 0 means they
agree.* The day-by-day figures are now fixed-width chips in a right-aligned
column, so they sit under their own header instead of drifting left of it, and a
day that differed is marked while a day that agreed is not.

## 5 · "Where do I see the latest stock in our system?" — the new page

```
https://followup.dr-manoj.in/finance/stock/page/now
```

**Stock as we hold it.** For the newest day the server has: every item, our
computed figure, Marg's figure, and the gap — with four tiles (items · agree ·
differ · below zero) and three filters. It opens with the readiness header like
the others, and it says in its own words that it is **not a count**: a count is
what settles a difference; this is what tells you where to look. The *below
zero* filter explains itself rather than alarming — a negative line is a sale
rung up against goods whose purchase bill has not been entered yet, and it
clears itself when the bill is entered.

There is no portal tile for it yet. That is one line in `portal.py`, a
different live file, and it is deliberately not bundled into a stock kit.

## Proof

| walk | what it does | result |
|---|---|---|
| `WALK_drift_truth_s226.py` | Rebuilds the morning of 06-Sep exactly: three Marg pushes of 05-Sep (one after the merge, one item fewer), two of ours, a day compared once. Every check in it **fails on the code he was looking at.** | **32 / 32** |
| `WALK_screen_drift_s226.py` | Both pages in a real browser at 390×844. Reads the headers, **measures the day-by-day column against its own header's right edge**, clicks the filters, and watches for a page error. | **17 / 17** |
| `WALK_readiness_s226.py` (from `S226_READINESS`) | Re-run unchanged, as the regression. | **50 / 50** |

Run any of them from inside this folder:

    python WALK_drift_truth_s226.py
    python WALK_screen_drift_s226.py

## Still not fixed here, and why

`BIO D3 MAX` will keep showing its 7 until the re-exported sale report for
04-Sep actually reaches this system — the bill `A003396` that explains it was
entered after that day's export was taken (settled at S225). **As at 08:32 IST
on 06-Sep nothing had been captured since 03:10 IST**, so the morning's
re-exports had not left the medical PC. No code can close that line; the export
has to arrive.
