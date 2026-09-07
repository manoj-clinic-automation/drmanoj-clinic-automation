# S228_LIVE_TOOLS — the manojz files this session changed

Captured at the S228 close, 07-Sep-2026. **Verified BOTH ways** (A11): the kit's own SUMS, and
each captured file against its LIVE SOURCE on the machine. A kit verified only against its own
copy proves nothing about what is running.

| file | live path on manojz | md5 | what changed |
|---|---|---|---|
| `marg_router.py` | `D:\Downloads\margsync\MargPull\marg_router.py` | `5e034804b8cce5af86d309089cdd2410` | **F-349.** `read_preamble()` no longer assumes the header row starts in column A — it finds the first column the header begins in and returns `(title, header, header_row, c0)`; `dates_from()` takes that `c0`; `RE_RANGE` now accepts "FROM a - b" as well as "FROM a TO b". Backup beside it: `marg_router.py.bak_S228` (`fb32045c…`). |
| `signatures.json` | `D:\Downloads\margsync\MargPull\signatures.json` | `3ecab70a701335c8fb850363dad946ca` | new signature `STOCK_ITEM_LEDGER / BATCHWISE`, `uploadable: false` (the ledger is read here, not pushed). Backup: `signatures.json.bak_S228` (`c0a37268…`). |
| `marg_item_ledger.py` | `D:\Downloads\margsync\_analysis\marg_item_ledger.py` | `01d365dad09cb01f47de3091af2ea776` | **NEW.** Reads Marg's BATCH WISE STOCK item ledger. **F-348:** quantities are Excel TIME and are converted to tablets at the door; negative balances arrive as text (`-2:10`); the footer is found by its marker, not a fixed column. |

**Regression after the router change:** the whole archive re-routed, 152 files — **148 identical,
4 changed, and all four are the item-ledger exports that were previously refused.**

**Nothing else on manojz changed this session.** No install order, no new scheduled task, no new
credential. The pull chain (`PULL_FROM_MEDICAL.bat`, `expected_on_capture.py`) is untouched.
