# REPORT S619_ORDER_TRACKER — 22-Oct-2026 (installed; clinic-finance restarted 13:21:04 IST, the box's clock)

**For you (Dr Manoj):**
1. **One order list for you and Shavez** — on your Purchase-orders home, a card "The order list: N late · M came short · K scans to redo" opens it: every order since 12-Oct with its five steps (Ordered → Arrived → Bill scanned → In Marg → All lines came), sections for not arrived, bill scanned but not in Marg yet, came short, scans to redo, bills saved under another dealer, and complete. Yours is in English, Shavez's the same list in Roman Hindi; nobody else can open it.
2. **Late = two days after ordering (Sunday not counted), at 6 p.m.** Reception now sees "Order ka maal nahi aaya — call karo" with the dealer, a Call button and "Maal aaya" — including part orders, as you said. Every WhatsApp order now ends with your delivery line ("Kripya maal dopahar 3 se shaam 6 baje ke beech, ya subah 11 baje tak bhejein."), and both printed sheets carry it once.
3. **A medicine that did not come now goes back on that dealer's next order by itself** — shown on the card as "pichhle order se baaki (date)", in the WhatsApp and on the paper. Today **7 medicines** were put back this way (THIO Q AP, ZUPRINOR 5, C2CALZ, FLACORT 6, POWERGESIC 100 PATCH, XGESIC LA, LINVIZ 600). They ride on the dealer's next order; they do not make an order on their own.
4. **Darpan** reads one line on Kal ka hisaab, e.g. "20-10 ke order: 9 supplier ka maal aa gaya, 1 ka aana baaki — 22-10 shaam tak · 3 dawa nahi aayi — agle order mein khud jud gayi." Nothing for him to tap. Reception's "remove" on a dealer's line now asks why: "Dealer ke paas nahi hai" (it comes back when Darpan's next sheet still has it) or "Abhi nahi chahiye".
5. **Today's numbers differ from the mock-up** because the data moved this morning: Marg entered the 20–21 Oct bills at 09:40 and reception marked Verma (53) and Bass (55) "Nahi mila" at 12:29. So now: **1 order not arrived** (Yuvika, 20-10 — late from 6 p.m. today if it does not come), **10 orders with something short**, 1 bill scanned and waiting for Marg (Shivaaz 12-10, whose scan is actually a Kedar paper). Drug Deal 16-10 shows "arrived, XGESIC LA short".
6. **It is live and working.** Everything was tested on copies first (82 checks green; the same test on the old files went red on all 29 controls). Cost: about $15 of the $90 budget when this was written.

---

## For the chat

### FROM → TO, read back on the box (`md5sum`, 13:21, after placing)
| file | FROM | TO (read back) |
|---|---|---|
| /root/finance/order_sheet.py | ff9375f98c46f0a004a02a3582693a83 (S618's TO) | 1bba95ab52126a2e354ba8eca7bfe8f6 |
| /root/finance/porders_s454.py | 4d1506480b2b1388ae1020c302e71a84 (S618's TO) | 53ef850f5c337f44f3d24e1ca83dd960 |
| /root/finance/darpan_kal.py | d6ba4882b5f8c4d365016eff87ddba52 | 6159b75b09257d5087111f6aebac611a |
| /root/finance/darpan_kal.html | c0ddc0eaa167b78bbb39bcebbb53c1b0 | 81dbb26a02043562bac6476326d9b9ed |
| /root/finance/order_sheet_pdf.py | 7a6d47c040536a24407ebfbb91d171e1 | 7dc646c6294b576dd2e09673bdc9d8ed |
| /root/finance/marg_order_pdf.py | bdcf2d00f303a6932c9d1ffe686afffa | abd410e19f60807d1876d10e2c7ad5e6 |
| /root/finance/order_track.py | (new) | a8c46700c4d3e2cbbb48767b6c46fa65 |

**Pins.** All six FROM pins matched at the open (12:26 IST) and at the installer's gate (13:14:00). Read-only files, matched both times: porders b1736494 (S613's TO), supplier_msg 4e3911a7, purchase_app 447b745f, stock_figure 8c66b6b1 (S613's TO), stock_watch f0d9092a, amir_day 1169a3d6, order_rules 8d078dbe, item_check 6f3faf89, sanjeevni_approvals 792f4a9a, owner_console 2b985708, /root/shared/scan_quality.py 16fb2402 (S618's TO), /root/assetapp/asset_register.py 70e35b10 (S618's TO); printed: scan_register.py 904f07b1. Proved unmoved at the end: finance_app.py, portal.py, tile_grants.json, the crontab (84 lines), every published `deploy_kits/S5*`, `S6*` folder (one hash, before and after).

**Builder.** `make_s619.py`: 49 anchored edits on the live bytes, each anchor found exactly once; rebuilt on the box at the gate, each file at its TO pin. The kit in `deploy_kits/S619_ORDER_TRACKER/` is byte-identical to `/tmp/s619kit`, which ran (SUMS.md5 checked on the box before the run).

**Backups.** `finance.db.bak_S619_20261022_131400` (42,676,224 bytes, sqlite backup API); `.bak_S619_<from8>` beside each of the six replaced files.

**Database.** `order_sheet.ensure` on live after placing: table `order_carry`, column `s454_line_edit.reason`, the five settings (`order.deliver_days` 2, `order.deliver_skip` SUN, `order.deliver_window` 15:00-18:00,-11:00, `order.wa_delivery_line`, `order.track_since` 2026-10-12). The first carry pass (`order_track.carry_pass`, keyed by line — the step `cron_pass` runs on every tick and page read): `{'written': 7, 'done': 0, 'dropped': 0}` — rows 1–7: (22 THIO Q AP 10 strips), (24 ZUPRINOR 5 4 pcs), (25 C2CALZ 2 strips), (25 FLACORT 6 20 strips), (33 POWERGESIC 100 PATCH 5 pcs), (34 XGESIC LA 20 strips), (38 LINVIZ 600 10 strips), all `marg_short`. No DELETE, no hand edit.

**Service.** clinic-finance restarted once at **13:21:04** — healthz 200; /finance/porders, /s454/late, /s454/track, /darpan/kal/api/day answered 302 to a plain curl (the login gate, expected); journal clean (no Traceback / ImportError / NOT mounted). `DOCTOR_AUTO_OFF` written before, removed after. Nothing else restarted.

**The duty map's SQL on live, after (read only):** reception.order_arrival `0 None` (Yuvika 54 is due 22-10 18:00); reception.medicine_orders `0 None`; reception.bill_scan `2 2026-10-05`; shavez.order_followup `7 2026-10-22` (the 7 open carries).

### The section 4.1 table — live, 13:21:08 IST (after; identical to the 12:59 / 13:14 "before" except the carries)
```
 21 A.A. PHARMACEUTICALS   12-10 complete  scan B-0158, in Marg, 3 of 3 came
 22 DEEPAM PHARMA          12-10 short     scan B-0154, in Marg; THIO Q AP 10 strips short
 23 GUNINA PHARMACEUTICALS 12-10 complete  scan B-0155
 24 JANTA PHARMACEUTICALS  12-10 short     scan B-0156; ZUPRINOR 5 4 pcs short (billed 2 of 6)
 25 KEDAR PHARMACEUTICAL   12-10 short     scan B-0157 (+ B-0146 through Marg's bill); C2CALZ 2 strips, FLACORT 6 20 strips short
 26 L.K. DRUG HOUSE        12-10 complete  scan B-0186
 27 MANNAT PHARMA          12-10 complete  scan B-0152
 28 SHIVAAZ FORMULATIONS   12-10 awaiting  scan B-0161 (a Kedar paper: conflict note in the full half), not in Marg; TOLTRIS PLUS waits for Marg
 29 YUVIKA SURGICALS       12-10 complete  scan B-0174
 30 BASS PHARMA            12-10 complete  scan B-0148
 31 DAANSHI PHARMA         12-10 complete  scan B-0153 (set aside; its head B-0151) + B-0151 through Marg's bill
 32 A.A. PHARMACEUTICALS   16-10 complete  scan B-0185
 33 DEEPAM PHARMA          16-10 short     scan B-0187; POWERGESIC 100 PATCH 5 pcs short
 34 DRUG DEAL              16-10 short     arrived 17-10 18:20 by scan B-0182 (through Marg's bill 6579), in Marg; XGESIC LA 20 strips short
 35 ESS KAY AGENCIES EXTN  16-10 complete  scan B-0188
 36 GUNINA PHARMACEUTICALS 16-10 complete  scan B-0172 (+ B-0177 through Marg's bill)
 37 JANTA PHARMACEUTICALS  16-10 complete  scan B-0169 (+ B-0170 through Marg's bill)
 38 KEDAR PHARMACEUTICAL   16-10 short     scan B-0180; LINVIZ 600 10 strips short
 39 L.K. DRUG HOUSE        16-10 short     scan B-0196 + B-0186; LANZOL JUNIOR 60 strips short (still on Marg's order: not carried)
 40 MANNAT PHARMA          16-10 complete  scan B-0173
 41 RADHA MEDICAL          16-10 complete  scan B-0181
 42 SHIVAAZ FORMULATIONS   16-10 complete  tap 17-10 11:41 (+ B-0178, B-0190 through Marg's bill); 3 lines 'tapped Nahi mila; Marg billed …'
 43 SHRADDHA MEDICOSE      16-10 complete  scan B-0171
 44 YOGENDRA AGENCIES      16-10 complete  scan B-0166
 45 YUVIKA SURGICALS       16-10 complete  scan B-0174 through Marg's bill 738; no longer asks for a scan
 46 A.A. PHARMACEUTICALS   20-10 complete  scan B-0200
 47 GUNINA PHARMACEUTICALS 20-10 complete  tap 20-10 17:22 (+ B-0193)
 48 KEDAR PHARMACEUTICAL   20-10 complete  tap 21-10 17:30 (+ B-0199)
 49 KRISHNA MEDICOS        20-10 complete  scan B-0198
 50 MANNAT PHARMA          20-10 complete  tap 20-10 17:23 (+ B-0194)
 51 SHIVAAZ FORMULATIONS   20-10 short     scan B-0192 (+ B-0195 through Marg's bill); PANTAVIN 40 12 strips short (on Marg's sheet 6: not carried yet)
 52 SHRADDHA MEDICOSE      20-10 complete  scan B-0201
 53 VERMA BROS. AND CO.    20-10 short     tap 22-10 12:29 'Nahi mila'; SILVEREX-HEAL 6 pcs short (on Marg's sheet 6: not carried yet)
 54 YUVIKA SURGICALS       20-10 NOT ARRIVED  due 22-10 18:00 (ANKLE BINDER BAMBOO M, RIB BELT UNIVERSAL UNISON)
 55 BASS PHARMA            20-10 short     tap 22-10 12:29 'Nahi mila'; DYNAPAR QPS PLUS 10 pcs short (on Marg's sheet 6: not carried yet)
```
Counts: 35 orders since 12-10 · not arrived 1 (54; late from 22-10 18:00) · part 0 · bill scanned, not in Marg yet 1 (28) · with a short line 10 (22, 24, 25, 33, 34, 38, 39, 51, 53, 55) · complete 23. **Why not the brief's "3 not arrived / 8 not in Marg":** Marg's detection at 09:40 today billed orders 46–52, and reception tapped 53 and 55 "Nahi mila" at 12:29 — after the brief was written. **Carries:** 7 written; PANTAVIN 40 (51), SILVEREX-HEAL (53) and DYNAPAR QPS PLUS (55) are still printed on Marg's newest open order (sheet 6, the sheet they were ordered from), so — by the same rule that keeps LANZOL JUNIOR from being carried twice — they are carried by the first pass after a newer Marg sheet stops printing them.

### The walk (walk_s619.py), on the box, scratch copies (backup API), 13:14–13:20 IST
Final lines: `WALK OK S619: 82 checks, 55 controls green on the new files` and `WALK OK negative control S619: 29 controls red on the old files` (0 green). Verbatim (the per-order table lines of section 1 are the table above):
```
   -- S619 walk on the new files: /tmp/s619_inst_20261022_131400/new/finance . db f619.db
      the real finance app loaded from the scratch folder; parts that did not load: none; order_track NEW (S619)
   -- 9 (first) nothing else moved: the pages, the plan, the test and payment bodies on the quiet copy
     ok   the page /finance/darpan/kal/api/day as darpan (200, 2119 bytes)
      unchanged on /finance/darpan/kal/api/day for darpan
     ok   the page /finance/darpan/kal/api/order as darpan (200, 1585 bytes)
      unchanged on /finance/darpan/kal/api/order for darpan
     ok   the page /finance/porders/s454/order as reception (200, 11990 bytes)
      unchanged on /finance/porders/s454/order for reception
     ok   the page /finance/porders/s454/scan as reception (200, 10759 bytes)
      CHANGED on /finance/porders/s454/scan for reception: 9 line(s) gone, 0 new
         - YUVIKA SURGICALS · 1 bill
         - 16-10 ka maal
         - Maal aa gaya, bill scan baaki
         - BASS PHARMA DISTRIBUTORS PVT LTD · 1 bill
         - 20-10 ka maal
         - Maal aa gaya, bill scan baaki
         - VERMA BROS. AND CO. · 1 bill
         - 20-10 ka maal
     ok   the page /finance/amir as amir (200, 7060 bytes)
      unchanged on /finance/amir for amir
     ok   the page /finance/purchase/page/pay as shavez (200, 73720 bytes)
      unchanged on /finance/purchase/page/pay for shavez
     ok   the page /finance/salecheck/api/days as bhati (200, 586 bytes)
      unchanged on /finance/salecheck/api/days for bhati
     ok   the page /finance/porders/s454/q as reception (200, 10043 bytes)
      unchanged on /finance/porders/s454/q for reception
     ok   the page /finance/stockmatch/api/state as manoj (200, 92807 bytes)
      unchanged on /finance/stockmatch/api/state for manoj
     ok   the page /finance/porders?old=1 as manoj (200, 49486 bytes)
      unchanged on /finance/porders?old=1 for manoj
      the order engine's plan md5 f6e5bc29; the payment and test bodies built (the WhatsApp's test and payment kinds)
     ok   the order engine's plan (order_rules.plan) is byte-equal to the OLD files' on the quiet copy
     ok   the test message's and the payment messages' bodies are equal to the OLD files' (untouched)
     ok   Bill scan karna hai changes only on purpose (3.3): rows 'dd-mm ka maal · Maal aa gaya, bill scan baaki' gone for orders that ask no more, nothing added
     ok   every page dump (Darpan's day less his order line and order tab's yesterday, reception's order list / q pages, Amir's page, the pay page, Bhati's sale check, the stock match, the owner's old page less S619's settings rows) is byte-equal to the OLD files' (0 differ)
   -- 1  the five steps on the copy (orders 21-55)
      the section 4.1 table, orders since 2026-10-12, now = 22-10 12:00 (computed here, by section 3.1's rules):
      not arrived at 22-10 12:00: [54] (late then: []); late at 22-10 18:01: [54]
     ok   C: the orders of 20-10 not arrived are not late at 22-10 12:00 and are late at 22-10 18:01 (two days, Sunday not counted, at 18:00): [54]
     ok   C: order 34 (Drug Deal 16-10) arrived -- its scan B-0182 through Marg's bill 6579 (the bill's link) -- with XGESIC LA short; OLD's Maal aaya hid it and named no short line
     ok   C: order 42's three lines tapped 'Nahi mila' came by Marg's figures, each with the note 'tapped Nahi mila; Marg billed ...'
     ok   C: 22, 25, 33, 38, 39 are short by name (THIO Q AP, FLACORT 6, POWERGESIC 100 PATCH, LINVIZ 600, LANZOL JUNIOR)
     ok   C: order 24's ZUPRINOR 5 is short by 4 (billed 2 of 6) -- '4 pcs'
      47, 48, 50 (the brief: 'arrived by tap, not in Marg' on the morning's copy): {47: ('tap', True), 48: ('tap', True), 50: ('tap', True)} -- Marg entered their bills at 09:40 today
     ok   47, 48, 50 arrived by reception's tap (their arrival moment is the tap's)
     ok   the light half reads finance.db only: light_all ran with no assets.db and no spine (every order has its five answers)
   -- 2  late and the delivery hours (synthetic orders, its own copy)
     ok   C: a Saturday order (17-10) is due Tuesday 20-10 18:00; a Sunday order (18-10) is due Tuesday 20-10 18:00
     ok   C: a part order (one line came by tap, one open) is late once its two days are past (20-10 18:01) and not before (17:59): part / part
     ok   C: a 'Maal aaya' tap at 19:40 -> the time shown (outside the delivery hours): '19:40'
     ok   C: a scan at 19:40 -> nothing (a scan's time never sets the mark); the order arrived by its scan alone waits for Marg, not late: '' awaiting late=False
   -- 3  the soft note: the 'not seen' rate; a note never moves a count
      the scan half: 53 pharmacy scans, 186 readings, scans to redo excluded [155, 157, 176, 180, 199]
     ok   C: a note never changes a count -- the tiles and every order's place are equal with and without the scan half
      GATE (a note, so no bar): on orders 21-45, Marg as the answer key, the false 'not seen on the scanned bill' rate is 27 of 54 Marg-billed lines (50%): 23 DFO 4X GEL, 23 GEN D3 NANO, 23 JAKMAC 5, 23 SHELCAL XT, 24 KETOROL DT, 24 ZUPRINOR 5, 25 FLUXIC P, 25 PATOPAN DSR, 25 ASTOFEN R, 25 C2CALZ, 25 LOFTYPRED 80 INJ, 26 SALAZAR DS, 27 ORICOX P, 29 TYNOR WRIST SPL LF L ELASTI, 30 DYNAPAR QPS PLUS,
     ok   the soft-note rate was measured on orders 21-45 (Marg-billed lines held against every usable scan of the dealer up to its next order)
     ok   order 28's tie (B-0161, a Kedar paper saved under Shivaaz) carries the conflict note and lights no 'Bill scanned' dot
     ok   'Saved under another dealer' lists B-0161 and B-0167 on the copy: ['B-0161', 'B-0167']
   -- 4  the tie: the Drug Deal case, the order-45 case, the stock effect
     ok   C: the order-45 case (received by Marg, every line billed, no tie) no longer asks for a scan (OLD asks)
     ok   C: an order whose only line was tapped 'Nahi mila' never asks for a scan (OLD asks)
     ok   C: the Drug Deal case (an old order whose only line is 'Nahi mila', a new sent order, a scan) -> the scan ties to the NEW order (OLD: the old one)
      the stock effect (stock_figure.scan_lines / porders._on_order count a scan-tied order's unanswered lines as stock): lines newly counted -- [(130, 'W619 XGESIC', 57)]
      the copy's replay: ties tie_pass made on the real scans -- none
     ok   the copy's replay makes the same real ties on the OLD and the NEW files (no real stock figure moves on the copy)
   -- 7a the papers on the quiet copy: Marg's order PDF and the order sheet carry the delivery line
      Marg's order PDF: 1 page(s); the delivery line found 1 time(s); the order sheet: 2 page(s), the line 2 time(s)
     ok   C: Marg's order PDF (Marg's rows as Marg printed them) carries the delivery line exactly once, after the last row
     ok   C: the printed order sheet carries the delivery line once in each page's foot (2 pages)
   -- 5  the carry: the five lines on their dealers' next cards, the WhatsApp, the paper; LANZOL JUNIOR not doubled; an order closes it
      carry_pass on the quiet copy: {'written': 0, 'done': 0, 'dropped': 0}; the carries: [(22, 'THIO Q AP', 10, 'marg_short'), (24, 'ZUPRINOR 5', 4, 'marg_short'), (25, 'C2CALZ', 2, 'marg_short'), (25, 'FLACORT 6', 20, 'marg_short'), (33, 'POWERGESIC 100 PATCH', 5, 'marg_short'), (34, 'XGESIC LA', 20, 'marg_short'), (38, 'LINVIZ 600', 10, 'marg_short')]
     ok   C: the five lines (XGESIC LA, THIO Q AP, FLACORT 6, POWERGESIC 100 PATCH, LINVIZ 600) are carried, each once, keyed by its line
     ok   C: LANZOL JUNIOR (still on Marg's newest order, sheet 6) is NOT carried -- its words: 'already on Marg's order'
     ok   a second carry_pass writes nothing (keyed, idempotent)
      a newer Marg sheet laid by the walk (sheet 7: DRUG DEAL, DEEPAM, KEDAR a line each; L.K. carries LANZOL JUNIOR itself); carry_pass: {'written': 3, 'done': 0, 'dropped': 0}
      the cards: {'DEEPAM PHARMA': [('sheet', 'W619 FILLER DP'), ('carry', 'THIO Q AP'), ('carry', 'POWERGESIC 100 PATCH')], 'DRUG DEAL': [('sheet', 'W619 FILLER DD'), ('carry', 'XGESIC LA')], 'KEDAR PHARMACEUTICAL': [('sheet', 'W619 FILLER KP'), ('carry', 'C2CALZ'), ('carry', 'FLACORT 6'), ('carry', 'LINVIZ 600')], 'L.K. DRUG HOUSE': [('sheet', 'LANZOL JUNIOR')]}
     ok   C: the five lines appear on their dealers' next cards as carried lines (src carry)
     ok   C: LANZOL JUNIOR is on L.K.'s card once (the sheet's line), never doubled by a carry
     ok   C: the supplier screen shows XGESIC LA with 'pichhle order se baaki (16-10)'
     ok   C: the printed sheet carries exactly the carried lines of the cards (one reader: entries()), each 'pichhle order se baaki (dd-mm)'
     ok   the PDF's text has 'pichhle order se baaki (16-10)' beside XGESIC LA
     ok   C: an order made for Drug Deal (whatsapp) carries XGESIC LA and closes its carry (done_order_id)
      the WhatsApp body (as queued): Sanjeevni Medicos, G 15 Rampur Garden, Bareilly | W619 FILLER DD — 2 pcs | XGESIC LA — 20 strips · pichhle order se baaki (16-10) | Kripya maal dopahar 3 se shaam 6 baje ke beech, ya subah 11 baje tak bhejein.
     ok   C: the WhatsApp body says 'XGESIC LA — ... · pichhle order se baaki (16-10)' and its last line is the delivery line
   -- 6  the remove door: a reason chip; dealer_no off the card, the plan, the body; printed so; refused with a draft; lifts on a newer sheet
     ok   C: the supplier screen's remove asks one reason chip -- 'Dealer ke paas nahi hai' / 'Abhi nahi chahiye' (OLD: no chip)
     ok   C: a remove with no reason is refused (400 reason_needed; OLD removed it)
     ok   C: 'Dealer ke paas nahi hai' on a pending card -> 200, stored as s454_line_edit.reason dealer_no; off the card, the plan and the body
     ok   C: the paper prints it 'dealer ke paas nahi' (never 'order karna hai'), with no Order box
     ok   a remove on a card whose order is already made is refused (409)
     ok   C: the removal lifts when a newer Marg sheet arrives that still carries the line -- it is back on the card
     ok   C: a carried line removed with a reason (Abhi nahi chahiye) is dropped (dropped_at, dropped_by) and leaves the card
   -- 7  the screens: reception's call row and its page, Maal aaya, Darpan's line and order tab, the order list, the WhatsApp, both papers
     ok   C: reception's home with a late order and a part order -> 'Order ka maal nahi aaya — call karo' 2 (= order_track's late count 2); S605's 'Aaj ke order' row gone
     ok   C: the call row's page: the late order 'aaj tak nahi aaya' with Call and Maal aaya; the part order 'N mein se M dawa aayi · W619 P2 B baaki' with Baaki maal aaya
     ok   C: Maal aaya lists the order awaited and not yet late, never the late one
      Darpan's line, state all: 14-10 ke order: saara maal aa gaya ✓
      Darpan's line, state waiting: 14-10 ke order: 1 supplier ka maal aana baaki — 16-10 shaam tak
      Darpan's line, state late: 14-10 ke order: 1 supplier ka maal der se — W619 Day. Reception call kar raha hai.
      Darpan's line, state short: 14-10 ke order: 1 dawa nahi aayi — agle order mein khud jud gayi.
     ok   C: Darpan's four states, dated (never 'Kal'): all came / some not come (with the day they are due) / some late (named, 'Reception call kar raha hai') / some short
     ok   C: Darpan's day payload carries the one order line ('20-10 ke order: 9 supplier ka maal aa gaya, 1 ka aana baaki — 22-10 shaam tak 20-10 ke order: 3 dawa nahi aayi — agle or'), under 100 KB (2200 bytes) and 2 s (0.27 s)
     ok   C: his order tab ('कल के ऑर्डर — क्या हुआ', 2026-10-20, 10 suppliers) reads the same reader (order_track)
     ok   C: the order list as the owner (English): the heading, five tiles, the six sections, the five dots, the late order under Not arrived; its read leaves both copies byte-equal
     ok   C: the order list as Shavez (porders.rescan_askers): the same list in Roman Hindi ('Purchase orders ka haal', 'Nahi aaye', 'Kam aaye')
     ok   C: darpan / alisha / shivani / reception refused (403); Bhati redirected (302) as today: {'darpan': 403, 'alisha': 403, 'shivani': 403, 'reception': 403}, bhati 302
     ok   C: the owner's home carries the order list's card (the one way in; S618's separate 'Scans to redo' link folded into it)
     ok   C: a WhatsApp order's last line is the delivery line (built through wa_body, both queue paths): 'Kripya maal dopahar 3 se shaam 6 baje ke beech, ya subah 11 baje tak bhejein.'
     ok   C: the printed order sheet carries the delivery line once on each page (1 of 1 pages)
      Marg's order PDF now (the walk's own newer sheet has no export file): the one-page notice
   -- 8  the duty map v19: each due_sql equal to its screen's count on the copy
     ok   the kit's DUTY_MAP.json is v19 and carries shavez.order_followup
      reception.order_arrival due_sql on the copy: [(2, '2026-10-18')]
      reception.medicine_orders due_sql on the copy: [(3, '2026-10-22')]
      reception.bill_scan due_sql on the copy: [(3, '2026-10-05')]
      shavez.order_followup due_sql on the copy: [(10, '2026-10-18')]
     ok   every due_sql is ONE read-only SELECT returning one row (n, since)
     ok   C: reception.order_arrival (rewritten: the late rule, door marker 'Order ka maal nahi aaya') equals the call row's count on the copy (2 = 2)
     ok   C: reception.medicine_orders (dealer_no removals lifted by a newer sheet; carries never make a card) equals the card count (3 = 3)
     ok   C: reception.bill_scan (the two asking rules of 3.3) equals Bill scan karna hai's count, scan_lines (3 = 3)
     ok   C: shavez.order_followup (door /finance/porders/s454/track) = late orders + open carries (10 = 2 + 8)
   -- 10 the staff-eye walk: reception (shared login + name), alisha, shivani, darpan, shavez, the owner
     ok   C: staff-eye: reception -- duty reception.order_arrival due (n 2): the tile 'Purchase orders' on the portal home and 'Order ka maal nahi aaya' on /finance/porders
     ok   C: staff-eye: reception -- duty reception.medicine_orders due (n 3): the tile 'Purchase orders' on the portal home and 'Order karna hai' on /finance/porders
     ok   C: staff-eye: reception -- duty reception.bill_scan due (n 3): the tile 'Purchase orders' on the portal home and 'Bill scan karna hai' on /finance/porders
     ok   C: staff-eye: alisha -- duty reception.order_arrival due (n 2): the tile 'Purchase orders' on the portal home and 'Order ka maal nahi aaya' on /finance/porders
     ok   C: staff-eye: alisha -- duty reception.medicine_orders due (n 3): the tile 'Purchase orders' on the portal home and 'Order karna hai' on /finance/porders
     ok   C: staff-eye: alisha -- duty reception.bill_scan due (n 3): the tile 'Purchase orders' on the portal home and 'Bill scan karna hai' on /finance/porders
     ok   C: staff-eye: shivani -- duty reception.order_arrival due (n 2): the tile 'Purchase orders' on the portal home and 'Order ka maal nahi aaya' on /finance/porders
     ok   C: staff-eye: shivani -- duty reception.medicine_orders due (n 3): the tile 'Purchase orders' on the portal home and 'Order karna hai' on /finance/porders
     ok   C: staff-eye: shivani -- duty reception.bill_scan due (n 3): the tile 'Purchase orders' on the portal home and 'Bill scan karna hai' on /finance/porders
     ok   C: staff-eye: shavez -- duty shavez.order_followup due (n 10): the tile 'Purchase orders' on the portal home and 'Purchase orders ka haal' on /finance/porders/s454/track
     ok   staff-eye: darpan -- his Kal ka hisaab carries the one read-only order line, nothing to tap (no duty of his moves)
     ok   staff-eye: the owner -- his Purchase orders home opens the order list (the card)
      the owner's Needs-you line: {'cls': 'warn', 'target': 'porders', 'text': 'Orders: 2 late, 8 medicines came short (back on the next order) — the order list'}
   WALK OK S619: 82 checks, 55 controls green on the new files
```

**The negative control (the same walk on the OLD files), verbatim — every control red (29):** sections 1, 2, 3 (exception: no order_track) · the order-45 case · the 'Nahi mila' order asking · the Drug Deal tie · Marg's PDF delivery line · the order sheet's delivery line (7a) · section 5 (exception) · the reason chip · remove with no reason · dealer_no off the card · printed 'dealer ke paas nahi' · the lift on a newer sheet · a carried line dropped · reception's call row (S605's row on OLD) · the call row's page (404) · Maal aaya's rule · Darpan's four states · his day line · his order tab · the order list as owner / as Shavez (404) · the refusals (404) · the owner's card · the WhatsApp's last line · the order sheet's delivery line (7) · sections 8 and 10 (exception).

**The soft note (3.2) — the gate:** on orders 21–45, Marg as the answer key, the false "not seen on the scanned bill" rate is **27 of 54 Marg-billed lines (50%)**, every usable scan of the dealer from the order to its next order (scans on S618's "Scans to redo" list — B-0155, B-0157, B-0176, B-0180, B-0199 — excluded as the brief says). It is a note only: the walk proves the tiles and every order's place are equal with and without the scan half. R1 measured 40–44% with a different set of scans; the exclusion of the redo scans costs most of the difference (35% without it, measured in rehearsal).

**The stock effect (3.3), walked:** the Drug Deal case laid synthetically — the scan now ties to the NEW sent order (OLD: the old 'Nahi mila' one) and its unanswered line (W619 XGESIC) is newly counted by `stock_figure.scan_lines` / `porders._on_order` until Marg carries it. On the copy's replay of the real scans, OLD and NEW make the same ties (none) — no real stock figure moves on install day.

**S618's, S613's and S605's walks (brief 4.9), OLD (live) vs NEW, check lines compared:** walk_s618: one line differs — `the owner's home links 'Scans to redo: N' while there is any` (ok → FAIL: on purpose, folded into the order list's card); walk_s613: one line differs — `C: (3) the call row counts today's orders still awaited` (ok → FAIL: on purpose, S605's call row retired for the late row); walk_s605 (59 lines), walk_s603 (79), walk_s598 (62): every check line equal. Red on BOTH sides (the live day, not this kit): walk_s618 the 22-turned-scans render check; walk_s613 order 20's L S BELT family-bill words; walk_s605 its six (Darpan's हाँ ×4, the send-all hand-out, the 'Aaj ke order' Ho chuke count); walk_s603 `stock_figure.py untouched (md5 51e1fc63)`; walk_s598 two (S593's seven rows by id; the re-judge clause). The installer allowed only the two named lines; any other new red line would have stopped it.

### DUTY_MAP (v18 → v19, `da46a0b8…`; DUTY_MAP.md and .json together)
`reception.order_arrival` rewritten to the late rule (door marker "Order ka maal nahi aaya"; one SELECT with a recursive CTE for the skip days, finance.db only); `reception.medicine_orders` honours a removal's reason (a dealer_no removal lifts on a newer sheet); `reception.bill_scan` carries the two asking rules; **`shavez.order_followup` added** (tile Purchase orders, door /finance/porders/s454/track, marker "Purchase orders ka haal", due = late orders + open carries). Each due_sql proved equal to its screen's count on the copy (2 = 2, 3 = 3, 3 = 3, 10 = 2 + 8) and run on live (above). The staff-eye walk signed in (its own secret and user store) as reception (shared login + name cookie), alisha, shivani and shavez and found each due duty's tile and marker; Darpan's payload carries his line; the owner's home carries the card.

### Calls I made (the brief left them open), and why
1. **A carry rides on the dealer's next card; it never makes a card by itself** ("goes back on that dealer's next order"). Making carry-only cards would have put 4 extra dealer cards (Deepam, Janta, Kedar, Drug Deal) on reception's "Order karna hai" at install. So `reception.medicine_orders` needs no carry arm ("including carries" holds: a carry never adds a card).
2. **An order whose bill was scanned but Marg has not entered is not late** (it sits under "Bill scanned, not in Marg yet"): otherwise reception would call dealers for goods that came. "Part order" = a line tapped "Kam aaya" with Marg not in, or an untapped line beside a tapped one; once Marg bills any line, an unbilled line is short (and carried), not awaited.
3. **"Kam aaya" (tapped short) alone does not carry** — it waits for Marg ("once Marg's bill shows it did not come — or reception tapped Nahi mila"); the carry reasons are `marg_short` / `tapped_missing` only.
4. **A carry is not written while Marg's newest open order still prints the item** (LANZOL JUNIOR's rule, applied the same to every line) — so 51/53/55's three lines wait for Darpan's next sheet. A carry also closes if the line turns out to have come (Marg bills it later), besides the brief's three ways.
5. **`reception.bill_scan`'s Marg arm now counts a Marg bill whose verdict is WRONG, as the screen shows it.** The v18 SQL skipped it, the screen lists it (Kedar A000211, 15-10): equal now (one rule). A WRONG bill asking to be scanned is itself worth a look (below).
6. **The arrival moment's tie-break:** a tap and a scan in the same minute → the tap (47, 48, 50).
7. **The settings card** validates the five new settings (`order.deliver_days` 0–7; skip days MON..SUN; the window's shape; the line ≤ 200 characters, no digit run; a date).
8. **The first carry pass ran from the installer** (the same keyed step cron_pass runs within ten minutes anyway), so this report can name what it wrote.

### What I did not do, and why
- **The board's PLANNED lines**: the board is not reachable from this PC or the box (as S605/S618 found); no other build's lock or runner log was active (the lock was free at 12:26 and 13:14).
- **"Baaki maal aaya" on a part order** opens the existing arrive page; for an order already marked received (a tapped "Kam aaya") that page shows "Maal darj ho gaya" and offers the bill scan — the remainder is confirmed by Marg. No new arrival door (not in the brief).
- **No `node --check` of darpan_kal.html**: no node on the box; the walk read the day payload and the order tab through the real app (the HTML edit is one function and one call).
- **walk_s618 made a few Claude calls** on its scratch copy (its own backfill of any unchecked scan), on both sides, against its scratch cap.

### Seen, not touched (outside the brief)
- **Kedar's Marg bill A000211 (15-10) has verdict WRONG yet reception is asked to scan it** — someone should decide what WRONG should mean on "Bill scan karna hai".
- **The soft note misses half the lines** (27 / 54) — Claude's spellings vs Marg's (DYNAPAR QPS PLUS, ORICOX P, ZYLORIC, PRETOL-16/-4…); learning `s454_item_name` from `claude_reading` (not only `bill_items`) would close much of it — a later kit.
- The dealer-correction door for B-0161 (Kedar as Shivaaz) and B-0167 (Mannat as Yogendra) — listed with "Open the scan" only; **the next small kit** (board line at the close).
- `order_rules.lead_learned` / `order.lead_days` 1 beside `order.deliver_days` 2 (the engine plans cover on one day, the list calls late after two); `purchase_app._wa_text` (the staff send) does not carry the delivery line; `purchase_app._carried_shorts` still feeds `order_rules.plan` on source system / darpan; reception's pages write on a GET (F-925); `received_at` keeps its three meanings; one scan per order; `stock_watch.arrival_needs_you` and `amir_day._d712_owner_lines` remain the owner's other two arrival voices; an owner_console section is the parent's (a line to the parent).

### Behaviour changes (rule 4, 7)
Reception: the late call row (part orders too) replaces "Aaj ke order — call karo"; "Maal aaya?" shows only orders not yet late; the remove asks a reason; carried lines on the cards, the WhatsApp and the paper; the WhatsApp's last line; "Bill scan karna hai" no longer asks for an order where nothing came, or one Marg has fully answered (today: Yuvika 16-10, Verma 20-10, Bass 20-10 left that list). Darpan: one line and his order tab's arrived/not from the new reader. The owner and Shavez: the order list (the card replaces "Scans to redo"); one Needs-you line. The tie: two asking rules and the reading's pick (and their stock effect, above). DUTY_MAP v19 with Shavez's duty.

### Cost
API credits used by this build when the report was written: about **$15 of the $90** budget (the runner writes its own cost line at the close).

### Lock
`/root/deploy/.claude_code_build.lock` was taken at 13:14:00 IST by S619_ORDER_TRACKER (owner file written by the installer). It is released after this report and the publish with `rm -f /root/deploy/.claude_code_build.lock/owner; rmdir /root/deploy/.claude_code_build.lock`.
