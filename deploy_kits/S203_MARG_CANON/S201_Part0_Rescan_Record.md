> ## ⚠ SUPERSEDED — DO NOT ACT ON THIS DOCUMENT
> **Superseded on 26-Aug-2026 by `MARG_PIPELINE_REFERENCE_v1.md` §7**
> (md5 `97b3cf73f7f83c0860bde2d911596ff7`) and `MARG_PIPELINE_MAINTENANCE_FLOW_v1.md` §3
> (md5 `c2b5251f55762490ad219b8855a18dd8`), which carry the rescan as standing procedure.
> The rescan is live and is now documented as a repeatable operation rather than a one-off event.
> What stays unique to this file is **history**: the eleven rescued business dates and the
> `index.csv.before_rescan_20260825-142311` backup name. Read those here; take the procedure from the
> two references above.
> Label added at S203, 26-Aug-2026. **Retained, not deleted (F-23).**

# S201 Part 0 — quarantine rescue + type/date-range classification · LIVE RECORD

**25-Aug-2026 · installed and applied on manojz · recorded as it moved (F-97).**

## The fault this closes

`marg_router.py` blacklists a file by content md5 the moment it is indexed:

```python
219     seen[row.get("md5", "")] = row          # load_index
249     if digest in seen:
250         out("  = already indexed, skipping"); return None
```

`process()` returns **before** `open_sheet()`, before `identify()`. And `append_index()` opens
`index.csv` in `"a"` mode with no update path. So a report filed as UNKNOWN before its signature
existed could never be re-examined, whatever the registry later learned, and its row could never be
corrected. **Every signature added stranded whatever it should have rescued.**

*Correction on the record:* earlier in S201 this was described as "the router re-files but forgets to
fix the index row". That was wrong. There is no re-filing path at all. The two July purchase reports
found sitting in `PURCHASE_*` folders were **hand-made copies placed out-of-band** on 23-Aug —
byte-identical duplicates, no `.txt` sidecar, mtimes matching the folder-creation minute rather than
the `copy2`-preserved source mtimes.

## What was installed

| file | change | backup |
|---|---|---|
| `MargPull/marg_rescan.py` | **NEW.** Re-judges `_UNKNOWN` + `_REFUSED` against the current registry; rewrites the index row instead of appending a contradiction; moves a rescued file out of quarantine once a byte-identical copy is proven filed. Selftest **12/12**. | — |
| `MargPull/RESCAN.bat` | **NEW.** Dry run by default; `APPLY` commits; `TIDY` relocates. Prints the PC's Python version. | — |
| `MargPull/marg_router.py` | `INDEX_COLS` gains **`data_from` / `data_to`**; `process()` records them. | `marg_router.py.before_S201` |
| `MargPull/signatures.json` | adds **`STOCK_CLOSING / TOTALS`** — header `S.No. · Description · Total Stock · Unit` | `signatures.json.before_S201` |
| `MargArchive/index.csv` | migrated 13 → 15 columns, 11 rows corrected | `index.csv.before_rescan_20260825-142311` |

**Design rule enforced:** `marg_rescan.py` makes no classification decision of its own. It imports
`marg_router` and calls `identify()`, `verify()`, `dates_from()`, `canonical_name()`. Re-implementing
the router's opinion is the exact fault that left a two-builds-old parser on the medical PC claiming
byte-identity with the server (AF-5). A second opinion is a second thing to drift.

## The classification change (the owner's point)

`date_from`/`date_to` are what the **title claims**. `data_from`/`data_to` are the dates the **rows
actually carry**. They are recorded separately and neither is inferred from the other.

This matters: a title reading `FROM 23-08-2026 TO 24-08-2026` over a file holding only 24-Aug rows
already misled a reader into believing 23-Aug traded nothing. `PURCHASE_BILLWISE` is the first
archived report where both ranges are present and agree.

## Result

**11 reports rescued** (were UNKNOWN/REFUSED, now VERIFIED and correctly filed):

| type / variant | business date(s) |
|---|---|
| STOCK_CLOSING / TOTALS | 2024-01-20 · 2024-10-05 ×2 · 2025-06-03 · 2026-06-03 · 2026-08-09 |
| STOCK_CLOSING / DEFAULT | 2026-07-01 (scrap store) |
| STOCK_EXPIRY / DEFAULT | 2026-08-23 ×2 |
| PURCHASE_SUPPLIERWISE | 2026-07-01 → 2026-07-31 |
| PURCHASE_BILLWISE | 2026-07-01 → 2026-07-31 |

Index: VERIFIED 16 → 26 · UNKNOWN 5 → 1 · REFUSED 13 → 7. No file exists in two places.
`_rescued/` holds the 11 quarantine copies and their stale sidecars — a record, not a deletion.

**Still quarantined, correctly** — none of these are Marg exports: three untitled ITEM LIST files,
`SANJEEVNI SUPPLIER LIST`, two test workbooks, `SALE BOOK FORMAT` (a hand-made sample), and
`SANJEEVNI ORTHOTIC STOCK 22 JAN 2024` (header `S.No. · Description · MARG · ACTUAL` — the owner's
manual physical-count comparison sheet). No signature was written for that last one deliberately: it
is not the pipeline's business.

## New fault found, NOT yet fixed — log as F-###

**`.xlsx` support on manojz depends on an old Python, silently.** `xlrd 1.2.0` reads `.xlsx` only
below Python 3.9 — `ElementTree.getiterator()` was removed in 3.9. Proven this session: the same
`ITEM DUMP STOCK 9 AUG 2026.xlsx` opens fine under manojz's Python and raises
`'ElementTree' object has no attribute 'getiterator'` under 3.10.

The day manojz's Python is upgraded, **every `.xlsx` Marg export becomes "not a readable .xls"** —
and it will look like a refusal, not a breakage. Marg does emit `.xlsx`. Fix belongs in Part 3: read
`.xlsx` with `openpyxl`, leave `xlrd` for OLE2 `.xls`.

---
*S201 Part 0 · applied by the owner on manojz · no patient identifiers reproduced; no tokens read or
printed.*
