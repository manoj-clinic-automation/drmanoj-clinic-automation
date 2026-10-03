# Claude Code brief — S454 (the pharmacy's purchase flow, whole: the order comes from Darpan's Marg sheet; reception orders, receives and scans on one simple screen; scans pair with Marg; the owner's register; Amir left as he is)

Written 03-Oct-2026 by the Sanjeevni chat (S283 post-close) from `S283_PURCHASE_FLOW_DECISIONS_03OCT.md`, the record of the owner's rulings of that day. **This text replaces every earlier text of this file** (hashes beginning e43cb026, 979c3cec, edecf773, 5f8d091c, accd1b70, 6aef2c22). Read `CLAUDE.md` first.

**Kit S454 · decisions D662, D663, D665, D666, D667, D668, D669 · faults F-690, F-691, F-695, F-696, F-701, F-702.** It serves D650 (Marg's entry is final), D640 (a tap per line), D643 (the scanner is asked nothing while scanning), D648 (every duty has a door), D626 (the buying rules).

**Three files beside this one, in `claude_code_briefs\`:**

- `S454_BILL_REGISTER_MOCK.html` — the twenty screens. **Read it before §4.** On the staff screens (1 to 18) the words, the order and the buttons bind you. On the owner's screens (19, 20) the names of the states and the shape bind you. The counts are examples. The owner has accepted every screen, 5 and 6 included, as drawn.
- `S454_ORDER_SHEET_SAMPLE.txt` — Darpan's real order sheet of 02-Oct as Marg saves it, with the phone numbers and the letterhead's numbers blanked (F-185). It is the fixture for §3.
- `S454_ORDER_SHEET_PROTOTYPE.py` — the chat's own reader and A4 layout for that sheet. It is a reference for the parsing rules and for the look of the printed page, **not code to install**: it uses a PDF library the server does not have. Where it and the mock differ, the mock wins.

**The real sheet, with its numbers, is outside the repository:** `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S283\MARG_ORDER_SHEET_02-10-2026.txt` (§3.5).

**Runs on S452's files** (live 02-Oct 23:51 IST; the pins of §14 are those of the 03-Oct 01:35 nightly bundle).

**Touches — all Sanjeevni's, declared:**

- Server, `/root/finance/`: `porders.py`, `porders.html`, `order_rules.py`, `purchase_app.py`, `supplier_msg.py`, `amir_day.py`, `reports_tile.py`, `darpan_kal.py`, `darpan_kal.html`, `stock_watch.py`, `stock_app.py` (one column at the count's recording, §9.2), `marg_door.py`; a new module for the order sheet and new templates beside `porders.html` are allowed — pin them.
- Server, `/root/marg_ingest/`: `signatures.json`, `marg_take.py`.
- The medical PC, `D:\SendToClinic\`: `marg_txt.py`, `marg_watch.py`, `marg_push.py` (only if the refusal note of §10 cannot be sent without it), `KIT_MANIFEST.txt`.
- manojz: `D:\Downloads\margsync\MargPull\signatures.json` (the same new entry; it is not in the bundle — read its hash live).
- `claude_code_briefs/DUTY_MAP.md` + `.json`.
- The crontab: `order_rules`'s own line only, if §4.4 needs the clearing to run without a page being opened. Declare it.

**READ ONLY:** `assets.db` and the asset app (its intake link and its re-lane route are called as they are), `item_alias.py`, `sanjeevni_approvals.py`, `stockmatch.py`, the spine, `ring_common` (the push).

**No parent file:** not `finance_app.py`, `portal.py`, `tile_grants.json`, `finance_ui/finance_approvals.html`, `asset_register.py`, `packs.py`, `medical_agent.py`. If one turns out to be needed, stop and report; do not edit it.

**Build, walk and INSTALL part by part, in this order.** A part is installed only when its own walk is green; then go on to the next. Write `REPORT_S454.md` after each part.

1. **Part 1** — §3 (the order sheet: reader, road, loader) and §4 (the reception screen), with the settings they use, §7.5's cards except the gap card, and §7.3's lines about ordering.
2. **Part 2** — §5 (pairing), §6 (Amir), §7 (the owner's pages), §8 (Vendor payments), §12 (the duty).
3. **Part 3** — §9 (the shelf figure, and why the system's list differs).
4. **Part 4** — §10 (the medical PC's refusal note). **The watcher there is not replaced before 04-Oct 13:00 IST** (§10.3). Until this part is in, a sheet the medical PC itself refuses reaches nobody: say so to the owner in Part 1's report.
5. **Part 5** — §11 (the items).

If you must stop, stop at a part's boundary, say in the report exactly what is installed and what is left, and end. The owner then pastes the second line of §16.

**On a continued run, do §17 first** (corrections to Part 1, found when it was read live on 03-Oct), as its own small folder in the same kit, walked and installed before Part 2 is begun. It also adds a card with the reception phone's state and a test message (17.7).

## 0 · The rules this build stands on

1. **A staff screen shows only what that person has to do.** The owner: "They should only see what they need to do. What has already been accepted by the system is not a part of their flow. They should get it in very simple terms." One task on the screen at a time. No counts of settled things, no day counts, no tags, no explanations.
2. **The staff must not be burdened.** The owner: "The only part I am worried is this staff will get too much burdened by this flow." Reception has **two habits**: send the order, and scan the bill when goods come. Everything else is done by the system or is optional. Nothing is kept twice by hand.
3. **Staff pages in Roman Hindi; the owner's in English.** The screens are used on the **reception mobile**: phone width first, buttons at least 44 px, typing only where a number on a paper must be given.
4. **Darpan decides the order.** The owner: "the orders currently decided by Darpan, until and unless you build and validate your own system, which has multiple deficiencies right now." The system's own list is worked out but shown to no staff.
5. **Amir is asked nothing new.** "A soft start is what I want for Amir. Abruptly we cannot change the system. We will keep both the flows." No new kind of line reaches any list of his.
6. **September is parked.** "Do not absolutely drop the September part. Park it separately so that it is optional to clear it. And it will be a template for future also." A parked month is behind its own link: no count on the home, no reminder, no alert, nothing to Amir.
7. **Every threshold is a setting the owner can change on his screen** (§13).
8. **The old page stays one tap away** (§4.9).
9. **"REPORT" means: write it in `REPORT_S454.md`.** It never means wait for the owner. The only stops are the ones this brief names.

## 1 · How this came — the owner's rulings of 03-Oct, in his words

- **The regular flow:** "The goods come with the bill and the bill is scanned then or within a day." Amir's Marg entry follows two or three days later; the system pairs the two.
- **The order's source:** "The only part is the system capturing Darpan's orders as he makes them in the order sheet… and the staff is given a sheet which you have decided, and the flow in the purchase app which you have decided." The sheet is saved as text: "it has been operational for the stock report and the daily sale export, and it gets saved in the default way as the others are." Of its name: "It only gets a name 'report'… cannot expect the staff to [rename] this correctly. So you have to find your own ways." Orders "are not generated every day; they are generated every few days."
- **Old pending lines:** "The pending old orders are not removed by staff; they will be always populating the data, and for this we need to develop a system that these need to be highlighted in the printed sheet and in the app also, so that unnecessary ordering is avoided… this is only for the transition period."
- **Ordering by phone:** "One card per supplier will be 'order karo'. They call from there only; the click to call should exist… a tap, 'order ho gaya'. If they do not tap, we keep it posted as a pending order." "Click to call should also show the number."
- **WhatsApp:** "WhatsApp from the reception mobile to the suppliers was decided to be sent through a single click to all the suppliers, and they should not be tied to ordering by phone call. Both are independent… either can be done or both can be done."
- **The printed sheet:** "The staff should also be able to print the purchase order the system generated as a PDF on an A4 sheet with suitable columns to tick, so that a physical page is also available for them to pursue."
- **Out of stock at the stockist:** "Leave it as such."
- **Arrival:** all received unless tapped. "The bill scan there needs to be optional and not compulsory."
- **Stock:** "The order quantities worked out from 6 September count becomes a norm for future stock, stock check flow also." "We have the daily stock report export from Marg also… that could also help us in deciding the orders."
- **Amir:** his paper bill and the physical purchase register stay; scans go into Marg's digital entry without him only "once this flow is established and running… that might take one or two months."
- **Slips:** two Yuvika papers shown as "not in Marg" were handwritten estimate slips for the procedure room: "not related to the Marg pipeline."
- **Vendor payments:** "The vendor payment sheet should be limited to me and Shavez."
- **Also in this build, at his word:** "The item check screen and learning the supplier item names can be added to this build. Medical PC's refusal note also needs to be done."
- **Three changes to lighten the staff's work, agreed:** a bill scan counts as arrival; "Order ho gaya" is ticked on the list itself and an unticked order closes on its bill's scan; one reminder a day.

## 2 · What was read — REPORT the same facts first, as they stand on your day

### 2.1 Scans against Marg (`/finance/purchase/page/scans`, `/page/sarvam?month=2026-09`, as the owner, 03-Oct)

- September: 81 Marg bills · 63 linked to a scan · 18 with no scan · 12 scans with no Marg bill. *Scan ka kaam*: To scan 11 · Is this the bill? 8 · Choose the supplier 3 · Match the amount 4 · second scans 1 · S441's questions 6.
- **F-691:** those counts are what they were on 30-Sep. Nobody worked the list and nothing told anyone.
- **F-690:** the Sarvam page says of the 63 linked bills: supplier wrong 13, bill number 7, date 9, total 10. Read cell by cell, in substance: supplier 3, bill number 4, date 9, total 10. The rest are a full stop, a bracket or a prefix. Item lines: 28 of 158 read right.
- **F-695:** scans B-0007 and B-0018 (Yuvika estimate slips, nothing read) were on Amir's list as bills Marg does not have. Both were moved to the clinic lane in the owner's login on 03-Oct; Amir's list reads 0.

### 2.2 Ordering (`/finance/porders/api/state`, as the owner, 03-Oct)

- The ordering screen is live (S410): 18 suppliers, 39 lines planned, stock as on 01-Oct. **No medicine order has ever been sent through it.** The staff order from Darpan's printed Marg sheet.
- **F-696.** Against the 21 items Darpan ordered on 02-Oct, **9 are in the system's plan** (TENDOZAC TAB, CHYMORAL AP, DFO MR, VOLITRA APS SPRAY, MEG QCS, NARCOGEN FORTE, PANTOCID DSR, DECA INSTABOLIN 50, CROCAL — several at another quantity); **12 are not** (VERC 16, CCM, KT ROS DT, LONAC AQ INJ, PRETOL-4, RANIMIG 150, CEECIT MZ, OSTOVAXL DM, PREGHYPE NT TAB, PRETOL 8, AURAB L CAP, FENARIC T4 TAB); the plan has **about 27 lines the shop did not order** (TYRO BR 110 strips and PATOPAN DSR 60 strips among them, both with large stock by the count) and nothing for one supplier on the sheet (SHRADDHA MEDICOSE).
- The count is all there: `stock_count` id 1 (06-Sep), 373 items in `stock_count_item`, each with `counted_qty`. Marg's stock and the count differ a great deal on some items (MEG QCS: counted 640, Marg 477 on 30-Sep); the count's vouchers are not in Marg yet.

### 2.3 Darpan's order sheet (the owner's file of 02-Oct, read in full)

- Marg's report **"PENDING ORDERS (PURCHASE)"**, saved as text under the default name. **11 suppliers, 32 lines: 21 dated 02-10-2026 (10 suppliers), 11 older** (23-07, 10-08, 19-08, 01-09, 09-09 twice, 17-09 twice, 25-09 three times) that Marg goes on printing because nobody closes an order there.
- Its own arithmetic holds: every supplier's units come to its printed subtotal, and the subtotals to the printed TOTAL, 4,046 units. The line values come to 41,228 against a printed 41,226: **the value is rounded per line.**
- Its shape is in §3.1.

### 2.4 Code facts that shape this build (read in the 03-Oct bundle; check each before you rely on it)

- **The reader** `marg_txt.py`: `kind()` returns SALE, STOCK or nothing, by the title and column heads in the first 4000 characters and `*** End of Report ***` in the last 400; `convert()` makes a real `.XLS`; the watcher hot-reloads the reader (no restart). Samples are module constants that `marg_watch.selftest` imports by name.
- **The road:** the watcher spools `<stamp>__<slot>_TXT__<md5-8>.XLS`; `marg_push` POSTs it to `/finance/api/marg-file`; `marg_door.api_marg_file` → `marg_take.take()` → `marg_router.process` with `signatures.json`; a file matching no signature is `_UNKNOWN` or REFUSED in `mi_file` and shows to the owner as "Report refused today". `verify()` refuses a report with no dates unless its signature says `dating: file_mtime`, and treats `dd-mm-yyyy` cells **in the first body column** as data dates.
- **A refusal on the medical PC reaches nobody today:** it is a file in `_captured_txt\refused\` and a log line; the pusher sends only `.xls/.xlsx/.pdf`; `take()` refuses anything else before the database. The owner's surface exists already: any `mi_file` row of today with `pc_verdict='REFUSED'` shows in Needs-you and on the reports tile.
- **`purchase_order`** has no supplier key, no external reference and no order date other than `created_at`. `detect_supplies` (which clears a line when Marg's purchase arrives) and the learnt lead time key on `created_at`; it matches the ordered item to Marg's purchase line **clipped to 27 characters**; **it runs only when someone opens the page.**
- **The phone's queue** (`supplier_msg`): `_queue_row(con, month, vendor_norm, vendor, kind, ref, to_number, body)` is generic and the table has `kind` and `ref`. But every reader of the table counts all kinds as payment messages; **there is no in-flight state** (a row handed out and not answered is handed out again: a duplicate send is possible — **F-702**); `next` gives one row a call and the setup page tells the macro to call every five minutes; `supplier_msg.phone_last` records the last call, good or bad.
- **The reminders** are Web Push to `order.notice_to`, from `SLOTS` in `order_rules.py` (`"remind": ((12,0),(15,0),(17,0))`), sent by the cron's `tick`. The owner's approvals page has the times in a hard-coded sentence (a parent file).
- **No route edits the global `order.*` settings.**
- **A scan's supplier:** written at the scan's creation only when the intake link carried it; otherwise filled by the OCR, a background job that can take minutes. The matcher re-runs only when the count or the highest id of pharmacy scans changes — **a supplier filled in later does not trigger it.** `bills.created_at` is UTC; `bills.submitted_at` is IST. `purchase_scan_state` is deleted and rewritten at every pass: nothing durable may live there. `_vendor_ctx_s439`'s list of suppliers holds only those with a Marg bill.
- **`_arrive` (all received)** sets every line as supplied in full and the order to `received`; after it `api_arrive` refuses any correction, and `received_unbilled` raises a "Scan karo" line for an order received with no Marg bill.
- **Spot counts exist** (S428, `stock_watch.py`): a daily roster for Darpan on `/finance/stockmatch`, answers as `stock_point` rows, `expected_units()` = Marg's latest closing − sold + bought + tapped arrivals. Nothing computes "count + purchases − sales" for medicines; `porders._apportion()` does it for orthotics, reading only the root count. The canonical item key is the spine's `k20`.
- **Three probable gaps in the system's own medicine plan** (read, not tested): a line tapped "Aa gaya" while its order is still `sent` is counted nowhere; `_in_transit` matches the item name exactly though purchase names are clipped; `_pace` keys sales by a 20-character name and `plan()` skips an item with no pace.
- **The server has no PDF library.** Its PDFs are written by hand (`clinic_day_pdf.py`, and the paid-NEFT PDF of S452).
- **F-701:** the medical PC's agent installs a `.py` from the kit on a compile check alone; the manifest's md5 is not compared for it. Not repaired here (the agent is not deliverable by kit): confirm the reader's hash from the heartbeat.

## 3 · PART 1A — the order comes from Darpan's Marg sheet (D666)

### 3.1 The report, exactly

- A letterhead, then the title `PENDING ORDERS (PURCHASE)`, a rule of dashes, the column heads `ITEM NAME · ENTRY NO. · DATED · ORDER QTY · RECEIVE · PENDING · RATE · VALUE · DUEDT · PARTY ORDER NO.`, a rule.
- **A supplier line** at the left margin: the supplier's name as in Marg (sometimes followed by spaces and the town), then `Ph.` and zero, one or more phone numbers (a number can be printed twice; one on the real sheet has eleven digits).
- **An item line**, indented two spaces: item name, packing (`1*10`, `1*15`, `1*1`, `1*40`; once with a stray full stop), entry number (`OP-0326`), date (`dd-mm-yyyy`), order quantity, receive (`-`), pending, rate, value. **A name that fills its column leaves only ONE space before the packing** ("KNEE IMMOBILISER UNIS 1*1"): split on the packing's own shape followed by the entry number, never on "two or more spaces".
- **Quantity:** `20:0` = 20 strips and 0 loose; a plain number = pieces.
- **A subtotal** between two short rules: order units, pending units, value. Units = strips × pack size + loose, or the plain number as it stands. A supplier with one line has none.
- **Page furniture:** `Continued..2`, then the shop's name, the title with `Page No..2`, and the heads again. **A supplier's block can break across the page** (its name on one page, its items on the next).
- **The foot:** `TOTAL` with total order units, total pending units, total value; a rule; `*** End of Report ***`.

### 3.2 The reader on the medical PC (`marg_txt.py`)

- A third kind, **ORDER**, recognised by the title and the column heads, with `*** End of Report ***` at the end. The file's name is never looked at.
- **Refused, with the reason:** a line of a kind the reader does not know; a supplier's lines not coming to its subtotal in units; the subtotals and single lines not coming to the TOTAL in units; no TOTAL. The value is checked with a tolerance of one rupee a line.
- **The output** is the same kind of `.XLS` the other two kinds make, with one row per item line. Columns: supplier, phones, item, packing, entry number, date, order quantity, receive, pending, rate, value. **The date is not the first column** (§2.4). A title row, the heads, and a last row with the totals.
- The same bytes every time for the same input.
- **Selftest:** a sample constant made from `S454_ORDER_SHEET_SAMPLE.txt` (no phone number in the repository), recognised as ORDER while SALE and STOCK stay themselves; the page break inside a supplier; the one-space name; the supplier with no subtotal; each refusal above; the same bytes twice.
- **Delivered through the kit folder as S446 delivered it** (`ToMedical\_kit`, `KIT_MANIFEST.txt`); the watcher reloads the reader by itself. Confirm by the heartbeat's line for `marg_txt.py`.

### 3.3 The road and the server

- `signatures.json` (the server's, and manojz's copy): one new entry for this report, with `dating: file_mtime`. Without it the file shows to the owner as refused.
- **A loader** on the server takes each verified order sheet, at once when it arrives (the way `marg_take` calls the rename check for a stock file) and again on the page's load as a fallback. It is idempotent: the same file twice adds nothing.

### 3.4 What the loader does with the lines

For each item line, keyed by **(entry number, item)**:

- **Known** — the system holds it from an earlier sheet: nothing is added. Marg goes on printing a line for ever; the system's own record of it decides its state.
- **New** — not known, and dated less than `order.sheet_max_age_days` (7) before the sheet's newest date: it is **to be ordered**, under its supplier.
- **Old pending** — not known, and older: it is kept and **shown apart, highlighted, never ordered by itself** (§4.2, §4.3, §7.5).

Then:

- **The item is resolved** to Marg's item (the sheet prints about 21 characters; the item master and the spine's key are the way). The printed name and the resolved name are both kept. A name that does not resolve still loads, under its printed name, and is listed to the owner.
- **The supplier** is keyed with `supplier_key`, so that it equals Marg's own supplier on the purchase bills.
- **The phone book stays the source for dialling.** A number printed on the sheet for a supplier with none in the phone book is offered to the owner as one line; it is not written by itself.
- **What an old pending line says of itself**, worked out at each load and each page read: **"aa chuka"** with the date and bill number, when Marg has a purchase of that item from that supplier dated on or after the line's date; otherwise **"nahi aaya"**.
- **Every line has a way out:**
  - a new line whose supplier was never ticked, when Marg shows a purchase of that item from that supplier dated on or after the line's date: the line is closed as supplied, with no order made by anyone ("aa chuka, bina order ke");
  - a new line still not ordered `order.sheet_max_age_days` after its date becomes old pending, and the owner reads one line: an order of that date to that supplier was never placed;
  - an old pending line that reads "aa chuka" is shown to the staff for `order.old_done_days` (7) days from the day it first read so, then only on the owner's list;
  - an old pending line that reads "nahi aaya" is shown until it is ordered again, or reads "aa chuka", or is older than `order.old_show_days` (60); then only on the owner's list.
- Keep the sheets and their lines in tables of their own. REPORT the tables.

### 3.5 The first load — yesterday's paper order

The order of 02-Oct was placed by phone from Marg's print, and part of it has arrived. At Part 1's install, the installer takes `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S283\MARG_ORDER_SHEET_02-10-2026.txt` from manojz — it goes up with the installer and is written neither into the repository nor into the kit — converts it with the reader's own code (§3.2), and runs the loader on the result once, with a switch that means **already ordered**: its new lines become one order per supplier, made "on paper" at 15:00 IST on the sheet's date (the moment the scan tie of §4.4 compares with), awaiting arrival. They show under "Maal aaya?", never under "Order karna hai". What Marg already has as purchases clears itself. A later sheet, if one has reached the server by then, is loaded as new. REPORT what you loaded and what cleared.

### 3.6 Who decides: one setting, and a silent comparison

`order.source` = `marg_sheet` (the default) or `system`.

- **On `marg_sheet`:**
  - the staff's "Order karna hai" holds only the sheet's new lines;
  - the system's own proposals are still prepared every order day **but shown to no staff**; they raise no notice at 09:00 and no "Order not sent" line;
  - at each sheet's load the system's plan of that moment is compared with the sheet's new lines and kept: in both (with both quantities) · only on the sheet · only on the system's list;
  - the owner reads one line per sheet: **"Orders of <date>: the system agreed on X of Y items with Darpan's sheet"**, with the three lists one tap away (screen 19).
- **On `system`:** the same screens of §4, with the system's proposals of the day as the lines to order (S410's rules for sending apply: the rules approved, the minimum, a paused supplier), and the orthotic shortage (S403) as one more supplier card. A sheet that still arrives is compared and shown to the owner only.
- **The orthotic shortage card (S403) stays as it is today on both settings** — the owner made orthotic ordering live for the staff on 26-Sep. It is that supplier's card in the same list. When the sheet also has new lines for that supplier, they are in the same card; an item on both is shown once, with the sheet's quantity.
- The owner moves it. REPORT the comparison for the sheet of 02-Oct; it should read 9 of 21 on Marg's stock.

### 3.7 Darpan (`darpan_kal.py`, `darpan_kal.html`) — screen 16

- One card, "Order sheet", on his *Kal ka hisaab*: when the newest sheet arrived, how many medicines and suppliers, and that it has reached reception. Under it, always, the one instruction: "Marg mein order banane ke baad report ko TEXT mein save kijiye, jaise stock report save hoti hai. Naam badalne ki zaroorat nahi."
- When the newest file was refused — by the server in Part 1, and by the medical PC itself once Part 4 is in: "Order sheet adhoori thi, system ne nahi li — Marg se dobara TEXT mein save kijiye."
- His old line about today's orders (`order_rules.day_summary`) counts the sheet's suppliers still to be ordered while the source is the sheet.
- If he only prints the old way and saves nothing, nothing breaks: the paper serves for that day and the screen has no order to show.

## 4 · PART 1B — the reception screen (`/finance/porders`), one task at a time

For every login in `porders.senders` (manoj, darpan, shavez, shivani, alisha, reception). The owner sees the same screens in English. A viewer (`porders.viewers`) keeps the old page. S441's "who is working" on the shared reception login stays, and that name is the person on every record below.

### 4.1 The home — "Aaj ka kaam" (screens 1, 14)

- A large button first, always: **"Naya bill scan karo"** (the asset app's intake with the pharmacy lane, coming back here).
- Then one row for each kind of work, **shown only when its count is above zero**, with its count and its name and nothing else:
  1. **"Order karna hai"** — suppliers still to be ordered (§4.2).
  2. **"Maal aaya?"** — orders made and not yet received (§4.4).
  3. **"Bill scan karna hai"** — papers still to be scanned (§4.5).
  4. **"Photo dekh kar bataiye"** — questions about scans (§4.6).
- When no row has work: one green card, "Sab kaam ho gaya", and "Naya bill aate hi yahan dikhega."
- At the foot, a small text link for each parked month that still has work: **"Purana kaam: September"** (§4.8).
- Nothing else: no stock, no cover, no rules, no history.

### 4.2 Order karna hai (screens 2, 3, 4, 5)

**The list (screen 2).**

- One line at the top saying whose order it is and its date ("Darpan ka order · 02-10 · 10 supplier, 21 dawa").
- **"Sab ko WhatsApp bhejo"** and **"Order sheet print karo"** (§4.3).
- The line "Call se order kiya? Us supplier par 'Order ho gaya' dabaiye."
- Then one card per supplier still to be ordered: the name, how many medicines, and **two buttons: "Kholiye" and "Order ho gaya"**. Three or four cards, then "Baaki N supplier dikhaiye".
- At the foot, when Marg's sheet carries old pending lines: a small text link **"Purane pending: N"** (below).

**A supplier is ordered when either thing is done; the two are independent.**

- **A supplier's lines still to be ordered make one order, whatever is tapped** (a later sheet's lines for the same supplier make a later order). For those lines the supplier is in exactly one of three places: *still to be ordered* · *WhatsApp in the phone's line* · *ordered*. Only an ordered supplier's order is under "Maal aaya?".
- **WhatsApp to all, one tap.** For every supplier in the list with a number in the phone book, that supplier's order is made and its message is put in the reception phone's queue (the road of S407). No WhatsApp window opens, nothing is typed.
  - Until the phone has sent it the supplier reads **"WhatsApp line mein hai"** and is neither pending nor ordered.
  - When the phone says it was sent, the supplier is **ordered**. Screen 3 shows that moment: a green line saying how many went and who sent; "Abhi baaki" with the suppliers that could not be sent; "Ho chuke", each with "WhatsApp gaya" and a **"Call"** button still there ("WhatsApp + call ho gaya" when both were done).
  - A message the phone could not send, or not sent within `order.whatsapp_wait_min` (60), is **withdrawn from the queue**, and the same order goes **back among those still to be ordered** with "WhatsApp nahi gaya — call kijiye". "Order ho gaya" then confirms that same order; it never makes a second one.
  - **If the phone is not set up, or has not asked the server for `order.phone_alive_min` (30) minutes**, the button is drawn disabled with "Reception phone set nahi hai — call se order kijiye", and the owner gets one line.
- **By phone.** "Kholiye" opens the supplier (screen 4): the medicines and quantities in the order's own unit; **"Call karo"**, a `tel:` link, **with the number shown under it** (the second number too when the phone book has one); the line "Baat ho gayi? Tab yeh dabaiye. Phone nahi laga to BACK, order yahin baaki rahega."; **"Order ho gaya"**; and a small text button "Quantity badalni hai?" (S410's plus, minus, remove). The call's tap is recorded. **There is no tap for a call that failed.**
- **"Order ho gaya" on the list itself** does the same without opening the supplier — for staff who called from the printed sheet. Tapped for a supplier whose WhatsApp is in the line, it confirms that same order and the message still goes.
- **No phone number:** no WhatsApp, no Call button, the line "Is supplier ka phone number yahan nahi hai"; "Order ho gaya" still works; the owner gets one line.
- **A supplier nobody ticked leaves the list by itself:** when its bill is scanned, its order is made by that scan (§4.4); when Marg shows the purchase first, its lines are closed as supplied (§3.4).

**What "ordered" writes.** One purchase order for that supplier, as `send_proposal` writes one today (the same tables), made at that moment by that person, saying how it went (WhatsApp, call, or the bill's scan), and carrying Marg's entry numbers and that it came from the sheet. REPORT the columns you added.

**Old pending lines are highlighted, never mixed in (D669; screen 5).**

- On a supplier's screen they are a separate block under today's medicines: **"Purane pending — dobara order tabhi, jab zaroorat ho"**. Each line: the medicine, its order date, and what the system knows — **"aa chuka dd-mm"** or **"nahi aaya"**. Each has one small button, **"Dobara order karo"**, which adds it to today's order: from that tap it is a new line, counted from that day. "Remove" under "Quantity badalni hai?" puts it back among the old pending.
- They are never in the WhatsApp message, never in the list read out on a call, and never counted in "Order karna hai", unless that button was tapped.
- The foot link "Purane pending: N" opens all of them by supplier, with the same words and the same button — this is where a supplier with only old lines is found.

**If the stockist says an item is not there,** nothing new is tapped: it is answered at arrival, as today.

**The reminder is one a day.** `order.remind_times` (default `17:00`): a push to `order.notice_to`, only if a supplier is still to be ordered, naming them. The 12:00 and 15:00 notices go. On `marg_sheet` the 09:00 notice goes too; instead, when a sheet arrives: "Darpan ki order sheet aa gayi: N supplier, M dawa." The sentence about the times on the owner's approvals page is in a parent file: do not edit it; REPORT it for the parent.

**Untouched:** the owner's approval of the rules, the freeze (when ordering is frozen the row is not shown), holidays, the repeat guard, and the orthotic rules and their card (S403; §3.6).

**The reception phone's queue, for this (`supplier_msg.py`).**

- Order messages are their own kind. **Every reader that counts payment messages counts only payment kinds** — the pay card, its pending line, the owner's line, the phone's state line.
- **F-702:** a message handed to the phone is not handed out again for `supplier_msg.handout_gap_min` (10) minutes. This protects the payment notices too.
- When the phone says a message of this kind was sent, the order is marked so.
- The message is the order's text as built today (the shop's heading, then one line per medicine with its quantity and unit). It has several lines: **test it through the phone's own steps** as far as the server can (the JSON and the encoding), and say on the phone-setup page, in the instructions it already prints, that after each message the phone asks again at once until the answer is empty. **Do not print, log or report the key.**
- REPORT the macro's interval as the setup page states it, and how long ten messages take.

### 4.3 The printed order sheet (screen 6)

**"Order sheet print karo"** gives an A4 PDF, portrait, made the way the server makes its other PDFs. `S454_ORDER_SHEET_PROTOTYPE.py` and screen 6 show the page the staff were given on 03-Oct, used, and accepted:

- **Head:** the shop's name, "ORDER SHEET", the page number; a line with the order's date, whose it is, how many suppliers and medicines.
- **One row of column heads** at the top of each page, not one per supplier: Item · Pack · Qty · Order · Aaya · Kam aaya / nahi aaya.
- **One shaded band per supplier:** the name, the phone number(s) from the phone book ("(number nahi hai)" when none), and three small boxes at the right: WhatsApp · Call · Bill scan.
- **One row per medicine:** name, packing, quantity in bold ("20 strip", or the plain number of pieces), an empty box under Order, an empty box under Aaya, an empty cell to write in.
- **Old pending lines** (those §3.4 still shows to the staff) sit under their supplier's new lines, each with the small tag "purana, dd-mm" and what the system knows ("aa chuka dd-mm" or "nahi aaya"), and **no box under Order**. A supplier with only old lines comes after the others, under one line "Sirf purane pending".
- **Foot:** one line of instruction and "Order kisne kiya / Maal kisne liya / Tareekh".
- A normal order fits one page; a supplier's block is never split across pages.
- `order.sheet_print_old` (1): 0 leaves the old lines off the page.
- **The paper is the staff's working copy; nothing on it has to be typed into the screen.** **The layout is settled:** the staff are fine with it (the owner, 03-Oct). Build it as screen 6 and the prototype draw it; keep it in one place all the same.

### 4.4 Maal aaya? — one action: scan the bill (D668; screens 7, 8, 9)

**Scanning the supplier's bill records the delivery by itself.**

- A pharmacy-lane scan whose supplier has an order with no bill scan yet — awaited, or already received on the arrival screen — scanned at or after the moment that order was made (compare `submitted_at`, IST, to the minute), is tied to **that supplier's oldest such order**. A received order that has stopped asking for its bill ("One paper, one line", below) is no longer such an order. If the order was still awaited, **it has arrived.** One scan is tied to at most one order; keep the tie in a table of its own, never in `purchase_scan_state`.
- **A bill older than the order ties nothing:** when a bill date was read on the scan and its day and month (the year is not trusted, as in §5) fall before the order's day, the scan is not tied.
- The scan's supplier is the one the intake link carried, or the one the reading resolves to exactly or by a learnt spelling, or the one reception chose. A merely similar spelling ties nothing. The suppliers of the orders awaited are added to the list a reading is resolved against.
- **A supplier filled in after the scan was made must still be seen:** extend what triggers the matcher, and run this tie and Marg's clearing from the cron as well, so that neither waits for someone to open the page.
- **What "arrived by the scan" means:**
  - the order leaves "Maal aaya?";
  - its quantities count as on the shelf from that moment (§9), in full, until Amir's Marg entry gives the real ones;
  - **its lines stay open in the data**, so that Marg's bill, when entered, records ordered against supplied by itself. The staff are given no further step: whoever wants to say that something came short does so **before** scanning, through the small link below;
  - it raises no "Scan karo" line for itself.
- **A supplier that was never ticked** (§4.2) and whose bill is scanned **after the sheet was loaded** (and, where a bill date was read, its day and month on or after the sheet's newest date): its order is made at that moment, "by the bill's scan", and has arrived.

**The screens.**

- **"Maal aaya?" opens a list** (screen 7): one line at the top, "Maal aaya? Bill scan kijiye, bas. Maal apne aap darj ho jayega."; then one card per order awaited: the supplier, "Order dd-mm · N dawa", one button **"Bill scan karo"** (the intake with that supplier filled in), and a small text link **"Bill nahi hai, ya kam aaya?"**
- **The link opens the arrival screen** (screen 8), which is no longer a required step: the medicines, each shown as received; "Jo kam aaya ya nahi mila, us par tap kijiye."; a tapped line opens "Kam aaya" (with "Kitna aaya?"), "Nahi mila", "Aa gaya"; **"Maal aa gaya"** saves it by today's rules; "Abhi nahi aaya" leaves.
- **After "Maal aa gaya"** (screen 9): "Maal darj ho gaya", then "Bill abhi scan karna hai?" with two buttons of equal weight, **"Bill scan karo"** and **"Baad mein"**, and "Baad mein karenge to yeh 'Bill scan karna hai' mein milega."
- The big green button on the home does the same as "Bill scan karo" without coming here.

**One paper, one line.** An order received by the arrival screen with no bill scanned waits under "Bill scan karna hai" as "<supplier> · <dd-mm> ka maal". It leaves when its supplier's scan is tied to it; or when a Marg bill of that supplier dated on or after the order's day appears with no scan — that bill's own line takes its place, never both; or after `purchase.arrival_scan_days` (7).

Goods that came without any order have no line here; the staff use "Naya bill scan karo".

### 4.5 Bill scan karna hai — a short list by supplier (screen 10)

- **What is in it:** orders received with no bill scan (§4.4), and Marg bills of a counted month with no scan and no likely scan.
- **Grouped by supplier**, as the papers are filed: "KEDAR PHARMACEUTICAL · 3 bill". One line per paper: the bill number (or "<dd-mm> ka maal"), the date and amount where known, one grey sub-line saying which kind it is ("Maal aa gaya, bill scan baaki" / "Marg mein hai, scan nahi"), and **"Scan karo"**. Five lines at a time, oldest first, then "Agle 5 dikhaiye".
- A small text button at the foot, **"Koi paper nahi mil raha?"**: the Marg-bill lines with a tick each and one button "Paper nahi mila". It is recorded; the line leaves the staff's list and shows on the owner's register.

### 4.6 Photo dekh kar bataiye — one question on the screen (screens 11, 12, 13)

A queue, oldest scan first. Each card: "Sawaal i / N" and a thin progress line; the scan's first page, large; one line saying which paper; the question in one line; big buttons; "Baad mein", which sends the card to the end of the queue. After the last: "Sab kaam ho gaya".

1. **Is this the bill?** (for a scan not yet paired) "Kya yeh <SUPPLIER> ka bill <number> hai?" with "<dd-mm> · <amount>". Haan / Nahi, with today's meaning. Where that bill already has a scan: "Kya yeh <SUPPLIER> ke bill <number> ka doosra scan hai?"
2. **The amount differs** (for a paired scan). "Bill par total amount kya likha hai?" Two buttons with the two amounts, **not labelled as Marg's or the scan's**, and "Koi aur amount" with one box. In a counted month what follows the answer is what follows today. In a parked month the answer is recorded on the register only.
3. **The supplier is not known.** "Yeh bill kis supplier ka hai?" Up to three likely suppliers as buttons, then "Koi aur" with today's list.
4. **Is it a pharmacy bill?** (§4.7).
5. **S441's questions** join the queue with their own words and answers.

**No card is made for a date or a bill number that differs on a paired scan.** Marg's entry stands (D650).

### 4.7 A paper with no bill number and no amount is never Amir's (F-695)

**The supplier never decides the lane; the paper does.** Yuvika sells the pharmacy its orthotics on printed bills and the procedure room its plaster on handwritten slips.

- A pharmacy-lane scan on which neither a bill number nor an amount was read, or whose reading is headed Estimate, Challan or Quotation, is never in *Marg ka intezaar*, never on Amir's list or in its count, and never counted on the register as waiting for Marg.
- It is a card: **"Kya yeh dawa (pharmacy) ka bill hai?"** with two buttons and nothing to type.
  - **"Haan, pharmacy ka bill"** — it stays in the pharmacy lane (if its supplier is not known, the supplier card comes next). If figures were read on it, it is matched by §5 like any scan. If nothing was read it is an **unread pharmacy paper: it never pairs with a Marg bill by itself.** When exactly one unscanned Marg bill of that supplier is dated within `purchase.unread_pair_days` (7) either side of the scan day, a kind-1 card is asked; its "Haan" pairs it ("Has its scan", with the note "paired by reception; nothing was read on the paper").
  - **"Nahi, pharmacy ka nahi"** — the scan leaves the pharmacy lane for the clinic lane through the asset app's own re-lane route, as "Galat lane" does today. Its exact lane is set there later by Shavez or the owner.
- **Such a paper marks an order as arrived (§4.4) only after "Haan"**, and only when its supplier is known: it is then a delivery's paper even though nothing on it could be read.
- S440's line "manager isse theek karega" goes.
- **Not here, the parent project's (D664):** how clinic consumables are grouped, one PDF for a bill and its warranty cards.

### 4.8 Parked months (screen 15)

- `purchase.register_from` (2026-10-01) is the first counted month. The home's rows hold work of counted months only.
- `purchase.parked_months` (default `2026-09`): each month named there that still has work shows as a link at the home's foot, "Purana kaam: <month>". Behind it: one line, "Yeh zaroori nahi hai. Jab samay ho, tab kijiye."; then the same two rows, "Bill scan karna hai" and "Photo dekh kar bataiye", for that month only, opening the same screens.
- A parked month raises no count on the home, no line on Shavez's page, no Needs-you, no reminder, and nothing to Amir. What S440 already put on Amir's *Marg sudhar* stays as it is; nothing is pulled off his lists.
- An earlier month that is not named is not shown to the staff at all.

### 4.9 The old page, and the owner's settings

- `porders.simple` = 1 serves these screens; 0 puts everyone back on today's page.
- `/finance/porders?old=1` serves today's page. A small link at the home's foot, "Purana page", for the owner and Shavez only.
- **The owner's settings card** is on the old page, for the owner only: every key of §13, each with its plain meaning, changed through one owner-only route and audited.

### 4.10 Screens the mock does not show — build them in the same pattern

The supplier card of §4.6; the second-scan wording; S441's cards; the tick list of "Koi paper nahi mil raha?"; the list behind "Purane pending: N"; "WhatsApp line mein hai" and "WhatsApp nahi gaya — call kijiye"; the disabled WhatsApp button; a supplier with no phone on screen 4; the owner's English; the owner's settings card. Put a picture of each (a saved page from the walk) in the kit and name them in the report.

## 5 · PART 2 — a scan is paired with its Marg bill on what a scan reads well (`purchase_app.py`)

One set of rules, in one function, used by the matcher, the questions, the register and the Sarvam counter. Two pages must not be able to disagree about a bill.

**How a field agrees**

- **Supplier:** start from what `_vendor_match` and `supplier_key` do today, and add only this: punctuation and brackets are dropped; "&" equals "AND"; the standalone words PVT, LTD, P, CO and M/S are dropped (never a letter inside a name); a trailing BAREILLY is dropped. Then the learnt spellings. The shop's own name, or a heading such as "WHOLE SALE CHEMIST & DRUGGIST", is never a supplier: the field is "not read".
- **Bill number:** Marg's number, leading zeros dropped, equals **one whole run of digits** in the scan's reading. A run that is the financial year, and any reading shaped like a drug-licence number, is never the bill number.
- **Date:** the day and the month agree. A year other than Marg's is a misreading and is ignored.
- **Total:** within Rs 1 is equal (fixed). Up to `purchase.total_noise_rs` (10) agrees, with the difference shown. More differs.

**The states of a Marg bill that has a scan — each bill in exactly one**

- **Amount differs:** paired, and the total differs by more than the noise. One card (§4.6, kind 2). After the answer the row is Verified or Has its scan, or it stays here and says "the paper reads <amount>".
- **Verified:** the total agrees, the bill number agrees, and at least one of supplier and date agrees. This is how the matcher pairs by itself. If the other of the two was read differently or not read, the row is still Verified and carries one note.
- **Has its scan:** paired, the total agrees or was not read, and the row is not Verified. Such a pair comes from reception's "Haan" or from the auto-link below. Marg's entry stands. One note says what the scan read. Nobody is asked.

A link that exists today is never undone by these rules; they only give it its state.

**What the intake link carried is known.** A scan started from a line of this screen has that line's supplier from its first second (§2.4): its supplier card and its §4.7 card are not asked. **It settles no bill by itself:** it still pairs only by these rules or by "Haan". A wrong paper scanned from a line must not settle that line's bill.

**The system asks less (auto-link).** Before a kind-1 card is made: if the supplier agrees, the amount is within Rs 1, and **exactly one** unscanned bill of that supplier carries that amount, pair them with no card (audit `auto_link`). Two candidates: a card.

**Before anything of this part is placed**, run the rules on September on a copy and REPORT: how many of the 12 unlinked scans now pair by themselves; how many of the 63 are Verified; how many questions are left; every row whose state changes. **If a rule pairs a wrong scan and bill on the copy, stop and report.**

## 6 · PART 2 — Amir: nothing new is asked of him (`amir_day.py`, `purchase_app.py`) — screen 18

`purchase.entry_mode`: `paper` (the default) → `both` → `digital`. The owner moves it.

- **On `paper`:** his step 2 card is headed **"Scan ho chuke bill (N)"** and reads: "Reception ne jo bill scan kiye hain aur Marg mein abhi nahi hain, woh yahan dikhenge. Aap apne register se jaise daalte hain, waise hi daaliye. Chahein to bill ki file yahan se le sakte hain." The downloads stay. The line "N scan abhi reception ki jaanch mein hain — Marg mein mat daaliye" is not shown. His step 7 never lists these as work. No reminder and no Needs-you line comes from them.
- **On `both`:** S452's words and its grey line return.
- **`digital` is not built.** The setting refuses the value with one line saying so.
- His list never holds an unread paper (§4.7).
- **Nothing in this kit adds a new kind of line to *Marg sudhar*, to his board or to his step 7.**
- The physical purchase register stays the lock against double entry while both flows run.

## 7 · PART 2 — the owner (`purchase_app.py`, `porders.py`, `order_rules.py`, `reports_tile.py`)

New owner lines are added through the modules' own `needs_you_lines`; `sanjeevni_approvals.py` is not edited.

### 7.1 The month's register — the Scan links page (screen 20)

`/finance/purchase/page/scans?month=YYYY-MM`, default the newest month.

- **One row per Marg purchase bill of the month**, in exactly one state: **Verified** · **Has its scan** (with its note) · **Amount differs** (both amounts, and "waiting for reception" or "the paper reads <amount>") · **No scan** (with "scan <stamp> is probably this bill" where a question waits; "paper not found" where reception said so; the days waited, in a counted month only) · **Entered twice in Marg** (as S440 marks it; the two entries are one row; this state wins over every other) · **Accepted without paper** (the owner's own tap on a "paper not found" row, audited, undoable; counted months only).
- **Under them, the scans with no Marg bill**, each in one state: probably a bill already in Marg · supplier not known · to be named by reception · unread pharmacy paper · waiting for Marg's entry · second scan.
- **The head line:** the count of each state, **Verified and Has its scan shown apart**, and "N of M settled" (Verified, Has its scan, Accepted without paper). "M of M ✓" with its date when every bill is settled and no scan of the month is open.
- **At the foot, one block:** the Sarvam counter's figures for the month's linked bills (§7.4), linking to the Sarvam page.
- **A parked month is headed as parked:** no accept tap, no day counts, no alert.
- English only on this page. Phone width: no sideways scroll.

### 7.2 Is the new flow ready? — one line a week

On the register's head: **"Last 7 days: N bills entered in Marg · n had their scan before the entry · m paired with no tap."** This tells the owner when to move `purchase.entry_mode`.

### 7.3 What reaches a person — counted months only

- **Shavez's morning page** (`reports_tile`; screen 17): one line while a line of "Bill scan karna hai" of a counted month waits: "Bill scan baaki: N · sabse purana X din", with "Kholiye". Place it apart from the report rows, so that their counts stay right. The order sheet is not a report row of his page (it is Darpan's); a refused file of any kind still shows there as refusals do today.
- **The owner's Needs-you:**
  - the oldest counted line of "Bill scan karna hai" is older than `purchase.scan_wait_days` (3);
  - a paper reception could not find: his tap accepts it;
  - a read pharmacy scan waiting for Marg's entry for more than `purchase.entry_wait_days` (7): for his eyes only, never Amir's;
  - a supplier to be ordered with no phone number;
  - the reception phone not set up or silent — only while an order message waits for it, or after someone met the disabled WhatsApp button; never as a standing nightly line;
  - an order of the sheet that was never placed (§3.4);
  - an order sheet refused (§10);
  - an item of the sheet whose name did not resolve; a phone number on the sheet that the phone book lacks.
- **`DUTY_MAP`:** rows for "save the order sheet as text" (Darpan), "order from the sheet's suppliers", "scan the bill when goods come", "answer the question about a scan", each with its screen as its door; Amir's scan list with no due state. The staff-eye walk asserts them.

### 7.4 The Sarvam counter

**F-690:** the Sarvam page counts by §5's rules. Punctuation and prefixes are not misses. A date, a bill number or a supplier read differently on a paired scan is a miss here, and only here. Batch and expiry are not verified from a scan.

### 7.5 The owner's ordering lines (screen 19)

On the owner's view of the old page, as cards in English:

- **Who decides the order** — the setting of §3.6, with its switch.
- **"Orders of <date>: the system agreed on X of Y items with Darpan's sheet"** — and the three lists.
- **"Marg shows N old pending orders: n already supplied since, m never came"** — the list, by supplier, with dates. Nobody is asked to close them in Marg.
- **The order sheet's own state** — the newest sheet taken, its lines; a refused file and why.
- **"Marg and the shelf figure moved apart on N items"** (§9.3).

## 8 · PART 2 — Vendor payments: the owner and Shavez only (D663) (`purchase_app.py`, `supplier_msg.py`)

The Vendor payments page still opens for every medical login and draws the annexure with every supplier's full account number and IFSC.

- **The Vendor payments page** (`/finance/purchase/page/pay` and its month pages), **the covering letter, the annexure, the bank advice and the payment pack** (S265, S380), on screen and in print, open only for the logins in `supplier_msg.senders` (today: manoj, shavez). Every other login gets the page's own refusal, and the "Vendor payments" link is not drawn for them.
- **No page a login opens under `/finance/purchase/` or `/finance/amir/` serves an account number or an IFSC to a login outside that list.** REPORT each address you closed.
- **Not touched: the reception phone's keyed queue.** It is not a login; the payment notices carry the account number and IFSC by the owner's own ruling.
- **Amir keeps what the owner ruled for him in S452, on his own pages:** the one NEFT line, and his month pack on step 2 ("Paid NEFT sheet (PDF)" and the two bank statements), once the month is confirmed. That is not the payment pack above. His Paid NEFT sheet carries supplier and amount only; if it carries account numbers today, take them out of his copy.

## 9 · PART 3 — one shelf figure (D667), and why the system's list differs (F-696)

### 9.1 The figure

**For every item: its newest physical count + purchases − sales + returns since that count, + what has arrived and is not yet in Marg.**

- **The newest count** is the latest of: a spot-count answer or a "Stock batao" (`stock_point`), and the item's row in a full count — the whole count family (its parts and Darpan's recounts, the latest winning), not the root alone.
- **Movements** by the spine's item key, with the boundary the orthotic shelf uses (the count day's sales in, its purchases out). REPORT any count whose clock time makes that boundary wrong.
- **Arrived, not yet in Marg:** tapped arrivals and orders that arrived by a bill's scan (§4.4).
- Items that share one spine key are split as the orthotic shelf splits them, and marked approximate. An item with no count keeps Marg's figure and is named. A result below zero is taken as zero and named.
- **One function, in one place.** Base units, with the pack size beside it.

### 9.2 Where it is used

- **The system's own order list** (`order_rules.py`): `order.stock_basis` = `count` (the default) or `marg`. On `marg` the plan equals today's plan line for line.
- **The spot counts** (`stock_watch.py`): the figure a spot-count answer is compared with is this one.
- **A full count** (`stock_app.py`): when a count is recorded, this figure is stored beside Marg's on each row and shown to the owner. **The loss desk goes on judging by Marg's figure in this kit;** judging a full count by the shelf figure is the next kit's, and the report says so.

### 9.3 Marg's daily stock beside it

- At each new closing-stock report, keep for each item the gap between the shelf figure and Marg's.
- On the count day the gap is the count's own correction. It stays as it is until Amir files that item's voucher, and then closes by the voucher's quantity.
- **A gap that changes with no voucher** means a movement one side has and the other has not: the item goes up Darpan's spot-count roster (one more reason in its ranking, never past the roster's cap), and the owner reads one line with the count of such items and their names. An approximate item is never flagged.
- `stock.gap_min_packs` (1): a change smaller than this many packs of the item is not counted.

### 9.4 Why the system's list differs from Darpan's — measure, then mend what the data proves

REPORT, for the sheet of 02-Oct:

- for each of the 12 items only on the sheet: why the system did not list it (no sale pace found for its name; enough cover by its stock figure; not under that supplier; held under the minimum; other);
- for each line only on the system's list: why it was listed;
- each of the three probable gaps of §2.4, tested against the data, and **repaired where the data proves it**;
- the comparison again on the count basis: X of Y before and after.

This is the ground on which the owner will one day move `order.source`. Do not tune the rules to match the sheet; say what you found.

## 10 · PART 4 — the medical PC tells the owner when it refuses a file

### 10.1 What is sent

When the reader refuses a text file, or the watcher keeps a file as not recognised, the medical PC sends a short note: the file's name, its md5, the kind it looked like, and the reason. No file content. **The watcher sends it** (at the place it keeps a refused file), with the token and the address the pusher already uses; if that cannot be done without `marg_push.py`, edit it, declared. The watcher's wording for "why not" learns the order sheet in the same delivery.

### 10.2 Where it lands

`marg_door.api_marg_file` takes the note on the same address and with the same token as a file, before `take()`, and writes one `mi_file` row marked refused by the PC, with the reason. The owner's Needs-you and the reports tile already show such a row. **`finance_app.py` is not touched.** Darpan's card (§3.7) reads the same row for an order sheet.

### 10.3 The order of delivery

1. The reader (§3.2) — any time; the watcher reloads it by itself.
2. The signatures (§3.3).
3. **The watcher, last, and not before 04-Oct 13:00 IST.** Its delivery restarts it, and a restart makes it try again every refused text younger than three days: before that hour it would send the refused sale texts of 30-Sep and 01-Oct once more.

Confirm each by the heartbeat. REPORT the retry it made at its start.

## 11 · PART 5 — the items

### 11.1 The items check, a page for the owner

For a month: each Marg bill whose lines' own value (quantity × rate, less discount, plus tax, from `purchase_line`) does not come to the bill's amount within the noise setting — the bill, the difference, and its lines. A head line: how many bills add up and how many do not. English. REPORT August's and September's figures before you draw it.

### 11.2 Learning the suppliers' item names

- From a **Verified** bill whose scan has as many item lines as Marg's entry, pair a scan's line with a Marg line where the quantity and the rate agree and no other line of that bill does. The name that supplier printed is learnt against Marg's item.
- The Sarvam page's item figure then judges a name by the learnt names first.
- It changes no stock, no order and no bill. REPORT September's item figure before and after (28 of 158 before).

## 12 · PART 2 — one duty reads a wrong figure (`DUTY_MAP.json`)

`manoj.returns_ok` reads 7 in the staff-eye walks of S446 and S452 while the owner's own line reads 3. Its `due_sql` does not apply `returns.act_from` (02-Sep). Make it read the rule the owner's line reads.

## 13 · The settings, all on the owner's card (§4.9)

| key | default | what it does |
|---|---|---|
| `porders.simple` | 1 | the one-task screens; 0 returns the old page |
| `order.source` | marg_sheet | who decides the order: Darpan's sheet, or the system's list |
| `order.sheet_max_age_days` | 7 | a line of the sheet this old or older, and unknown, is "old pending" |
| `order.sheet_print_old` | 1 | old pending lines on the printed sheet |
| `order.old_done_days` | 7 | how long an old line that has since been supplied stays before the staff |
| `order.old_show_days` | 60 | how long an old line that never came stays before the staff |
| `order.remind_times` | 17:00 | when the one reminder goes |
| `order.whatsapp_wait_min` | 60 | after this a message not sent puts the supplier back among the pending |
| `order.phone_alive_min` | 30 | the phone silent this long: the WhatsApp button is disabled |
| `supplier_msg.handout_gap_min` | 10 | a message handed to the phone is not handed again within this |
| `order.stock_basis` | count | the system's list works from the shelf figure, or from Marg's stock |
| `stock.gap_min_packs` | 1 | the smallest change of the gap that counts, in packs of the item |
| `purchase.entry_mode` | paper | paper, or both; digital is refused |
| `purchase.register_from` | 2026-10-01 | the first counted month |
| `purchase.parked_months` | 2026-09 | earlier months shown to the staff behind their own link |
| `purchase.total_noise_rs` | 10 | a total difference up to this is not a question |
| `purchase.scan_wait_days` | 3 | the owner hears of a bill waiting to be scanned after this |
| `purchase.entry_wait_days` | 7 | the owner sees a scan not yet entered in Marg after this |
| `purchase.arrival_scan_days` | 7 | how long a received order asks for its bill's scan |
| `purchase.unread_pair_days` | 7 | how near in date a Marg bill must be for reception to be asked whether an unread paper is that bill |

## 14 · Pins — the 03-Oct 01:35 bundle; read each live before its first edit

| file | pin |
|---|---|
| `/root/finance/porders.py` | `3620b374` |
| `/root/finance/porders.html` | `7a6799ae` |
| `/root/finance/order_rules.py` | `00a60efb` |
| `/root/finance/purchase_app.py` | `341c663e` |
| `/root/finance/supplier_msg.py` | `5cc35d2a` |
| `/root/finance/amir_day.py` | `85f208d0` |
| `/root/finance/reports_tile.py` | `8a987041` |
| `/root/finance/darpan_kal.py` | `377ffd63` |
| `/root/finance/darpan_kal.html` | `9269afb0` |
| `/root/finance/stock_watch.py` | `9cca2f2a` |
| `/root/finance/stock_app.py` | `f14a1cfa` |
| `/root/finance/marg_door.py` | `598ba2df` |
| `/root/marg_ingest/marg_take.py` | `21e37b0e` |
| `/root/marg_ingest/signatures.json` | `b2dcb211` |
| medical `D:\SendToClinic\marg_txt.py` | `70f920c4` |
| medical `D:\SendToClinic\marg_watch.py` | `81145aa7` |
| medical `D:\SendToClinic\marg_push.py` (only if edited) | `566e189e` |
| manojz `D:\Downloads\margsync\MargPull\signatures.json` | read live |

Read only, for reference: `sanjeevni_approvals.py` `792f4a9a`, `stockmatch.py` `f09d9516`, `item_alias.py` `5168c3c0`, `marg_router.py` `318086e3`, `salts_refresh.py` `40cb2615`.

## 15 · Walk (scratch copies of `finance.db`, `assets.db` and the spine; rows keyed W454*; dates from today; **no phone number in any output**)

**Part 1 — the sheet**

- The sample is recognised as ORDER; SALE and STOCK samples stay themselves. It gives 11 suppliers, 32 lines, 4,046 units; the supplier whose block breaks across the page has its four lines; the one-space name is read whole; the supplier with one line and no subtotal is read.
- Refused, each with its reason: a line removed (the subtotal fails); the TOTAL altered; the last line cut off; a line of an unknown kind.
- The same sample twice gives the same bytes. Loaded twice it adds nothing. The converted file passes the server's signature and its verify on a scratch router, and is refused there when its heads are altered.
- The first load: 21 new lines under 10 suppliers, 11 old pending; with a crafted Marg purchase of one old line's item from its supplier after its date, that line reads "aa chuka dd-mm"; the others "nahi aaya".
- A second sheet reprinting the first's lines and adding one supplier's new entry: only the new entry's lines are new.
- A name that does not resolve loads under its printed name and gives the owner one line.
- The first load "as already ordered": no card under "Order karna hai"; the orders are under "Maal aaya?" with the sheet's date; a crafted Marg purchase clears its line.
- A new line never ticked, with a crafted Marg purchase of its item: closed as supplied, no order, its supplier's card gone when no line is left. A new line eight days old and never ordered: old pending, and the owner's line. An old "aa chuka" line on its eighth day, and an old "nahi aaya" line on its sixty-first: gone from the staff's block and sheet, still on the owner's list.
- The comparison for the sample reads X of 21 with the three lists. On `system` the same screens show the system's proposals as the lines to order. A crafted orthotic shortage shows as its supplier's card on both settings; with the sheet's own lines for that supplier it is one card, an item on both shown once. S410's and S403's walks pass on the old page.
- Darpan's card: a sheet arrived; a sheet the server refused. His old line counts the sheet's suppliers still to be ordered.

**Part 1 — the screen**

- **The home.** With crafted work of each kind: the scan button and the four rows with counts, nothing else on a row; a row with no work is absent; with nothing, "Sab kaam ho gaya". The parked link shows only while September has work.
- **Order.**
  - The list's cards carry the two buttons; "Order ho gaya" on a card makes one order with that supplier's lines and Marg's entry numbers, by the named person, and the card is gone; a second tap within ten minutes makes no second order.
  - "Kholiye": the lines in the order's unit; the Call link is a `tel:` link and the number is on the page; its tap writes one audit row; Call tapped and the screen left: the card stays and reads "call kiya tha, order baaki".
  - "Sab ko WhatsApp bhejo": one order and one queued message of the order's kind per supplier with a number; none for the supplier without; the pay card's counts, its pending line and the owner's bank line are unchanged by them; the queue's `next` hands a message once and not again within the gap. While a message waits, its supplier is in the line: not pending, not under "Maal aaya?". The phone's "sent" makes it ordered. "Failed", or silence past the wait: the message is withdrawn, the supplier is pending again with its line, and "Order ho gaya" then leaves **one** order for that supplier, not two. A supplier is never in two of the three places.
  - The phone silent past its limit: the button is disabled with its line; the owner's line appears once someone has met it, and not otherwise. With no key set: the same. A supplier with no number: the owner's line.
  - A quantity changed goes into the order and the message.
  - An old pending line is in no message and no count; "Dobara order karo" adds it as a new line of that day; "Remove" puts it back; the foot link lists all of them.
  - The reminder: one push at 17:00 naming the pending suppliers; none when nothing is pending; none at 12:00 or 15:00; on `marg_sheet` none at 09:00; one when a sheet arrives.
  - Frozen: the row is not shown and the routes refuse.
  - **No key and no phone number appears in the walk's output or the report.**
- **The printed sheet.** A PDF of one A4 page for the sample's new lines; with the old lines on, each carries its tag and its words and has no box under Order; a supplier's block is never split; `order.sheet_print_old=0` leaves them off; a supplier with no number prints "(number nahi hai)". The page's text holds every medicine and quantity of the order.
- **Arrival by the scan.**
  - A crafted pharmacy scan of an awaited supplier, made after the order: the order leaves "Maal aaya?", its quantities count as arrived in today's in-transit rule, its lines are still open in the data, and no "Scan karo" line is raised for it. A second scan of that supplier is tied to the next order, not the same one. With an older order of that supplier received on the arrival screen and unscanned, and a newer one awaited: the scan goes to the older. With the older one past its seven days, or replaced by its Marg bill's line: the scan goes to the newer.
  - A scan made before the order ties nothing. A scan whose read bill date is before the order's day ties nothing; the same date with a wrong year is judged by its day and month. A scan whose supplier is only similar ties nothing. A scan whose supplier was filled in two minutes after it was made is tied at the next cron run, with no page opened.
  - Afterwards a crafted Marg bill records ordered against supplied on the open lines.
  - An unticked supplier whose bill is scanned after the sheet's load: one order "by the bill's scan", arrived, and its card gone. The same scan made before the sheet's load, or with a read bill date before the sheet's newest date: nothing.
  - An unread paper ties nothing before its "Haan", and ties after it.
  - A re-run of the matcher loses no tie.
- **The arrival screen.** From the small link: all received in one tap; one line short with a quantity and one "Nahi mila" are saved by today's rules; "Abhi nahi aaya" saves nothing. Then both buttons; "Baad mein" puts the order under "Bill scan karna hai"; it leaves on its scan, on a crafted Marg bill (whose own line takes its place, the count unchanged), and on the eighth day.
- **The scan list and the questions.** Grouped by supplier, five lines, "Agle 5"; "Paper nahi mila" on Marg-bill lines only. One card at a time with "Sawaal i / N"; kinds 1, 2, 3 and S441's; the two amounts unlabelled; a paired scan whose date or bill number differs makes **no card**; "Baad mein" moves a card to the end.
- **Is it a pharmacy bill?** A crafted scan with nothing read is a card, is not in *Marg ka intezaar*, not on Amir's list or in its count; "manager isse theek karega" is in no served page. "Haan" with the supplier unknown: the supplier card next. "Haan" with nothing read: it pairs with no Marg bill by itself; with one crafted Marg bill inside the window a kind-1 card is asked; with two, none. "Nahi": it is in the clinic lane on the scratch `assets.db`.
- **Parked.** September's lines are in no home row and no count; behind the link the two rows open the same screens for September only; a kind-2 answer there raises nothing for Amir; an earlier month not named in the setting shows nowhere for the staff; **count Amir's *Marg sudhar*, his board and his step 7 before and after: nothing is added and nothing is removed.**
- **The old page and the settings.** `?old=1` and `porders.simple=0` serve today's page and S440's and S410's walks pass on it. "Purana page" is on the home for the owner and Shavez and for nobody else. Each key that Part 1 uses is changed on the owner's card, takes effect, and leaves an audit row; another login cannot open the card or call its route. Each later part walks its own keys the same way.
- **The owner's cards of Part 1** (§7.5, without the gap card): who decides; the agreement line and its lists; the old pending orders with what Marg says of each; the newest sheet's state.
- **The pictures of §4.10** are in the kit.

**Part 2**

- **The rules.** "PVT. LTD.", "(EXTN)", "&" against "AND" and a trailing BAREILLY agree; a "P" inside a name is kept; the shop's own name is "not read". A printed number with its series and year agrees with Marg's short number; a licence-shaped reading agrees with nothing. A wrong year agrees. A wrong month with supplier, number and total agreeing is Verified with its note; a misread number with the rest agreeing is "Has its scan". No bill is in two states. Rs 6 off agrees; Rs 243 off is "Amount differs" with one card. The auto-link pairs one candidate and asks on two. Every link that existed before the run exists after it. A wrong paper scanned from a line does not settle that line's bill.
- **Amir.** On `paper`: the new heading and words, the downloads, no grey line, nothing in step 7. On `both`: S452's walk passes. `digital` is refused. His paid NEFT sheet holds no account number.
- **The register.** The head's figures add up to the Marg bill count, Verified and Has its scan apart; every bill in one state, the same on every page; a bill entered twice is one row; a parked month has its heading and no accept tap; a counted month's accept settles the row and is undoable. No Roman Hindi on the page.
- **What reaches a person.** A crafted counted line four days old: Shavez's line and the owner's Needs-you show and leave on the scan. The same in a parked month: neither. A read scan waiting eight days: the owner's line, nothing on Amir's pages. The weekly readiness line on crafted rows.
- **The Sarvam page.** September's header figures equal §2.1's "in substance", or the difference is explained row by row; a parked month's kind-2 answer shows on the register.
- **Vendor payments.** As amir, darpan, bhati and the reception login: the page, the letter, the annexure, the advice and the pack refuse; no link to them; no page they can open holds a seeded account string. As shavez and the owner: unchanged. The phone's keyed queue answers as before. Amir's own month pack opens for him.
- **The duty.** `manoj.returns_ok` equals the owner's returns line.

**Part 3**

- A crafted item: counted 100, then 30 sold, 20 bought, 2 returned: 92 whatever Marg says; with 10 arrived by a scan and not in Marg (an order of §4.4): 102; with a later spot answer: that answer is the base; with only a part of the count family holding it: that part's figure; with no count: Marg's, and named; below zero: zero, and named.
- On `marg` the plan equals today's line for line. On `count` the plan's lines carry both figures for the owner and neither for a staff screen.
- A spot answer is compared with the shelf figure.
- A count recorded on the scratch database stores the shelf figure beside Marg's on each row; the loss desk's figures are unchanged.
- The gap card of §7.5 and its owner line. The gap: constant over three crafted closings, no flag; closing by a crafted voucher's quantity, no flag; changing by a pack with no voucher, the item is on the next roster within the cap and in the owner's line; an approximate item is never flagged.
- The three gaps of §2.4: one crafted case each, red before the repair and green after, for those you repaired.

**Part 4**

- A refused text on a scratch watcher sends a note; the door writes one refused row with the reason; the owner's line and the reports tile show it; Darpan's card reads "adhoori" for a refused order sheet; the same file again adds no second row; a bad token is refused; a note carries no file content.
- The reader's and the watcher's own selftests pass with their new counts.

**Part 5**

- The items page lists a crafted bill whose lines do not add up and not one whose lines do. The learning pairs a crafted line on quantity and rate, learns the name once, and does not learn from a bill that is not Verified or whose line counts differ.

**Every part**

- The staff-eye walk (CLAUDE.md, "Every duty has a door") for the reception login, darpan, shavez, amir and the owner, at phone width.
- Earlier walks re-run: S403, S407, S410, S414, S417, S428, S439, S440, S441's scan checks, S444, S446, S452 — each adjustment named.
- A negative control on the box as it is.

## 16 · Done means

Kit `deploy_kits\S454_BILL_REGISTER\` · each part installed, published and reported in `claude_code_briefs\REPORT_S454.md`, owner lines first:

- What reception now does, in two sentences, and the pictures of the screens the mock did not show.
- What Darpan does that is new, and what he sees.
- The order of 02-Oct as the system holds it: what was loaded, what has arrived, what is still awaited, and the old pending lines with what Marg says of each.
- "The system agreed on X of Y", and why it differed (§9.4).
- Whether the reception phone can send, and how long ten messages take.
- September as the register reads it; that it is parked; that Amir's work is unchanged.
- That Vendor payments opens for you and Shavez only.
- The settings, and where you change them.
- That the orthotic shortage card stays as it was (S403) beside Darpan's sheet, and how the two share one supplier's card.
- **What is not built, and why.** At least: scans going into Marg's digital entry without Amir; judging a full count by the shelf figure; the repair of F-701; the sentence about reminder times on the approvals page (the parent's).
- **What you need to do**, each as one line with its full address.

The owner's two lines:

```
Read CLAUDE.md, then build claude_code_briefs\S454_BILL_REGISTER.md — install, verify, publish and report.
```

```
Read CLAUDE.md, then continue claude_code_briefs\S454_BILL_REGISTER.md from where claude_code_briefs\REPORT_S454.md stops — install, verify, publish and report.
```

The report ends with:

```
https://followup.dr-manoj.in/finance/porders
```

```
https://followup.dr-manoj.in/finance/purchase/page/scans
```

## 17 · Corrections to Part 1 — do these first on the continued run

Part 1 (installed 03-Oct 12:24 IST, with 1B at 12:28) was read against this brief and against the live screens on 03-Oct, in the owner's login, read only. **It stands.** The home, "Order karna hai", "Maal aaya?", the old pending list, the owner's cards and the fourteen settings are as §3 and §4 ask. One thing is wrong, and it is all in the printed order sheet (`order_sheet_pdf.py`, live pin 9c28df38 — read it live before the edit): 17.1 to 17.5. One thing is added, about the reception phone (`supplier_msg.py`, `porders.py` or its S454 module): 17.7. (17.6 records a ruling and asks for no code.) Build all of it as folder `P1C_SHEET_PAGE_AND_PHONE` in the same kit; walk it; install it; report it; then begin Part 2. **Install this before anything else.**

**17.1 The page carries the whole open order, not only what is still to be ordered.** This completes §4.3, which did not say it.

- As installed, on 03-Oct the page printed 6 suppliers and 12 items ("2 naye, 10 purane pending") while 9 suppliers and 16 medicines of the 02-Oct order stood under "Maal aaya?". The staff's paper had lost exactly the lines they are waiting for.
- **The rule.** The page prints every line of the order that is not yet closed, under its supplier:
  - lines still to be ordered;
  - lines whose WhatsApp is in the phone's line;
  - lines ordered and awaited (everything under "Maal aaya?");
  - then the old pending lines, as §4.3 has them.
- A line leaves the page when its goods are recorded (by the bill's scan or by Marg), or when it lapses. A supplier with nothing left does not print.
- **What is already done is drawn done.** A line that is ordered has its "Order" box ticked. A supplier ordered by WhatsApp or by call has that box in its band ticked; an order whose way is not known (the first load of §3.5) ticks only its lines. "Aaya" and "Bill scan" are always empty: a supplier whose bill is scanned is no longer on the page.
- The orthotic card's lines (S403) print under their supplier as new lines, as they do now.
- **The head line counts what is on the page**, in this shape: "Order: dd-mm-yyyy · Darpan (Marg) · N supplier · M dawa: A order karna hai, B ka maal aana hai, C purane pending". A part that is zero is left out.
- A supplier's block is never split across pages. The page may run to a second sheet when the order is long; say in the report how many lines one page holds.

**17.2 The old-pending tag never prints over another column.** On 03-Oct three lines did: KNEE IMMOBILISER UNISON M (the tag ran across Pack and reached Qty), POWERGESIC 100 PATCH and ARM SLING XL HOPE (the tag ran into Pack). Put the tag on its own second line inside the Item cell, the row growing to hold it; or measure the name and the tag and wrap. Do not shorten the medicine's name.

**17.3 The foot's instruction line stays inside the page.** As installed it ran off the right edge and its end ("jab zaroorat ho.") was cut. Wrap it to the page's width; two lines if needed.

**17.4 The walk for this.**

- Every piece of text on the page lies inside its own cell and inside the page's margins. Measure it from the PDF's own text positions and the font's widths, not by eye.
- Run it on: the order as it stands live (a copy); a medicine name of 30 characters with an old-pending tag; a supplier with two phone numbers; a supplier with none; an order long enough for a second page.
- The counts in the head line equal the rows on the page.
- An awaited line is on the page with its "Order" box ticked; after its supplier's bill is scanned (a crafted scan), the supplier is gone from the page.
- **Negative control:** the page as installed fails the first check (the three lines and the foot) and the awaited-lines check.
- No phone number in any output of the walk.

**17.5 One word.** The owner's English view says "1 medicines"; make it "1 medicine". Check the Hindi reads rightly for one ("1 dawa").

**17.6 Payment messages go as they do today — nothing is held.** The owner, 03-Oct, was asked whether the payment messages waiting since 26-Sep should go out when the reception phone is set up. He first said to send them later; then, before 13:36 IST: *"We can send vendor payment messages now, so proceed accordingly."* **His later word stands.** Do not hold, skip or re-queue any payment message; add no setting for it. An earlier text of this section (brief md5 ac1e7915) asked for a hold: it is withdrawn. He is setting the phone up now, so the waiting messages may already have gone when you read this — REPORT how many payment messages are waiting, sent and failed as you find them, and change none.

**17.7 A card that shows the reception phone's state, and a test message.** So that the phone can be checked at any time — after WhatsApp changes its screen, say — without a real message and without opening the page that shows the key.

- A card for the owner, **"Reception phone"**, among his cards on `/finance/porders?old=1`. **The key is never on this card.** It shows:
  - when the phone last asked the server ("never" until it has);
  - messages waiting for the phone: orders, and payments, each as a count;
  - **"Test number"** — a field the owner fills once, kept in the setting `supplier_msg.test_to`; after saving it is shown with all but its last four digits masked. It is never written to a log, an audit detail, a walk's output or the report;
  - **"Send a test message"** — queues one message of its own kind (`test`) to that number. Two lines, to prove the line break and the encoding: "Sanjeevni test · dd-mm hh:mm" and "Yeh sirf jaanch hai — ₹ 1,234.50". Disabled, with the reason, when no test number is saved;
  - **the last test's state**, with clock times in IST: queued · handed to the phone · sent, or failed with the phone's reason.
- A test message is counted nowhere else: not with payments, not with orders, not in any staff's line.
- The phone-setup page itself is left as it is, apart from what Part 1 added. Do not open it in a way that shows the key to a walk, a log or the report.

**17.8 The walk for 17.7.**

- A test message: handed out once (F-702), the phone's "sent" marks it sent, the card shows the three times; the phone's "could not send" shows the reason. It appears in no payment or order count, and on no staff screen.
- Payment and order messages are handed out exactly as before this folder: the same rows, in the same order, on a copy of the live queue. **Control:** the box as it is gives the same answers.
- A login that is not the owner does not get the "Reception phone" card or its taps.
- No phone number and no key in any output.

**Report**, owner lines first:

- one sentence that the printed sheet now shows the whole open order, and how many lines it holds on a page;
- the payment messages as you found them: waiting, sent, failed;
- that the phone can be tested with a message to his own number, and the address of the card.
