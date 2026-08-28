# S206_SANJEEVNI_MARG_PURCHASE — Q1 step 1: the purchase-side parser

**Staged, not installed.** Nothing here runs on a schedule, touches the VPS, or writes to a
live path.

| file | what it is |
|---|---|
| `marg_purchase.py` | reads a Marg **SUPPLIER/ITEM WISE PURCHASE STATEMENT** `.XLS` into normalised rows |
| `selftest_marg_purchase.py` | asserts it against the **real archive** — 29 checks, and it can fail |

## Why the sale side is not here

`marg_report.py` (live, in `S205_LIVE_TOOLS\manojz\`) already reads the **BILL WISE SALES
STATEMENT** and is not touched. Q1 needs both sides; only the purchase side was missing.

## Run it

```
python3 selftest_marg_purchase.py [ARCHIVE_DIR]
```
Default archive dir is `~/mnt/Downloads/margsync/MargArchive`; on Windows pass
`D:\Downloads\margsync\MargArchive`. Exit 0 = all passed. Needs `xlrd` (`pip install xlrd`) —
xlrd 2.x reads legacy `.xls`, which is what Marg writes.

## The one thing to know before using the rows

**Item rows over-state. Supplier TOTAL rows do not.** Measured over five months: the TOTAL rows
sum to GRAND TOTAL exactly, every month; the item rows over-sum by up to **+2.13%**. Any figure
that must be right to the rupee comes from the totals. The item rows are for *shape* — which item,
which batch, which expiry — not for reconciling money.

## Added in the same session — the stock side and the report

| file | what it is |
|---|---|
| `marg_stock.py` | reads CLOSING STOCK (4 stores) and STOCK EXPIRY |
| `selftest_marg_stock.py` | **25 checks**, headed by the cross-store identity that caught a real sign bug *(this line said 17; measured 25 on 28-Aug — corrected, not quietly)* |
| `load_archive.py` | parses the whole archive once into a JSON cache (de-duplicates overlapping sale exports) |
| `build_report.py` | writes the self-contained HTML report into `_analysis\` |

### Two corrections this session made to its own earlier work

1. **`-0:10` is −10, not +10.** The minus sign covers the whole quantity, not the packs field.
   Caught by `WHOLE STORES == MAIN + DTH + SCRAP`, which went red on two items and now closes on
   all 375.
2. **The sale item line carries the MRP per pack, not the line amount.** Read as an amount it
   reported "28 items sold below cost, Rs 18,259". Read as `units × rate ÷ pack size` — which
   reproduces whole bills to the paisa — **nothing is sold below cost.**

---

## S207 — WHAT THE FIVE SELFTESTS DO WHEN THE ARCHIVE IS NOT THERE

**Measured 28-Aug-2026 with `D:\Downloads` disconnected: three of these crashed.**
`selftest_marg_stock` raised `KeyError: 'WHOLE STORES'`, `selftest_purchase_returns` raised
`IndexError: list index out of range`, and `selftest_units` printed a bare `FAILED` and exited 1.
**A traceback looks exactly like a real regression**, and a check that always looks broken is the
one that gets waved through (D316). None of them was broken — every check past that point asserts
against the real Marg exports, and there were none to assert against.

**All four now stop cleanly and say so, and the exit code carries the distinction:**

| exit | meaning |
|---|---|
| **0** | every check passed |
| **1** | a check genuinely **failed** — look at it |
| **2** | **the archive was not reachable.** Not a code failure. Connect the folder and re-run. |

`selftest_purchase_returns.py` and `selftest_units.py` also **accept the archive path as argument 1**
now — the new message tells you to pass one, and two of the four could not take one. A runbook line
nobody can follow is the fault, not the wording.

### Proven both ways, 28-Aug-2026

| | |
|---|---|
| with the real archive | **29 · 25 · 19 · 7 · 17 = 97 checks, 0 failures**, all exit 0 — *identical to before the change* |
| with no archive | all four exit **2**, **zero tracebacks**, each naming the export it could not find and how many data-free checks passed first |

*The with-data path was not touched. Only the empty-archive path changed.*
