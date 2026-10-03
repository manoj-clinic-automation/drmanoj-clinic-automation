# S454_BILL_REGISTER · part 1 — P1_ORDER_SHEET_RECEPTION

Session 283, 03-Oct-2026 · D666 (who decides the order), D668 (reception's one-task screen), D669 (the settings) · F-690, F-695, F-702.
Brief: `claude_code_briefs/S454_BILL_REGISTER.md` §3, §4, §7.3, §7.5 and the settings of §13 (part 1 of five).

## What it does

- **Darpan's sheet is the order.** Marg's *PENDING ORDERS (PURCHASE)* saved as text on the medical PC is converted by the reader
  (`medical/marg_txt.py`, S454: the ORDER kind), pushed to the door as before, verified by the new signature `ORDER_PENDING`, and loaded at
  once by `marg_take`'s hook into `order_sheet` / `order_sheet_line` (idempotent: the same file twice adds nothing). A sheet the
  server refuses is named on Darpan's *Kal ka hisaab* card and in the owner's Needs you.
- **Reception's screen** (`/finance/porders` while `porders.simple` = 1): *Aaj ka kaam* — the scan button and four rows
  (Order karna hai · Maal aaya? · Bill scan karna hai · Photo dekh kar bataiye), one task at a time (`porders_s454.py`). WhatsApp goes
  through the reception phone's queue as kind `order` (the payment messages are counted apart; F-702's ten-minute gap between
  hand-outs); Call; the order list ticked on the list itself; old pending lines with what Marg says of each; the printed A4 order sheet.
  The old page is one tap away (`?old=1`); the owner's ordering cards and the settings card are there.
- **Arrival by the bill's scan** (§4.4): a pharmacy scan after an order ties to that supplier's oldest awaited order (its own table,
  `order_scan_tie`); the order has arrived, its lines stay open until Marg's bill answers them — and they are still counted by S403's
  orthotic shortage and S410's interim check until then. The tie and Marg's clearing run from the cron too.
- **One reminder a day** at `order.remind_times` (17:00), only while a supplier is still to be ordered; the 12:00 and 15:00 notices
  go; on `marg_sheet` the 09:00 notice goes and a sheet's arrival is announced instead.
- **September parked** (`purchase.register_from` 2026-10-01): no "Bill scan pending" for a parked month; Amir's lists unchanged.
- **The first load** (install step 10): Darpan's sheet of 02-Oct, as already ordered — one paper order per supplier at 15:00 that day.

## Files on the box (FROM → TO, md5)

| file | FROM | TO |
|---|---|---|
| /root/finance/porders.py | 3620b374a8fb3ac4988b8e6525795f84 | d4842f2c0f40a6ff69bd9a6d0425778f |
| /root/finance/order_rules.py | 00a60efb515972313839662ff7f83495 | d29efa8e6425fa359ea28d38c0758ccc |
| /root/finance/supplier_msg.py | 5cc35d2af444b5ab1996f636db8e54cf | fc6c1724d6da4e1d04897b60d61c13b8 |
| /root/finance/purchase_app.py | 341c663e52076f0ee264c356b49cf49e | 591432422d6b06af3dff886a8a0fc378 |
| /root/finance/darpan_kal.py | 377ffd63786261cef4a6113482d43bb5 | 911cf637a288fad85c75e54227149633 |
| /root/finance/darpan_kal.html | 9269afb04a454b626895a27666032752 | c20ab05d8484e37a667ddae32a4c792b |
| /root/marg_ingest/marg_take.py | 21e37b0e6fa6505a8825b32b7c24d41d | b41195e4ce853272ecf25b06343e3e16 |
| /root/marg_ingest/signatures.json | b2dcb2115a208bff81fac1c37c839428 | 64943ac6719a0f2ee06a15ef56d8c3d1 |
| /root/finance/order_sheet.py | (new) | 4cf2f231ef026904d1ae42754846aea7 |
| /root/finance/porders_s454.py | (new) | 05716f3c040478d09fd2016561c7c99c |
| /root/finance/order_sheet_pdf.py | (new) | 9c28df38435a25d7e1d65c34b8d43ec9 |

Built by `make_s454p1.py` from the live bytes (every anchor exactly once; the blocks `*_block_s454.py` appended; the three new
modules copied as they are; `sig_entry_s454.json` inserted). **Crontab:** order_rules' own S410 line only, `0,30 5-17` → `*/10 5-21`.
**Data:** the S454 tables and columns made on first use; the S454 settings at their defaults; the first load's rows.
**Restarts** clinic-finance only. **Not touched:** finance_app.py, portal.py, tile_grants.json, finance_ui/, sanjeevni_approvals.py,
packs.py, asset_register.py, item_alias.py, stockmatch.py, amir_day.py, reports_tile.py, stock_app.py, stock_watch.py.

`DUTY_MAP.json` / `.md` v4 (`make_dutymap_s454p1.py` from v3): reception.medicine_orders (Order karna hai, source-aware),
reception.order_arrival (Maal aaya?), reception.bill_scan (counted months), reception.scan_questions (Photo dekh kar bataiye),
shavez.supplier_messages (payment kinds), darpan.order_sheet (new: a refused sheet, door *Kal ka hisaab*).

## Outside the box

- `medical/` — the reader `marg_txt.py` S454 (ed17bb763c202f81cb8b3708fac61b52, from S446's 70f920c4 by `make_marg_txt_s454.py`) and
  `KIT_MANIFEST.txt` (kept here with LF line ends, 5959bde8a431b9375a300cac9ef7f999; delivered with CRLF as the live one is,
  05fb348589ba967e26bf8b7c9ff2aebc, from bdd277686cb76f944d4569e666a9d89f: only the marg_txt line's md5 changes, plus one `# S454 (D666)` comment above it) go to `H:\My Drive\Clinic Data Archive\ToMedical\_kit\`; the watcher (S397,
  81145aa7) picks the reader up by itself and is **not** replaced (part 4, not before 04-Oct 13:00 IST). `PROVE_S454_MEDICAL.txt`: 8 of 8.
- `manojz/apply_manojz_sig_s454.py` — the same signature into `D:\Downloads\margsync\MargPull\signatures.json` (a987a08e → 7f72c572).
- `pictures/` — the screens the mock did not show, as the walk rendered them (numbers masked).

## Run

```
SHEET=/tmp/s454p1/<Darpan's sheet of 02-Oct>.txt KITS=<deploy_kits> DUTYMAP_OLD=<claude_code_briefs/DUTY_MAP.json v3> bash install_S454_P1.sh
```
`DRY=1` runs every gate, the build, `walk_s454p1.py` and the twelve earlier walks (`plan_old_s454p1.py` / `walks_old_s454p1.py`, each
adjustment named) on scratch copies, and places nothing. The build lock `/root/deploy/.claude_code_build.lock` (owner S454_BILL_REGISTER)
must be held for a real run. Red after placing: every file restored byte-identically, the crontab restored, clinic-finance restarted.

**Undo:** put back the `.bak_S454_<from8>` files beside the eight files, remove the three new ones, `crontab /root/finance/crontab.bak_S454_<stamp>`,
restart clinic-finance, healthz 200, read the md5s back. The new tables stay (nothing reads them without these files).
