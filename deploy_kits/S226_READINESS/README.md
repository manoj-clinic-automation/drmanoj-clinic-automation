# S226_READINESS — "Read first, know the data"

The owner's ruling, 06-Sep-2026:

> The drift page must open with data-readiness lines, before any result: sale
> report current to *date* with the **last bill number** · purchases current to
> *date*, with the **last day's bills listed as the Bill-wise purchase report
> shows them** · the **stock export's date and time**, and when it was
> processed. *"Read first, know the data."*
>
> Every stock-check result is logged with: the counted and the expected stock ·
> purchases current to date with that last day's bills · the last sale bill
> number and date · and the sentence *"all sale returns up to credit-note ___
> dated ___ have been processed."*

## Why it matters, in one paragraph

On 05-Sep thirteen items computed **below zero**. Nothing was missing from the
shelf: purchases were known only to 03-Sep, and sales had been rung up against
goods whose purchase bills were not yet entered. The page had no place that
said so where a reader would look first. A difference read without the horizon
of the books that produced it is unreadable — so the horizon now opens the page.

## What changes

**`stock_app.py`** — one new section, `S226 READINESS`, appended, plus four
small edits:
* `readiness(con)` and its four blocks (`_r_sale`, `_r_purchase`, `_r_stock`,
  `_r_returns`) — read-only, each guarded on its own.
* `GET /finance/stock/api/readiness` — the header's own endpoint.
* `/api/drift` now carries `readiness` so the drift page needs one round trip.
* `stock_check_readiness` — a new table. `_f_seal` freezes the horizon into it
  in the same transaction that seals the finding, so a result read a month
  later shows what the books could see on the day.
* `/api/finding/<id>` returns that frozen header (and says `frozen:false` with
  a note for findings sealed before this kit existed).

**`stock_drift.html`** and **`stock_check_live.html`** — the same self-contained
header card, above everything else on both pages. Its own escaper, its own
styles, its own failure text, so it depends on nothing in the page it sits in.

Nothing computes stock. Nothing decides. No live table is written except the
new one.

## The rule this kit was built under

*A readiness header that can take a page down is worse than no header at all.*
Every block returns a plain English "unknown" line on any failure, and the walk
proves it: with `purchase_bill` **dropped**, the drift page still serves 200 and
the other three lines still stand.

## Proof

| walk | what it does | result |
|---|---|---|
| `WALK_readiness_s226.py` | builds the real schemas, fills them with the shape of 05/06-Sep, mounts the blueprint the way `finance_app` does, and reads the payload, both pages' markup, a submitted count, its seal and its frozen log — then drops a table and an empty server | **50/50** |
| `WALK_screen_s226.py` | opens both pages in a real browser at phone width and reads what a person reads | **16/16** |

Both evidence files are beside this README.

Run either from inside this folder:

    python WALK_readiness_s226.py
    python WALK_screen_s226.py

## Observed, not raised as a fault

`stock_check_live.html` has loaded Google Fonts from the internet since S213.
Unchanged by this kit; on a phone without a connection the page falls back to
system fonts and still counts.
