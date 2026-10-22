# S619_ORDER_TRACKER — one order, five steps, the same on every screen

Brief: `claude_code_briefs/S619_ORDER_TRACKER.md` (v2, the Sanjeevni chat, session 335; R1 folded in). Runs after S618_SCAN_QUALITY.
The owner's rulings of 22-Oct-2026: late = two days after ordering (Sunday not counted), the delivery line on every WhatsApp order, a medicine
that did not come goes back on that dealer's next order "by itself", a part order is followed up by reception or Shavez ("either to do").

## What it does

* **`order_track.py` (new) — the one reader.** Ordered → Arrived → Bill scanned → In Marg → All lines came, for every order since
  `order.track_since`. Its light half reads finance.db only (reception's call row, Maal aaya, Darpan's line and order tab, the owner's
  Needs-you line, the duty map's SQL); its full half adds assets.db read-only (the head of a set-aside scan, a paper of another dealer,
  scan moments, the soft note "not seen on the scanned bill — Marg will confirm"). It writes nothing except `carry_pass`.
* **Late** = past `order.deliver_days` days (`order.deliver_skip` not counted; an order made on a skip day counts from the next day) at
  18:00, with a line still open — nothing came, or a part order (a line tapped "Kam aaya" with Marg not in yet, or an untapped line beside a
  tapped one). An order whose bill was scanned and is waiting for Marg is NOT late (the bill came). The outside-hours mark is set only by a
  "Maal aaya" tap (never a scan or Marg's time).
* **Short** = Marg billed less than ordered (by the difference), or Marg's bill came without the line, or reception tapped "Nahi mila". A
  scan never makes a line short. A short line gets one `order_carry` row (keyed by its line) — unless Marg's newest open order still carries
  the item (LANZOL JUNIOR) or a later order of that dealer already carried it. The carry rides on the dealer's **next card** as
  "pichhle order se baaki (dd-mm)" (never a card by itself), on the WhatsApp body and the printed sheet (one reader: `entries()`), and
  closes when an order carrying it is made, when Marg's newest order carries it, when the line turns out to have come, or when reception
  removes it with a reason.
* **Reception** (Roman Hindi): "Order ka maal nahi aaya — call karo" (replaces S605's "Aaj ke order — call karo") → `/finance/porders/s454/late`,
  each card with Call and "Maal aaya" / "Baaki maal aaya" (the existing arrive page). "Maal aaya?" lists only orders not yet late. The one
  remove door (`api_qty remove`) asks a reason chip — "Dealer ke paas nahi hai" (lifts on a newer Marg sheet that still carries the line;
  printed "dealer ke paas nahi") or "Abhi nahi chahiye"; only on a card with no order made yet (`s454_line_edit.reason`).
* **Darpan**: one read-only line on Kal ka hisaab after "Aaj ke order" — the last order day on or before the viewed date, dated, in four
  states; his order tab's "कल के ऑर्डर — क्या हुआ" reads the same reader.
* **The owner and Shavez**: `/finance/porders/s454/track` (owner English; `porders.rescan_askers` Roman Hindi; every other sender 403;
  Bhati 302 as today) — five tiles, Not arrived (late first, part orders too), Bill scanned not in Marg yet (soft notes), Came short, Scans to
  redo (S618's `rescan_list`, embedded), Saved under another dealer (Open the scan only), Complete (folded). Its card on their Purchase-orders
  home replaces S618's separate "Scans to redo" link. The owner's Needs-you gets one line: "Orders: N late, M medicines came short (back on
  the next order) — the order list".
* **The tie**: an order whose every line was tapped "Nahi mila" never asks for a scan; a received order whose every line is answered, Marg
  having billed one, stops asking (order 45); two or more orders of a dealer waiting → the scan's reading picks (after it is in, ten minutes
  at most), else the oldest. Existing ties are never moved.
* **The delivery line** (`order.wa_delivery_line`): the last line of every WhatsApp order (`wa_body`, both queue paths), once in every page
  foot of the order sheet, once after Marg's last row on Marg's order PDF. Test and payment messages untouched.

## Pins (FROM → TO; TO rebuilt from the live bytes by `make_s619.py`, 49 anchored edits, each anchor exactly once)

| file | FROM | TO |
|---|---|---|
| /root/finance/order_sheet.py | ff9375f98c46f0a004a02a3582693a83 (S618's TO) | see PINS.sh |
| /root/finance/porders_s454.py | 4d1506480b2b1388ae1020c302e71a84 (S618's TO) | see PINS.sh |
| /root/finance/darpan_kal.py | d6ba4882b5f8c4d365016eff87ddba52 | see PINS.sh |
| /root/finance/darpan_kal.html | c0ddc0eaa167b78bbb39bcebbb53c1b0 | see PINS.sh |
| /root/finance/order_sheet_pdf.py | 7a6d47c040536a24407ebfbb91d171e1 | see PINS.sh |
| /root/finance/marg_order_pdf.py | bdcf2d00f303a6932c9d1ffe686afffa | see PINS.sh |
| /root/finance/order_track.py | (new) | see PINS.sh |

Read only (STOP if moved): porders.py, supplier_msg.py, purchase_app.py, stock_figure.py, stock_watch.py, amir_day.py, order_rules.py,
item_check.py, sanjeevni_approvals.py, owner_console.py, /root/shared/scan_quality.py, /root/assetapp/asset_register.py; printed:
scan_register.py. Proved unmoved at the end: finance_app.py, portal.py, tile_grants.json, the crontab, every published S5*/S6* kit.

## Database

finance.db: table `order_carry` (`order_track.CARRY_DDL`, made by `order_sheet.ensure`), column `s454_line_edit.reason` (guarded ALTER), five
settings (`order.deliver_days` 2, `order.deliver_skip` SUN, `order.deliver_window` 15:00-18:00,-11:00, `order.wa_delivery_line`,
`order.track_since` 2026-10-12) by INSERT OR IGNORE; the first carry pass. No DELETE, no hand edit. Service: clinic-finance, restarted once.

## DUTY_MAP v18 → v19

`reception.order_arrival` rewritten to the late rule (door marker "Order ka maal nahi aaya"); `reception.medicine_orders` honours a removal's
reason; `reception.bill_scan` carries the two asking rules (and counts a Marg bill whose verdict is WRONG, as the screen shows it);
`shavez.order_followup` added (door `/finance/porders/s454/track`, due = late orders + open carries). Each `due_sql` proved equal to its screen's
count on the scratch copy by the walk.

## Left as they are (named, with why)

* `porders._on_order`, `stock_figure.scan_lines` / `arrival_moment` — stock questions, not "did the order come" (read-only files here).
* `order_sheet.open_order`'s groups, `marg_closed_order`, `_marg_hit` — Marg's own open order, a different question; the arrive page still
  refuses an order Marg has closed (S543).
* `stock_watch.arrival_needs_you` and `amir_day._d712_owner_lines` — the owner's other two arrival voices (read-only files); the new
  Needs-you line says only what they do not (late, came short).
* `purchase_app._carried_shorts` — read first (4968): it carries short-supplied lines of RECEIVED orders into `order_rules.plan` (the
  system's own list, order.source system / darpan) only; it never reaches Marg-sheet cards and never sees a line Marg's bill came without.
  It is left feeding the plan; on those sources a carried item already on the card is shown once (entries() skips a carry whose item is there).
* `purchase_app._wa_text` (the staff send) — not changed (read-only file); it does not carry the delivery line.
* One scan per order (`order_scan_tie` PK): a second bill of a delivery is reached only through Marg's link.

## Files

`order_track.py` (new) · `make_s619.py` (the anchored builder; `s619_os_block.txt`, `s619_p4_block.txt` inserted byte for byte) ·
`walk_s619.py` (the walk; `--facts` for the installer) · `install_S619_ORDER_TRACKER.sh` · `PINS.sh` · `DUTY_MAP.json` / `DUTY_MAP.md` (v19) ·
`KIT_ID.txt` · `SUMS.md5`.

## Undo

`\cp -p` each `/root/finance/<file>.bak_S619_<from8>` back, `mv /root/finance/order_track.py /root/finance/order_track.py.undone`,
`systemctl restart clinic-finance`, healthz 200, md5s read back. The table `order_carry` and the column stay (unread by the old files).
