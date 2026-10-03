# REPORT S454 — S454_BILL_REGISTER · Part 1 of 5 (with its fixes 1B and 1C) · installed 03-Oct-2026 12:24 IST (1B 12:28, 1C 15:36 IST) · published

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

### Not done, and why
- Parts 2–5 are not started; they come with the second line. The watcher is not replaced: Part 4, not before 04-Oct 13:00 IST.
- The reception phone was not set up; that needs the owner's login on that phone. The phone has not asked since S452
  (`supplier_msg.phone_last` absent; 18 NEFT messages queued since 26-Sep 19:49).
- The approvals-page sentence about reminder times is **for the parent**: `finance_ui/finance_approvals.html` line 1255 still names
  09:00, 12:00, 15:00 and 17:00. S454 sends one reminder at `order.remind_times` (17:00) and none at 09:00 on `marg_sheet`.
- F-701 was not repaired; it is outside this brief.
- `.gitignore`: two exact-path exceptions were added for this kit's `DUTY_MAP.json` and `sig_entry_s454.json`, the same as S446/S452.
  The blanket `*.json` rule would hide them otherwise.

### Noticed outside the brief
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
