# Duty map — every recurring staff duty, and the door that shows it

**01-Oct-2026 · kit S444_STAFF_SAFE · decision D648; updated 02-Oct-2026 by S446_AMIR_STAGES_BILLS (D649, D650) and by S452_AMIR_PANEL_FIXES (F-686, F-687; the owner's rulings of 02-Oct evening); 03-Oct-2026 by S454_BILL_REGISTER part 1 (D666, D668, D669: the one-task reception screen, Darpan's order sheet); 03-Oct-2026 by part 2 (D662, D663, D665: pairing on what a scan reads well, Amir asked nothing new, the bill-scan line after purchase.scan_wait_days, manoj.returns_ok on the owner's own rule).** Built from the live box, read only: the tiles each login is shown
(`portal.py` TILES + `tile_grants.json` v30), the per-unit roles (`unit_role` in finance.db), and every pending-work table the
Sanjeevni and finance modules keep (finance.db opened read-only, 21:50 IST). The machine part is `DUTY_MAP.json` beside this
file; a duty's id from that file is shown in brackets, e.g. `[amir.count_vouchers]`.

**05-Oct-2026 · kit S482_BILL_CHAIN (D675 b):** `[shavez.bill_chain_gap]` added — the bill-number chain's gap line on Shavez's *Aaj ki reports*. `DUTY_MAP.json` is v6.

**05-Oct-2026 · kit S485_DARPAN_ORDER_TAB (D677):** `[darpan.order_review]` added — Darpan confirms the system's order list on the second tab of his own page. `DUTY_MAP.json` is v7.

**How to read a row.**
*Due when* = the table and the condition that say the work is waiting. *Door* = the tile on that person's own portal home, and
the page it opens, where the waiting work is shown. *Owner's line* = what reaches the owner if it is missed:
**Needs-you (module)** = already raised by code on the Sanjeevni approvals Needs-you list (or, for the clinic, the clinic owner's
list `clinic_money.owner_queue` on /finance/clinic/money); **JSON** = the duty's owner line is written in `DUTY_MAP.json`, and
the duty-map check (run on every read of Needs-you, read-only) raises it **when the duty has no door** (an orphan) — a duty WITH
a door raises it only once it is marked `"raise": true` in the JSON (none is yet: the owner's call); **none** = nothing reaches
the owner today. A report card the owner has to go and open (the Amir-day card, the hub's Marg card,
the records line) is not counted as reaching him — F-671 showed a line on such a card can sit for twelve days.

**Whose module.** *Sanjeevni* = the pharmacy modules (amir_day, amir_salts, reports_tile, export_watch, darpan_kal, darpan_app,
returns_desk, stock_app, stockmatch, stock_watch, claim_queue, porders, order_rules, purchase_app, supplier_msg, sale_check,
item_alias, sanjeevni_approvals). *Parent's* = the clinic side (clinic_money, clinic_register, slip_log, slip_adjust, records,
petty_book, packs, staff_register, the asset app, portal.py, tile_grants.json).

---

## Amir (login `amir`) — part-time purchase clerk, medical viewer

Home: **Amir ka kaam** (/finance/amir), **Aaj ki reports** (/finance/reports/aaj), Meri attendance.
Parked for him (masked): Forms & Downloads, Scan Purchase, Staff Register, Attendance. His stock board
/finance/stock/page/amir has **no tile**.

| Duty | Due when (system state) | Door on his home (tile → page) | Owner's line if missed |
|---|---|---|---|
| Punch in on arrival (step 1) | `amir_step` step 1 not ticked on a visit day; punch in /root/punches.csv | Amir ka kaam → /finance/amir/step/1 | none (owner's Amir-day card only) |
| Key every purchase and purchase-return bill in Marg exactly as printed (step 2) | `amir_step` step 2 not ticked on a visit day | Amir ka kaam → step 2 | none (Amir-day card: "bills not confirmed entered") |
| Export the purchase pair, 1st to today (step 3/4) `[amir.purchase_exports]` | `purchase_export` ITEMWISE + BILLWISE of the day; `export_watch.verdict='red'` on a punched day | Amir ka kaam → step 3 "Do report nikaaliye" (and Aaj ki reports, on his days) | export_watch push to the owner's phone + red line on the Marg Purchases hub (coded) |
| Answer every purchase bill (Theek hai / what was wrong) `[amir.bills_answer]` | `purchase_bill` (bill-wise, from 01-Sep, in a live export) with no `amir_bill_disposition` row | Amir ka kaam → step 5 "Har bill par ek tap" | JSON: "Amir's purchase bills unanswered: N" |
| His own Marg correction, until Marg's next export shows the paper's amount `[amir.own_correction]` (S444) | `amir_bill_disposition.reason='self'` | Amir ka kaam → step 5 "Marg ki agli export ka intezaar" | Needs-you, amir_day (b) |
| Salt / name work for the day's items (step 6 tick) | `purchase_salt_task.done=0` (22 open today); `amir_step` step 6 | Amir ka kaam → step 6 → /finance/amir/salts | none |
| Export the SALT WISE ITEM LIST (Excel) after salt ticks `[amir.salt_list]` | ticks in `purchase_salt_task` newer than the newest VERIFIED `mi_file` SALT_WISE_ITEM_LIST | Amir ka kaam → step 6 and the close: "Ek export aur: SALT WISE ITEM LIST" | Needs-you, amir_day (a) |
| Enter the stock count's Marg vouchers BY STAGE `[amir.count_vouchers]` — **door added S444, staged S446 (D649)**: A the orthotic vouchers (7) → verified on the next closing-stock export → B the renames → verified → C the medicine vouchers, **12 a visit, more on request (S452: "Aur voucher kholiye" under the lot)** | `stock_voucher_line` batches with no non-empty newest `stock_voucher_entered` row (37 batches, 7 orthotic); the stage from `stock_stage_event` + the proof (S304's drift test over the stage's lines) | Amir ka kaam → the "Marg sudhar" card on every step ("Orthotic voucher baaki: N", "Ab closing stock export kijiye", the wrong items named, "Dawa voucher: aaj ke 12 (baaki N)") → his board /finance/stock/page/amir?count=1, which lists only the stage's vouchers, numbered 1..N | Needs-you, amir_day (d), named by stage; "Count #1: Stage …" (one info line) |
| Rename the orthotic items in Marg | `marg_item_rename` planned / amber (22 planned) | Stage B of the same card: "Naam badlo: N naam" — shown only once Stage A is verified (S446; it no longer waits on the medicine vouchers) | Needs-you once: "Orthotics verified and renamed — live orthotic ordering can start" |
| Pick a Sunday for the full stock count `[amir.full_count_sunday]` | `stock_count_plan.status='open'` | **door added S446**: his card, every step — "Poori ginti ka Sunday chuniye — kholiye" → board, section 4 | Needs-you, stock_watch: "Full count is due … Amir picks a Sunday on his board" |
| Key the bill for goods tapped as arrived `[amir.arrival_bill_entry]` | `purchase_order_line` arrived, supplied > 0, no billed bill, older than `arrival.bill_grace_days` (S454 part 2: the door's own grace -- the card reads stock_watch's own "bill entry baaki" list) | **door added S446**: his card — "Maal aa gaya, Marg mein bill baaki: N — kholiye" → board, section 4 | JSON: "Arrived goods with no Marg bill" |
| Put a selling rate in Marg for each orthotic short line the close-by-rule run could not price `[amir.rate_entry]` (S452) | the newest `stock_writeoff_run` of kind `ortho_close`: its `ortho_loss` lines with no `mrp_p`, less every item that now has a rate — Marg's own item export (the spine: the newest S.RATE or MRP above 0, mirrored into `stock_rate_marg` whenever the list is read) or the server's `stock_rate` — 2 on 02-Oct (FINGER COT SPILNT REMEDE, SOFT COLLAR BODY AID S: S.RATE and MRP 0.0 in Marg) | **door added S452**: his card, every step — "N item ka rate Marg mein daalna hai — kholiye" → board, section 3 (b) Rate daalo | JSON: "Orthotic selling rates not in Marg" (raised only if the door is ever removed — it has a door) |
| Fix lines from the stock traces | `stock_trace` with a fix, `status<>'fixed'` (28 open, all first-count and none carrying a fix today, so nothing shows) | **door added S446**: his card — "Stock trace ke sudhar: N — kholiye" → board, section 4 | Needs-you, stock_watch (trace notices, 7 days) |
| Look at each month's pack ("dekh liya") | `packs.amir_pack(month)`: ready (both Sanjeevni statements on the shelf) and no `pack_tick` amir_seen — every month of the last three, oldest first (S446, F-673: August now) | Amir ka kaam — inside the card, every step ("Mahine ka pack — August 2026", the two statements, "Dekh liya"; S452: the paid NEFT sheet only once that month's NEFT is confirmed, as a PDF) | none |
| Enter the month's supplier payments in Marg once the NEFT is done (S452) | no server state (Marg's own payment entry); the NEFT is confirmed when the bank's SMS is read (`purchase_neft_event.source='sms'`) or a statement line confirms it (`bank_line_id`), or the owner enters it (`source='owner'`) | Amir ka kaam — every step, the NEFT block: one line ("NEFT August 2026 — payment 24-09 ko ho gaya (Doctor sahab ne darj kiya)" / "… bank ka kaam ho gaya, dd-mm") and "Paid NEFT sheet (PDF)"; nothing before it is confirmed | none (no due state: not in the JSON) |
| Upload each scanned medicine bill in Marg's digital entry (S446, D650) | captured pharmacy scans (assets.db) with no `purchase_scan_link` **and, since S452 (F-686), no likely Marg bill and a known supplier** (S440's "Marg ka intezaar", `purchase_scan_state`) — another database, so no JSON line | Amir ka kaam → step 2 "Marg mein daalne ke bill (N)": Download each (`<stamp>_<SUPPLIER>[_<billno>]_<dd-mm-yyyy>.pdf`), "Aaj ke sab" as one zip; a bill leaves by itself when his export links it; a grey line counts the scans held for reception ("N scan abhi reception ki jaanch mein hain — Marg mein mat daaliye") | none (the owner's monthly Sarvam-against-Marg line counts what was linked) |
| Close the day (step 7) | `amir_day.closed_at` empty for a visit day | Amir ka kaam → step 7 | none (Amir-day card) |

## Darpan (login `darpan`) — pharmacy counter, medical maker

Home: **Kal ka hisaab**, **Daily Sale**, **Vaapsi Desk**, **Stock milaan**, **Purchase orders**, Forms & Downloads, Meri
attendance, Scan Purchase. (Kal ka hisaab also links to his old card /finance/darpan, "din ka card".)

| Duty | Due when (system state) | Door on his home (tile → page) | Owner's line if missed |
|---|---|---|---|
| Each morning: yesterday's cash handed over, and to whom `[darpan.cash_handover]` | a counter `day_entry` since `darpan_kal.log_from`, not covered (`cash_handover_cover`), not approved after the anchor, with no `darpan_kal_day.handed_p` | Kal ka hisaab → /finance/darpan/kal "किसको दिया?" (page drawn by script) | JSON: "Darpan's cash handover not typed for N days" |
| Give a reason when the cash is short | `darpan_kal_day.state='open'` with a difference | Kal ka hisaab "वजह चुनिए" | Needs-you, darpan_kal: "Darpan: N items where his word and the data differ" |
| Answer yesterday's flagged returns | flagged returns of the day (finance_returns_audit) with no `darpan_kal_return_answer` | Kal ka hisaab "कल की वापसी" | Needs-you, darpan_kal (contradictions / 'other' only) |
| Chase the supplier for Amir's bill claims `[darpan.amir_claims]` | `amir_claim.state<>'settled'` (claim #1 settled by the owner's ruling at S444; none open on 02-Oct) | **door added S446**: Kal ka hisaab → "Amir ke claim — N": supplier, bill, amount, raised when; two taps, nothing to type ("Supplier se baat ho gayi" → contacted, "Credit / maal mil gaya" → settled) | Needs-you, amir_day (c) (S444, after 7 days) |
| Spot mornings (Mon/Wed/Sat): count 'Aaj ki ginti' `[darpan.spot_count]` | `stock_spot_roster.answered_at IS NULL` | Stock milaan → /finance/stockmatch "Aaj ki ginti" | Needs-you, stock_watch: "Spot counts: Darpan left the morning list unanswered on N of the last 7 days" |
| Yes / no to Amir's full-count Sunday `[darpan.count_sunday_yes]` | `stock_count_plan.status='picked'` | Stock milaan "Poori ginti" | Needs-you, stock_watch ("Darpan's yes pending") |
| Answer each pursued count shortage, "Bina bill?" `[darpan.count_claims]` | `claim_line.state='open'` | Stock milaan "Bina bill" (also /finance/darpan) | JSON |
| Recount an item the owner asks for ("Phir se gino") | `stock_recount_ask` (0 asks) | Stock milaan | none |
| Vaapsi Desk "jaankari": count the shelf after a flagged return `[darpan.desk_shelf_counts]` | `stock_spot_check.status='due'` with no `jaankari_answer` (kind spot) | Vaapsi Desk → /finance/returns/desk "जानकारी चाहिए" (script tab) | JSON |
| Vaapsi Desk "jaankari": name / clinic ID that disagree `[darpan.desk_identity]` | `identity_dispute.status='open'` with no `jaankari_answer` (kind dispute) | Vaapsi Desk "जानकारी चाहिए" | JSON |
| Send the orthotic order to Yuvika | orthotic shortage computed by porders (count + purchases − sales vs keep) | Purchase orders → /finance/porders; card "Orthotic kam hai" on Kal ka hisaab | Needs-you, porders: "Orthotic shortages: N items -- order not sent" |
| **S454:** after making the order in Marg, save PENDING ORDERS (PURCHASE) as TEXT, the default way `[darpan.order_sheet]` | due only when the newest order-sheet file was refused (`mi_file` not VERIFIED, ORDER_PENDING) and no later sheet was taken | Kal ka hisaab → card "Order sheet": "<dd-mm> ki sheet mil gayi · N dawa · M supplier · reception ke paas pahunch gayi", or "Order sheet adhoori thi, system ne nahi li — Marg se dobara TEXT mein save kijiye"; the one instruction always under it | Needs-you, order_sheet: "Darpan's order sheet refused today" |
| Each order day from 09:30: confirm the system's order list `[darpan.order_review]` (S485, D677; while `order.source = darpan`) | an `order_proposal` row of today with status `open`, once `order.darpan_list_time` has passed | Kal ka hisaab → /finance/darpan/kal, the second tab "आज का ऑर्डर": hold a line, add a medicine, − / +, पक्का per supplier (then it is on reception's "Order karna hai" cards) | Needs-you, order_rules: an order not sent rides to its next order day and raises "Order not sent: …" (as on `system`) |
| Daily Sale by hand — only when the Marg autofile fails | a counter day with no `day_entry` | Daily Sale → /finance/daily | Needs-you (1) once filed: "N days to approve" |

The jaankari lists are shared by every desk login (`returns.desk_users` = darpan, shavez, alisha, shivani, bhawna); the JSON names Darpan.

## Shavez (login `shavez`) — manager; Marg report generator; clinic checker

Home: **Aaj ki reports**, **Morning match**, **Vendor payments**, **Mahine ka kaam**, **Staff Register**, **Check karein**,
**Report baaki**, **OPD & X-ray/Proc Slips**, **Purchase orders**, **Docterz daily collection**, Vaapsi Desk, Call Tracker,
Docterz Revenue, Bhati aaj, Asset Register, Staff Ledger — Entry, Forms & Downloads, Meri attendance, Scan Purchase.

| Duty | Due when (system state) | Door on his home (tile → page) | Owner's line if missed |
|---|---|---|---|
| Before sales: yesterday's bill-wise sale report `[shavez.sale_report]` | counter days (Mon–Sat) after the newest `sale_bill.business_date`, up to yesterday | Aaj ki reports → /finance/reports/aaj "… ki bikri report aur closing stock nikaliye" | JSON (the hub's Marg card also shows it) |
| Before sales: yesterday's closing stock `[shavez.closing_stock]` | counter days after the newest VERIFIED `mi_file` STOCK_CLOSING / `stock_feed` push snapshot | Aaj ki reports (same card) | JSON |
| 1st–7th: Stock valuation and Stock expiry of last month `[shavez.month_reports]` | no VERIFIED `mi_file` STOCK_VALUATION / STOCK_EXPIRY received this month | Aaj ki reports "Stock valuation" row | JSON |
| A gap in Marg's bill numbers: re-export the days the line names `[shavez.bill_chain_gap]` (S482, D675 b) | `mi_bill_chain` holds a row with `gap_before` or `gap_inside` (the chain is rewritten whenever a sale report or an EMPTY day lands; never by the calendar) | Aaj ki reports → /finance/reports/aaj, one red line per gap: "Bill … nahi mile (… se … ke beech) — … ki bikri report dobara banaiye." It leaves by itself when the re-export closes the gap | the tile's own English line (`reports_tile.status` → `line`: "Bill chain: … missing between … — re-export both days."); nothing on Needs-you (a duty with a door raises nothing there) |
| The salt list when Amir's did not come (S444: "Shavez kal subah nikalega") | same state as `[amir.salt_list]` | Aaj ki reports salt row (S444 adds "N din se baaki") | Needs-you, amir_day (a) |
| Morning match: check reception's first pass `[shavez.match_check]` | `clinic_money_day.status='maker_done'` | Morning match → /finance/clinic/match — lands on yesterday only (older days: see findings) | JSON |
| Morning match first pass himself when reception is away | as `[alisha.match_first_pass]` | Morning match | JSON |
| Staff Register: check and approve each day | staff_register.db `day_review.status='draft'` (none today: September approved to 01-Oct) | Staff Register (tile shows "to approve") | none (other database) |
| Verify present / exit requests | staff_register.db `present_request.status='pending'` (none) | Staff Register | none |
| Month-end checklist | `packs_item` not auto-done and no `packs_done` for the month | Mahine ka kaam → /finance/packs/checklist | Needs-you, packs (after the 10th): "Shavez's month-end checklist for <Month>: N items open" |
| Backup send of a supplier NEFT message unsent 30 min `[shavez.supplier_messages]` | `supplier_msg.status` queued / failed, queued 30+ min, kind neft / cheque (S454: an order message is the order screen's) | **door added S446**: Vendor payments shows "Pichhle mahine ka baaki: N" above the current month while an earlier month holds unsent messages or NEFT lines with no NEFT recorded; one tap opens that month ("Pending — baaki … Bhejo") | Needs-you, supplier_msg: "N supplier messages unsent" |
| Log every slip at the chamber | `slip` against the night's Docterz lines | OPD & X-ray/Proc Slips → /finance/slips | none (night report only) |
| Room ticks Paid / Done when in the X-ray room | `slip` series xp with `paid_at` / `done_at` empty | OPD & X-ray/Proc Slips → room | none |
| Check karein, Report baaki (X-ray), Purchase orders, Vaapsi Desk | shared with the reception desk — see Alisha and Reception | same tiles | as there |

## Alisha (login `alisha`) — reception desk; clinic maker

Home: **Docterz daily collection**, **Morning match**, **Check karein**, **Report baaki**, **Staff Register**, **OPD &
X-ray/Proc Slips**, **Purchase orders**, **Vaapsi Desk**, **Call Tracker**, Docterz Revenue, Bhati aaj, Forms & Downloads,
Meri attendance, Scan Purchase.

| Duty | Due when (system state) | Door on her home (tile → page) | Owner's line if missed |
|---|---|---|---|
| Each night: the counter sheet (cash / UPI / card, physiotherapy too) `[alisha.counter_sheet]` | a day among the last 45 `clinic_day_revenue` days, before today, with no `clinic_register_day` | Docterz daily collection → /finance/clinic/register (opens the newest unfilled day; the list /register/list marks each "— not entered FILL") | JSON (clinic_money adds an owner flag only on days someone opens the match card) |
| Each morning: Morning match first pass `[alisha.match_first_pass]` | a clinic day since 13-Sep with no `clinic_money_day` (maker_done / closed) | Morning match → /finance/clinic/match — yesterday only | JSON |
| Explain each open match flag `[alisha.match_flags]` | `clinic_money_flag.owner=0, status='open'` | Morning match → the day's card | JSON |
| Staff Register: enter each day (maker) | staff_register.db `day_review` missing / draft (none today) | Staff Register (tile shows "to enter") | none |
| Check karein: blood test with no report after 2 days `[alisha.check_blood]` | `blood_order` (from 19-Sep) with no `lab_report` within 7 days and no live `record_check` answer | Check karein → /finance/checks "Blood test likha tha, report nahi aayi" | JSON |
| Check karein: X-ray file with no clinic ID `[alisha.check_xray_files]` | `xray_filing.state='check'` not answered `not_xray` / `id_fixed` | Check karein "X-ray file ka clinic ID nahi mila" | JSON |
| Check karein: reports patients sent on WhatsApp | `record_wa` not yet saved / answered (none open) | Check karein | none |
| Report baaki: put each X-ray photo in the folder by next noon `[alisha.xray_photo]` | X-ray slip (from 23-Sep) with no `record_file` X-ray for that ID and day | Report baaki → /finance/slips/pending?t=xray "photo baaki" | JSON |
| Report baaki: place a lab report that came with no clinic ID | `lab_noid` with no ID and no answer, last 7 days (1 open) | Report baaki (blood tab) | none |
| Log a slip at the chamber when Shavez is away | `slip` | OPD & X-ray/Proc Slips | none |
| Follow-up calls | the Call Tracker Google Sheet (no table on the server) | Call Tracker | none |
| Purchase orders, Vaapsi Desk jaankari | shared — see Reception and Darpan | same tiles | as there |

## Shivani (login `shivani`) — reception desk; clinic maker

Home: exactly Alisha's tiles. **Same duties, same doors, same owner's lines as Alisha** — the two share one desk and one set of
queues; `DUTY_MAP.json` names `alisha` for each shared line (`alisha.counter_sheet`, `alisha.match_first_pass`,
`alisha.match_flags`, `alisha.check_blood`, `alisha.check_xray_files`, `alisha.xray_photo`). The staff-eye walk renders both homes.

| Duty | Due when | Door | Owner's line |
|---|---|---|---|
| Counter sheet, match first pass and flags, Staff Register entry, Check karein, Report baaki (X-ray), slips at the chamber, Call Tracker, Purchase orders, Vaapsi Desk jaankari | as in Alisha's table | the same tiles on her home | as in Alisha's table |

## Reception (shared login `reception`) — the phone whose WhatsApp sends the orders

Home: **Purchase orders**, **Call Tracker**, Forms & Downloads, Attendance, Meri attendance, Staff Register, Scan Purchase.
The page asks once per sitting who is working (Shivani, Alisha, Darpan, Sukhveer, Shavez). The same Purchase-orders duties show
on Darpan's, Shavez's, Alisha's and Shivani's homes (`porders.senders`).

| Duty | Due when (system state) | Door on its home (tile → page) | Owner's line if missed |
|---|---|---|---|
**S454 (03-Oct-2026, D666 / D668): the Purchase-orders tile opens "Aaj ka kaam" — the big "Naya bill scan karo" and a row for each kind of work, shown only while it has work.** The old page stays one tap away (`?old=1`, "Purana page" for the owner and Shavez).

| Order from the suppliers still to be ordered `[reception.medicine_orders]` | `porders.simple`=1: Darpan's sheet lines `order_sheet_line.state='to_order'` (on `order.source`=system: today's open `order_proposal`); the orthotic shortage card (S403) beside them | Purchase orders → /finance/porders "Order karna hai" → a card per supplier: "Sab ko WhatsApp bhejo", "Kholiye" (Call karo, the number under it), "Order ho gaya" | Needs-you, order_sheet: a supplier with no number; an order of the sheet never placed; the phone silent while messages wait. One push a day at `order.remind_times` (17:00) naming those still to order |
| When goods come, scan the bill `[reception.order_arrival]` | `purchase_order.status='sent'` with no bill scan tied (`order_scan_tie`) | Purchase orders "Maal aaya?" → "Bill scan karo" (the scan records the delivery by itself); "Bill nahi hai, ya kam aaya?" for a short delivery | JSON |
| Scan each paper still to scan `[reception.bill_scan]` | orders received on the arrival screen with no bill scan (for `purchase.arrival_scan_days`), and Marg bills of a counted month (`purchase.register_from`) with no scan and no likely scan, not marked "paper nahi mila" | Purchase orders "Bill scan karna hai" → by supplier, five at a time, "Scan karo"; "Koi paper nahi mil raha?" | Needs-you, porders |
| Answer the question about a scan `[reception.scan_questions]` | the matcher's questions (likely bill, amount, supplier), S441's, and "is it a pharmacy bill?" for a paper with nothing read — counted months | Purchase orders "Photo dekh kar bataiye" → one question on the screen, "Sawaal i / N" | JSON |
| A parked month's work (optional) | `purchase.parked_months` (2026-09): its bills to scan and its questions | Purchase orders → "Purana kaam: September" at the foot of the home | none (no count, no reminder, no alert, nothing to Amir) |
| **S454 part 2:** the month's register (owner, English) | `/finance/purchase/page/scans?month=`: every Marg bill in one state -- Verified, Has its scan, Amount differs, No scan, Entered twice in Marg, Accepted without paper -- and the month's scans with no Marg bill | Scan links | Needs-you, scan_register: "Bill scan waiting: N · the oldest X days" (after `purchase.scan_wait_days`), "Paper not found by reception", "Scanned and not yet in Marg for more than 7 days" (owner only) |
| Amir: the scanned bills Marg does not have `[amir.scan_files]` | never due (S454 6: nothing new is asked of him) | Amir ka kaam → step 2 "Scan ho chuke bill (N)" (purchase.entry_mode = paper) | none |
| Shavez: bills to scan, one line | a counted line of "Bill scan karna hai" | Aaj ki reports → "Bill scan baaki: N · sabse purana X din" → Kholiye | (the owner's own line above) |
| Keep the phone's MacroDroid sending supplier NEFT messages | `supplier_msg` queued (18 since 26-Sep 19:49) | **no door** on this home | Needs-you, supplier_msg |
| Follow-up calls | Call Tracker Google Sheet | Call Tracker | none |

## Bhati (login `bhati`) — physiotherapist; petty-book keeper; sale checker

Home: **Medical sale check**, **Petty book**, **Physiotherapy** (view), **OPD & X-ray/Proc Slips**.

| Duty | Due when (system state) | Door on his home (tile → page) | Owner's line if missed |
|---|---|---|---|
| Check each pharmacy day not yet approved ("Sahi hai" / "Galti hai") `[bhati.sale_check]` | `day_entry` submitted / draft since `darpan_kal.log_from` with no `sale_check_day` | Medical sale check → /finance/salecheck "Sahi hai" | JSON (his mistakes: Needs-you, sale_check "Bhati found mistakes on N days") |
| Enter the cash Darpan handed for a checked day | `sale_check_cash` for the day (none ever written) | Medical sale check | none |
| Say whether he comes today ("Aaj aayenge?") `[bhati.availability]` | no `petty_available` row for today or later | Petty book → /finance/petty "Aaj aayenge? … batayein" | JSON |
| Tick each physiotherapy day reception wrote `[bhati.physio_tick]` | `clinic_physio_day` (last 14 days, money > 0) with no `petty_physio_check` | Petty book "Theek hai" | JSON |
| Petty payments and diary top-ups (Shavez, Darpan) | event-driven: `petty_entry` | Petty book | none |
| Slips at the chamber / room ticks, now and then | `slip` | OPD & X-ray/Proc Slips | none |

## Sukhveer (login `sukhveer`) — lab; slips viewer

Home: **Report baaki** (blood tab), Forms & Downloads, Meri attendance, Scan Purchase.

| Duty | Due when (system state) | Door on his home (tile → page) | Owner's line if missed |
|---|---|---|---|
| Get the lab to mail each blood report, tap "Mail kar diya" `[sukhveer.blood_mail]` | `blood_order` (last 14 days, before today) with no `lab_report` within 7 days, not "not tested", not put off | Report baaki → /finance/slips/pending "der ho gayi" | JSON |

## The owner (login `manoj`)

Home: every doctor tile. His own recurring duties, so the map is whole:

| Duty | Due when (system state) | Door (tile → page) | Owner's line |
|---|---|---|---|
| Approve each pharmacy day `[manoj.approve_days]` | `day_entry.status` submitted / draft | Sanjeevni Medicos → /finance/approvals | Needs-you (1): "N days to approve" |
| OK the counter returns `[manoj.returns_ok]` | returns_kinds' own rule (S406: counter returns, real items, from `returns.act_from` 02-Sep — earlier ones accepted, S219); on 02-Oct: 3 (2 of September, 1 of October). The 7 August rows still marked pending in `darpan_return_approval` predate the rule | Sanjeevni Medicos | Needs-you (3) — **every open month since S446**: "Counter returns waiting for your OK: N, Rs X (oldest dd-Mon)" |
| Clinic money flags that reach him `[manoj.clinic_flags]` | `clinic_money_flag` to_owner, or owner=1 and open / explained / cannot | Morning match → /finance/clinic/money | clinic_money.owner_queue |
| Approve a slip discount / free / cancel `[manoj.slip_adjust]` | `slip_adjust.state='pending'` | OPD & X-ray/Proc Slips → /finance/slips | JSON |
| Mark Darpan's cash received `[manoj.cash_received]` | `darpan_kal_day` handed, `received_at` empty | Kal ka hisaab → /finance/darpan/kal | JSON (amber on the Kal ka hisaab owner card only) |
| Mark physiotherapy money received `[manoj.physio_received]` | `clinic_physio_day.received_at` empty, money > 0 | Physiotherapy → /finance/physio | JSON |
| Confirm money given to Bhati / OK his loan `[manoj.petty_confirm]` | `petty_entry` receive / loan_out not confirmed | Petty book → /finance/petty | JSON |
| Finalise last month's purchases `[manoj.purchase_month_final]` | `purchase_month` of last month not 'final' | Marg Purchases → /finance/purchase/page/hub | JSON |
| Settle a scan amount reception could not `[manoj.scan_amount]` | `purchase_scan_state.amount_state='owner'` | Purchase orders | Needs-you, porders (S440) |
| Approve the medicine buying rules | porders `_rules_ok` | Purchase orders | Needs-you, porders: "Buying rules for medicines await your approval" |
| Record the NEFT once the bank SMS comes | `purchase_neft_event` for the finalised month (August: provisional, no bank line yet) | Vendor payments | Needs-you, bank_sms / supplier_msg |
| Send the month-end pack | `pack_send` for the month | Month-end packs → /finance/packs | Needs-you, packs (empty shelf cells after the 10th) |
| Decide present / exit requests; lock salary | staff_register.db | Staff Register, Salary — approve & lock | none (other database) |

---

## No-door findings

A duty whose waiting state is real but no screen on that person's own home says it is due. **S446 (02-Oct-2026)** gave doors to
findings 1, 2, 3, 4 and 9 (each marked below); 5 is the phone's own step (below); 6 and 7 are the parent's; 8 is reported only.

1. **Darpan — Amir's supplier claims** (`amir_claim`). No page Darpan can open reads this table: only Amir's step-7 counters and
   the owner's Amir-day card. Claim #1 (raised 01-Oct 09:04 IST; S444 settles it by the owner's ruling at install) is the live case. S444 codes the owner's
   line after 7 days, but Darpan still has no door. *Sanjeevni* (amir_day; Kal ka hisaab or Stock milaan would carry it).
   **→ door added S446: Kal ka hisaab, "Amir ke claim".**
2. **Amir — pick a Sunday for the full count** (`stock_count_plan` open). Only on his stock board /finance/stock/page/amir, which
   has no tile; S444's step-6 card opens the board only while vouchers are open. *Sanjeevni* (stock_watch / stock_app).
   **→ door added S446: his card on every step, while due.**
3. **Amir — key the bill for goods tapped as arrived** ("bill entry baaki", `purchase_order_line`). Same board, same gap. *Sanjeevni.*
   **→ door added S446: his card, while due.**
4. **Amir — fix lines from the stock traces** (`stock_trace`, 28 open). Same board, same gap. *Sanjeevni.*
   **→ door added S446: his card, while due** (none of the 28 first-count traces carries a fix today, so nothing shows).
5. **Reception phone — supplier NEFT messages not leaving** (`supplier_msg`, 18 queued since 26-Sep 19:49 IST). The `reception`
   home has nothing that says its phone is not sending; only Shavez's Vendor payments page and the owner's Needs-you show it.
   *Sanjeevni* (supplier_msg). **S446 read the queue door's own log: the phone asked only twice, on 26-Sep 09:08, both refused for a
   wrong key (401) — before the 18 were queued at 19:49 — and never since. The fault is on the phone: its MacroDroid macro must be
   set up again from /finance/purchase/page/phone-setup (a fresh key). Nothing on the server is broken.**
6. **Reception login — seats without tiles.** `reception` holds a clinic maker seat and a checks maker seat (`unit_role`) but
   carries no Docterz daily collection, Morning match or Check karein tile. If the night counter sheet is filled on that phone, it
   has no door. *Parent's* (tile_grants.json).
7. **Morning match — every day but yesterday.** /finance/clinic/match always opens yesterday. The 13 clinic days with no first
   pass (since 14-Sep) and the 2 days waiting for Shavez's check (24 and 25-Sep) open only by typing a dated address.
   *Parent's* (clinic_money).
8. **Spine tasks with no owner** (`marg_task`, 48 open since 07-Sep: 12 questions, 9 ambiguous names, 2 merges, 1 name clash,
   24 renames). No page shows them and no person is named. *Sanjeevni* (marg_spine) — name a person or retire the list.
9. **Shavez — supplier NEFT messages unsent** (`supplier_msg`, 18 queued since 26-Sep). Found by S444's staff-eye walk: his
   Vendor payments tile opens the CURRENT month's sheet (/finance/purchase/page/pay → /pay/2026-09), which shows nothing of them;
   "Pending — baaki … Bhejo" is only on the NEFT month's sheet (/pay/2026-08). The owner's line exists (supplier_msg). *Sanjeevni*
   (purchase_app — READ ONLY in S444): the tile should land on the month whose messages wait. **→ door added S446: "Pichhle mahine
   ka baaki: N" above the current month, one tap to that month.**

**Doors that exist but the work is not being done** (measured 01-Oct 21:50 IST; the JSON check raises each of these the day its
duty is marked `"raise": true` in DUTY_MAP.json — not done in S444, the owner's call):
Vaapsi Desk jaankari — 48 shelf checks and 30 name/ID disputes since 02-Sep, 2 answers ever · counter sheet — 28 clinic days
unfilled in the page's 45-day list (oldest 11-Aug) · Morning match — 13 days with no first pass, 13 staff flags open ·
Check karein — 36 X-ray files with no clinic ID since 20-Sep · Report baaki — 16 X-ray photos not filed since 26-Sep ·
bill scans — 18 since 01-Sep · physiotherapy received — 12 days since 14-Sep · Spot counts — 4 items since 28-Sep.

Outside the nine people: Awdhesh (X-ray room, slips maker) ticks Paid / Done (`slip`, 6 open in the last 7 days); Dr Bhawna
shares the cash-received, physiotherapy-received and petty confirmations.

---

## How to keep this map

Two rules, written into CLAUDE.md by S444 for every later kit:

1. **A kit that adds, moves or removes a staff duty updates `claude_code_briefs/DUTY_MAP.md` and `DUTY_MAP.json` in the same
   kit** — the row, its due state, its door, and the owner's line (or why there is none). A new duty's `due_sql` is one read-only
   SELECT returning one row `(n, since)`, run on the live database before it is written in.
2. **The staff-eye walk.** The kit's walk signs in, on the scratch copy, as every login the kit affects, renders that login's
   portal home and the door page, and asserts that each of its pending duties is visible there (the `door_marker` text). A kit is
   not done until it passes. A page drawn by script (Kal ka hisaab, Vaapsi Desk, Purchase orders, Stock milaan) carries its
   marker in the page it serves; where a kit can, it also checks the same API call the page makes (S444's walk checks the page).

`since` in the JSON may carry a time (`2026-09-27T12:59:13`); compare on its first 10 characters.
