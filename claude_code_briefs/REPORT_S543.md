# REPORT S543_ORDER_SHEET_MARG — installed and working (14-Oct-2026, placed 08:35:25 IST)

**For the owner**
- Reception's ordering page now follows **Marg's own open order**: a medicine shows while Marg's newest pending-orders export carries it, and leaves only when Marg drops it. The page heading reads *"Marg mein khula order (12-10 14:35) · 12 supplier, 26 dawa"*. That is the same figure Darpan's card and the printed sheet now give.
- *Purane pending* went from 10 to 2: UPRISE (with *Dobara order karo*) and COCYP (*"maal aa gaya · Marg mein baaki"*, with no re-order button). The nine lines Marg has closed are gone. *Maal aaya?* shows 3 orders (L.K., Shivaaz, Yuvika).
- Every quantity now carries its unit in the shop's words: "10 patte", "10 botal", "30 vial", "12 tube", "6 nag". Your view shows the English words.
- A second button, **"Marg ka order (PDF)"**, sits beside *Order sheet print karo*. It prints Marg's own export exactly as Marg prints it. Both buttons show whenever Marg's order has a line, including today, when nothing is left to order.
- Tested first on copies of the live data (75 checks green; all 38 of the checks built to fail on the old code did fail). Installed, server healthy. Undo is one line (below).

---

## For the chat

### Pins (read back on the box after placing; the installer's own read-back, then again at 08:35:50 IST)
| file | FROM | TO (read back) |
|---|---|---|
| `/root/finance/order_sheet.py` | 012e21c9 | **8c50d41e**da61ba31198156b2fae2f12f (35 counted edits) |
| `/root/finance/porders_s454.py` | 9c463e7c | **72e7fd56**3dadf2ae657fadef66e4e72e (28) |
| `/root/finance/order_sheet_pdf.py` | 6e7a5e1a | **d0735df8**4f17a67474bc0cecd58e5c6c (21) |
| `/root/finance/marg_order_pdf.py` | new | **c9cd44a5**5d4cb39247d3c2e8e2602f1d |
| `claude_code_briefs/DUTY_MAP.json` (clone, by `git pull --ff-only`) | f499dd1f (v12) | **ead2be78**869605dfd2580347f33d4017 (v13, kit S543) |
| `claude_code_briefs/DUTY_MAP.md` | **not edited** (96219048 before and after) | see "Not done" |

The 11 read-only files were pinned and unchanged: porders a5a823bf, qty_words 706db7cc, order_rules 79f21c1e, darpan_kal fd799a56, darpan_kal.html f5e279eb, supplier_msg 2f43af75, loss_piles 81ae481e, aaj_seed a97cd07b, aaj_kaam cd232b1c, owner_console 2b985708. Also unchanged: marg_take 5cad2d24.
`finance.db`: two additive columns on `order_sheet_line` (`marg_recv_raw`, `marg_pend_raw`), laid by `ensure()`. `heal_marg_cols` filled 26 lines; a second run filled 0. Nothing was deleted.

### Install (installer output, read)
Gates → pins → install-day state → collector → compile on both pythons → rebuild from live bytes (all at their TO pins) → walk and control → backups → place → md5 read-back → pull (map v13; kit in the clone byte-identical to the run) → **one restart of `clinic-finance`** (ActiveEnterTimestamp 08:35:26 IST) → healthz 200; `/s454/order`, `marg.pdf`, `sheet.pdf` answer 302 without a login (expected) → journal clean (the one "ERROR" line is gunicorn's own "Worker was sent SIGTERM" at the restart) → heal 26/0 → state after → the page as shavez on a copy: 200, heading, both buttons. The build lock was held from before the install until this report.
**Backups:** `finance.db.bak_S543_20261014_083449` (backup API), `order_sheet.py.bak_S543_012e21c9`, `porders_s454.py.bak_S543_9c463e7c`, `order_sheet_pdf.py.bak_S543_6e7a5e1a`.
**Undo:** `\cp -p /root/finance/order_sheet.py.bak_S543_012e21c9 /root/finance/order_sheet.py && \cp -p /root/finance/porders_s454.py.bak_S543_9c463e7c /root/finance/porders_s454.py && \cp -p /root/finance/order_sheet_pdf.py.bak_S543_6e7a5e1a /root/finance/order_sheet_pdf.py && rm -f /root/finance/marg_order_pdf.py && systemctl restart clinic-finance`

### Install-day state (read-only, before = after except the healed columns and the map version)
Newest export: sheet 4, stamp 20261012-143518, giving **12 suppliers, 26 lines**. Groups: to_order 0 · in_line 0 · ordered 24 · old 2. *Purane pending*: UPRISE 6L INJ, COCYP T SYP. *Maal aaya?*: orders **26 L.K., 28 Shivaaz, 29 Yuvika**. Map v12 → v13: medicine_orders (0, —) both; order_arrival (3, 2026-10-12) both. Collector: the newest ORDER_PENDING file (12-10 14:35) VERIFIED, on disk, taken.
**Where today differs from the brief's §0 / §3 (state moved after the brief; nothing typed, the walk reads everything by key):**
- *Maal aaya?* is **3, not 5**. A.A. (order 21) was tied to a bill scan on 13-10 at 14:00, and Kedar (order 25) on 13-10 at 11:22.
- **CHYMORAL's order 3** was marked arrived on the arrival screen on 13-10 at 18:10, so it had already left *Maal aaya?* before this install. The walk proves the "closed by Marg" rule on a made-up order instead (W543, ext_ref OP-W5430): off *Maal aaya?*, refused by the page and the API, counted by v12 and not by v13.
- The printed sheet has **21** Aaya ticks, not 12: orders 21 and 25 are tied too.

### The walk (`walk_s543.py`, on scratch copies; same result in the DRY run, three rehearsal runs and the live install)
`WALK OK S543: 75 checks green`. Its parts, with the facts read on the copy:
1. **One-to-one:** union = the file's 26 keys, each once (0/0/24/2). The heading *"Marg mein khula order (12-10 14:35) · 12 supplier, 26 dawa"* shows for darpan, shavez, shivani, alisha and reception, and in English for manoj. Both buttons show with nothing to order. Sheet: 26 Marg rows, each once. Head: *"Marg ka khula order: 12-10-2026 14:35 · 12 supplier · 26 dawa: 24 order ho gaya, 2 purane pending"*. 21 Aaya ticks, and COCYP is an old row with Aaya empty.
2. **Named lines:** COCYP reads "Order 06-10 · maal aa gaya · Marg mein baaki" with no button. UPRISE reads "Marg mein baaki" with the button. Both are on their supplier pages. None of the 10 closed lines (the nine plus VINDAC 25) is on a page or the sheet. The made-up closed order behaves as in the state notes above.
3. **Marg's word:** a newer export (stamp 20310301-100000) drops COCYP, FLUXIC P and PATOPAN DSR from every page. The new line is a Kedar card at "5 patte". ASTOFEN R with RECEIVE 4:0 / PENDING 6:0 reads "Marg: 4 patte aaya, 6 patte baaki" and "6 patte". The 22 lines of the 12-10 orders stay *ordered*. Nothing shows on both *Maal aaya?* and *Purane pending*. An older export (stamp 20261011-090000) leaves `newest_sheet`, M and Marg's columns unchanged, with no notice. 8 days on: a tied line (RYCOBAL D3 / C2CALZ) is old, reading "maal aa gaya · …" with no button; SALAZAR DS (still under *Maal aaya?*) stays ordered.
4. **No guess:** UPRISE as to_order with a made-up Marg purchase stays to_order after `refresh()`. A line off M still closes (`closed_marg`). The 21 tied ordered lines stay on the sheet.
5. **Drafts:** a new Kedar line prints at once as 'new' while the draft is the card, and joins the card after `on_message_done`. A dropped draft keeps its card. The head shows "1 WhatsApp line mein", and its parts add up to M. DYNAPAR's draft card reads "10 botal".
6. **Units:** the brief's 26 words on the supplier pages and on the sheet. Old block: "18 vial" and "10 botal". CCM 1*40 3:0 reads "3 botal".
7. **Marg's PDF:** 26 names, 14 entry numbers (26 cells), TOTAL 4567/77441, RATE with two decimals, title, foot "Marg se nikala: 12-10-2026 14:35 (Darpan)". No two text runs overlap. A4 landscape. The route gives 200 application/pdf for shavez and manoj, with one audit row each (`s454_marg_pdf_printed`). With no file, a one-page notice, 200. The sheet's own PDF stays portrait.
8. **Reorder:** UPRISE gives 200 and a Radha card. Refused with 409: COCYP; a removed-by-edit line (lapsed, and to_order); a line off M ("Yeh line ab Marg ke order mein nahi hai."); a line under *Maal aaya?*.
9. **Heal:** 26 NULL → 26 filled → a second run writes 0. Each value equals Marg's own cell.
10. **Map = screens** (plain and through aaj_kaam's floored reader): install day v13 (0,3,0,3) = screen (0,3). With a removed-edit line, v13 (1,3,1,3) = screen (1,3) while v12 counts 2. Walk 3's copy: 1 = 1, 3 = 3.
11. **Not broken:** `order_sheet.cron_pass` twice (second pass: refresh 0, heal 0); `day_summary`; `darpan_card` 26/12; `owner_lines` directly and through porders; `on_message_done`; `marg_take._order_sheet` on a loaded file ("already", nothing added); the home and `api/s454/state` show the same counts; `wa_body` byte-identical; 31 staff page reads, all under 100 KB and under 2 s. **Staff-eye:** the 'Purchase orders' tile is on the portal home of all five reception logins; the door `/finance/porders` shows "Maal aaya?" to each while v13's order_arrival is due (n 3); alisha's *Aaj ka kaam* carries the arrival line.
12. **Greps** (all *.py in the finance folder): `old_visible`, `old_done_days`/`old_show_days`, `qty_text(`, `line_qty_text(`, `_qty_of_order_line`, `_sheet_of_order(` are all empty. `FROM order_sheet_line WHERE state='to_order'` appears only in `refresh` (order_sheet.py:694).
**`newest_sheet(` callers (each still right):** order_sheet 467, 521, 573, 691, 727, 742, 1636, 1654, 1700 · porders_s454 653, 1044, 1441 · marg_order_pdf 135. (The brief's list, renumbered: order_sheet 448/1433/1451/1496, porders_s454 573/642/1400, order_sheet_pdf 199. The PDF now reads the sheet through `open_order`.)

### Negative control (the same walk on the OLD files): `every one of the 38 'C:' checks is red (38 of 69 checks red)`
Including:
- the old heading "Darpan ka order · 12-10 · 11 supplier, 22 dawa"
- no PDF button
- the old sheet: 13 rows, COCYP absent, the closed lines printed, head "7 supplier · 13 dawa"
- 0 Aaya ticks
- the nine closed lines shown
- the made-up closed order on *Maal aaya?*, and arrived through the API (200)
- "5 strip" on the card
- the older export moves `newest_sheet` and pulls lines off M, and queues a notice
- `refresh` closes a line Marg carries
- the removed-by-edit and off-M lines accepted by the reorder door
- DYNAPAR "10"
- Darpan's card 22/11
- the retired names still present

**Rehearsal** (`rehearse_s543.sh`, a made-up root with a stand-in service): (1) red after placing gives back every file byte-identically and removes marg_order_pdf.py; (2) green installs; (3) a second run says ALREADY INSTALLED.

### Calls made (no question was put to the owner)
- **DUTY_MAP.md STOPPED (rule 1).** It moved after the brief's S316 re-anchor: 7e213492 → 96219048 at 07:04 IST today. S554 edited Bhati's `bhati.physio_register` row: "floor moved back to 01-Oct by S554". So the kit does **not** add S543's `.md` row and log line. DUTY_MAP.json v13 (the part the code reads) is in place. **For the chat:** re-anchor the md at 96219048 and add the row and log line ("No duty added, moved or removed; reception's order and arrival counts read Marg's open order").
- `qty_of(l, en, pend, recv)` also takes an optional `con=` (reloads the whole-unit list), because the screens on `order.source=system` would otherwise never load it. `wa_body` uses the same one loader, and its text stays byte-identical.
- The reorder door also refuses a **lapsed** line that carries a removed edit row (R3-13's reading of "a line removed by an edit"). Without that, pressing the button would do nothing visible.
- The brief's "`order_rules.cron_pass`" does not exist. order_rules runs `tick()`, which calls `order_sheet.cron_pass` (R3-18). The walk ran `order_sheet.cron_pass` twice.
- The made-up exports use far-future (newer) and past (older) stamps, so they rank right whatever Darpan exports before the install.
- When ordering is frozen, the printed sheet leaves Marg's to_order and in_line rows off (as `entries()` does today). The one-to-one rule is for unfrozen ordering, as the brief says.

### Not done
- DUTY_MAP.md (above).
- Nothing else in the brief was left out.

### Charter
**Retired:** `old_visible`; the readers of `order.old_done_days` / `order.old_show_days` (their `setting` rows stay); `qty_text`, `line_qty_text`, `_qty_of_order_line`; `order_sheet_pdf._sheet_of_order` (moved into `order_sheet.sheet_lines_of_order`); the system's closing of a line Marg carries; `refresh`'s `marg_date` write on old lines; the owner card's "already supplied since / never came" split; `_awaited` for orders of Marg's sheet.
**Left for later:** the owner's dated layout of 12-Oct; the edit store's undo; the map's count of the orthotic card and of a withdrawn draft.
**Seen, not touched:**
- R1-30: `owner_lines` "An order of … was never placed" reads every lapsed line, on M or not.
- R1-34: `marg_take` stamps a nameless upload with the upload time (427), so a rescued old export uploaded without a stamp would rank newest.
- R2-22: a withdrawn draft is a card the map does not count.
- `_sheet_notice`'s push text still counts `day_order` ("Darpan ki order sheet aa gayi: 11 supplier, 22 dawa"), while the heading, the sheet and his card now say 26/12. The brief changed only `darpan_card`. `day_summary` also keeps `day_order` (its own question).
- The map's ELSE branch serves `darpan` as `marg_sheet` (pre-existing).
**Dependency at install:** the collector was green (the newest ORDER_PENDING file VERIFIED, on disk, taken).

### Outside the brief, noticed
- `PUBLISH_ALL.bat` also published two pending briefs from the chats (`S315_READING_COMPARE.md`, `S555_DESK_CORRECTIONS.md`). That is expected under the charter.
- The server's scratch copies with database copies (`/tmp/s543dev`, `/tmp/s543walk`, `/tmp/s543rh`, `/tmp/s543_inst_*`, the probe's `f.db`) were deleted after the install. The build lock was released (its owner file removed, then the empty folder). **Left in /tmp:** `/tmp/s543kit` (the kit's own files) and `/tmp/s543probe` (probe scripts and their masked output). Neither holds a database copy. The permission list refused the recursive delete, so they are left for the server's /tmp cleanup.
