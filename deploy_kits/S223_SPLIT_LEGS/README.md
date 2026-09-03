# S223_SPLIT_LEGS — what a split payment was actually paid with

**The owner:** *"give breakup details of any split payment also"*

## The problem, stated exactly

The Day Revenue sheet records a bill's payment **mode** but not its **legs**. `Split Payment` is
all it can say. The legs live one step upstream, in the raw Docterz export:

    1100 (Wallet: 600, Online Payment: 500)

and the live tracker's `split_payment()` searches for two words — cash, and online — where Docterz
emits seven.

## What that has cost, measured on the clinic's own retained exports

**79 raw exports are retained on the clinic PC**, back to April. Run through the seven-token parser:

- **103 split bills across 61 days, ₹1,77,999 in 206 legs**, and not one unrecognised token
- **26 of those bills carry tender the old reader could not see at all: ₹18,100** —
  **Debit Card ₹9,400 · Wallet ₹7,100 · Patient APP ₹1,600**

**No revenue was ever lost by this.** The day's GRAND TOTAL comes from `Bill Amount`, not from
tender, which is why no total ever looked wrong. What was lost is the **split** — which of that
money was cash and which was not — and that is precisely the figure the bank statement has to
agree with. The ₹600 found on 19-Aug was one instance of an ₹18,100 pattern.

## How it reaches the screen, with no new plumbing

`push_day_tenders.py` runs on the clinic PC, reads the retained exports, and writes **one file**:

    <tracker>\outputs\Day_Tenders.csv

`outputs\` is already the folder Google Drive syncs — it is where `Staff_Action_Today_*.xlsx`
comes from, and the folder the VPS reader already reads. So there is **no new push, no new
endpoint, no new credential, and no change to the tracker itself.** The file appears beside the
workbooks; the reader picks it up; the day page grows a block.

**Already run**, 04-Sep-2026: 206 rows written. It touched nothing else on that PC.

## What the file carries, and what it refuses to carry

`business_date, clinic_id, invoice_no, tender, amount_p, source_file`.

**No patient name. No mobile number.** Neither is read out of the row. The clinic ID is the join
key and is already present in every Day Revenue sheet in that same Drive folder — so this file adds
no exposure that the folder did not already have. It was scanned before it was written: zero
mobile-shaped and zero UID-shaped strings in 206 rows.

## On the page

A day with splits grows one block — **SPLIT PAYMENTS — how each was actually paid** — listing the
clinic ID, the invoice, the legs (`Wallet ₹600 + Online Payment ₹500`) and the bill total. It sits
below the sections, in the same A4 print layout, and it is **absent, not empty**, on a day with no
splits or before the PC pass has run.

## Proven — 46/46 GREEN

`EVIDENCE_splitlegs_s223.txt`.

**Stated so nothing is overclaimed:** the *parser* is proven on the 79 real exports (the numbers
above). The *page* is proven by a labelled fixture built from clinic IDs that really are on the day
under test — because those raw exports are on the clinic PC, not in the build container. The
checks cover the block appearing, each leg named with its own amount, the legs adding up, the block
totalling the bills, the count of bills, and the block being **absent rather than empty** when no
legs are stored.

## The honest limit

This recovers the legs for the **79 exports the PC has kept**. A day whose raw export is gone keeps
its total (that never depended on tender) and simply shows no breakup. And the underlying fault is
still live in the tracker: `split_payment()` on that machine still reads two tokens of seven, so
**tomorrow's split will need this pass run again**. Fixing it at source — the tracker-side parser
patch, already written and proven offline — is what stops that, and it is not in this kit.
