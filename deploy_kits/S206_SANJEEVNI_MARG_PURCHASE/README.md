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
| `selftest_marg_stock.py` | **17 checks**, headed by the cross-store identity that caught a real sign bug |
| `load_archive.py` | parses the whole archive once into a JSON cache (de-duplicates overlapping sale exports) |
| `build_report.py` | writes the self-contained HTML report into `_analysis\` |

### Two corrections this session made to its own earlier work

1. **`-0:10` is −10, not +10.** The minus sign covers the whole quantity, not the packs field.
   Caught by `WHOLE STORES == MAIN + DTH + SCRAP`, which went red on two items and now closes on
   all 375.
2. **The sale item line carries the MRP per pack, not the line amount.** Read as an amount it
   reported "28 items sold below cost, Rs 18,259". Read as `units × rate ÷ pack size` — which
   reproduces whole bills to the paisa — **nothing is sold below cost.**
