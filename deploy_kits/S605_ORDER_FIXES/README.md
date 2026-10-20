# S605_ORDER_FIXES — Darpan's yes to the orthotic list, one WhatsApp per order, the send-all asks once, the call row, the numbers, the sizes' own keys

Brief: `claude_code_briefs/S605_ORDER_FIXES.md` (v1, 20-Oct-2026, the Sanjeevni chat, session 334). Owner's ruling **D749**; repairs
**F-959, F-960 (F-702), F-961, F-962, F-951, F-957**; the owner's numbers ask of 15:28 / 15:54 IST. Mock-up v3 (the owner's yes 15:58 IST).

## What it does
1. **Darpan says yes first (D749, F-959).** The orthotic shortage no longer reaches reception's order cards, "Sab ko WhatsApp bhejo" or the
   printed order sheet by itself. It waits in *Orthotic kam hai — N · Yuvika ko order?* on Darpan's Kal ka hisaab with हटाओ on each line and
   हाँ, ऑर्डर में डालो / इस बार नहीं. Only the lines he keeps go on Yuvika's card. A line whose shelf (or family) figure is below zero is never
   put to him; it is one line on the owner's Needs-you. His answers are rows of a new table `ortho_yes` (never updated, never deleted).
2. **One hand-out (F-960, F-702).** The reception phone is handed each message once (the owner's test message apart). A message handed and
   never confirmed within `order.whatsapp_wait_min` is not withdrawn and never re-queued: its order becomes *sent* by WhatsApp, marked
   unconfirmed (audit `s454_whatsapp_unconfirmed`; the message `skipped` with `last_error` "unconfirmed: …" — `supplier_msg`'s CHECK admits
   no new status value), and the owner reads one line. A message never handed is withdrawn as before.
3. **The send-all asks once (F-961).** "Sab ko WhatsApp bhejo" opens *WhatsApp bhejna hai?* (GET `/finance/porders/s454/order/whatsapp`, a read
   that writes nothing): the suppliers it will queue with their numbers, those with no number; *Haan, WhatsApp bhejo* posts the list shown
   (409 "List badal gayi — dobara dekhiye" when it moved); then the order list says *Reception phone unlocked rakhiye. WhatsApp khud khulega,
   har minute ek supplier (N minute).*
4. **The call row (F-962).** Once nothing is left to order, the home keeps *Aaj ke order — call karo* (the *Ho chuke* count) to the same page.
5. **The numbers.** *Call: … · WhatsApp: …* (the phone book through `book_card`) on the pending cards, the *Ho chuke* lines and the confirm
   list; on the order sheet's band in place of *Ph.*; and in Marg's own order PDF, a shaded *Phone book — …* line under each supplier's group
   (Marg groups its export by supplier — three archived exports read).
6. **F-951.** In the spine, a rename whose old 20-character key is shared by more than one ticked rename (the eight orthotic families, 22
   renames) is not aliased: each new name keeps its own key from the family's split day (the first full closing printing a new name,
   10-10 for all eight); on that day each size takes Marg's closing figure for it and the old key gives the same total (`RENAME_SPLIT`, never a
   sale or purchase kind). Every row of every other key is byte-equal (spine_cmp_s605.py).
7. **F-957.** S603's and S598's walks lay their own days: S603's section 1 uses its own visit day 43 days ahead; S598's walk puts its seven
   rows back on its own copy from the S598 install's JSON before reading them (`--rows-json`), accepts a later kit's KIT line, and knows the
   F-951 keys. This kit's copies are `walk_s603.py` / `walk_s598.py` here (their published kits stay frozen).

## Pins (FROM → TO; TO in PINS.sh)
| file | FROM | TO |
|---|---|---|
| /root/finance/order_sheet.py | 1f1e85c1 | see PINS.sh |
| /root/finance/porders_s454.py | 40f1755a | see PINS.sh |
| /root/finance/supplier_msg.py | 6366ed0f | see PINS.sh |
| /root/finance/order_sheet_pdf.py | 7fca11db | see PINS.sh |
| /root/finance/marg_order_pdf.py | c9cd44a5 | see PINS.sh |
| /root/finance/darpan_kal.py | b28d7342 | see PINS.sh |
| /root/finance/darpan_kal.html | 7c939191 | see PINS.sh |
| /root/finance/spine/spine_build.py | e3d3ed85 | see PINS.sh |
| claude_code_briefs/DUTY_MAP.json (by the publish) | b75ea78e (v16) | v17 (a note: Darpan's orthotic duty moves; no row) |
| claude_code_briefs/DUTY_MAP.md (by the publish) | 59c6bf98 | Darpan's orthotic row; one dated line |

Read only, must not move: purchase_app 447b745f, amir_day 1169a3d6, stock_app 40f2c922, stock_watch f0d9092a, amir_salts fc5c1d16,
stock_figure 51e1fc63, order_rules 8d078dbe, porders e5a5c4d4, porders.html 7a6799ae, spine_read 10697b38, spine_rules.json dd6c7616;
proved unmoved: finance_app, portal.py, tile_grants.json, the crontab (84 lines).

## What it touches
Eight files above; `finance.db` gains one table (`ortho_yes`, made by `order_sheet.ensure` on the first read after the restart) — no DELETE,
no hand edit, no new setting. Service `clinic-finance`, restarted once. One spine build after placing, the way the cron runs it (under its
flock). Nothing else.

## Files
`make_s605.py` (the anchored builder; `make_s605_walks.py` holds the two walks' edits, read with exec, never imported) · `walk_s605.py`
(the walk: sections 1–9 of the brief, `--expect-red` the negative control, `--state` the install-day state) · `spine_cmp_s605.py` (the
stop conditions of 3.6 on two scratch spines) · `install_S605_ORDER_FIXES.sh` · `PINS.sh` · `KIT_ID.txt` · `SUMS.md5` · `DUTY_MAP.json`,
`DUTY_MAP.md` (v17, as built) · `walk_s603.py`, `walk_s598.py` (F-957, as built).

## Retired (charter 9)
The 10-minute re-hand of a handed message; the direct POST of `#waall`; *Ph.* on the order sheet; the orthotic card on the order without a
हाँ (the dated `ortho:<day>` line ref); `porders.shortage_summary` as Darpan's section (sale_check and the approvals card keep it, read-only).

## Undo
Put back the `.bak_S605_<from8>` files beside each placed file (`/root/finance/*.bak_S605_*`, `/root/finance/spine/spine_build.py.bak_S605_e3d3ed85`),
`systemctl restart clinic-finance`, healthz 200, read the md5s back. The next spine build (every 10 minutes) then builds the old way. The
table `ortho_yes` stays, unread. The database backup `finance.db.bak_S605_<stamp>` is used only if the chat decides a data change must be
reversed (this kit makes none but the new table's rows Darpan writes).
