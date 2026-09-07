# S229_MARG_INGEST — four new Marg report types, and the rescue tool repaired

**07-Sep-2026.** Two files. Both are ALREADY LIVE on manojz — this kit is the repository copy,
so the repo and the machine agree. Nothing here has to be installed.

## What changed

### 1 · `signatures.json` — 13 signatures to 17

| new | variant | title | why |
|---|---|---|---|
| `SALT_WISE_ITEM_LIST` | DEFAULT | `SALT WISE ITEM LIST` | the salt spine — salt, packing, P.RATE / S.RATE / M.R.P. |
| `STOCK_VALUATION` | **STRIPS_TAB** | `STOCK VALUATION` | the 6-column edition. **Listed FIRST on purpose** |
| `STOCK_VALUATION` | DEFAULT | `STOCK VALUATION` | the 4-column edition |
| `ITEM_MASTER` | DEFAULT | `LIST OF ITEMS` | Marg's own item list |

Two things that must not be "tidied":

- **The STRIPS_TAB block must stay above the DEFAULT block.** `identify()` compares only the first
  *n* columns, so the 4-column signature would match the 6-column file and its STRIPS/TAB columns
  would be lost with no error anywhere.
- **`Compnay` is Marg's own spelling** in the item master's header row. Spelling it correctly
  would refuse every real file.

`SALT_WISE_ITEM_LIST` and `ITEM_MASTER` carry `"dating": "file_mtime"` — neither report has an as-on
date in its title or a date column in its body, and without that key `verify()` refuses the file for
having no dates. That is precisely how two salt lists and the item master sat in quarantine for ten days.

`SALES STATEMENT AS ON` is deliberately NOT onboarded — the owner declined it on 07-Sep as useless.

### 2 · `marg_rescan.py` — F-351

At the S228 close `read_preamble()` began returning four values instead of three (the `c0` indent fix
for Marg's batch-wise stock report). `marg_rescan.py` still unpacked three, so it raised `ValueError`
on the first quarantined file of every run.

The ten-minute pull logged it as `PROBLEM: rescan=1` — **69 consecutive cycles**, from
06-09-2026 23:40:51 to 07-09-2026 11:00:32 IST. Nothing else said a word. The rescue tool being dead
is why the quarantine never cleared even though the registry already knew what three of the files were.

The fix unpacks four and passes `c0` on to `dates_from`, exactly as the router does — one judgement,
not two. First green cycle after it: `07-09-2026 11:10:32.52  ok`.

## Proof

- `marg_router.py --selftest` — SELFTEST OK
- `marg_rescan.py --selftest` — 13/13
- `py_compile` — clean
- all six real files identify correctly, including the 4-column vs 6-column ordering trap
- regression over the ten pre-existing types — **0 changed**
- live, on manojz, by his own scheduler: **11 reports rescued** from quarantine across the
  11:10 and 11:21 IST cycles; quarantine 28 files to 18; `index.csv` 175 of 184 rows VERIFIED

## Verify this kit

Run from INSIDE this folder — its rows are rooted here:

```
md5sum -c KIT_MANIFEST.md5
```
