# S454_BILL_REGISTER · part 3 — P3_SHELF_FIGURE

Session 283 (Sanjeevni), 03-Oct-2026 · the brief's section 9 · D667 · F-696.

## What and why

- **§9.1–9.2 One shelf figure (`shelf_figure.py`).** For each medicine: the newest physical count (the full count and its parts, a later spot
  answer, or a shelf fix), then every sale, sale return and purchase in the spine since that day, then what arrived by a bill's scan and is not
  yet in Marg. Marg's own closing figure is kept beside it.
  - Sales on the count day are in (the count is taken before the shop opens). Purchases on the count day are not (they are in the count).
  - **The boundary repair (found on live data while building):** a bill dated on, or up to 7 days before, the count day but entered in Marg
    after the count was missed. PANSPED L was counted 0 at 14:41 on 06-09; its 1,000-tab bill of 06-09 came in later. SHELCAL XT had a
    bill of 05-09. Marg's own figure at the count (`stock_count_item.marg_qty`) settles it. What Marg gained since the count, beyond its
    sales, returns, later purchases and the count's vouchers filed, is such bills. They are taken in newest first while they fit that gain.
    On 03-Oct this touched 3 of 378 items: PANSPED L +1,000, SHELCAL XT +300, DECA INSTABOLIN 50 +10.
  - An item no count has reached keeps Marg's figure, named `no_count`. A figure below zero is shown as 0, named `below_zero`.
  - Items that share one spine key share its sales by their counted share, marked approximate.
  - The boundary report lists any base taken after 09:00 IST on a day that already had sales.
- **The system's own list** (`order_rules.plan`) works from the shelf figure when `order.stock_basis` = `count` (the default). Each line carries
  both figures for the owner; no staff screen prints them. On `count`, an order that arrived by its scan is in the shelf figure, so it is not
  counted again as on the way. On `marg` the plan is the same as before, line for line.
- **§9.3 The gap at each closing (`s454_shelf_gap`).** At each new Marg closing the gap (shelf figure − Marg) is recorded per item. It is flagged
  when Marg moved by `stock.gap_min_packs` (1) pack or more beyond its own sales, returns, purchases and the count vouchers Amir filed. The flag
  stays until the item is counted again. An approximate item is never flagged.
  - The owner gets one line: "Marg and the shelf figure moved apart on N items". It also shows as a card on his ordering screen.
  - On Darpan's spot-count roster a flagged item gets one more reason. The roster's cap does not change.
- **The spot count and the full count.** A spot answer is compared with the shelf figure. A recorded count stores the shelf figure beside
  Marg's on each row (`stock_count_item.shelf_qty`). The loss desk still judges by Marg's figure in this kit.
- **§9.4 / F-696, why the system's list differs from Darpan's sheet** (`report_s454p3.py`, run by the installer on scratch copies; its output
  is in the report). Three suspected gaps were tested against the data:
  - (1) a line tapped "Aa gaya" while its order is still "sent": not proven, not changed.
  - (2) the exact-name match of goods on the way: not proven, not changed.
  - (3) Marg's sale export prints only 20 characters of a name, so a medicine with a longer name never met its own sales: **proven**.
    Repaired in `purchase_app._pace` on `count`: such an item takes the pace of its 20-character name.

## Pins (FROM → TO), `/root/finance/`

FROM is in `install_S454_P3.sh` (part 1D's `order_rules.py`, part 2's `purchase_app.py` / `order_sheet.py` / `porders_s454.py`, and
`stock_watch.py` / `stock_app.py` as they are). TO is in `PINS.sh`. New file: `shelf_figure.py`.

## Files

- `make_s454p3.py`: the patcher. Blocks go above each file's `__main__` guard.
- `shelf_figure.py`
- `report_s454p3.py`: S454 §9.4.
- `walk_s454p3.py`
- `plan_old_s454p3.py` + `walks_old_s454p3.py`: the earlier walks; part 2's adjustments now apply to both runs.
- `data_s454p3.py`: the two settings and the first gap rows.
- `install_S454_P3.sh`: it also runs the crons' own commands (`order_rules.py tick`, `stock_watch.py job`) as scripts on scratch copies, and
  one live tick after placing.
- `PINS.sh`

The duty map does not change: the owner's gap line is a Needs-you line, and the roster's reason sits inside Darpan's existing spot-count duty.
