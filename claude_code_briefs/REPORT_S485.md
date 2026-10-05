# REPORT — S485_DARPAN_ORDER_TAB (05-Oct-2026)

Brief: `claude_code_briefs/S485_DARPAN_ORDER_TAB.md` · kit `deploy_kits/S485_DARPAN_ORDER_TAB/` · D677 · no F-number.
Built, walked, installed, published and read back by Claude Code on manojz, 05-Oct-2026. Every clock time below is read (IST).

## For the owner

- **Darpan's page "Kal ka hisaab" now has a second tab, "आज का ऑर्डर" (today's order).** From 09:30 each order day it shows the
  system's list for the day, supplier by supplier. He can drop a medicine, add one, change a quantity with − / +, and press
  **पक्का** (confirm) for each supplier, or **सब पक्का** for all.
- **Reception sees a supplier on its "Order karna hai" cards only after Darpan presses पक्का**, with exactly his lines. Calling,
  WhatsApp, "Order ho gaya" and arrival work as before.
- **The way back to the Marg sheet is one tap:** your Purchase orders page → the card "Who decides the order" → "Change to Darpan's
  sheet".
- **It is live already today, not from tomorrow.** Nothing had been ordered today, and today's list (9 suppliers, 24 medicines) is
  on his tab now. If he confirms it today, reception gets it today. If not, tonight it carries over to the next order day as usual.
  Until he confirms, reception's cards show only the surgical supplier's items (Yuvika), which is how they work every day.
- Darpan's phone is not signed up for alerts, so the 09:30 message will not reach him yet. The new tab, and his new duty line, are
  the signal. Checked on a phone-sized and a laptop-sized screen. The finance service restarted once (15:24) and is healthy.

## For the chat

### 1 · Every pin, FROM → TO, read back on the box (15:24:42, and again after the publish)

| file (`/root/finance/`) | FROM (read before the first edit) | TO (read back after placing) | backup beside it (reads) |
|---|---|---|---|
| `darpan_kal.py` | `911cf637a288fad85c75e54227149633` | `c45bb343ac867f322f031da94882413d` | `.bak_S485_911cf637` (`911cf637`) |
| `darpan_kal_schema.sql` | `ecc6f0c53db4ea7e48bf8e3b1120e6b4` | `d7260467bd57e95d386c66cbcfa228d3` | `.bak_S485_ecc6f0c5` (`ecc6f0c5`) |
| `darpan_kal.html` | `c20ab05d8484e37a667ddae32a4c792b` | `ec8b64ae8f15c232d390b5ea0b8b266d` | `.bak_S485_c20ab05d` (`c20ab05d`) |
| `order_sheet.py` | `a5408df0fac852391d5845c5ae4d8865` | `16f21a6515a1317e1f6e31cb0a280513` | `.bak_S485_a5408df0` (`a5408df0`) |
| `order_rules.py` | `dac12be4c4a537d7ad2e4584a3423e6a` | `ee17c1872acd0c440868a915fa5014df` | `.bak_S485_dac12be4` (`dac12be4`) |
| `porders_s454.py` | `3681622b11043116f40bc0d4c3b557ad` | `9c463e7c326c95beb20da0829cc537cc` | `.bak_S485_3681622b` (`3681622b`) |

`porders_s454.py`'s live bytes were `3681622b` as the brief said (the board's `36816221` was a typo there). Read only, at the
brief's pins before and after (installer step 1 and step 12): `porders.py` `a5a823bf…`, `purchase_app.py` `254b7793…`,
`spine/spine_read.py` `712a1e4e…`, `shelf_figure.py` `23c34ebb…`; `finance_app.py`, `/root/portal/portal.py`,
`/root/portal/tile_grants.json` and the crontab unmoved (step 12).

**Data.** `finance.db.bak_S485_20261005_152419` (backup API, 31,330,304 bytes) made before anything was placed. Then, read back:
the table `order_darpan_edit` (0 rows); `order.darpan_list_time = 09:30`; `order.source` `marg_sheet → darpan` through
`order_rules._set_setting`, audit row 58 `('2026-10-05T15:24:32', 'S485 install', 'order.source', 'marg_sheet', 'darpan')`.

**Service.** `clinic-finance` restarted once, `ActiveEnterTimestamp` 15:24:32; `/finance/healthz` 200 after it, at the end, and
again in the owner's line; `/finance/darpan/kal`, `…/api/order` and `/finance/porders` 302 to plain curl (the login gate,
expected). The journal's only "ERROR" lines since 15:24:30 are the old gunicorn workers' "was sent SIGTERM!" of the restart; no
Traceback.

**Read back as the readers (installer step 11; the placed bytes on a fresh copy of the database as it was at 15:24):** manoj
`/finance/darpan/kal` 200 with the tab's marker; manoj `api/order` 200, source darpan, list time 09:30, opened, 9 suppliers / 24
lines, all open; darpan `api/order` 200, editable; shivani's "Order karna hai" 200 with the heading
`Darpan ki pakki list · 05-10 · 1 supplier, 2 dawa` and one card, `YUVIKA SURGICALS` (the surgical supplier's own card; a
proposal's supplier comes only after a Pakka). `READ_BACK OK`.

**The new duty, on live (after the install, read-only):** `darpan.order_review` due_sql → `(9, '2026-10-05')`. Darpan's older row
`darpan.order_sheet` reads `(0, None)`: it fires only on a refused Marg sheet, so the two do not both nag.

**The lock.** `/root/deploy/.claude_code_build.lock` taken 15:24:19 (owner `S485_DARPAN_ORDER_TAB`), released after this report
was written: 15:27:50 (healthz 200 and the six TO pins read again at that moment). The build's `/tmp/s485kit`, `/tmp/s485probe`
and `/tmp/s485eye` are cleared; no copy of a database is left in /tmp.

**Publish.** `PUBLISH_ALL.bat`: the number gate clean (14 files), commit `fd4fad7`, origin HEAD verified. On the server
`git pull --ff-only` → `fd4fad7`; `md5sum -c SUMS.md5` in the repository's kit: every file OK; `diff -r` against the copy that
ran: no difference (SUMS.md5 `b15c7cf9fa6170b466164a417dc90e4f`). The owner's line of the brief's §5 then answers
`ALREADY INSTALLED: the six files are at the kit's pins; clinic-finance active; healthz 200`. This report went up with a second
`PUBLISH_ALL.bat` run.

### 2 · The walk, whole (`walk_s485.py`, inside the real install at 15:24; the same 42 checks were green in the final dry run at 15:23)

Each line is cut at 330 letters; the full log is the installer's output on the box (`/tmp/s485kit/install.log`, cleared with the
build's /tmp folders).

```
     ok   both probes ran to the end (NEW = the box + S485, OLD = the box as it is), each on its own copies; the scratch day is today (2026-10-05) with the six real proposal rows of 2026-10-03 copied in, open
   -- 1  the door
     ok   darpan (maker on medical -> staff): the page 200, the tab's API 200; manoj (checker -> owner): 200 / 200   [({'page': 200, 'api': 200}, {'page': 200, 'api': 200})]
     ok   shavez, shivani, alisha (viewer, no recipient party): the page itself is 403 as today, and the API with it; a login with no role on the unit (bhati) never reaches the page -- the app's own gate turns it away (302), as today   [{'shavez': {'page': 403, 'api': 403}, 'shivani': {'page': 403, 'api': 403}, 'alisha': {'page' …
     ok   the owner may tap (hold, then take back: 200, 200, two audit rows by manoj); a viewer's or a stranger's tap is refused ([403, 403, 302])   [([200, 200, [['hold', 'XYCAL K2', 20, 'manoj'], ['unhold', 'XYCAL K2', 20, 'manoj']]], [403, 403, 302])]
     ok   negative control, OLD darpan_kal.py: api/order is 404 for Darpan (the page itself 200)   [{'page': 200, 'api': 404}]
     ok   order_sheet.source() reads the new value: NEW 'darpan'; OLD falls back to 'marg_sheet' for it
   -- 2  the list
     ok   before the list time (the clock at 09:00, order.darpan_list_time 09:30): opened false, no supplier shown
     ok   at 09:31: opened true, source darpan, editable; 6 blocks, 10 lines -- [('A.A. Pharmaceuticals', 1), ('Janta', 2), ('Kedar', 2), ('Mannat', 1), ('Shivaaz', 3), ('Yogendra', 1)]
     ok   PATOPAN DSR (236 of 1*10): on_hand_text '23:6', 20 strips, ~4 days left; MECOVIXR FORTE INJ (a unit item): on_hand_text '11', unit   [({'added': False, 'cover_days': 6, 'days_left': 4, 'held': False, 'item': 'PATOPAN DSR', 'on_hand_text': '23:6', 'packing': '1*10', 'pid': 21, 'qty': 20, 'unit': 'strip', 'why': ['cover  …
     ok   the payload's shape: ['all_pakka', 'date', 'editable', 'frozen', 'list_time', 'me', 'n_lines', 'n_suppliers', 'ok', 'opened', 'order_day_names', 'source', 'suppliers', 'yesterday', 'yesterday_date']; a line: ['added', 'cover_days', 'days_left', 'held', 'item', 'on_hand_text', 'packing', 'pid', 'qty', 'unit', 'why']
   -- 3  hold / unhold / quantity
     ok   नहीं चाहिए on PATOPAN DSR: held in the answer and in the proposal's own lines; वापस लो: the flag is gone
     ok   − − − + + + + from 20 strips: [10, 5, 5, 10, 15, 20, 30] (10 at 20 or more, else 5, never below 5); a unit item from 2: − − + -> [1, 1, 2] (never below 1)
     ok   every tap is one order_darpan_edit row carrying who: [('hold', 20), ('unhold', 20), ('qty', 10), ('qty', 5), ('qty', 5), ('qty', 10), ('qty', 15), ('qty', 20), ('qty', 30)]; the engine's own figure is kept beside his (qty_engine 20)
     ok   a held line (DEFVAX 6, Shivaaz) is absent from send_proposal's lines: NEW would send ['MECOVIXR FORTE INJ', 'TRAMAVIN GEL']   [{'code': 409, 'error': 'w485_captured', 'lines': ['MECOVIXR FORTE INJ', 'TRAMAVIN GEL']}]
     ok   negative control, OLD order_rules.py: the same held line IS sent (['DEFVAX 6', 'MECOVIXR FORTE INJ', 'TRAMAVIN GEL'])   [{'code': 409, 'error': 'w485_captured', 'lines': ['DEFVAX 6', 'MECOVIXR FORTE INJ', 'TRAMAVIN GEL']}]
   -- 4  add
     ok   api/order/items?q=ROS: ROSIKA FORTE among 2 hits, with its usual supplier and lot ({'item': 'ROSIKA FORTE', 'packing': '1*10', 'qty': 50, 'supplier': 'Deepam', 'supplier_norm': 'DEEPAM PHARMA', 'unit': 'strip', 'usual': True}); two letters return nothing; 23 supplier chips   [{'item': 'ROSIKA FORTE', 'packing': '1*10', …
     ok   adding ROSIKA FORTE: its usual supplier DEEPAM PHARMA had no proposal today -> a row kind 'darpan', open, is made for it; usual lot 500.0 units of 1*10 -> 50 strips shown; added, why ['Darpan ne joda']   [[['darpan', 'open', [['ROSIKA FORTE', 50, True, ['Darpan ne joda']]]]]]
     ok   adding ASTOFEN P (usually from Kedar, lot 200.0 units of pack 10): it lands in Kedar's open list with 20, added   [{'item': 'ASTOFEN P', 'code': 200, 'lot_units': 200.0, 'pack': 10, 'line': {'qty': 20, 'unit': 'strip', 'added': True, 'vendor_norm': 'KEDAR PHARMACEUTICAL'}}]
     ok   adding ALCOXIB MR (never bought): with no supplier tapped -> 409 need_supplier; with the Mannat chip -> under Mannat, 10 strips, why ['Darpan ne joda']; a second time -> 409 already; a name not in Marg's list -> 404   [{'item': 'ALCOXIB MR', 'no_chip': [409, 'need_supplier'], 'code': 200, 'line': {'qty': 10, 'unit': 's …
     ok   three add rows in order_darpan_edit, by darpan
   -- 5  पक्का
     ok   पक्का on Kedar: 200, status darpan_ok in the answer and in the table, pakka_at 15:24, one audit row   [{'status': 'darpan_ok', 'pakka_at': '15:24', 'db': 'darpan_ok', 'edit': [['pakka', '', 2, 'darpan']]}]
     ok   reception's 'Order karna hai' (as shivani) on order.source = darpan: NO proposal card before any Pakka ([]); after it exactly Kedar's (['KEDAR PHARMACEUTICAL']) -- heading 'Darpan ki pakki list · 05-10 · 2 supplier, 4 dawa'   [(['YUVIKA SURGICALS'], ['KEDAR PHARMACEUTICAL', 'YUVIKA SURGICALS'])]
     ok   Kedar's card holds its live lines only: the held PATOPAN DSR absent, TYRO BR and the added ASTOFEN P present (['TYRO BR', 'ASTOFEN P']); entries() agrees   [{'KEDAR PHARMACEUTICAL': ['TYRO BR', 'ASTOFEN P'], 'YUVIKA SURGICALS': ['ANKLE BINDER BAMBOO L', 'L S BELT CONT GRAY UNISON XXX']}]
     ok   'Order ho gaya' on Janta (api/s454/ordered, as shivani): make_order writes the purchase_order (('sent', 's454', 'call')) and _mark_sources sets the proposal sent with its order id; the tab shows it   [{'code': 200, 'ok': True, 'order': {'vendor': 'JANTA PHARMACEUTICALS         BAREILLY', 'status': 'sent', 'total_p': 47 …
     ok   the same rows the system road produces (the same six rows on a copy with order.source = system, the same tap): the order, its lines and the proposal are equal field for field   [({'vendor': 'JANTA PHARMACEUTICALS         BAREILLY', 'status': 'sent', 'total_p': 47551, 'section': 'Medicines', 'supplier_norm': 'JANTA PHAR …
     ok   negative control, OLD order_sheet.py with order.source = darpan and Kedar's row darpan_ok: reception sees the Marg sheet's lines (['SHRADDHA MEDICOSE']) -- the fallback of an unknown value -- and never the proposals   [{'code': 200, 'sns': ['SHRADDHA MEDICOSE', 'YUVIKA SURGICALS'], 'whose': 'Darpan ka order · 02-10 · 5 …
     ok   सब पक्का: every block is pakka or sent, all_pakka true   [{'code': 200, 'all_pakka': True, 'statuses': ['darpan_ok', 'sent'], 'pakka': ['A.A. PHARMACEUTICALS', 'DEEPAM PHARMA', 'MANNAT PHARMA', 'SHIVAAZ FORMULATIONS', 'YOGENDRA AGENCIES']}]
   -- 6  the notice
     ok   tick at 09:30 with source darpan and proposals open: slot 0930, ONE notice, to darpan only -- 'आज का ऑर्डर तैयार है — कल का हिसाब पेज पर देखिए' -> /finance/darpan/kal#order   [({'slot': '0930', 'notice': {'ok': True, 'slot': '0930', 'text': 'आज का ऑर्डर तैयार है — कल का हिसाब पेज पर देखिए', 'sent': {'darpan': {'sent':  …
     ok   once: the tick at 09:40 sends nothing (slot none, still 1 push); the slot forced again answers 'already'
     ok   silent with no open proposal (no open proposal); silent on the Marg-sheet source (order.source = marg_sheet)
     ok   the 09:00 slot (each on a copy of its own): on darpan silent, why 'order.source = darpan'; on marg_sheet silent, why 'order.source = marg_sheet' -- the OLD words; on system the same notice as the OLD file sends, word for word, to the same logins   [({'slot': 'prepare', 'silent': None, 'why': None, 'text': 'Aaj 9 order  …
     ok   negative control, OLD order_rules.py: its tick knows no 0930 slot (slot 'none' at 09:30, no notice of that kind); on darpan its 09:00 why still says marg_sheet
   -- 7  nightly
     ok   yesterday's rows of the walk's own suppliers: darpan_ok -> ['merged', '2026-10-05'], open -> ['merged', '2026-10-05'], sent -> ['sent', None]; the merged ones are found by the next order day's 'carried' read   [{'rows': {'W485 SUPPLIER OK': ['merged', '2026-10-05'], 'W485 SUPPLIER OPEN': ['merged', '2026-10-05'], 'W485 …
     ok   negative control, OLD: a darpan_ok row of yesterday is left as it is (['darpan_ok', None]), never merged
   -- 8  the way back to the Marg sheet
     ok   order.source = marg_sheet (before the switch and after going back): reception's cards are the Marg sheet's lines again (['SHRADDHA MEDICOSE']), no proposal card; Darpan's tab shows the list read-only (source marg_sheet, editable false, 7 blocks) and a tap is refused -- 'अभी मार्ग की शीट से ऑर्डर हो रहा है'   [({'code': …
     ok   Darpan's count line on darpan counts open + pakka as still to go: Aaj 7 order: 1 bheja, 6 baaki — A.A. Pharmaceuticals, Kedar, Mannat, Shivaaz, Yogendra, Deepam
   -- 9  the page (the machine half; the rendered page is read by eye at build time)
     ok   the page carries the tab (id tabOrder), the viewport line, every word of the brief's section 2 in Devanagari (34 checked), the bottom padding under the fixed bar; nothing between the tab's own tags is a Latin word   [([], [])]
     ok   found by eye at build time, held here: the owner's view decides 'no buttons' from the answer's own me=owner (not from which fetch lands first) and opens every block for him; every tap on the tab is 44 px or more, with room between + and नहीं चाहिए and between the supplier chips; वापस लो is not greyed with its line; the …
     ok   negative control, OLD page: no tab
   -- 10  everything else on कल का हिसाब
     ok   api/day for yesterday, on the same copy before any tap: the same JSON from the NEW file as from the OLD (1443 bytes)
     ok   the duty map's existing darpan rows on this page still find their markers (['darpan.amir_claims', 'darpan.cash_handover', 'darpan.order_sheet']), as on the OLD page   [{'darpan.cash_handover': True, 'darpan.amir_claims': True, 'darpan.order_sheet': True, 'darpan.order_review': True}]
     ok   the new row darpan.order_review: its marker 'आज का ऑर्डर' is on the NEW page (not on the OLD); its due_sql on the copy -> [1, '2026-10-05'] on darpan with the list time passed (clock 15:24, list time 09:30), [0, None] on the Marg sheet   [{'row': {'id': 'darpan.order_review', 'person': 'darpan', 'tile': 'Kal ka hisaab' …
   WALK_S485 GREEN -- 42 checks
```

Negative controls, each red on the OLD files and shown above: the API 404 (1); `source()` falls back to marg_sheet (1); a held line
IS sent by the old `send_proposal` (3); the old `order_sheet.py` shows the Marg sheet's lines on `darpan` (5); the old tick knows
no 0930 slot (6); the old nightly leaves a `darpan_ok` row unmerged (7); the old page has no tab, none of the eye-walk's fixes, and
no marker for the new duty (9, 10).

### 3 · Section 9 by eye: what was looked at, what it found, what changed

A scratch copy of the app (the kit's six files, backup-API copies of the three databases, bound to 127.0.0.1 only, as darpan on
one port and as manoj on another), opened in a browser through an ssh tunnel at 390 × 844 and at desktop width (1024). Measured
with the page's own geometry, then the screenshots were read by **two independent sub-agents** given a checklist, not my
conclusions. The scratch app and its copies were removed afterwards (`/tmp/s485eye` gone, no listener left).

Found and fixed in the kit before the install (each is now a check in the walk, red on the old page):
1. `नहीं चाहिए`, `वापस लो`, `बंद करो` and the three tabs were 37–39 px tall → all 44 px or more.
2. `+` and `नहीं चाहिए` under it were about 6 px apart (both readers called this the worst risk) → 12 px. The supplier chips were
   about 6 px apart → 10 px.
3. `वापस लो` was greyed with its held line and looked disabled → only the line's text is greyed.
4. The black message strip after a tap sat over the fixed bar's two buttons → it sits above the bar while the tab is open.
5. The owner's "no buttons" depended on which of two page fetches finished first, so his view could draw the buttons → it now
   comes from the answer's own `me = owner`. A confirmed block was folded for him, hiding its quantities → all blocks open for him.
6. A block sometimes stayed open after its पक्का: a "toggle" event from the blocks drawn before the tap could land while the tap
   was still in flight → the fold is set after the answer, and events from blocks already redrawn are ignored.

Measured after the fixes: no element is under 44 px; no sideways scroll at 390 px (page and add sheet `scrollWidth` 390 = width);
at the page's foot the last supplier's `पक्का` ends 324 px from the top of the screen and yesterday's list ends at 665, with the
fixed bar starting at 780; after `सब पक्का` all six blocks fold, the `सब पक्का` button hides and `सब पक्का — रिसेप्शन ऑर्डर करेगी।`
shows; in the owner's view 0 buttons and no bar.

Read by both readers and **left as they are** (reported, not changed — outside the brief or the brief's own wording):
- the page's header `Sanjeevni — Kal ka hisaab`, the link `din ka card` and the greyed third tab `Claim (jaldi)` stay Roman as
  before; the owner's title `Darpan — the day` too;
- `शेल्फ 23:6` (strips:tablets) is the brief's form, and a reader new to it may take it for a clock time;
- `मार्ग` in the add sheet's hint `जैसे मार्ग में लिखते हैं` also means "road" in Hindi; the brief chose the word;
- `आज 6 सप्लायर का दिन` (more than three order-day suppliers; the brief's own example names one) and the `आज का दिन` badge on every
  block when every supplier's day is today;
- the polite `चुनिए` beside the familiar `जोड़ो / करो / लो` — both are the brief's words.

### 4 · The words as placed

Tab `आज का ऑर्डर`; header `सोम 05-10-2026 · 6 सप्लायर · 10 दवा` + `आज Kedar का दिन` (up to three names) or
`आज N सप्लायर का दिन`; `आज की सूची 9:30 बजे आएगी।`; `आज कोई ऑर्डर नहीं बनता।`; `सब पक्का — रिसेप्शन ऑर्डर करेगी।`; a block
`name · N दवा` + `आज का दिन`; a line `शेल्फ 23:6 · ~4 दिन` / `खत्म`, `20 पत्ता` / `11 नग`, `नहीं चाहिए` → `इस बार नहीं` +
`वापस लो`, the tag `जोड़ी`; `पक्का` → `✓ पक्का — रिसेप्शन को गया HH:MM`; the bar `+ दवा जोड़ो` · `सब पक्का`; the add sheet
`दवा जोड़ो`, `नाम के पहले 3 अक्षर`, `जैसे मार्ग में लिखते हैं`, `सप्लायर चुनिए`, `इस नाम की दवा नहीं मिली`, `बंद करो`; the foot
`कल के ऑर्डर — क्या हुआ (N)` with `ऑर्डर हो गया HH:MM · माल आया ✓` / `अभी नहीं आया` / `फ़ोन नहीं उठा — रिसेप्शन फिर करेगी` /
`ऑर्डर बाकी`; refusals `अभी मार्ग की शीट से ऑर्डर हो रहा है`, `दवा का ऑर्डर अभी बंद है`; fail-soft
`सूची अभी नहीं खुली — थोड़ी देर में फिर देखिए`; the owner's line `Darpan ने पक्का किया HH:MM`; the notice
`आज का ऑर्डर तैयार है — कल का हिसाब पेज पर देखिए` → `/finance/darpan/kal#order`.

**The strip word is `पत्ता` and the unit word `नग`**, as the brief rules: they are the words `returns_desk.html` already shows after
a count, and no other Hindi strip word exists on a staff page. They are written by the tab's own `oqty()`, not through
`qty_words.py`: CLAUDE.md's pharmacy rule says quantities go through `qty_words.py`, but that module writes Roman/English words, and
this brief fixes Devanagari ones. The brief decides; named here. In the same way CLAUDE.md rule 12 says staff pages are Roman
script, and this brief rules Devanagari for the tab.

### 5 · The duty-map row (DUTY_MAP v7, in `claude_code_briefs/DUTY_MAP.json` + `.md` and in the kit)

`darpan.order_review` — person darpan; duty "Review today's order list and confirm it (Pakka) per supplier"; `duty_hi`
`आज का ऑर्डर देखना और पक्का करना`; tile `Kal ka hisaab`; door `/finance/darpan/kal`; door_marker `आज का ऑर्डर`; `due_sql` one
read-only SELECT returning `(n, since)`: today's proposals with status `open` when `order.source = darpan` and
`order.darpan_list_time` has passed (run on live before it was written in, and again after: `(9, '2026-10-05')`); allowed_days 1;
owner_line `Today's order list is not confirmed by Darpan: {n} supplier(s) still open since {since}`. The staff-eye walk signs in
as darpan and finds the marker on his door while the row is due (section 10), and the three older darpan rows on this page still
find theirs.

### 6 · `entries()` and `send_proposal`: anything beyond the one `held` condition

- `entries()`: the one condition (`l.get("held")` skipped) and the status read (`"darpan_ok" if source == "darpan" else "open"`,
  through `_proposals_today`'s new `status` parameter). Nothing more.
- `send_proposal`: the one condition, placed once — its base list is filtered (`if not l.get("held")`), and both line loops read
  that base, so one condition serves both loops instead of two. Plus the brief's status change (admits `darpan_ok`).
- `_mark_sources`: the brief's one word (`'darpan_ok'`).

### 7 · Calls made (the brief left them open; each also in the kit's README)

- `~N दिन` on a line is shelf ÷ daily sale (`days_left`). The line's own `cover_days` is the cover target (6 on every line), while
  the approved mock shows ~4 for PATOPAN DSR; both are sent, the tab shows `days_left`.
- An edit is taken only while a supplier's proposal is `open`; after पक्का the block is read-only. The engine's quantity is kept
  beside Darpan's (`qty_engine`), so K2 can compare them.
- A recipient login (the cash hand-over view) is refused on the order API. The owner may tap through the API, as the brief says,
  but his page draws no button.
- `send_notice` gained `to`, `text`, `url`, `title`; the 0930 notice lands on `/finance/darpan/kal#order`, which opens the tab.
- Supplier names stay as porders prints them (`Kedar`), also inside a Devanagari sentence.
- The read-back after placing runs the placed bytes on a fresh copy of the database, never a second process on the live one.
- A login with no role on the unit (bhati) is turned away by the app's own gate with 302 before the page's 403 (the brief said
  403); the same as the old file, and the walk checks it is the same.

### 8 · Not done, and why

- **The brief expected today's proposals to be `merged` already ("say so").** They were not: at 15:24 today had 9 `open` + 2
  `held` proposals, no Marg-sheet lines pending, and no purchase order made. The install followed the brief (source = darpan), so
  the tab went live today with today's list. This is said to the owner above. Nothing else was changed for it.
- The page's script could not be run on the server (no `node` there). It ran in a real browser at build time (section 3), and the
  walk reads the served page.
- The 09:30 notice was proven on a scratch copy; it has not yet fired on live (next order day, 09:30).
- The brief wrote `allowed_days` = "the order days (not Sunday)". In the map the field is a number, as in the existing rows, so the
  row carries `1`. Sunday is covered by the data instead: the engine makes no list on Sunday, so the row's `due_sql` reads 0 then.

### 9 · Noticed, outside the brief (nothing touched)

- **Darpan has no push subscription** (every `order_notice` row shows darpan sent 0). The 0930 notice is wired; it reaches him
  only once he subscribes on his phone.
- `order_rehearsal` (23:58) scores `order_proposal` rows whatever their status. From tonight it will score Darpan-edited lines,
  added lines included; whether added lines should count is for the chat (K2).
- Darpan's other duties on live now: spot counts 8 due since 28-Sep, return-shelf checks 48 since 02-Sep, name/ID disputes 33 since
  02-Sep. They are older than this kit and none is touched by it.
- The tab's header still reads "Sanjeevni — Kal ka hisaab" while the order tab is open.
- `.gitignore` gained the exact-path line `!deploy_kits/S485_DARPAN_ORDER_TAB/DUTY_MAP.json`. The blanket `*.json` rule would
  otherwise hide the kit's duty map, as for S482.
