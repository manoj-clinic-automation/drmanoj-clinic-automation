# S227_PINPOINT — one quantity vocabulary, every residue pinpointed

**Session 227 · 06-Sep-2026 · supersedes S227_DESK**

## The owner's read of the live desk

"400 units is a confusing remnant — the qty taxonomy has to be globally implemented; 40 strips is
neat and a quick grasp." "(Marg loose 500) is confusing and of no use." "You have all data, find and
pinpoint, otherwise ask for a specific lookup." "A syrup, and we use strips." "What happened to the
40 items carried forward from last year with no movement?"

## What this kit does

**One vocabulary.** `_qw(units, ps)` / `_qws` on the server: strips and tabs for a strip item, pcs for
a bottle, vial or belt (pack 1). Every lane reason, every purchase line, every residue sentence uses
it. A purchase line reads `48 strips (40 + 8 free on the bill)`; the bill's own figures sit small in
brackets, the Marg loose figure is gone.

**Pinpointing.** `_item_life` now works the residue export day by export day. For each span with a
residue it looks for a bill (or two) dated on the span's first day or the three days before it whose
quantity equals the residue — a bill keyed in Marg *after* that day's export was taken. Found → the
span is EXPLAINED in words ("+48 strips is bill 2767 of 27-08-2026 — keyed in Marg after that day's
export was taken; the documents agree, nothing to chase"), the residue for the lanes drops to zero,
and the line leaves the Marg lane (its loss reason carries the note). Not found → ONE question,
pinpointed: "Marg > item ledger > TYRO BR TAB > 02-09-2026 to 03-09-2026: what voucher moved 40
strips out? No bill, return or sale on the server for it." The question is on the line (`lookups`),
in the life (red span), and on **Amir's lookup list** `/finance/stock/api/pad/lookups/<count>.xlsx`
(one row per span: item, the question, a write-in column, a tick).

**The carried-forward stock.** The desk ends with a card "No movement since April — shelf matches
Marg": N items carried forward, not one sold this year; nothing to decide; the items listed ("Marg 4
strips = shelf · last bought …"); Amir's no-movement list. The closing card offers the lookup list.

## Files

| file | change |
|---|---|
| `stock_app.py` | `_qw`/`_qws`; `qty_text`/`on_bill` on purchase lines; span-by-span detector with `spans`, `explained_units`, `lookups`; lane reasons in words; `res_where`/`res_note`; `/api/pad/lookups/<cid>.xlsx`; `links.lookups` |
| `stock_desk.html` | words in the life; span lines; the no-movement info card; lookup links |
| `stock_report.html` | Quantity column; span lines under the residue; lookup link |

## Proof

366 checks at 390 px — `INSTALL.txt` lists them. The audit walk grew the TOLTRIS, TYRO BR and syrup
fixtures and checks both pages.
