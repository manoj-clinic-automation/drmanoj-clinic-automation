# S228 LOSS DESK — the owner's own page

*Built at Session 228, 06-Sep-2026, on the owner's ruling D389 and `S228_BUILD_BRIEF` item 4.*

> "A real assessment of the loss of pharmacy from my side, item and qty wise, for my
> record — I do the play here."

## What it is

`/finance/stock/page/loss` is the owner's page and nobody else's — a member of staff
who opens it, reads its numbers, or tries to log against it is refused by the server,
not merely unlinked.

It holds every **shortage** on a count (a line that came up *over* has no business on
a loss desk), priced two ways: at MRP, which is the owner's basis, and at what it cost
him. The sections are his order, not the data's:

1. **Where the money is** — every shortage worth ₹1,000 or more at MRP.
2. **Where the quantity is** — 10 or more short and not already above. This is the
   section that exists because value alone hides it: 15 strips gone is 15 strips gone
   whether it is ₹75 or ₹7,500.
3. **The rest** — largest value first. A section longer than ten folds after eight,
   with one button to open it; fourteen near-identical lines are not fourteen screens.

Three lines at the top and no fourth (D383, ruling 17), one number to a line, and once
a sheet is out the third line reconciles itself: *"₹7,861 still standing — ₹1,700 back
of ₹9,561 given to him."*

## The sheet, and why it is frozen

**Make the sheet for Darpan** takes the marked lines and writes them down once: an A4
portrait page with the item, the shortage in strips and tabs, the MRP each, the loss at
MRP, a total, and an empty box per line for his answer. No purchase rate appears on it
anywhere — Darpan is not shown what the shop paid.

The moment it is made, the lines are serialised, fingerprinted by md5, and kept in
`pad_uploads/loss_shares/<md5>.pdf`. Every later request returns those bytes. If a
price moves next week the sheet does not: the paper in Darpan's hand and the screen in
the owner's hand say one number for one medicine, which is the whole point of a shared
record. The desk honours the same rule — a line already on a sheet displays the
sheet's figure, is marked *on sheet 1*, and can never be put on a second sheet.

## What comes back

Against a sheet, per item: **found on the shelf** (valued at the price that was on
that sheet, never a fresh one), **money recovered**, or **accepted as lost**. Every
entry is append-only, stamped with the hour, shown on the line itself so no row reads
gross while the top of the page reads net, and kept for the next stock check.

## Darpan's lists moved here

> "Move from here to a place where I own it and get it done from Darpan."

Cutting a list, printing it and marking it returned are now on the owner's page. The
tranche engine is untouched — this page drives the same endpoints, and the printed
list still carries no rupee. Amir keeps the **typing** of Darpan's answers and nothing
else about the lists: his work does not grow, and the owner's does not become typing
(F-339). His typing table, four columns on a 390 px phone, now scrolls sideways
instead of being sliced by the card edge.

## How it was built

`patch_loss_desk_s228.py` builds the four changed files from the S227 pins and refuses
if a source file is not the pinned one, so the change is a readable transform rather
than a hand edit of 225 KB. `_block_loss.py` and `_block_receipt.py` are the two new
blocks it inserts.

## What it was checked against

496 checks in a real browser at 390 px, no failures — 93 on the new page, 403 in
regression across the eight S227 walks and three S226 ones. `WALK_staff_s227` was
updated rather than the product: it asserted that Darpan's lists live on Amir's board,
which is the shape D389 supersedes.

Screens were read by a sub-agent three times. The first read found four real defects
sitting behind 79 green checks — a pack line sliced by the row rule on the printed
sheet, a second sheet re-listing everything already on the first, a top box carrying
five figures across eight lines, tick boxes too small for a thumb. The second found
the screen and the paper disagreeing on a repriced item, and a headline that did not
reconcile with the page beneath it. The third found nothing left to fix. This is the
S208/S209 lesson again: green gates prove the machinery, not the page.

## Left standing, deliberately

* The orthotics family verdicts on Amir's board still read `short 2 -- fitted and not
  keyed` — a raw double hyphen, and a bare count where D384 asks for strips. Both are
  S227 strings that the S227 walks assert; changing them belongs in its own step.
* The tranche pool can still put an item that came up *over* into a list of shortages
  to explain. S227 behaviour, unchanged here.
* The reason legend on Amir's board is one dense bilingual run-on line.
