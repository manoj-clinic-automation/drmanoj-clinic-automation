# S454_BILL_REGISTER · part 1B — P1B_COMPARE_FIRST

Session 283, 03-Oct-2026 · D666 · found after part 1 was installed, by reading part 1's own first-load output on the box.

## Why

Part 1's first load (Darpan's sheet of 02-Oct, "as already ordered") made the sheet's ten paper orders **first** and compared the sheet
with the system's own list **after**. S410's plan counts the units on a sent order as on the way (`order_rules._on_order_units`), so it
dropped exactly the sheet's items, and the owner's card read "the system agreed on **0** of 21 items". Made with those orders absent, on
a copy of the live data, the comparison reads **5 of 21** (DFO MR, VOLITRA APS SPRAY, MEG QCS, CROCAL, OSTOVAXL DM). A sheet that arrives
through the door is not loaded "as ordered" and was never affected. Part 1's folder is left as it ran (byte-identical to what was
installed); this part is the fix.

## What it does

- `/root/finance/order_sheet.py` **4cf2f231ef026904d1ae42754846aea7 → 93f55d87730e749d78ea5561de38266f** (`make_s454p1b.py`, one
  anchored edit in `load_rows`: the comparison block moved above the paper orders; nothing else).
- Data: `recompute_s454p1b.py` makes the comparison again for each sheet loaded as already ordered whose figure is still part 1's, on a
  backup-API scratch copy with that sheet's own paper orders taken away, and writes it into that sheet's row (only a row unchanged since
  part 1; one audit row `s454_cmp_recomputed`).
- Restarts clinic-finance only. Backups: `finance.db.bak_S454_<stamp>`, `order_sheet.py.bak_S454_4cf2f231`.

## Walk

`walk_s454p1b.py` on two backup-API copies of the live finance.db: the walk takes away its own rows by key (the sheet's md5 and the
orders made from that sheet), loads the 02-Oct sheet again as already ordered with part 1's own helper (`first_load_s454.py`, copied out)
and reads the comparison. NEW: 10 paper orders made again, the comparison kept equals the one made with them absent (5 of 21), no push
left the walk. NEGATIVE (the box as it is): 0 of 21.

## Run

```
SHEET=/tmp/s454p1/<Darpan's sheet of 02-Oct>.txt bash install_S454_P1B.sh
```
Needs part 1's folder beside it (`../P1_ORDER_SHEET_RECEPTION`: the first-load helper and the reader). `DRY=1` places nothing.

**Undo:** `order_sheet.py.bak_S454_4cf2f231` back, restart clinic-finance, healthz 200, md5 read back. The figure stays corrected
(it is a report figure; the database backup holds part 1's).
