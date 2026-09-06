# S226_PAD_IMPORT — the counted sheet becomes the count

> *"Entering then will be a breeze and not more than a few minutes job."*
> *"Accept the staff-filled excel and not reject it — rather give a follow-up
> excel then and there."*
> *"The second sheet only gives them what is to be done now, and not what has
> been accepted by the system."*
> — the owner, 06-Sep-2026

Transcribing 373 items into a screen one card at a time is not a few minutes
however fast the screen is made. So the sheet they filled **is** the entry.

```
https://followup.dr-manoj.in/finance/stock/page/pad
```

## The flow

1. **Upload** the filled pad. Before anything is written the page says exactly
   what it read: how many counted, how many agree with Marg, how many differ,
   how many were never reached, the differences with their value at MRP, and
   every row it could not use — with its row number and why.
2. **Record.** Everything clean becomes that day's count — sealed, with the
   data horizon frozen — pinned to who counted, who entered, and the bill.
3. **The result workbook is handed back on the spot**, and stays at the same
   link — five tabs, to the owner's approved layout of 06-Sep:
   **SUMMARY** (who, when, the bill, the four *Read first* lines frozen at the
   moment, the count in numbers, explanations so far) · **DIFFERENCES** (item,
   packing, Marg stock and physical count *in strips and tabs*, the difference
   as *short 1 strip 3 tablets*, at MRP, and three optional columns for reason,
   cause, decision) · **NOT COUNTED** (names only, shaded cells to fill — *no
   figure from Marg*) · **SENT BACK TO FIX** (the rows that could not be used,
   name as written, what to fix, shaded cells to correct it) · **MATCHED**.
4. **Staff fill the two fill-in tabs and the same workbook is uploaded.** It
   carries *"PART OF COUNT #N"*, records as a part of that count, closes each
   sent-back row **by its original row number** (not by the name, which is what
   was wrong), and the next result shows the true state of the whole family.
5. **A fresh pad for a new count** is one link on the same page — the shop's
   item list as it stands, no figures.

The only thing that stops a recording is a sheet with **nothing** usable in it.

## Rules it is built to

**A counted figure is never silently dropped.** What cannot be used is kept —
figure and all — against the count, in `stock_count_pad_issue`, so the follow-up
can be handed back now and again later. A sheet a person has to ask for twice is
a sheet that gets lost.

**The bytes that were checked are the bytes that commit.** The file's own md5
must come back with the confirmation.

**Nothing sealed ever changes.** A follow-up is a new count linked to the first
(`stock_count_part`), not an edit of it. The report reads the family together.

## Reading and writing .xlsx with nothing installed

**Stdlib only, both ways.** `padreader.py` opens the workbook with `zipfile` and
`ElementTree`; `padwriter.py` writes one the same way — inline strings, a
handful of styles, real formulas for the total, frozen header, autofilter,
print titles. `openpyxl` may or may not be in the VPS venv and a stock count is
not the moment to find out. The written pads open in **LibreOffice** (all 375
formulas recalculate, zero errors — 20 strips × 20 + 5 = 405) and in
**openpyxl** (shading, bold header, frozen row and filter all present) — two
readers that are not ours.

**The reader does not trust the TOTAL column.** It is a formula, and a formula
written by a program has no cached value until something recalculates it. The
total is computed from STRIPS and LOOSE and the pack size — the counting page's
own arithmetic. The walk saves the pad **deliberately without recalculation**
and proves the figures come out identical either way.

Names match on the project's one key — case, inner spacing and **trailing dots**.

## One helper, two ways in

`api_count` (the counting page) and `api_pad_commit` (the sheet) both go through
`_record_count()`. Two ways in, one way through.

## What the walk caught

Three defects in the code, all on paths a unit test would have passed: a
normaliser that does not exist in this module; a server error reaching the page
as *"Unexpected token '<'"*; and the extracted helper leaving `items` behind —
**so the preview worked perfectly and recording threw.** Then two in the walk
itself, both the same slip: it counted the pad's footer labels as items.

## Proof — 230 checks

| walk | result |
|---|---|
| `WALK_pad_import_s226.py` — the real pad, filled and saved without recalculation, driven in a browser: preview, record, ledger read back; a dirty sheet **accepted**, the clean rows recorded, the result workbook handed back and opened in a second reader — five tabs in order, every approved column, no MRP block on the summary, no Marg figure on the fill-in tab; both fill-in tabs filled and **joining** the count, the total settled from the shop's pack size, a corrected name closing its own row; the next result showing the family's true state; a fresh pad on demand; a swapped file refused | **54 / 54** |
| the counting page against the refactor — search and revisit, report and send, the safe store | **77 / 77** |
| readiness, drift truth, drift screens — unchanged | **99 / 99** |

**Carried into the report design:** in a full-size 373-item run every difference
came back unpriced, and in production only about half the shop carries a rate.
The preview says how many differences it could not put a rupee value on.

## Recorded here, the owner's direction for what follows

* The Excel is **a phase**. After real feedback the staff system is upgraded
  and the Excel retired.
* **Spot checks of random items live in the main VPS stock-check system only** —
  one place, not scattered.
