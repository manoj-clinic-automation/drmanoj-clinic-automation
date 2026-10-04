# S470_ORDER_ON_SPINE — the medicine order engine reads the spine

Brief: `claude_code_briefs/S470_ORDER_ON_SPINE.md` (session 285, 04-Oct-2026; D672, D673; F-718, F-719).
Report: `claude_code_briefs/REPORT_S470.md`. It finishes rung 4a of `S272_SPINE_ARCHITECTURE.md` §5.

## What and why

The system's own medicine list (`order_rules.py`) took its three numbers — the sale rate, the stock, the supplier and lot — from four old
tables that nothing checks. The spine is the one store that is checked against Marg every ten minutes. This kit moves the engine's reads
onto the spine's one read door, behind one setting, and makes the nightly trial score the list the engine really made.

**What it does not do:** it does not change which list the staff see (`order.source` stays `marg_sheet`), any buying rule or its value,
or any staff screen. It does not build the buying model.

- **`order.engine_source`** = `spine` (the default after install) or `tables`. On `tables` the four old calls run exactly as before; the
  walk shows the two plans equal there, line for line. If the spine cannot be read the engine takes the old tables for that plan and the
  plan says so (`engine`).
- **On `spine`:**
  - Marg's stock is the spine's latest accepted closing (`closing`).
  - The sale rate is `purchase_app._pace`'s own formula on the spine's sale lines, returns deducted (`sales_daily`, `last_sale`).
  - The supplier, the cost per pack, the box, and the lot and free are read from the spine's purchase lines (`purchase_lines`).
  - The count basis is still `shelf_figure.figures()`, which is not touched.
- **The item list** (names, packings, pack sizes) is still Marg's newest stock list (`stock_snapshot`). No figure is read from it. The
  spine keeps a closing by 20-letter key, not by item, and its own item table holds one item twice where two reports spell its packing
  differently ("1*10" and "1*10."), so it cannot be the list.
- **A family** (items of the stock list under one 20-letter key, F-719) is planned on the family's cover: its stock and its rate are both
  shared equally among its members, and the line carries `family = n`. Today no medicine is in a family; eight orthotic keys are.
- **Arrivals not yet in Marg — one rule on both bases.** Received goods, and goods that arrived by a bill's scan, count as stock until
  the spine shows a purchase line of that item from that supplier dated on or after **the order's own day**. The old rule waited for a
  bill dated after the tap; Marg dates the bill by the supplier's date, so the goods were counted twice until the 14 days ran out.
- **A sold item never bought** is still ordered from nobody, but `plan()` now returns it under `no_supplier` and the owner's card counts it.
- **Six constants are settings** at their present values, on the settings card of `/finance/porders?old=1`: `order.engine_source` (spine),
  `order.pace_days` (28), `order.dead_after_days` (60), `order.on_order_days` (4), `order.in_transit_days` (14),
  `order.lot_history_days` (180).
- **The nightly trial** (`spine/order_rehearsal.py`, replaced whole) keeps every `order_proposal` row of the day, read read-only, and
  scores it against the spine's purchases. It never calls the engine and never writes `finance.db`. It writes the owner's weekly line
  to `spine/orders/order_score_latest.json`.
- **The owner's card** (`porders_s454.py`): one line a week, after "Who decides the order"; the count of medicines with no supplier; a
  family member said as such; a line when the engine is not on the spine.

## Pins (FROM = the 04-Oct 01:35 bundle, read live at 13:42 IST on 04-Oct; TO = `PINS.sh`, written when the kit was packed)

| file | FROM | TO |
|---|---|---|
| `/root/finance/order_rules.py` | 734fc6bcd67bb23da1bea2a6e927fcad | dac12be4c4a537d7ad2e4584a3423e6a |
| `/root/finance/purchase_app.py` (one edit: `plan_line`'s third argument) | 979391b6e191e0d2468f3db6fc57366e | 254b77939ca40d20e46509a678bcb5d8 |
| `/root/finance/porders_s454.py` | c3562c5bc5602ecdb32e416a231ba30c | 3681622b11043116f40bc0d4c3b557ad |
| `/root/finance/spine/spine_read.py` | ab55344ee280b0b4847a45cebe6d3843 | 712a1e4ef827f6be4e8b23415c3ceb62 |
| `/root/finance/spine/selftest_spine.py` | bfa607b980e4e838dfc7198f0bc7c9c9 | fc63d2c683a1970c58f60502302187a9 |
| `/root/finance/spine/order_rehearsal.py` (replaced whole by the kit's file) | 02582fbea29f51606a6ba8bb8694d3fc | 104d366d2e284ccfedef46ca0a744230 |

## What it touches

- The six files above. Backups beside each: `<file>.bak_S470_<from8>`.
- `finance.db`: six rows in `setting` (INSERT OR IGNORE). Backup first: `finance.db.bak_S470_<stamp>` (backup API).
- `/root/finance/spine/orders/`: the trial's files from 28-Sep on. S341's files of those nights are copied to `orders/before_S470/` first.
- It restarts `clinic-finance`. Nothing else: not `spine.db`, not `shelf_figure.py`, `stock_watch.py`, `order_sheet.py`, a parent
  file, the crontab or the duty map.

## Files

- `make_s470.py` — the anchored patcher (every anchor exactly once, else stop).
- `order_rules_block_s470.py`, `spine_read_block_s470.py`, `selftest_block_s470.py`, `porders_block_s470.py` — the blocks it places.
- `order_rehearsal.py` — the new trial, placed whole.
- `compare_s470.py` — what the install prints before placing: the spine's closing against `stock_snapshot`, the plan on spine against
  the plan on tables, the `no_supplier` list.
- `walk_s470.py` — the walk (the brief's §5, steps 1 to 10), every section with its negative control on the box as it is.
- `plan_old_s470.py`, `walks_old_s470.py` — step 11: the earlier walks (S403 … S452, and S454's P1C, P1D, P2, P3, P3B, P5) on the
  box as it is and on the patched files. One adjustment (P9: they run on `order.engine_source = tables`, because they make up their
  rows in the old tables only) and one intended red (I7: S454 P1D's "the same names" check; S470 adds names) are named in the file.
- `data_s470.py` — the data step's two read-backs.
- `install_S470_ORDER_ON_SPINE.sh` — gates → pins → build → compile on both pythons → the crons' commands as scripts → the spine's
  selftest → the compare → the walk → the earlier walks → backup → place → md5 read-back → restart → healthz → the data step → one live
  tick → restore on red. `DRY=1` places nothing.
- `PINS.sh`, `KIT_ID.txt`, `SUMS.md5`.

## To undo

Copy each `<file>.bak_S470_<from8>` back over its file (six files), restart `clinic-finance`, read `/finance/healthz` (200) and the six
md5s. Or, to keep the files and only go back to the old reads: set `order.engine_source` to `tables` on the settings card. The six
setting rows and the files in `spine/orders/` can stay: the old files read none of them. The database backup is not needed for an undo.
