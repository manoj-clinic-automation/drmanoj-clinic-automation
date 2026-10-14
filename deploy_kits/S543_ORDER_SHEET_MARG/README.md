# S543_ORDER_SHEET_MARG — the ordering pages follow Marg's own open order; units in the shop's words; Marg's own order PDF

**Brief:** `claude_code_briefs/S543_ORDER_SHEET_MARG.md` (v3.1, Sanjeevni session 312, after the reads R1, R2, R3). **The owner's ruling:** D716,
13-Oct-2026 05:24 IST. Faults F-876, F-877, F-878 (units half). Kit shape: S537's (no data step; additive columns filled by the code itself).

## What it does

- **One rule (`order_sheet.open_order`):** a medicine is on the ordering pages and on the printed sheet exactly while Marg's newest
  *PENDING ORDERS (PURCHASE)* export prints it. "Newest" is decided by the export's own capture stamp (`RANK`, one rank for the code and the
  duty map). Every line of it is in exactly one group: *to_order* · *in_line* · *ordered* (its order under *Maal aaya?*, or made less than
  `order.sheet_max_age_days` days ago) · *old*. Nothing the system guesses (a bill scan, an arrival tap, a Marg purchase, a day count) removes a
  line Marg carries or keeps one Marg has closed.
- **Only the newest export moves a line;** an older export loaded late changes nothing and sends no arrival notice.
- **Marg's RECEIVE / PENDING** are kept on each line (`marg_recv_raw`, `marg_pend_raw`, two additive columns laid by `ensure()`), filled from
  the archived file by `heal_marg_cols` (in `order_sheet.cron_pass` on every tick and page read, and once by the installer).
- **The screens:** the heading *"Marg mein khula order (12-10 14:35) · 12 supplier, 26 dawa"* on every source; *Order sheet print karo* and the
  new *Marg ka order (PDF)* whenever Marg's open order has a line; *Purane pending* = the old group, each line *"Marg mein baaki"* (after
  *"maal aa gaya · "* when its order came; *"Marg: 4 patte aaya, 6 patte baaki"* when Marg records a part), Marg's pending quantity, one
  colour; *Dobara order karo* only on a line never ordered here and not removed by an edit — and the door refuses everything else (a line
  off Marg's order: *"Yeh line ab Marg ke order mein nahi hai."*). An order none of whose lines Marg still prints leaves *Maal aaya?*; its
  arrival page and API refuse it (*"Yeh order Marg mein band ho chuka hai."*).
- **Units:** one `qty_of` through `qty_words` replaces `qty_text`, `line_qty_text` and `_qty_of_order_line` ("10 patte", "10 botal",
  "30 vial", "12 tube", "6 nag"; English on the owner's pages; CCM "3 botal"). `wa_body` (the supplier's WhatsApp) is unchanged.
- **The printed sheet** takes Marg's lines from `open_order`, each once: new / WhatsApp line / ordered (Order ticked, **Aaya ticked when its
  order is tied to a bill scan**) / old; lines outside Marg's sheet keep their place; the head names what it counts.
- **Marg's own PDF** (`marg_order_pdf.py`, route `/finance/porders/s454/marg.pdf`): the export as Marg printed it, A4 landscape, its eleven
  columns and TOTAL, the export's time at the foot; a one-page notice when the file is not on the server. Audit `s454_marg_pdf_printed`.
- **Darpan's card** gives the same 26 / 12 for the same sheet. **DUTY_MAP v13:** `reception.medicine_orders` counts only the newest export's
  lines not removed by an edit; `reception.order_arrival` leaves out an order Marg has closed (its two tables written `main.` so aaj_kaam's
  floored views do not hide them).

## Files

| live file | FROM → TO | what |
|---|---|---|
| `/root/finance/order_sheet.py` | 012e21c9 → see `PINS.sh` | 35 counted edits (`make_s543.py`) |
| `/root/finance/porders_s454.py` | 9c463e7c → see `PINS.sh` | 28 counted edits |
| `/root/finance/order_sheet_pdf.py` | 6e7a5e1a → see `PINS.sh` | 21 counted edits |
| `/root/finance/marg_order_pdf.py` | new | shipped whole |
| `/root/deploy/repo/claude_code_briefs/DUTY_MAP.json` | f499dd1f (v12) → v13 (`PINS.sh`) | 3 counted edits; reaches the box by the repository's pull |

Read only, pinned, never edited: `porders.py`, `qty_words.py`, `order_rules.py`, `darpan_kal.py`, `darpan_kal.html`, `supplier_msg.py`,
`loss_piles.py`, `aaj_seed.py`, `aaj_kaam.py`, `owner_console.py`, `/root/marg_ingest/marg_take.py`, the clone's `DUTY_MAP.md`.
`finance.db`: two additive columns, filled from Marg's file; backup first; never a DELETE. Restarts `clinic-finance` only.
**`DUTY_MAP.md` is NOT edited by this kit:** it moved after the brief pinned it (S554, 14-Oct 07:04 IST) — rule 1 stopped that file; its
S543 row and log line are left for the chat.

## Proof (on the box, scratch copies only)

`walk_s543.py` — the brief's twelve parts on copies of the live database, the real finance app (header sign-in for that process only), the
real portal for the staff-eye tiles; made-up rows dated 2031 or named W543. **Negative control:** the same walk on the old files, every
`C:` check red (the old heading "22 dawa · 11 supplier", COCYP absent, the nine closed lines shown, the older export pulling lines off, …).
`state_s543.py` prints the install-day state before and after, read-only.

## Install — from a copy of the kit, BEFORE the repository is pulled

`rm -rf /tmp/s543kit && cp -rp <the kit> /tmp/s543kit && bash /tmp/s543kit/install_S543_ORDER_SHEET_MARG.sh` (`DRY=1` before `bash`: every gate,
the state and the walk; nothing written). The installer pulls `/root/deploy/repo` itself after placing (the map goes to v13 then).

## Undo

`\cp -p /root/finance/order_sheet.py.bak_S543_012e21c9 /root/finance/order_sheet.py && \cp -p /root/finance/porders_s454.py.bak_S543_9c463e7c /root/finance/porders_s454.py && \cp -p /root/finance/order_sheet_pdf.py.bak_S543_6e7a5e1a /root/finance/order_sheet_pdf.py && rm -f /root/finance/marg_order_pdf.py && systemctl restart clinic-finance`

The two added columns are harmless to the old files. The map v13 reads only tables the old files also have; to put v12 back, revert it in
the repository. The `finance.db.bak_S543_<stamp>` is for reversing data only and is not needed for the undo.

## Charter

**Retired:** `old_visible`; the readers of `order.old_done_days` / `order.old_show_days` (their `setting` rows stay); `qty_text`,
`line_qty_text`, `_qty_of_order_line` and `order_sheet_pdf._sheet_of_order` (now `order_sheet.sheet_lines_of_order`); the system's closing of
a line Marg carries; `refresh`'s `marg_date` write on old lines; the owner card's "already supplied since / never came" split; `_awaited`
for orders of Marg's sheet.
**Left for later:** the owner's dated layout of 12-Oct; the edit store's undo; the map's count of the orthotic card and of a withdrawn draft.
