# REPORT S593_ORDER_ENGINE_ONE_SOURCE — installed 19-Oct-2026, 08:03 IST

## For the owner

1. **Nothing changes in what reception orders.** Marg's open order is still the list (`order.source = marg_sheet`). This kit is plumbing under the order engine, which today reaches only Darpan's unused order tab and the weekly score.
2. **The engine now reads every item's stock from the one stock function and the one "goods arrived" rule** — the same figures your arrival lines and the stock page already use. This morning the engine's stock stood on the closing of 16-10 (the 17-10 09:20 print) carried forward by the spine's sales and purchases; before, it read the 18-10 09:37 morning print raw, which the one rule does not use until Amir's next export verifies it. 368 items stand on their count (the shelf figure), 16 on Marg's figure; none of those 16 moved against the old reading, and no item came back at 0 from "not printed".
3. **Suppliers' buying rhythm is now read from the spine** (Marg's purchase bills as the spine holds them). No supplier's cadence moved. The two "BASS PHARMA" spellings of the old tables are one supplier in the spine; L.K. Drug House counts 19 bills in 90 days instead of 24, still weekly.
4. **Reception's order page — the Yuvika fix you approved:** a supplier with a card under "Abhi baaki" is not repeated under "Ho chuke", and a done line from an earlier day shows its date. This morning the page reads "Abhi baaki: 1" with Yuvika's one card, and the 13 WhatsApp orders of 16-10 read "✓ 16-10 · WhatsApp gaya" under "Ho chuke: 13" (yesterday they read "✓ WhatsApp gaya" with Yuvika among them, 14). The banner, the buttons and every other word are unchanged — checked word for word on reception's, Darpan's, Amir's and Shavez's screens.
5. **Marg's "billed" mark on order lines works again.** The old rule had matched none of the 24 open order lines for weeks. On install the one rule marked 7 of them billed from Marg's own bills: ANKLE BINDER BAMBOO M (1 of 2 came — short 1), KNEE SUPPORT HINGED XL, CAST SHOE M TYNOR and L S BELT CONT GRAY UNISON XXX from Yuvika's bills of 28-09 and 07-10; CROCAL (24 of 30 — short 1) and PREGHYPE NT TAB from Shivaaz's bill of 01-10; BRUTAFLAM GEL from Gunina's bill of 06-10. Because of that, **Yuvika's card now shows 4 items** (ANKLE BINDER BAMBOO M 1, KNEE SUPPORT HINGED XL 2, L S BELT CONT GRAY UNISON XXX 1, RIB BELT UNIVERSAL UNISON 1) — the system catching up with the bills, not a new shortage. **One thing to know:** sizes of one orthotic (KNEE SUPPORT HINGED XL and XXL; ANKLE BINDER BAMBOO M and L) share one name key in the spine, so the first order line took the whole family bill (XL ordered 2, billed 6) and the other size's arrival is now called "not in Marg's purchases" on your Needs-you (two new lines: ANKLE BINDER BAMBOO L, KNEE SUPPORT HINGED XXL). That is a known gap of the arrivals rule (S583 named "one bill line answers at most its own units" as left for later) — for the chat to close, not this kit's.
6. Three small safety fixes for the day the order source ever leaves Marg's sheet (a sender cannot send a list Darpan has not confirmed; the heading and the duty map count the same suppliers) and one missing database rollback. No new setting, no new screen. **Installed and working:** healthz 200, every page answering, the service restarted once at 08:03:22 IST.

## For the chat

### Files, FROM → TO (read back on the box after placing, 08:03 IST)

| file | FROM | TO |
|---|---|---|
| /root/finance/order_rules.py | 79f21c1ee1f763b1ac06b370e3d77b79 | 8d078dbe1b63a4706dc6f35e3c31ac9a |
| /root/finance/porders.py | a5a823bf30661a4bf65ced39b2355500 | 78ea72be7d87a7c56c65de7d4c96a952 |
| /root/finance/porders_s454.py | 8307976393e6ea161f8d3a94bcb0692c | 40f1755a7655deb733765456b9a466fe |
| /root/finance/order_sheet.py | f00f0163bdd66a074c5af261c9b80a49 | 1f1e85c12c64521b50a10cea48220170 |
| /root/finance/darpan_kal.py | 8128598f745fca48a08472905f47da97 | 325d988c61e1c7408a2a4b687a4822bb |
| /root/finance/spine/spine_read.py | 712a1e4ef827f6be4e8b23415c3ceb62 | 827b00402add288d028c910128084b90 |
| claude_code_briefs/DUTY_MAP.json (the clone, by the publish — R1-B6) | 891defd8431e291b1a152f9e3c85f8c6 | c2ef9c6c5adb8c930b21bff5441cc017 |

Read-only pins printed at the open and unmoved: stock_figure 92367a19, shelf_figure 23b2394a, stock_watch c5f3ce21, purchase_app 60f2d846, order_sheet_pdf 7fca11db, darpan_kal.html 75d5a5b5, finance_ui/finance_approvals.html b32da7ff, porders.html 7a6799ae, aaj_kaam cd232b1c, amir_day 3af992d9, spine/spine_build e3d3ed85, spine/selftest_spine 7d0edb4a, item_alias 111a8e48, qty_words 706db7cc. Proved unmoved by the installer: finance_app, spine/order_rehearsal, portal.py, tile_grants.json, the crontab, spine.db's schema (a66309303c25178a291ada6fb539fbe5 before and after — no table added to the spine). 35 anchored edits, each anchor exactly once; compiled on both pythons. The spine at install: passed 13/13, last success 2026-10-19T08:00:46+05:30 (1 min old). Settings printed at the open as the brief's §2 (`order.model` does not exist); the DUTY_MAP darpan arm's SELECT run read-only on the live database: n = 0.

### The install (one run, one placement)

- **08:01:21** DRY run (every gate, the scratch sides, both walks) green. **08:02:18** the build lock taken; pins exact; the state BEFORE and as the NEW files read the same copy; backups; **08:03:22** the six files placed by rename in one command and `clinic-finance` restarted — healthz 200; /finance/porders, /s454/order, /darpan/kal, /amir, /reports/aaj, /porders/api/day all 302 without a login (the gate, expected); journal clean; `detect_supplies` once on the live database (below); the state AFTER; nothing else moved; `DOCTOR_AUTO_OFF` removed; md5 read-back as the table above. **08:03:31** DONE.
- The kit ran from `/tmp/s593kit` (SUMS checked on the box); the kit in the repository is byte-identical (SUMS re-checked in the clone after the publish).

### The walk on the box (the install run, 08:02)

`WALK OK S593: 82 checks, 34 controls green on the new files` · negative control: `every control red on the old files (34)`. All thirteen sections green; the staff screens word for word except reception's order page (F-916's two: "Ho chuke: 14 → 13", three "✓ WhatsApp gaya" → "✓ 16-10 · WhatsApp gaya" among the lines shown), Darpan's rows losing `why` / `cover_days`, the owner's api/day gaining `inputs`.

**Control 1 (the stock base, one function) verbatim:**
```
plan: engine spine, as_on 16-10-2026, 17 suppliers / 38 lines, no_closing 2; inputs {"sales_through": "2026-10-17", "capture": {"md5": "7f4d5832", "as_on": "2026-10-16", "end_day": "2026-10-16", "stamp": "20261017-092035"}, "spine_built": "2026-10-19T08:00:46+05:30", "counted": 368, "marg": 16, "absent": 0}
ok  C: every uncounted item's qty == int(round(marg + taps + scans)) from a direct stock_figure call with stock_watch.Spine(); every counted item's marg_qty == Marg's pure figure
ok  every counted item's qty == shelf_figure.figures(...)['shelf'] (368 counted)
386 master names: 368 counted (shelf figure), 16 on Marg's figure, 2 with no figure (no capture holds the key): ['LINVIZ 600 6T', 'TOLIVANT PLUS']
OLD _s470_snap: printed day 2026-10-18, 384 items, 2 missing; NEW as_on 16-10-2026. Uncounted items whose figure MOVED old -> new: 0
items moved from 'missing' to qty 0 (by='absent'): 0; the plan lines they produce: 0; items read by the whole key (by='key'): 0
```
On the OLD files the same control is red for 18 items (marg_qty = the raw printed-day closing ≠ Marg's carried figure; two master names not in the snapshot). Control 2: transit holds only the on-the-way lines (XGESIC LA 300, LANZOL JUNIOR 900); one item with an arrival the spine does not carry yet — LINVIZ 600: Marg 30 + scans 100 → the engine's 130.

**Control 3 (`detect_supplies`) verbatim — the 24 open lines, OLD (the tables' match) vs NEW (`carried()`):** the OLD rule matched **none** of the 24; NEW: 9 lines carried by the order's own vendor's bill (rules c / d), 3 by another supplier's bill (rule e — stock only, never the line), 12 no carrying bill. The writes on the copy and, identically, on the LIVE database at 08:03:
```
line 2    order 1   ANKLE BINDER BAMBOO M          YUVIKA SURGICALS       ordered  2 packs -> billed  1 by bill YS…2627  of 2026-10-07 (rule d) supplied 1  short 1
line 3    order 1   KNEE SUPPORT HINGED XL         YUVIKA SURGICALS       ordered  2 packs -> billed  6 by bill 672     of 2026-09-28 (rule d) supplied 6  short 0
line 28   order 10  CROCAL                         SHIVAAZ FORMULATIONS   ordered 30 packs -> billed 24 by bill 3463    of 2026-10-01 (rule c) supplied 24 short 1
line 30   order 10  PREGHYPE NT TAB                SHIVAAZ FORMULATIONS   ordered 20 packs -> billed 24 by bill 3463    of 2026-10-01 (rule c) supplied 24 short 0
line 36   order 13  BRUTAFLAM GEL                  GUNINA PHARMACEUTICALS ordered 24 packs -> billed 24 by bill GPPPL3679039 of 2026-10-06 (rule d) supplied 24 short 0
line 47   order 20  CAST SHOE M TYNOR              YUVIKA SURGICALS       ordered  1 packs -> billed  1 by bill YS…2627  of 2026-10-07 (rule d) supplied 1  short 0
line 50   order 20  L S BELT CONT GRAY UNISON XXX  YUVIKA SURGICALS       ordered  1 packs -> billed  1 by bill YS…2627  of 2026-10-07 (rule d) supplied 1  short 0
```
Every write is in packs (the bill's own line for the key); no rule-(e) write; where OLD and NEW hit the same bill the packs agree (no such pair — OLD hit nothing). Rule-(c) hits: CROCAL and PREGHYPE NT TAB (bill 3463 of 01-10, the order of 02-10 — `billed_date < created_at`, `lead_learned` clamps it at 0). With the spine made unreadable: returns 0, writes nothing, one stderr line. Idempotence: two open lines of TYRO BR from Kedar (order of 01-10) carried by bills 201 (01-10) and A000207_ (06-10) in one run; a second run writes nothing. **The visible effect of the writes** (the walk, then live): the orthotic card RIB BELT UNIVERSAL UNISON 1 → ANKLE BINDER BAMBOO M 1, KNEE SUPPORT HINGED XL 2, L S BELT CONT GRAY UNISON XXX 1, RIB BELT UNIVERSAL UNISON 1; the owner's arrival lines 9 → 11 (ANKLE BINDER BAMBOO L and KNEE SUPPORT HINGED XXL UNISO added — rule (b) after the family bill answered the sibling line). Open lines after: 17 (were 24).

**Control 4 (the rhythm) verbatim:**
```
rhythm(): 25 suppliers NEW vs 26 OLD (purchase_bill, NET amounts); differences: 2
   ('BASS PHARMA DISTRIBUTORS PVT', 'old only', 1, 'monthly')          -- one supkey in the spine with "… PVT LTD"
   ('L.K. DRUG HOUSE', 'bills90 24->19', 'gap 4->5', 'amount90_p 4079800->4528300')
suppliers whose CADENCE moved: none
```
The money basis is the report's bill amount (the spine); the tables gave the NET amount per bill.

**Control 6 (`days_left`) verbatim:** (i) every `_line_out` row carries `days_left` == the OLD `_s485_days_left` arithmetic (38 lines); (ii) the stored proposal 86 served by `_s485_line` with the same `days_left`, keys `['added', 'days_left', 'held', 'item', 'on_hand_text', 'packing', 'pid', 'qty', 'unit']`; (iii) Darpan added AKLAVE 1000 through his door: stored with `days_left: 27`, served with 27; the API rows carry `days_left` and not `why` / `cover_days`.

**Control 7 (F-916, the real case on the install-day copy) verbatim:**
```
the page today (?all=1): banner ['WhatsApp chala gaya: 14 supplier', '16-10 · 1:46 pm · Alisha (Reception) ne bheja']; still 'Abhi baaki: 1'; cards ['YUVIKA SURGICALS']; donehead 'Ho chuke: 14'
   13 lines '✓ 16-10 · WhatsApp gaya' (A.A. … YOGENDRA) and 'A.A. PHARMACEUTICALS ✓ 18-10 · Call se order ho gaya', each with Call
done orders since the newest sheet: 15; of suppliers with a card (not to be repeated): ['YUVIKA SURGICALS']; earlier days among them: 15
ok  C: the done block reads exactly D743's list; ok  C: Yuvika has ONE card and is NOT repeated under 'Ho chuke'; the banner stays
ok  C: a supplier with a card is not repeated (a today's order of Yuvika filtered); ok  C: the walk's 16-10 order reads '✓ 16-10 · WhatsApp gaya' with Call, today's '✓ WhatsApp gaya'
```
Note for the chat: the brief's §2 described 18-Oct's `done` as Yuvika's order #45 alone; on the box every WhatsApp order of 16-10 (14) is in `_done_today` (since = the newest sheet's day, 15-10), so the mock-up's SECOND rule (the date) is what the page shows today, not an empty "Ho chuke" block. Control 8: on darpan with a mixed Yuvika card ({ortho, proposal}) and an A.A. proposal the heading reads "2 supplier, 3 dawa" (the old count would be 2 / 8); the v15 map's darpan arm returns 2. Control 10: two failing sheets → two rollbacks. Control 12: selftest_spine 50 checks OK; the spine copy's bytes unchanged. Control 13: `order_rehearsal.keep` keeps 17-10 (3 lines, 3 proposals) with its keys; plan() 1.18 s against 0.86 s (limit 1.36 s).

### Backups, restarts, lock

- `finance.db.bak_S593_20261019_080218` (40,464,384 bytes, the backup API); `order_rules.py.bak_S593_79f21c1e`, `porders.py.bak_S593_a5a823bf`, `porders_s454.py.bak_S593_83079763`, `order_sheet.py.bak_S593_f00f0163`, `darpan_kal.py.bak_S593_8128598f`, `spine/spine_read.py.bak_S593_712a1e4e` beside the files.
- `clinic-finance` restarted once at 08:03:22 IST. Nothing else restarted.
- The build lock `/root/deploy/.claude_code_build.lock` taken 08:02:18 by S593, released after this report; `/tmp/s593*` removed.

### Not done, decisions made, and findings outside the brief

- **Not done:** no edit to `order_sheet_pdf.py` (R1-B5); no data step; `DUTY_MAP.json` not placed by the installer (R1-B6) — it reaches the box by the publish and the clone's pull (verified after the publish, below).
- **Decided (the brief left it open or the box differed):** the packs are read by `stock_figure.key_of` (the identity `carried()` used), not `sw.key` — the same key, renames included; a hit with 0 packs is skipped (nothing written); the `inputs` note is kept per thread for `plan()` and per process for the owner's api/day (`None` until a plan is made in that process — the cron's plans are another process); the heading's filter reads `sources` as the LIST `entries()` hands out (R1-C11 said set); the brief's grep "no `purchase_line` / `EFF_LINE` in porders.py" is scoped to `detect_supplies` — `porders._movements` (S403's orthotic shelf, the tables when the spine is not fresh) keeps one such read, SEEN, not this kit's; `detect_supplies` on live was run directly (not through `cron_pass`, which would also send notices) — the ten-minute tick runs the same pass.
- **Finding — the 20-letter key families** (charter 12, S583's "left for later"): one spine key for the sizes of an orthotic means `carried()` + the bill's packs for the KEY marks the first open line with the whole family bill (KNEE SUPPORT HINGED XL: ordered 2, billed 6, supplied 6) and rule (b) then keeps that bill from the sibling line (XXL stays open, and the owner's arrival line "KNEE SUPPORT HINGED XXL UNISO … not in Marg's purchases" appears; likewise ANKLE BINDER BAMBOO L). The brief ordered this shape (R1-B2); the fix is units-based, per-line matching in `stock_figure` — a brief of its own.
- **Finding — `detect_supplies` had been dead:** the OLD table rule matched none of the 24 open lines (no effective `purchase_line` row matched by the 27-letter clip), so Marg's "billed" marks stopped weeks ago; the one rule carried 7 at once — the orthotic card and the owner's arrival lines moved on install day (named above for the owner).
- **Finding — the install-day state vs the brief's §2:** order #45 (Yuvika, 16-10) is `received` now, and 14 orders of 16-10 are in `_done_today`; the page shows the dated lines, not an empty done block.
- **Permissions:** the memory folder under the user's profile is denied by this folder's settings (`Write(~/**)`), so no memory note was saved for this session; nothing else asked or was refused.

### Charter

- **Retired:** `_s470_snap`'s own `sp.closing()` read and equal-share family split; `_s470_arrivals`; `detect_supplies`' `purchase_line` read and `ia.clip` match; `rhythm()`'s `purchase_bill` reads; `darpan_kal._s485_days_left`; `why` / `cover_days` on Darpan's API; `ON_ORDER_DAYS`; the dead loop in `lead_learned`.
- **Left (named):** `order.engine_source = tables` and the four `purchase_app` table reads (4b-2); the old page's `owner_cards` settings card (Kit II); `fixed` vs `levels` (Kit II); the three other `purchase_bill` reads in order_rules.py (rung 5); `_k20` for held sets (rule 12); the second Spine class (rung 5).
- **Seen, not touched:** `stock_watch.expected_units`; `_s454_shelf_snap` (two anchored edits only); `order_sheet.entries`' orthotic card; `porders.html ?old=1` English `why` lines; `order_sheet_pdf.py`'s stale comment at 22; `porders._movements`' table fallback; the key families (above).
- **Behaviour changes (rule 4, 1b):** an item the closing did not print but the spine knew stands at 0 and may be listed (none today); the rhythm's money basis is the report's bill amount; a rule-(c) bill may date a line's `billed_date` before its order day (CROCAL, PREGHYPE today); `detect_supplies` lives again.
- **Dependency state at install:** `order.source = marg_sheet`; the spine 13/13, 1 min old; the 18-10 09:37 start capture `pending` (the engine's `as_on` 16-10 until Amir's next export; `inputs` says so); count #1 at stage C.
