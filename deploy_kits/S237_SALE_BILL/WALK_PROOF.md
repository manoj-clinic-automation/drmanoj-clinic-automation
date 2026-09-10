# S237_SALE_BILL — THE LIVE-SHAPE WALK

**10-Sep-2026.** Run against **the clinic's real data**, not fixtures: all 29 archived sale exports
from `D:\Downloads\margsync\MargArchive\SALE_BILLWISE\`, and a copy of the **real 08-Sep nightly
database**. Nothing was written to anything live.

---

## 1 · WHAT THE ARCHIVE ACTUALLY CONTAINS

```
  bills                524 over 21 day(s)
  gross                Rs 507,965.16
  DISCOUNT             Rs  27,375.33   (5.39% of gross)  <- thrown away today
  net                  Rs 480,243.00
  cash                 Rs 419,716.00
  bills with a discount 347 of 524
  credit notes          32
  bills Marg rounded    181
```

**₹27,375.33 of discount, across 21 days, is parsed correctly and then discarded** — about ₹1,300 a
day that no report in the estate can see. That is the whole of Rung 1 in one number.

## 2 · IT REPRODUCES THE S236 HAND ANALYSIS — 6 of 6

The six single-appliance bills that F-385 was argued from, now produced **by the pipeline** instead of
by hand:

| bill | date | gross | discount | measured | ruled |
|---|---|---:|---:|---:|---:|
| A003160 | 24-Aug | 2,349.00 | 749.00 | **31.89 %** | 30 % |
| A003250 | 28-Aug | 2,349.00 | 699.00 | **29.76 %** | 30 % |
| A003251 | 28-Aug | 2,349.00 | 699.00 | **29.76 %** | 30 % |
| A003181 | 25-Aug | 456.56 | 114.14 | **25.00 %** | 25 % |
| A003278 | 29-Aug | 470.00 | 120.00 | **25.53 %** | 25 % |
| A003136 | 22-Aug | 1,060.00 | 0.00 | **0.00 %** | M.R.P. |

**Every one matches.** The S236 finding was hand-built from 446 bills; it now falls out of a table.

**And the four-appliance bill of 09-Sep** — `A003495`, gross **₹3,170.00**, discount **₹870.00**
(**27.44 %**), net **₹2,300.00**, residual **0** — the bill Rung 2 will use as its fixture.

## 3 · ⭐ IT JOINS — 100 % INSIDE THE WINDOW IT CAN BE TESTED ON

The whole point is that the header can be attached to the item lines. Measured against the real
database:

| | |
|---|---:|
| `sale_bill` rows written | **524** |
| with matching rows in `sale_line_item` | **448 (85.5 %)** |
| unmatched | **76** |

**And every one of the 76 is explained, not left as a gap.** The nightly backup's last day with item
lines is **05-Sep**; all 76 fall on **07, 08 and 09-Sep** — days whose bills the backup carries but
whose lines it does not yet.

> **Unmatched, not a credit note, and inside the covered window: ZERO.**

## 4 · THE ROUNDING IS DATA, NOT A TOLERANCE

**181 of 524 bills** carry a residual where `gross − discount + dr/cr ≠ net`, ranging **−49 to +50
paise** — Marg rounding a bill's net to the whole rupee. **None exceeds one rupee.**

It is stored in `round_p` rather than absorbed by a tolerance, so it is a number somebody can look at.
Anything beyond a rupee is **refused**, on the grounds that it is not rounding but a misreading.

## 5 · IDEMPOTENT, AND IT TOUCHES NOTHING ELSE

| run | result |
|---|---|
| first | 524 inserted, 0 updated, 0 kept |
| second, identical | **0 inserted, 524 updated, 0 kept** — same 524 rows, same ₹27,375.33 |

`sale_line_item` **17,848 rows** and `marg_item` **374 rows** — unchanged, before and after. The
module creates one table and writes to that table only.

Where the same day appears in several exports (02-Sep has four, 09-Sep has two), the **later export
stamp wins**, and the result does not depend on the order the files were read in — proven both ways
in the selftests.

## 6 · 🟠 ONE DAY THE ARCHIVE CANNOT GIVE, AND IT IS NAMED

```
SALE_BILLWISE_DETAIL__2026-08-27__20260828-070911__05383ef2.xlsx: parser refused it
  -- not a readable .xls file (Excel xlsx file; not supported)
```

**27-Aug is the one business day with no bill headers**, because its export was saved as `.xlsx` and
the repository's `marg_report.py` reads only the legacy `.xls`.

⚠ **This may not be true of the LIVE parser.** `marg_backfill.py`'s own help says *"path to the Marg
BILL WISE export (.xls or .xlsx)"*, and the live `/root/finance/marg_report.py` matches neither
repository copy — so the box may well read it. **The walk reports what the repository parser does;
the first live run will say what the live one does.** Either way the day is named, not silently
missing.

## 7 · THE INSTALLER WAS WALKED TOO — 22 checks, 0 failures

`_proof/install_walk.sh` runs the real installer against a real filesystem holding a real database,
and its central assertion is the one that matters for a money table:

> **after a green install, and after a red install, the database is byte-identical and no
> `sale_bill` table exists.** The install shows the numbers; only the owner's second line stores them.

It covers the green path, the green path with exports present, the green path over an existing file
(which must be backed up), the identity gate refusing, and a wrong box.

**And it earned its place immediately.** `--locate` used a hard-coded `/root/finance/...` list, so
with `FINANCE_DIR` pointed anywhere else it found nothing and reported *"no exports here"* — a
confident wrong answer of exactly the kind this project keeps paying for. It now follows
`FINANCE_DIR`.

## 8 · THE GATES

`py_compile` clean · **46 selftest checks, 0 failures** · **installer walk 22 checks, 0 failures** ·
the data walk above · kit gate **6 of 6 green from inside its own folder**.

One selftest failure was found and fixed on the way, and it was the fixture's fault, not the code's:
a test bill built with a net that did not follow from its gross was **correctly refused** by the
one-rupee guard. **The guard caught the test.**

---
*S237_SALE_BILL · WALK_PROOF · 10-Sep-2026. Real exports, real database copy, nothing live touched.*
