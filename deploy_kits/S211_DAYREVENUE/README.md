# S211_DAYREVENUE — K1 · the clinic day-income sheet, read on the VPS

**A reader, not a pipeline. The sheet was already there.**

The owner asked for the Docterz day-income sheet to be pushed to the VPS so Shavez,
Alisha, Shivani and he could work from it. It has been arriving every day already:
`Staff_Action_Today_<date>.xlsx` carries a **"Day Revenue"** worksheet, and
`push_to_vps.py` uploads that workbook to `/root/wa/followup-inbox` daily. **Nothing
was reading it.** His phrase for it was "this buried data", and that was literal.

So: no new push, no new endpoint, no new secret, nothing to change on the clinic PC.

## What it reads

**Summary** — Consultations (paid), X-ray, Procedures, Grand Total, Cash, Online/UPI,
and the morning/evening shift split.
**Detail** — one row per consultation: patient, clinic ID, amount, mode, shift, notes.

Row positions are **never hardcoded**. The sheet is laid out for a human, so blocks are
found by their labels. A sheet that grows a row must not silently shift what this reads
— that is the F-107 shape, a check pointed at the wrong place and still reporting green.

Read-only: it opens the workbook, returns a dict, and writes nothing.

## Proven across every real workbook — 8/8, on 67 files

`python REHEARSAL_dayrevenue.py --folder <the tracker's outputs folder>`

65 parsed; the 2 that could not are two June workbooks predating the revenue feature,
and the reader **says so** rather than returning silence. A sheet whose layout drifts,
and a workbook with no Day Revenue sheet at all, are both reported rather than crashed on.

### The finding that would otherwise have mislabelled every day's money

**The date must come from the sheet, never from the filename.** Measured across the
real workbooks: **60 of them carry a revenue date EARLIER than their own filename.**
The workbook generated on day N holds day N−1's revenue — the last *completed* day,
which is correct behaviour. Reading the date off the filename would have shifted every
day's takings by one day, silently and permanently.

### A second finding, for the owner rather than for the code

**18 of 65 days do not add up: cash + online does not equal the grand total.**
Differences are mostly ₹400–₹600, a few negative, **₹9,601 unexplained in total.**

The likely explanation for the positive ones is the `Pending` column that
`revenue_ledger.csv` already carries — billed but not collected, counted in the total
and not in the two payment modes. **The negative days are the interesting ones**: there,
cash and online together *exceed* what was billed. This kit does not guess; it reports
the difference and leaves it to the owner.

### What is deliberately NOT checked

The detail table against the summary counts. The detail lists more rows than the
summary counts paid heads, and its money column does not sum to the consultation line.
Until the owner says what that column means, asserting a relationship would be inventing
one — **a gate built on a guess is worse than no gate** (fault **i**, this same session).
It is reported, not asserted.

## Still to build

The screen: the same figures shown to Shavez, Alisha, Shivani and the owner, on the
clinic unit that is already live. This module is what it will read.
