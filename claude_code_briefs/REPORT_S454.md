# REPORT S454 — S454_BILL_REGISTER · Parts 1, 2 and 3 of 5 (with 1B, 1C, 1D) · installed 03-Oct-2026 12:24 IST (1B 12:28, 1C 15:36, 1D 16:35, 2 17:26, 3 18:17 IST) · published

**Where the run stands (03-Oct 18:20 IST):** Parts 1, 2 and 3 are installed, checked and published. **Parts 4 and 5 are not started.** Part 4
puts a new watcher on the medical PC, and the brief forbids that before 04-Oct 13:00 IST (§10.3). Part 5 follows Part 4 in the brief's
order. So this run stops at the Part 3 / Part 4 boundary. Nothing is half-installed. The continued run's line, any time after 04-Oct 13:00 IST:

```
Read CLAUDE.md, then continue claude_code_briefs\S454_BILL_REGISTER.md from where claude_code_briefs\REPORT_S454.md stops — install, verify, publish and report.
```

## For the owner — part 3 (the shelf figure; installed 18:17 IST)

- **The system's own medicine list now works from a "shelf figure".** That is the 6 September count, plus every sale, return and purchase
  since, plus goods that arrived and are not in Marg yet. Marg's own figure is kept beside it on your screens; staff screens show neither.
- **Against Darpan's sheet of 2 October the system now agrees on 9 of 21 medicines (it was 5 of 21).** For the other 12: ten have enough
  stock by the shelf figure for 11 days or more (CHYMORAL AP, for one, has 80 tabs, about 11 days). KT ROS DT has never been bought on
  the server's records. PRETOL 8 was last bought from Kedar, not Shivaaz.
- **One fault proven and repaired:** Marg's sales report cuts medicine names to 20 letters, so 5 medicines with longer names never had
  their sales counted. 2 of them sell, and now they are counted.
- **From the next Marg closing:** if Marg moves by a pack or more with no voucher, you get one line, "Marg and the shelf figure moved
  apart on N items". The item also goes up Darpan's spot-count list. Today's closing is the first one recorded, so nothing is flagged yet.
- **Worth knowing:** today 166 medicines differ from Marg by a pack or more. Most of these are the 6 September count's corrections
  that are not yet entered as vouchers in Marg (Amir's count-voucher duty shows 37 waiting). 5 show below zero and are counted as zero:
  TYRO BR (the count found 230 tabs fewer than Marg), NORTIMER TAB, GLI-ME SR1 and two ankle binders.

## For the owner — part 2 (bill scans and Marg bills, your month register, Vendor payments; installed 17:26 IST)

- **A bill scan is now paired with its Marg bill by one set of rules.** The bill number and the total must agree, plus the supplier or
  the date. Today this paired 4 more September bills by itself: two of L.K. Drug House, one of Essential Pharma and one of Saisun. Each
  was the only unscanned bill of that supplier for that exact amount, and each scan's medicine lines match the bill. No existing pair
  was undone.
- **Your month register** is the Scan links page. Every September Marg bill now sits in one state: Verified 53 · Has its scan 8 ·
  Amount differs 6 · No scan 12 · Entered twice in Marg 1. That is 61 of 80 bills settled. Two bills (MANNAT, KEDAR) now show "Amount
  differs": their scans read Rs 40 and Rs 243 more than Marg. Reception will be asked about them.
- **Amir is asked nothing new.** His step 2 shows "Scan ho chuke bill (N)" with the files, if he wants them. He still enters from his paper bill.
- **Vendor payments (and suppliers' bank details) now open only for you and Shavez.** Everyone else sees only the last 4 digits of an
  account in the phone book, and no IFSC. Amir's paid-NEFT sheet carries no account numbers.
- Your Needs-you list: the "bill scan waiting" line now comes only after 3 days. The returns line and its duty now count the same
  thing (3 each today). Checked, working.

## For the owner — part 1D (a fault of mine in part 1, found and mended at 16:35 IST)

- The ordering system's 10-minute background job had been failing since 12:30 today. It was a mistake in how part 1 was added to the file.
  The screens were not affected, because they do the same work whenever they are opened. But the job is what sends the 17:00 reminder
  and prepares tomorrow morning's lists. Mended and checked at 16:35 IST: the job now runs cleanly. Nothing else changed.

## For the owner — part 1C (the corrections of 03-Oct afternoon)

- **The printed order sheet now shows the whole open order.** It lists what is still to be ordered, what is waiting for its goods
  (with the Order box already ticked), and the old pending lines. Nothing prints over another column now, and the instruction line at
  the foot fits the page. One page holds 33 medicine lines. Today's open order (10 suppliers, 28 lines) prints on two pages, and no
  supplier is split across them.
- **Payment messages, as I found them at 15:36 IST:** 18 sent, 0 waiting, 0 failed. The phone has sent them all. One of them, the
  August NEFT note to A.A. Pharmaceuticals, was marked sent during the setup test but never went. It is back in the queue, so the phone
  will send it the next time it is awake. Nothing else was held or changed.
- **You can test the reception phone at any time with a message to your own number.** Open the "Reception phone" card, save your number
  once (it shows only its last 4 digits), then tap "Send a test message". The card shows when it was queued, handed to the phone, and
  sent (or why it failed). The key is never shown on this card. https://followup.dr-manoj.in/finance/porders?old=1
- The phone only asks the server while it is awake and unlocked, so the WhatsApp button now stays on for up to 12 hours of a dark phone.
  An order message that waits more than an hour still goes back to "WhatsApp nahi gaya — call kijiye" for the staff. The setup page's
  steps now match the macro you built (every minute, no loop, one WhatsApp only).

## For the owner — part 1

- **Reception now works from one simple screen.** "Purchase orders" opens on *Aaj ka kaam*: a scan button, then one row per kind of
  work: Order karna hai · Maal aaya? · Bill scan karna hai · Photo dekh kar bataiye. Each row opens one task at a time. To order, they
  tap a supplier and then either Call or WhatsApp, and tick "Order ho gaya". To receive, they just scan the bill. The scan marks the
  order as arrived, and a small link is there if something came short. Pictures of the new screens are in
  `deploy_kits/S454_BILL_REGISTER/P1_ORDER_SHEET_RECEPTION/pictures/`.
- **What is new for Darpan.** After he makes the order in Marg, he saves Marg's report as TEXT, the same way he saves the stock
  report. It reaches reception by itself. His *Kal ka hisaab* card shows "02-10 ki sheet mil gayi · N dawa · N supplier", and it says
  so if a sheet arrived incomplete. **Until Part 4 is in, a sheet that the medical PC itself refuses reaches nobody.** (A sheet the
  server refuses is already shown, on his card and in your Needs you.)
- **The order of 02-Oct is in the system.** It has 10 suppliers and 21 medicines, entered as already ordered. **2 orders have
  arrived by their bill's scan:** Kedar (scan B-0113, this morning) and Yuvika's orthotic order of 26-Sep (scan B-0099). The other 9
  are awaited under "Maal aaya?". The 11 old pending lines on Darpan's sheet all read "nahi aaya" in Marg. Ravi Medical Agency has
  no phone number in the phone book.
- **The system agreed on 5 of Darpan's 21 medicines.** Darpan ordered 16 that the system's list did not ask for. The system would
  have ordered 23 that are not new on his sheet; 3 of those are already on it as older pending lines. Part 3 shows the reason for
  each item (the shelf figure). (My first install showed "0 of 21". That was my mistake, now fixed: 1B.)
- **The reception phone cannot send yet.** It has not asked the server since the key was changed on 02-Oct (your one step from S452
  is still open). Until then the WhatsApp button stays grey and the staff call. Once the phone is set up, ten messages take about
  2 minutes. If the macro cannot ask again straight away, they take about 50 minutes (one every 5 minutes).
- **September is parked.** It raises no "Bill scan pending" and stays behind "Purana kaam: September". Amir's work is unchanged:
  his lists are the same with or without this kit. Everything was tested on copies of today's records (97 of 97 checks, plus the 12
  earlier tests) and checked again live.

**The settings** are on the owner's cards at the top of the old page (`/finance/porders?old=1`): who decides the order (Darpan's
sheet or the system), the reminder time (17:00, one reminder a day only while a supplier is left), how old a sheet may be (7 days),
and how long old pending lines show (7 / 60 days). They also cover WhatsApp waiting (60 min), when the phone counts as silent
(30 min), the gap between messages (10 min), when the register starts (01-10-2026), the parked months (2026-09), and how long an
arrival asks for its bill (7 days). Every change is recorded. **The orthotic shortage card (S403) stays as it was**, beside Darpan's
sheet. When both name the same supplier, reception sees one card, each item once, at the sheet's quantity. Today that card is
Yuvika with 2 items.

**Vendor payments** (for you and Shavez only) comes in Part 2.

**Not built yet, and why:**
- Parts 2–5: pairing, Amir, your register pages, Vendor payments, the shelf figure, the medical PC's refusal note, items. They follow
  in order; Part 4 not before 04-Oct 13:00.
- Scans going into Marg's digital entry without Amir, and judging a full count by the shelf figure: both outside this brief.
- The repair of F-701: outside this brief.
- On your approvals page, a sentence still lists the reminder times as 09:00, 12:00, 15:00 and 17:00. It is in a parent file I may not
  edit; it is reported for the parent chat below.

**What you need to do:**
- Set up the reception phone. Sign in as yourself on that phone, open the page below, copy the key into the macro's two HTTP steps,
  and sign out: https://followup.dr-manoj.in/finance/purchase/page/phone-setup
- Tell Darpan, once, to save Marg's order report as TEXT, the way he saves the stock report. The same line is on his card:
  https://followup.dr-manoj.in/finance/darpan/kal

## For the chat

### Part 1 · P1_ORDER_SHEET_RECEPTION — FROM → TO, read back on the box (install log 03-Oct 12:24:27 IST)

| file | FROM | TO (md5sum after placing) |
|---|---|---|
| /root/finance/porders.py | 3620b374a8fb3ac4988b8e6525795f84 | d4842f2c0f40a6ff69bd9a6d0425778f |
| /root/finance/order_rules.py | 00a60efb515972313839662ff7f83495 | d29efa8e6425fa359ea28d38c0758ccc |
| /root/finance/supplier_msg.py | 5cc35d2af444b5ab1996f636db8e54cf | fc6c1724d6da4e1d04897b60d61c13b8 |
| /root/finance/purchase_app.py | 341c663e52076f0ee264c356b49cf49e | 591432422d6b06af3dff886a8a0fc378 |
| /root/finance/darpan_kal.py | 377ffd63786261cef4a6113482d43bb5 | 911cf637a288fad85c75e54227149633 |
| /root/finance/darpan_kal.html | 9269afb04a454b626895a27666032752 | c20ab05d8484e37a667ddae32a4c792b |
| /root/marg_ingest/marg_take.py | 21e37b0e6fa6505a8825b32b7c24d41d | b41195e4ce853272ecf25b06343e3e16 |
| /root/marg_ingest/signatures.json | b2dcb2115a208bff81fac1c37c839428 | 64943ac6719a0f2ee06a15ef56d8c3d1 |
| /root/finance/order_sheet.py | (new) | 4cf2f231ef026904d1ae42754846aea7 → **93f55d87730e749d78ea5561de38266f** (1B) |
| /root/finance/porders_s454.py | (new) | 05716f3c040478d09fd2016561c7c99c |
| /root/finance/order_sheet_pdf.py | (new) | 9c28df38435a25d7e1d65c34b8d43ec9 |

**Crontab:** the S410 order_rules line only, `0,30 5-17` → `*/10 5-21` (`# S410_MEDICINE_ORDERING -- S454: every ten minutes,
05:00-21:50`). The line count is unchanged, read back. **Health:** finance healthz 200. `/finance/porders`, `/finance/porders/s454/order`,
`/finance/darpan/kal`, `/finance/purchase/page/scans` and `/finance/porders/s454/sheet.pdf` each answered 302 (the login gate,
expected). Nothing logged "NOT mounted" and there was no traceback. These were untouched, md5s compared before and after:
finance_app.py, portal.py, tile_grants.json, sanjeevni_approvals.py, packs.py, asset_register.py, item_alias.py, stockmatch.py,
amir_day.py, reports_tile.py, stock_app.py, stock_watch.py.

**Backups:**
- finance.db: `/root/finance/finance.db.bak_S454_20261003_120529` (part 1) and `…bak_S454_20261003_122844` (1B), both by the backup
  API.
- crontab: `/root/finance/crontab.bak_S454_20261003_120529`.
- `.bak_S454_<from8>` beside each of the eight files.
- `order_sheet.py.bak_S454_4cf2f231` (1B).

**Services restarted:** clinic-finance only (once per part).

**Outside the box:**
- Drive `ToMedical\_kit`, 12:29:09 IST:
  - `marg_txt.py` 70f920c4 → **ed17bb763c202f81cb8b3708fac61b52**;
  - `KIT_MANIFEST.txt` bdd27768 → **05fb348589ba967e26bf8b7c9ff2aebc** (CRLF, as live; the kit keeps the LF copy 5959bde8).
  - Both read back. The watcher (S397, 81145aa7) was **not** replaced.
  - The medical PC's heartbeat at 12:33:02 IST reads `marg_txt.py up to date (ed17bb76)`.
- manojz `D:\Downloads\margsync\MargPull\signatures.json` a987a08e → **7f72c572808218fbfc008373336beea8** (20 signatures), read back.
  Backup `signatures.json.bak_S454_a987a08e`.
- PROVE_S454_MEDICAL was GREEN 8 of 8, re-run 03-Oct before packing:
  - the live watcher's selftest passes with the S454 reader beside it;
  - `report.txt` is captured as one `.XLS` of the reader's own bytes (8845e680);
  - a sheet cut short is kept as refused;
  - 15-text parity with S446;
  - the real 02-Oct sheet reads ORDER, 11 suppliers, 32 lines.

**The first load** (live, step 10), from the owner's file in /tmp (deleted after, never in the repo):
- sheet of 2026-10-02, 32 lines: 21 new, 11 old pending; XLS md5 68d519a6;
- paper orders #2–#11 made 02-Oct 15:00 IST, one per supplier;
- cleared by Marg's purchases: 0 lines.
- First cron pass: 2 ties.
  - Order #6, Kedar ← B-0113: bill A000203, 03-10, Rs 4,267, scanned 10:57 IST.
  - Order #1, Yuvika, the S403 orthotic order of 26-Sep ← B-0099: bill dated 28-09, Rs 7,069, scanned 29-Sep 19:06 IST.
- The duty-map queries on the live database (read only):
  - reception.order_arrival n=9 since 2026-10-02;
  - reception.medicine_orders 0;
  - reception.bill_scan 0;
  - reception.scan_questions 0;
  - darpan.order_sheet 0;
  - shavez.supplier_messages 18 since 2026-09-26.

**The walk** (`walk_s454p1.py`, in the installer on backup-API copies of finance.db, assets.db and the spine): **WALK_S454P1 GREEN —
97 of 97.** It covers:
- the reader and its selftest;
- the road (door → ORDER_PENDING VERIFIED → loader, idempotent; altered heads refused; Darpan "adhoori");
- the home, Order karna hai, the phone silent / no key / alive, the WhatsApp line;
- F-702: the queue hands a message once per gap. The negative control is the box as it is, which hands it twice;
- withdrawals, the reminder (none at 12:00/15:00/09:00; one at 17:00), frozen 423, `order.source = system`;
- the orthotic card as one card, the PDF, the owner's cards and all 14 settings (audited, refused when bad);
- the first load, arrival by scan (all the tie rules);
- **new: an arrived-by-scan order's open lines still count in S403's shortage and S410's interim check until Marg answers them.** Its
  control: the old query drops them;
- the arrival screen, Bill scan karna hai, Photo dekh kar bataiye, F-695's unread paper;
- the negative control (the box puts it in "Marg ka intezaar" with "manager isse theek karega"), September parked, Amir's lists identical;
- the staff-eye walk on DUTY_MAP v4 for reception, darpan, shavez, amir and manoj (every tile, every due door);
- the negative control on the box as it is (/finance/porders is today's page; September raises "Bill scan pending on 18 purchase bills").

**The earlier walks** (`walks_old_s454p1.py`, each run on the box as it is AND on the patched files): **WALKS_OLD_S454P1 GREEN.**
Each walk is green on the patched files except for named reds, and each named red is word for word red on the box as it is too.

| walk | reds |
|---|---|
| S403 | 14 |
| S407 | 10 |
| S410 | 3 |
| S414 | 1 |
| S417 | 4 |
| S428 | 8 |
| S439 | 5 |
| S440 | 7 |
| S441 | 6 |
| S444 | 17 |
| S446 | 13 |
| S452 | 8 |

These reds are the walks' own controls ("the box before Sxxx", now gone) and today's data. The adjustments, each named in the walk
script and its output:
- **P0:** `porders.simple = 0` on the patched copy, for every walk except S444.
- **P2:** the S454 tables are made.
- **B1/B2** (both runs; S441 moved the box): the reception role, and the scanner's username.
- **P3:** S410 runs on `order.source = system`.
- **P4–P7:** S410's 12:00/15:00 reminders are silent, there is one 17:00 "Order baaki: …" (slot R1700) with 8 pushes, not 16, and the
  repeat is of 17:00. Once all proposals are sent, nothing proposed is named; S403's orthotic card may still be.
- **P8:** S444 reads the old page's BACK bar at `?old=1`, and checks the new screen for "Signed in: alisha" and one "← BACK" (green).

**Found while walking, fixed before install (in part 1):** S454's tie set an orthotic order to `received` the moment its bill was
scanned. S403's `_on_order` and S410's `_on_order_units` count only `status='sent'`, so the shortage came back. In S444's walk it read
"Orthotic shortages: 8 items -- order not sent", which would have asked reception to order Yuvika again. Both queries now also count
an order that arrived by its scan, until Marg answers its lines (`_s454_or_arrived`), which is the brief's §4.4. Live, the Yuvika card
holds the 2 items that were short before S454 (ANKLE BINDER BAMBOO L, L S BELT CONT GRAY UNISON XXX), not 8.

### Part 1B · P1B_COMPARE_FIRST (install log 03-Oct 12:28:54 IST)

Part 1's first load made its paper orders **before** `compare()`. S410's plan then counted them as on the way, and the stored
comparison read 0 of 21. That was found from the install's own output. The P1 folder is left byte-identical to what ran, and 1B is the
fix:
- `order_sheet.py` 4cf2f231 → 93f55d87: one anchored edit, the comparison above the paper orders.
- `recompute_s454p1b.py` remade sheet #1's figure on a scratch copy without its orders and wrote it to the unchanged live row, with an
  audit row `s454_cmp_recomputed`.

**WALK_S454P1B GREEN — 3 of 3.**
- New: 10 orders, 5 of 21, equal to the reference.
- **Negative control, the box as it was: 0 of 21.**

In both lists: DFO MR, VOLITRA APS SPRAY, MEG QCS (sheet 20 strip / system 10), CROCAL (30/20), OSTOVAXL DM (20/10).
- Only on the sheet (16): TENDOZAC TAB, VERC 16, CHYMORAL AP, CCM, KT ROS DT, LONAC AQ INJ, PRETOL-4, RANIMIG 150, NARCOGEN FORTE,
  PANTOCID DSR, DECA INSTABOLIN 50, CEECIT MZ, PREGHYPE NT TAB, PRETOL 8, AURAB L CAP, FENARIC T4 TAB.
- Only on the system's list (23): among them NUPTACH 200, OPTIFENAC TBR and UPRISE 6L INJ, which are already old pending lines on
  Darpan's sheet. The brief expected 9 of 21 on 01-Oct's stock; this is 02-Oct's stock (`as_on` 02-10-2026).

### Part 1D · P1D_TICK_GUARD (a fault of part 1; placed 16:35:21 IST by the file's own time)

- **The fault.** Part 1 appended its block to `order_rules.py` below the file's `if __name__ == "__main__":` line. That block holds
  `_s454_pass`, `_s454_remind`, `_s454_source` and `_s454_or_arrived`. The cron runs `order_rules.py tick` as a script, so every tick since
  12:30 IST died with `NameError: name '_s454_pass' is not defined` (`/root/finance/order_rules.log`).
  - The service imports the module, so it was unaffected. Page reads kept loading sheets, making ties and clearing lines.
  - What was lost until 16:35: the cron's own sheet loading, tie and clearing passes (the page reads covered them). No reminder was due
    before 17:00. Tomorrow's 05:30 nightly and 09:00 preparation would have failed.
  - Found while checking Part 2's own appended blocks for the same mistake. purchase_app.py, porders.py, supplier_msg.py,
    darpan_kal.py and marg_take.py were checked: only order_rules.py had it.
- **The fix.** The two guard lines move to the end of the file. order_rules.py d29efa8e6425fa359ea28d38c0758ccc →
  **6587dc84941f4e53ccc39d0847812123**, read back. Backup `order_rules.py.bak_S454_d29efa8e`. No data change, so no database backup was
  made. clinic-finance was restarted; healthz 200; `/finance/porders` 302 (the gate). These were untouched, md5s compared: finance_app.py,
  portal.py, tile_grants.json, porders.py, porders_s454.py, order_sheet.py, supplier_msg.py, purchase_app.py, marg_take.py,
  signatures.json.
- **WALK_S454P1D GREEN — 3 of 3.**
  - The cron's own command, run as a script on a scratch copy, exits 0 with the S454 pass in its JSON. **Negative control:** the live file
    fails with the same NameError.
  - Imported in-process, the module exposes the same names.
- **One live tick by hand after placing** (16:35:29 IST) exited 0:
  `{"slot": "none", "s454": {"sheets": 0, "withdrawn": 0, "refresh": 0, "ties": 0, "marg_lines": 0}, "notice": {... "why": "not yet"}}`.

### Part 1C · P1C_SHEET_PAGE_AND_PHONE (brief §17; install log 03-Oct, placed 15:36:14 IST by the files' own time)

| file | FROM | TO (md5sum after placing) |
|---|---|---|
| /root/finance/supplier_msg.py | fc6c1724d6da4e1d04897b60d61c13b8 | 2f43af754a160376cec955f92f3aa43a |
| /root/finance/porders_s454.py | 05716f3c040478d09fd2016561c7c99c | c2608914e56b0f7ce049d93aeed23d39 |
| /root/finance/order_sheet.py | 93f55d87730e749d78ea5561de38266f | cffbeef3f4405132ab1861ffc146bea9 |
| /root/finance/order_sheet_pdf.py | 9c28df38435a25d7e1d65c34b8d43ec9 | 6e7a5e1a7ae68cb4548c8c8f15cf27cb (v1.1, replaced whole) |

- **Health:** finance healthz 200. `/finance/porders`, `/finance/porders/s454/sheet.pdf` and `/finance/purchase/page/phone-setup`
  answered 302 (the login gate, expected). Nothing logged "NOT mounted" and there was no traceback. These were untouched, md5s compared
  before and after: finance_app.py, portal.py, tile_grants.json, porders.py, order_rules.py, purchase_app.py, sanjeevni_approvals.py,
  marg_take.py, signatures.json, amir_day.py, reports_tile.py.
- **Backups:** `finance.db.bak_S454_20261003_153557` (backup API); `supplier_msg.py.bak_S454_fc6c1724`, `porders_s454.py.bak_S454_05716f3c`,
  `order_sheet.py.bak_S454_93f55d87`, `order_sheet_pdf.py.bak_S454_9c28df38`.
- **Restarted:** clinic-finance only (ActiveEnterTimestamp 15:36:14 IST).
- **Data steps (`data_s454p1c.py`), as printed:**
  - payment messages as found: waiting 0 · sent 18 · failed 0 · skipped 0 (17.6: reported, none changed);
  - 17.9: message 1 read `sent` by `reception-phone` at 2026-10-03T15:00:27, so it was put back to waiting (queued, attempts 0, sent_at /
    sent_by / last_try_at cleared, and handed_at cleared too so the phone may take it at once). Audit row `s454_msg_reset` with the reason.
    Message 2 left as it is;
  - 17.10: `order.phone_alive_min` 30 → 720 (audit `s454_setting`);
  - payment messages after: waiting 1 · sent 17 · failed 0.
- **What changed, in code:**
  - `order_sheet_pdf.py` v1.1: the page carries the whole open order (to order · in the WhatsApp line · awaited under "Maal aaya?",
    Order box ticked · old pending). Awaited = status `sent`, no bill scan tied — the screen's own rule — less any line Marg recorded
    (`supplied` set). Band boxes are ticked only when nothing of that supplier is left to order; a paper order ticks only its lines. The
    head line counts what is drawn. Names wrap inside the Item cell (never shortened). The old tag stays after the name when it fits,
    otherwise it takes its own line inside the cell. Phone numbers move to a second band line when they would reach the boxes. The foot
    wraps. A block is never split (one longer than a page is continued with "(aage)"). **One page holds 33 one-line rows under one
    band.**
  - `porders_s454.py`: "1 medicine / supplier / bill" in the owner's English. The owner's "Reception phone" card, and two owner-only
    routes, `POST /finance/porders/api/s454/test_number` and `/test_send`. `order.phone_alive_min` accepted up to 1440.
  - `supplier_msg.py`: kind `test` (month `test`). The queue hands a test first, once per gap, and never retries a failed test
    (`kind NOT IN ('order','test')`). `s454_card_facts`, `s454_save_test_to` (the number is never in the audit: only its digit count),
    `s454_queue_test`. The setup page's printed steps are now the macro as built (17.10).
  - `order_sheet.py`: the default `order.phone_alive_min` 720. The owner's line reads "for 12 hours".
- **The walk** (`walk_s454p1c.py`, on backup-API copies; NEW = built files, OLD = the box as it is): **WALK_S454P1C GREEN — 33 of 33.**
  - The live order: no text outside its cell or the margins (2 pages, 28 rows). **Negative control:** the page as installed fails on
    three old tags (01-09, 09-09, 25-09; they ran 8.0, 56.2 and 32.4 pt past the Item cell) and on the foot (it ran to x 602.5 against a
    margin of 561.3).
  - Every awaited line is on the page with its Order box ticked: 16 of 16. **Control:** 0 of 16.
  - The head line, "Order: 02-10-2026 · Darpan (Marg) · 10 supplier · 28 dawa: 2 order karna hai, 16 ka maal aana hai, 10 purane
    pending", equals the rows drawn. No band box is ticked for the paper orders.
  - Crafted: a 30-character name with an old tag, a long supplier name with two numbers, a supplier with none — no violation (control:
    the tag ran out). A long order: 4 pages, 79 rows, no supplier split, head = rows. `sheet_print_old = 0`: no old rows. A crafted scan
    of DEEPAM's bill tied order #2 and DEEPAM left the page.
  - "1 medicine", "11 medicines", "1 dawa" (control: "1 medicines").
  - The card: shown to the owner only (shavez, reception, darpan: no card, 403 on both taps); the key is not on the page. A bad number
    gets 400. Once saved, the number shows masked and is never in full on the page or in the audit. A test is kind `test` with two lines
    and the ₹ line. It is counted nowhere else (payment list, pending, the setup page's count, the reception counts, order messages, the
    owner's lines: all unchanged). It is handed first and once, and its JSON keeps the line break and the ₹ to the saved number. "Sent"
    shows queued · handed · sent with times. No staff screen shows it. "Could not send" shows the reason and the test is never re-handed.
  - **Queue parity:** the same 7 rows in the same order, NEW = OLD: [19, 20, 21, 22, 23, 24, retry 21]. These are the walk's own rows,
    because the live queue was empty by then.
  - The 17.9 and 17.10 steps, each idempotent. Message 1 is left alone when it reads otherwise.
  - Setup page: the new steps are present, and "ask again at once" and "5 minute" are gone (control: still there).
- **17.10, the lines when the phone has been dark for an hour:** the phone still counts as alive, the WhatsApp button stays enabled,
  and the owner has **no line**. An order message waiting more than an hour is withdrawn. The staff card then reads "<supplier> · 1
  dawa · WhatsApp nahi gaya — call kijiye". **Dark 13 hours with an order message waiting**, the owner reads: "The reception phone has
  not asked the server for 12 hours -- 1 order message(s) wait".
- **The macro's interval** as the setup page now states it: every 1 minute, one message per run. Ten messages take about ten minutes
  while the phone is awake.
- Picture: `deploy_kits/S454_BILL_REGISTER/P1C_SHEET_PAGE_AND_PHONE/pictures/17_reception_phone_card.html` (the walk's own made-up
  number, masked).
- **Noticed:** `purchase_app._s446_earlier_card` counts *every* kind in `supplier_msg` for an earlier month's "unsent". From November,
  an order message of October that was withdrawn (`skipped`) is not counted, but one still `queued`/`failed` would be. Test messages
  carry month `test` and are never counted. This is for Part 2, which patches purchase_app anyway: payment kinds only.
- A copy of today's printed sheet (it carries the phone book's numbers) is still in the git-ignored local
  `_scratch\S454_BILL_REGISTER\view\`. Its deletion was refused by the permission list, so it was left there. It was never published.

### Part 2 · P2_PAIRING_REGISTER (brief §5, §6, §7, §8, §12; placed 17:26:14 IST by the files' own time)

| file | FROM | TO (md5sum after placing) |
|---|---|---|
| /root/finance/purchase_app.py | 591432422d6b06af3dff886a8a0fc378 | 4eee14b5e41a70c9450ed5cf6ff0bd29 |
| /root/finance/porders.py | d4842f2c0f40a6ff69bd9a6d0425778f | a5a823bf30661a4bf65ced39b2355500 |
| /root/finance/porders_s454.py | c2608914e56b0f7ce049d93aeed23d39 | e2228b8f8434e8ea3766b00e5e5e1a2e |
| /root/finance/order_sheet.py | cffbeef3f4405132ab1861ffc146bea9 | b2e61034790ea37fde4272859ccd1f58 |
| /root/finance/amir_day.py | 85f208d0d64def40fb5a02e02c531284 | 709f20c1078cbcb36fc1108e452c40c1 |
| /root/finance/reports_tile.py | 8a9870414cf299b0396bec4bc937ef04 | 9d2244a6d56d3791428982565f620a97 |
| /root/finance/scan_register.py | (new) | 8d100e60c467dab413830a251ef198fb |

- **Health:** finance healthz 200. These answered 302 (the gate, expected): `/finance/porders`, `/finance/purchase/page/scans`,
  `/finance/purchase/page/pay`, `/finance/amir`, `/finance/reports/aaj`, `/finance/purchase/page/sarvam`. No "NOT mounted", no traceback in
  the journal since the restart. Untouched, md5s compared before and after: finance_app.py, portal.py, tile_grants.json,
  sanjeevni_approvals.py, packs.py, asset_register.py, item_alias.py, stockmatch.py, stock_app.py, stock_watch.py, supplier_msg.py,
  order_rules.py, darpan_kal.py, marg_take.py, signatures.json.
- **Backups:** `finance.db.bak_S454_20261003_170649` (backup API); `purchase_app.py.bak_S454_59143242`, `porders.py.bak_S454_d4842f2c`,
  `porders_s454.py.bak_S454_c2608914`, `order_sheet.py.bak_S454_cffbeef3`, `amir_day.py.bak_S454_85f208d0`, `reports_tile.py.bak_S454_8a987041`.
- **Restarted:** clinic-finance only (ActiveEnterTimestamp 17:26:15 IST).
- **Every block sits above its file's `__main__` guard** (purchase_app.py, reports_tile.py have one). This is the lesson of 1D: the nightly
  `purchase_app.py rematch` cron runs the new rules.
- **The data step (`data_s454p2.py`), as printed:**
  - settings: purchase.entry_mode = paper · total_noise_rs = 10 · scan_wait_days = 3 · entry_wait_days = 7.
  - the matcher: 67 links stored (were 63) · 4 new · 0 dropped. Reasons: amount_differs 3, dup 1, no_bill_yet 8, number_differs 1,
    vendor_unknown 3.
  - The 4 new links (AUTO): L.K. DRUG HOUSE 75904 Rs 4,440 ← scan #33 · L.K. DRUG HOUSE 78354 Rs 1,199 ← #42 · ESSENTIAL PHARMA EP002243
    Rs 2,415 ← #48 · SAISUN PHARMA IP006767 Rs 8,479 ← #88.
  - returns.pending_ok = 3|2026-09-02.
- **§5's report on September** (`rules_report_s454p2.py`, scratch copies, before anything was placed): **RULES_REPORT GREEN**, no new pair is
  suspect.
  - The 63 links before the pass: Verified 53 · Has its scan 4 · Amount differs 6.
  - New pairs by the rules: 4 (OLD made 0), the four above. In each, the scan's one item line is the Marg bill's line. The scans misread the
    bill number ('KT-475964', 'RT-47834', 'EP012243', '6387') and three of them the year.
  - Links dropped: none.
  - Questions: "Is this the bill?" 8 → 4 · "Match the amount" 4 → 6 (513 MANNAT +Rs 40, 535 KEDAR +Rs 243 added: within 2%, beyond Rs 10)
    · "Choose the supplier" 3 → 3 · second scans 1 → 1 · S441's 6 → 6.
  - **The register of September, read on the live box after the install:** verified 53 · has_scan 8 · amount_differs 6 · no_scan 12 · double
    1 (a000163 / A000163) · accepted 0. 61 of 80 settled. Scans with no Marg bill: probably 4, vendor 3, second 1. October: 8 scans
    waiting for Marg, no Marg bill yet.
- **§7.4 The Sarvam counter for September, by the rules** (67 linked bills): misread supplier 4 · bill no. 8 · date 13 · total 10 · item
  lines 78 of 158 read right. Batch and expiry are not judged (with them it was 28).
  - Supplier, row by row: DRUG DEAL 5207 (scan B-0034 read the shop's own name 'SANJEEVINI MEDICOS'), DEEPAM PHARMA 601 (B-0072, 'M/S
    SANJEEVANI MEDICOS'), DRUG DEAL 5620 (B-0073, the heading 'WHOLE SALE CHEMIST & DRUGGIST'). These three are the shop's name or a heading:
    not read.
  - GUNINA 65194 (B-0038, 'GUNINA PHARMACEUTICALS P.L. LTD.'): the rule drops a standalone P / PVT / LTD / CO / M/S, but "P.L." leaves an
    "L", so by the brief's rule as written it differs. It is the same supplier. Adding "P.L." to the drop list is the chat's call; I did
    not widen the rule.
  - Bill no. (8): the four above, YOGENDRA 15496 ('7615486'), DEEPAM 856 and DEEPAM 623 (the licence '21/2014/BLY', '217/2014/BLY'),
    YUVIKA SURGICALS 672 ('15/0823/2026-27': 672 is no whole digit run of it). Date (13): mostly the year (2024/2025 for 2026). Total (10): e.g. GUNINA 71226 read 1,52,618 for 14,908; KEDAR 185 read 16,760
    for 18,700.
- **The walk** (`walk_s454p2.py`, NEW = built files, OLD = the box as it was; backup-API copies; walk-only portal secret and users):
  **WALK_S454P2 GREEN — 44 of 44.**
  - R, the rules: suppliers, bill numbers (series/prefix/brackets agree; licence and financial year never), dates, states, noise.
  - L, September's real data: no link lost; the four auto-links (**NEGATIVE:** the box as it was pairs none). One candidate pairs and two
    of the same amount ask. A wrong paper scanned from a line settles nothing. The intake link carries the supplier only (**NEGATIVE:** the old
    one carried the number and the amount).
  - Q, G, S: the amount questions [513, 518, 519, 523, 528, 535] equal the register's "Amount differs". The register is one state per bill,
    headed as parked, with no accept tap on a parked month and no Roman Hindi (**NEGATIVE:** no register on the box as it was). A counted
    month's accept is the owner's only, and audited; Undo restores. The Sarvam head equals the register's foot.
  - A, Amir: "Scan ho chuke bill (N)" on paper (**NEGATIVE:** the old words). S452's words on `both`; `digital` refused. His paid-NEFT
    sheet has no account number.
  - V, Vendor payments: amir, darpan, bhati and the reception login get 403 (or the 302 gate) on the page, the month, the letter, the
    advice and the pack, with no link and no account number or IFSC on any page they can open (**NEGATIVE:** the box as it was opened them
    to the staff). Shavez and the owner: as before. The phone book shows Darpan the last 4 digits, no IFSC, and refuses him a bank edit.
    The reception phone's keyed queue: unchanged.
  - D: manoj.returns_ok = the owner's own line (3 = 3; **NEGATIVE:** 7 vs 3 on the box as it was).
  - N: "Bill scan waiting" after 5 days for the owner, and "Bill scan baaki" for Shavez, both gone once paired. "Scanned and not yet in
    Marg for more than 7 days" for the owner only; Amir gets nothing new.
  - E: the staff-eye walk with DUTY_MAP v5 for reception, darpan, shavez, amir and the owner — every tile on its home, every due duty's
    marker on its door.
- **The earlier walks** (S403, S407, S410, S414, S417, S428, S439, S440, S441, S444, S446, S452), each copied to scratch and run twice: on the
  box as it was and on part 2's files. **WALKS_OLD_S454P2 GREEN.**
  - S403 13 reds, S407 5, S410 3, S414 1, S417 4, S428 8, S441 6, S444 14, S446 14: every one is red word for word on the box as it
    was too (their own controls are gone, plus today's data).
  - S439 23 = 5 as before + 18 intended. S440 27 = 7 + 20 intended. S452 11 = 9 + 2 intended. The intended ones, named in the log one by
    one with their reason:
    - I1: the same pairs, now made by the rule "verified (S454 5)" (the grade and rule words changed, never the pair).
    - I2/I4/I6: the walks' crafted near-match scans (one supplier, one amount, the only unscanned bill) are now paired by the auto-link.
      Their questions, answers and "open" lines no longer arise, and the groups' counts follow.
    - I3/I5: a scan whose total differs is no longer paired by S439's vendor + bill-tail rule. It is asked, and the amount question is now
      beyond Rs 10, not 2%.
  - The old page's checks read `?legacy=1` (Q1–Q5). S452's walk runs with `purchase.entry_mode = both` (Q6).
- **§8, the addresses closed to everyone but the owner and `supplier_msg.senders`:** `/finance/purchase/page/pay`, `/page/pay/<month>`,
  its `/letter`, `/advice.xlsx` and `/pack`, and `POST /api/pay-letter`, `/api/pay-verify`, `/api/pay-line`. The phone book page and
  `api_book` mask the account (last 4) and the IFSC/UPI, and refuse bank edits and verification to others. `_book_nav` draws the
  Vendor payments link for them only.
- **Found by the staff-eye walk, on live data (16:40 IST):** `amir.arrival_bill_entry` was due the minute an arrival was tapped (line 18,
  arrived 16:32), but its door (stock_watch's "bill entry baaki" on Amir's card) waits `arrival.bill_grace_days` (3). In v5 its `due_sql`
  waits the same grace. I ran it read-only on the live database before writing it in: (0, None). The owner's line still comes at 3 days.
- **Also in this kit:** `purchase_app._s446_earlier_card` now counts payment kinds only (`neft`, `cheque`), as noted under 1C.

### Part 3 · P3_SHELF_FIGURE (brief §9; placed 18:17:11 IST by the files' own time)

| file | FROM | TO (md5sum after placing) |
|---|---|---|
| /root/finance/order_rules.py | 6587dc84941f4e53ccc39d0847812123 (1D) | 1729e971982d0823f8d33b3976fa4d74 |
| /root/finance/purchase_app.py | 4eee14b5e41a70c9450ed5cf6ff0bd29 (2) | 61e6d26abe52293883e37cc61b459da5 |
| /root/finance/stock_watch.py | 9cca2f2a9e86e6523b9fcefb4f6df3bd | b429660ddc9a5291e261c5fa6fe652c0 |
| /root/finance/stock_app.py | f14a1cfaf9a47b1199a0763ac47d1006 | 7e159de737c0ec03cea890053f1bcd58 |
| /root/finance/order_sheet.py | b2e61034790ea37fde4272859ccd1f58 (2) | ebe1eb4b327c1a784e20174cda0abd4b |
| /root/finance/porders_s454.py | e2228b8f8434e8ea3766b00e5e5e1a2e (2) | eadbc8d3582991fa36ef3fde83253126 |
| /root/finance/shelf_figure.py | (new) | 23c34ebb1149996e1053c26573077460 |

- **Health:** finance healthz 200. These answered 302 (the gate): `/finance/porders`, `/finance/porders/s454/order`,
  `/finance/stock/page/count`, `/finance/amir`, `/finance/purchase/page/scans`. No "NOT mounted", no traceback. Untouched, md5s compared
  before and after: finance_app.py, portal.py, tile_grants.json, sanjeevni_approvals.py, packs.py, asset_register.py, item_alias.py,
  stockmatch.py, supplier_msg.py, porders.py, amir_day.py, reports_tile.py, scan_register.py, darpan_kal.py, marg_take.py, signatures.json.
  The duty map is unchanged: the owner's gap line is a Needs-you line, and the roster reason sits inside darpan.spot_count.
- **Backups:** `finance.db.bak_S454_20261003_175504` (backup API); `order_rules.py.bak_S454_6587dc84`, `purchase_app.py.bak_S454_4eee14b5`,
  `stock_watch.py.bak_S454_9cca2f2a`, `stock_app.py.bak_S454_f14a1cfa`, `order_sheet.py.bak_S454_b2e61034`, `porders_s454.py.bak_S454_e2228b8f`.
- **Restarted:** clinic-finance only (ActiveEnterTimestamp 18:17:12 IST).
- **The crons' own commands as scripts** (the lesson of 1D): `order_rules.py tick` and `stock_watch.py job` exit 0 on the built files
  (scratch copies). The tick's JSON carries `"gaps": 372`. One live tick by hand after placing (18:17:21 IST) exited 0, with `"gaps": 0`
  (the data step had just recorded the closing). Every block sits above its file's `__main__` guard.
- **The data step:** order.stock_basis = count · stock.gap_min_packs = 1.
  - Gap rows at Marg's closing of 2026-10-02: 372 written · flagged 0 (the first closing has nothing to compare with) · approximate 22 ·
    shelf and Marg a pack or more apart: 166.
  - The figure by kind: counted 367 · below_zero 5 · no_count 6.
  - The boundary report (9.1): one base after 09:00 IST, the count of 06-09 at 14:41, with 0 bills that day.
- **Found while building, on live data, and repaired in this kit: the count-day boundary for purchases.** A bill dated on (or up to 7 days
  before) the count day but entered in Marg after the count was missed.
  - PANSPED L: counted 0 at 14:41 on 06-09; its 1,000-tab bill of 06-09 came in later. The figure read 0 against Marg's 726.
  - SHELCAL XT: a bill of 05-09 for 300 (figure 0 against Marg's 123).
  - The fix: Marg's own figure at the count (`marg_qty`) settles it. What Marg gained since the count, beyond its sales, returns, later
    purchases and the count's vouchers filed, is such bills. They are taken in newest first while they fit that gain, within one pack.
  - The 6-Sep count is older than the first purchase export on the server (11-Sep), so no export time can tell. On 03-Oct the repair
    touches 3 of 378 items: PANSPED L +1,000 (now 726), SHELCAL XT +300 (now 123), DECA INSTABOLIN 50 +10 (Marg read −3 at the count,
    3 now; the shelf figure is 8).
  - Every other item checked by hand reconciles exactly as Marg + (counted − Marg at the count): CHYMORAL AP, DEFVAX 6, PATOPAN DSR,
    XYCAL K2, TYRO BR.
- **Found while building, and repaired for `count`: Part 1 counts an order that arrived by its scan twice on the system's list.**
  - Part 1's `_s454_or_arrived` keeps such an order "on the way". `order_sheet` also marks it `received`, so `purchase_app._in_transit`
    counts it as well. Live: 6 such orders, all with unanswered lines.
  - On `count` (the default now), on the way = a sent order not arrived. A counted item has the arrival inside its shelf figure. An item
    with no count has it once, through `_in_transit`.
  - On `marg` the old way stands, because the brief asks for today's plan line for line there. The walk shows the double count there as its
    negative control.
- **§9.4, the report** (`report_s454p3.py`, scratch copies, Darpan's sheet of 02-Oct with its own paper orders taken off the copy, as 1B
  did; stock as on 02-10-2026):
  - **The system agreed on:** OLD (the box as it was, Marg's stock) **5 of 21** · NEW on marg (the 20-character repair only) 5 of 21 · NEW
    on count (the default) **9 of 21**.
  - On both (count): TENDOZAC TAB, VERC 16, CCM, DFO MR, VOLITRA APS SPRAY, MEG QCS, CROCAL, OSTOVAXL DM, PREGHYPE NT TAB.
  - Only on Darpan's sheet (12), with the plan's own reason:
    - enough cover by the shelf figure: CHYMORAL AP 80 (Marg 106) 11 days · LONAC AQ INJ 12 (33) 26 days · PRETOL-4 31 (137) 22 days ·
      RANIMIG 150 113 86 days · NARCOGEN FORTE 54 (89) 20 days · PANTOCID DSR 92 (126) 21 days · DECA INSTABOLIN 50 8 (3) 56 days ·
      CEECIT MZ 115 (123) 20 days · AURAB L CAP 71 (115) 15 days · FENARIC T4 TAB 73 (84) 21 days;
    - KT ROS DT: no Marg purchase of it on the server, so no supplier to list it under;
    - PRETOL 8: bought last from KEDAR PHARMACEUTICAL, not SHIVAAZ FORMULATIONS.
  - Only on the system's list (28). Among them: XYCAL K2 (shelf 30, Marg 12), TYRO BR (shelf 0, Marg 114), DEFVAX 6 (2 / 69),
    PANTAVIN 40, TOLTRIS PLUS, and the old pending NUPTACH 200, OPTIFENAC TBR and UPRISE 6L INJ. The full list with its reasons is in the
    install log's [6/13]. PANSPED L (50 strips) and SHELCAL XT (10 strips) were on it before the boundary repair, and are off it now.
  - **The three suspected gaps of §2.4:**
    - (1) a line tapped "Aa gaya" while its order is still "sent": 0 such lines, not proven, not changed.
    - (2) `_in_transit`'s exact-name match: 0 received lines missed, not proven, not changed.
    - (3) `_pace` keys sales by the 20-character name: 5 medicines with longer names, with a pace OLD 0 → NEW 2. **Proven, repaired** (on
      count; on marg the plan stays today's).
- **The walk** (`walk_s454p3.py`, NEW = the box after part 2 + part 3's files, OLD = the box after part 2; backup-API copies; walk-only
  portal secret and users): **WALK_S454P3 GREEN — 26 of 26.**
  - F, the figure: counted 100, 30 sold, 20 bought, 2 returned = 92 whatever Marg says (555). +10 arrived by a scan = 102. A later spot
    answer is the base (98). A part of the count family (40). No count = Marg's, named. Below zero = 0, named. Two items on one key share
    by counted share (30/20, approximate).
  - The boundary: a count-day bill entered later is in (0 − 30 + 100 = 70). A bill Marg already had is not added twice (40).
    **NEGATIVE:** without it the item reads below zero.
  - P, the plan: on marg it is part 2's plan line for line (23 lines). On count, both figures are on the lines and no staff screen prints
    them. Goods received and not in Marg: once on count. **NEGATIVE:** twice on marg. The long-name medicine gets its line (**NEGATIVE:**
    the box as it was never lists it).
  - W: a spot answer is compared with the shelf figure (102; **NEGATIVE:** the box as it was had none). A recorded count stores the shelf
    figure beside Marg's; the loss desk is still by Marg (−460).
  - G, the gap: constant three closings, no flag. Closed by a filed voucher (+20), no flag, gap 0. A pack moved with no voucher: flagged,
    and it stays flagged. An approximate item is never flagged. The owner's line, the card, and one more roster reason, within the cap.
  - E: the staff-eye walk (DUTY_MAP v5) for reception, darpan, shavez, amir and the owner. Clean.
- **The earlier walks** (the same twelve; part 2's adjustments now on both runs): **WALKS_OLD_S454P3 GREEN.** Every walk's reds are the
  same, word for word, with and without part 3: S403 13, S407 5, S410 3, S414 1, S417 4, S428 8, S439 23, S440 27, S441 6, S444 14,
  S446 14, S452 11. Part 3 moved nothing they check.

### Published and checked on the box
- PUBLISH_ALL: the part-1 folder went out in another session's publish at 12:20 (722f564, S458/S459's), unchanged since. 1B, this
  report and the duty map went out in d43f0c1 (12:32).
- On the box, `/root/deploy/repo` was pulled `--ff-only` to d43f0c1 at 12:33:04 IST. Both part folders pass `md5sum -c` (48 and 6
  files) and match, by `diff -r`, the copies that ran. No `__pycache__` or `.pyc`. The NO_PHONE_NUMBERS gate is clean (63 files).
- The owner's Needs-you, as the live code builds it with v4 (on a backup-API copy):
  - no duty-map orphan line;
  - "Orthotic shortages: 2 items -- order not sent": Yuvika's order has arrived, and the 2 short items are on no open order;
  - "18 supplier messages unsent (30 min or more)";
  - the rest are unrelated lines, as before;
  - September's "Bill scan pending on 18 purchase bills" and S410's "Order not sent: Kedar …" are gone, by design.

- **Part 2:** published in 306b4c4. On the box, `/root/deploy/repo` was pulled `--ff-only` at 17:30:17 IST. `P2_PAIRING_REGISTER`
  passes `md5sum -c` (13 files) and is identical (`diff -r`) to the copy that ran. `claude_code_briefs/DUTY_MAP.json` / `.md` there read
  27d9d1b5… / ffd37cfe… (v5). All 45 duties' `due_sql` run on the live database (read-only) with no error. Due now includes
  manoj.returns_ok = 3 and reception.order_arrival = 4; amir.arrival_bill_entry is not due (its one arrival is inside the grace).
- The build lock was taken at 12:05:29 IST (owner S454_BILL_REGISTER) and released at 12:34:05 IST. Finance healthz was 200 and
  clinic-finance active at release. `/tmp/s454p1` (the owner's sheet, scratch copies) and `/tmp/s454w` were removed.

### Duty map
`claude_code_briefs/DUTY_MAP.json` / `.md` are now v4 (5a415824 / 758c8345), the same bytes as the kit's:
- reception.medicine_orders: source-aware, door "Order karna hai".
- reception.order_arrival: "Maal aaya?".
- reception.bill_scan: counted months only.
- reception.scan_questions: "Photo dekh kar bataiye".
- shavez.supplier_messages: payment kinds only.
- **darpan.order_sheet (new):** a refused sheet, door *Kal ka hisaab*, marker "Order sheet adhoori thi". The owner's line is the
  existing "order sheet refused today" Needs-you line.

Every due duty's door was seen in the staff-eye walk.

**Part 2: v5** (27d9d1b5 / ffd37cfe), the same bytes as the kit's `P2_PAIRING_REGISTER/DUTY_MAP.*`:
- manoj.returns_ok: its `due_sql` reads setting `returns.pending_ok`. amir_day writes it when the owner's Needs-you is built, from the
  owner's own rule (`returns_kinds`, `returns.act_from`). Duty 3 = owner line 3 today.
- reception.bill_scan: the owner's line comes only after `purchase.scan_wait_days`, from `scan_register.owner_lines`.
- amir.scan_files (new): never due. Its door is step 2's "Scan ho chuke bill". Amir is asked nothing new.
- amir.arrival_bill_entry: due only after `arrival.bill_grace_days`, as its door (above).
- Shavez's "Bill scan baaki" line on Aaj ki reports and the owner's register are in the .md.

### Not done, and why
- **Part 4 (§10, the medical PC's refusal note) and Part 5 (§11, the items) are not started.** The brief forbids replacing the medical
  PC's watcher before 04-Oct 13:00 IST (§10.3), and Part 5 follows Part 4 in its order. I did not install half of Part 4 (the server door
  without the watcher) tonight. Until Part 4 is in, a sheet the medical PC itself refuses still reaches nobody (as said in Part 1).
- **Not built in Part 3, by the brief:** judging a full count by the shelf figure (the loss desk still judges by Marg). That is the next kit's.
- The reception phone was not set up; that needs the owner's login on that phone. The phone has not asked since S452
  (`supplier_msg.phone_last` absent; 18 NEFT messages queued since 26-Sep 19:49).
- The approvals-page sentence about reminder times is **for the parent**: `finance_ui/finance_approvals.html` line 1255 still names
  09:00, 12:00, 15:00 and 17:00. S454 sends one reminder at `order.remind_times` (17:00) and none at 09:00 on `marg_sheet`.
- F-701 was not repaired; it is outside this brief.
- `.gitignore`: two exact-path exceptions were added for this kit's `DUTY_MAP.json` and `sig_entry_s454.json`, the same as S446/S452.
  The blanket `*.json` rule would hide them otherwise.

### Noticed outside the brief
- **S428's spine reading counts a credit note as a sale.** `stock_watch.Spine.sales` sums `sp_sale_line` units, and a CN bill's lines
  carry positive units (they are returns). The shelf figure reads `sp_move` (SALE / SALE_RETURN apart) and is not affected. S428's own
  pace and expectation are. Not changed: outside this brief.
- **Part 1's double count on `marg`** (above, under Part 3): mended for `count`, the default. On `marg` it stands, as the brief asks for
  today's plan there. The chat may want it mended there too.
- **GUNINA's "P.L. LTD."** is counted a supplier misread by §5's rule as written (above, under Part 2). Adding "P.L." to the drop list is
  the chat's call.
- **PUBLISH_ALL commits everything pending.** Part 2's publish (306b4c4) also carried three kits other sessions had left in the working
  copy: S465_PAPERS_JOIN, S466_EXPENSE_WARRANTY and S467_WARRANTY_ON_HEALTH. I did not open, run or change them. They passed the
  NO_PHONE_NUMBERS gate with the rest (40 files).
- The medical PC heartbeat says "BACKUPS: 6 kit backup files are lying about - the prune is not working", and Drive
  `ToMedical\_kit` holds a `__pycache__` folder dated 25-Aug. Neither was touched.
- S458's medical-PC reinstall kit (`deploy_kits/PC_KITS/medical/kit.zip`, packed 03-Oct) carries `marg_txt.py` 70f920c4 (S446). Its
  installer only fills what is missing, and the Drive agent then brings ed17bb76. Still, the next repack should take the S454 reader.
- B-0113's supplier reads "KEDAR PHAMACEUTICAL" (a misread). It was tied through a **learnt spelling**: `purchase_scan_alias` already
  maps it to KEDAR PHARMACEUTICAL. That is the brief's rule, not a similar spelling.

```
https://followup.dr-manoj.in/finance/porders
```

```
https://followup.dr-manoj.in/finance/purchase/page/scans
```
