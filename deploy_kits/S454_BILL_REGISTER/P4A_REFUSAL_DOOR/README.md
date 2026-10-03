# S454_BILL_REGISTER · part 4, the server side — P4A_REFUSAL_DOOR

Session 283 (Sanjeevni), 03-Oct-2026 · the brief's section 10.2.

## What and why

Until now a text the medical PC refused stayed on that PC and reached nobody: it was a file in `_captured_txt\refused\` and a log line. Its
watcher (P4B_REFUSAL_WATCHER) now sends a short note. This folder is the server's side of it.

- `marg_door.api_marg_file` takes the note on the same address (`/finance/api/marg-file`) and with the same key as a file. The app's front
  gate checks the key first, then the door does. The note is a POST with the header `X-Marg-Note: refused`. Its JSON body holds only `name`,
  `md5`, `kind` (SALE, STOCK, ORDER or empty) and `reason`. A note that carries a file, or any other key, is refused and writes nothing.
- Before `take()`, it writes one `mi_file` row: the type the kind maps to (SALE_BILLWISE, STOCK_CLOSING, ORDER_PENDING), verdict and
  `pc_verdict` REFUSED, and the reason as "the medical PC refused it: …". Its `drive_folder` is `pc_note`. No file is kept, and the size is 0.
  The same file's note again adds nothing.
- These readers already show such a row: the owner's Needs-you ("Report refused today", `amir_day`), the reports tile (`reports_tile`), and
  Darpan's order-sheet card ("Order sheet adhoori thi", `order_sheet.refused_sheet`). `finance_app.py` is not touched.
- A door nobody knocks on yet is harmless. It goes in before the watcher, as §19 orders.

## Pins (FROM → TO), `/root/finance/`

`marg_door.py` 598ba2df → TO in `PINS.sh`. No data step.

## Files

- `make_s454p4a.py`
- `walk_s454p4.py`: D (the door), O (who reads it), W (end to end: part 4's watcher on a scratch folder sends its note over HTTP to the scratch
  app; the watcher's and the reader's own selftests), S (the staff-eye walk). NEW is the box plus the door with the S454 watcher; OLD is the box
  as it is with the S397 watcher.
- `plan_old_s454p4a.py` + `walks_old_s454p4a.py`: the earlier walks.
- `install_S454_P4A.sh`
- `PINS.sh`

The duty map does not change. A refused order sheet is already Darpan's duty `darpan.order_sheet` (door *Kal ka hisaab*).
