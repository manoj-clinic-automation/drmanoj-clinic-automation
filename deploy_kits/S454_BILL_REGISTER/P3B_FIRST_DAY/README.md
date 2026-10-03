# S454_BILL_REGISTER · P3B_FIRST_DAY — what the first afternoon of use showed

Session 283 (Sanjeevni), 03-Oct-2026 · the brief's section 18 · F-711, F-712, F-713.

## What and why

- **§18.1, two bills in one scan (F-712).** Scan B-0121 is one PDF of two Shivaaz bills. The asset app stores **one reading per scan**: one
  header (supplier, bill number, date, total) and its item lines, with no page of its own (`page_of` is S441's join of a forgotten page). B-0121's
  four item lines add up to its first bill (Rs 7,658), so nothing of the second bill is stored. **No guess is built.** What the reader would have
  to keep is written for the parent in the report.
  - On the staff's screens, one line: **"Ek scan mein ek hi bill."** under "Naya bill scan karo" (the home) and under every "Bill scan karo" on
    "Maal aaya?". In the owner's English: "One bill per scan."
- **§18.2.** On the arrival screen ("Bill nahi hai, ya kam aaya?") the button reads **"Save kijiye"** (owner: "Save") while any line is tapped
  "Kam aaya" or "Nahi mila". With every line "Aa gaya" it reads "Maal aa gaya". What it writes does not change.
- **§18.3.** A standalone "P.L." in a supplier's name is dropped like PVT and LTD (`scan_register.sup_norm`). GUNINA PHARMACEUTICALS P.L. LTD.
  = GUNINA PHARMACEUTICALS. A "P.L." inside a name ("A.P.L.") is kept.
- **§18.4.** On `order.stock_basis = marg` an order that arrived by its bill's scan is on the way once (in transit), as part 3 made it on
  `count`. Before, it was counted twice there (in transit and on order).
- **§18.5 (F-713).** In the spot count's reading (`stock_watch.Spine.sales`, the 90-day pace, the roster's sales value) a credit note (bill
  CN…) is a return, not a sale. `u` is now sales net of returns and `ret` the returns, as `shelf_figure` reads them.
- **§18.6.** The owner's card "the system agreed on X of Y" keeps its stored figure and says on what stock it was taken: "on Marg's stock" or
  "on the shelf figure". `order_sheet.compare` stores the basis from now on. A comparison stored before part 3 was placed (03-Oct 18:17:11 IST)
  was taken on Marg's stock.

## Pins (FROM → TO), `/root/finance/`

FROM is in `install_S454_P3B.sh` (part 3's `order_rules.py`, `stock_watch.py`, `order_sheet.py` and `porders_s454.py`, and part 2's
`scan_register.py`). TO is in `PINS.sh`. No new file. No data step.

## Files

- `make_s454p3b.py`: the patcher. Every anchor occurs exactly once. The one appended block goes above any `__main__` guard.
- `report_s454p3b.py`: §18.3–18.5 on today's data (scratch copies), printed before anything is placed. It includes the matcher re-run on each
  side. A lost link stops the install. A new pair stops it until it has been read (`PAIRS_READ=1`).
- `walk_s454p3b.py`: A–F and the staff-eye walk. NEW is the box plus the built files; OLD is the box as it is, the negative control.
- `plan_old_s454p3b.py` + `walks_old_s454p3b.py`: the earlier walks, as part 3 ran them.
- `install_S454_P3B.sh`: it also runs the crons' own commands (`order_rules.py tick`, `stock_watch.py job`, `purchase_app.py rematch`) as
  scripts on scratch copies. After placing it runs one live tick.
- `PINS.sh`

The duty map does not change.
