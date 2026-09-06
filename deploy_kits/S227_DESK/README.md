# S227_DESK — the decision desk, the read-only report, the purchase data audit

**Session 227 · 06-Sep-2026 · supersedes S227_LANES**

## What changed and why

The S227_LANES report put every lane, every button and every tick on one page. The owner's
verdict: "too much data in a very confusing manner … too complex and daunting for a human."
This kit splits it in two.

**The decision desk** — `/finance/stock/page/desk?count=N` (checker only). One card at a time.
Cards come in the order a person would take them: the adjustment-stock items that need the
owner's own word (Kept elsewhere / Used or given / Genuinely missing), then each lane as one
card with its usual answer in one big button (Write off all · Explained · Send all to Darpan's
recheck · Send all to bill verification · Send all to the Marg check), then the real-loss items
one by one (Pursue / Write off / Darpan recounts). "See the N items" opens the list with a
button per line; "Its purchases and sales" opens the life; Skip for now; a Done strip with Undo
(an OPEN row — history kept). A find box at the top forgives a spelling slip ("Axemal" → AXIMAL
200) and jumps to the card that holds the item.

**The report** — `/finance/stock/page/report?count=N` — is now a document: no buttons, every
section folded on arrival, Show / Hide per lane, a card at the top that points to the desk with
the count of lines still wanting a word. Its search forgives a spelling slip and opens the lane.

## The purchase data audit

The owner, on BIO D3 MAX's purchase lines: "20 + 300 loose = 600 … this seems our fault … our
data is wrong … look for all other instances, do a complete data audit."

Root cause, two parts. (1) Marg's *loose* column on a purchase line is the **whole quantity in
units** (20 strips × 15 = 300), not a remainder; the server was adding it to strips × pack and
reading 600. (2) The same bill line reached the server through two overlapping exports
(`purchase_export.superseded_by` is set only for the same type *and* period), so each line
counted twice again.

From this build: purchase units are `loose` when the loose figure covers the paid strips (plus
the free strips if they are not inside it), else `strips × pack + loose remainder`; every line
says which reading it got (`basis`). A line whose export a later export replaced is not counted.
The same (vendor, bill, date, item, batch, qty, free, loose, direction) is counted once. The
item life reports how many lines were dropped and the page says so in words.

`/finance/stock/api/pad/audit.xlsx` (and `/api/pad/audit` as JSON) sweeps every purchase line
this financial year and lists: DOUBLE ENTRY, LOOSE = TOTAL, OLD EXPORT, FREE TOO HIGH (free more
than half the paid strips) — each with a plain-word WHY and a tick column. Nothing is deleted on
the server; the sheet is Amir's list to correct in Marg's purchase register. Linked from the desk
foot and the report's tools strip.

The box-sized-gap test now tolerates a fistful: a gap within one strip (or 15 % of a box) of a
whole number of boxes counts as "about N boxes" — AXIMAL 200, short 286 units, reads "about 3
boxes", which is what Darpan reported.

## Files

| file | role |
|---|---|
| `stock_app.py` | `/page/desk`; `_purchase_units`, `_dead_exports`, dedupe in `_item_life` and `_purchases_since`; `_purchase_audit`, `/api/pad/audit`, `/api/pad/audit.xlsx`; `links.audit`; the box-gap tolerance; `_lane_actions` drops a reopened line |
| `stock_desk.html` | NEW — the decision desk |
| `stock_report.html` | read-only; `.lane` cards with Show/Hide; forgiving search; audit link |
| `stock_check_live.html` | "Doctor: DECIDE — one card at a time" link (class `dl desk`) beside the report link |
| `pad_receipt.py`, `padreader.py`, `padwriter.py` | unchanged, for the walks |

## Proof

347 checks in a real browser at phone width — see `INSTALL.txt` for the list, `EVIDENCE_*.txt`
for the transcripts. `WALK_audit_s227.py` is the new walk: BIO-D3-MAX-shaped lines, a superseded
export, an overlapping export, a true remainder, AXIMAL's gap, and "Axemal" on both pages.

## Install

`INSTALL.txt` — one line, guarded on the S227_LANES pins (0ab2e957 · e28340bc · cb8dfe57),
backs up, compiles, restarts, prints the four sums; rolls back by itself if the service
does not come back.
