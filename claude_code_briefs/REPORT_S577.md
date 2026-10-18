# REPORT S577_STOCK_ON_SPINE — one place works out stock; the voucher check gains its second half; the Loss desk only reads

**For Dr Manoj:**
1. **One place now works out stock.** A new module gives, for every item, Marg's figure and the shelf figure, each with the closing it stands on. The voucher check for Amir, Darpan's spot counts and their loss lines, the shelf-gap flags on Darpan's spot list, the "bill entry baaki" line and your *stock now* and *drift* pages all ask it. Installed and working on the server at **12:14 IST today**; every screen answers as before (checked as Amir, Darpan, Shavez, reception and you).
2. **One name for an item.** A renamed item is recognised under its old and new names: the voucher check no longer calls it "not readable", and the 01-Oct Yuvika knee-immobiliser bill that "bill entry baaki" had lost is found. Two sizes that share Marg's short name are told apart at a closing and treated as one family between closings.
3. **A closing's time is the time Marg made it**, never the time the PC re-sent it at 22:30. Today's figures stand on the closing taken **17-10 at 09:20 for the end of 16-10**; the one taken this morning at 09:37 (inside shop hours) is not used.
4. **The voucher check has its second half.** A voucher line is never given to Amir when it would take Marg past the shelf figure; such a line is yours, on Needs-you, with its own sentence. Today no voucher line is pending or held, so nothing on Amir's card changed.
5. **Opening the Loss desk no longer changes the count.** The desk only reads. The two lines the system closed on 27-09 (DOLOGESIC SP, TYCOB 1500) stay as they are; the desk's data now carries the line *"2 lines were closed by the system on 27-09 as 'sold after count'…; from now on such lines are yours to decide."*
6. **What staff see changed in one place only:** Darpan's spot list loses the 22 shelf-gap reasons that were judged on this morning's shop-hours closing; judging starts again from two clean closings (the first clean set is written by the order-rules tick, within ten minutes of the install). A spot count on a size that shares a family figure (the knee supports, the belts, the splints, the binders, the immobilisers) is written down with the plain receipt only, no verdict, and goes to you as an approximate line, never as a loss.
7. **The old ways run beside it for one week.** The first side-by-side file is written; the nightly line for the crontab is in the kit's README for the parent to add (the crontab is the parent's).

---

## For the chat

**Kit:** `deploy_kits/S577_STOCK_ON_SPINE/` (board `_numbers` v472 → v473 is the chat's line). Installed 18-Oct-2026 from `/tmp/s577kit` (byte-identical
to the kit folder: `md5sum -c SUMS.md5` OK on the box before the run): lock taken **12:10:36 IST**, the spine files placed and the live spine
built **12:13:19 IST** (the cron command under `flock -w 300`), `clinic-finance` restarted **12:14:00 IST**, the first witness file written
**12:14:13 IST**, DONE (the box's `date`) 12:14:29 IST. The DRY run before it (12:06 IST) was green end to end.

### Live files — FROM → TO, md5 read back on the box

| file | FROM (pin matched at the open) | TO (read back after placing) |
|---|---|---|
| `/root/finance/stock_figure.py` | absent | cb5f24aacf7748752206619ce8bbb1e3 (NEW) |
| `/root/finance/stock_app.py` | 050587dfb5951da65f95937615ddf144 | f279a3be440878bb30e418c20a5cf608 |
| `/root/finance/shelf_figure.py` | 183c70fabb64ed1e5a43c645a225c560 | a544afda07b4632e9bc05e97c256dde6 |
| `/root/finance/stock_watch.py` | 0e6a42c4c7ae51eb8f8a0869fce2d101 | bc6885217a9f7ca7d8273021fcf6315a |
| `/root/finance/loss_piles.py` | 81ae481e4480a12fead3016515037214 | 2b9023fd06aadc0ddaef30e2f26eccb3 |
| `/root/finance/spine/spine_build.py` | 5d8b1f94d80189c16b2ee5b1e093429c | e3d3ed85973eab2df0326dc9621e230e |
| `/root/finance/spine/selftest_spine.py` | fc63d2c683a1970c58f60502302187a9 | 7d0edb4aafb17c83cf07be1052623f76 |

Read only, at their pins at the open and unmoved after: `item_alias.py` 111a8e48, `stockmatch.py` 10e30d28, `amir_day.py` 73882a83,
`order_rules.py` 79f21c1e, `qty_words.py` 706db7cc, `spine/spine_read.py` 712a1e4e, `purchase_app.py` 98f7d9f0, `order_sheet.py` f00f0163,
`porders_s454.py` 83079763, `porders.py`, `darpan_kal.py`, `finance_app.py`, `portal.py`, `tile_grants.json`, `DUTY_MAP.json`, the crontab.
Built on the box from the live bytes by `make_s577.py` (65 anchored edits on five files, each anchor exactly once; `stock_figure.py` placed byte
for byte); every built file compiled on `/usr/bin/python3` and the venv python; the placed files are byte-identical to the walked ones (`cmp`).
The five finance files were staged beside their targets and renamed in ONE command; the two spine files first (§5 of the brief).

### Backups and services
`finance.db.bak_S577_20261018_121036` (backup API, 40,177,664 bytes). `stock_app.py.bak_S577_050587df`, `shelf_figure.py.bak_S577_183c70fa`,
`stock_watch.py.bak_S577_0e6a42c4`, `loss_piles.py.bak_S577_81ae481e`, `spine/spine_build.py.bak_S577_5d8b1f94`,
`spine/selftest_spine.py.bak_S577_fc63d2c6`. **Services restarted:** `clinic-finance` only, once (12:14:00 IST). Before the restart the kit wrote
`/root/deploy/_off/DOCTOR_AUTO_OFF` (S578's off-switch) and removed it once healthz answered 200 (12:14 IST; the installer's step 11 line says so).
healthz 200 after the restart; `/finance/amir`, `/finance/stock/page/now`, `/finance/stockmatch`, `/finance/stock/page/loss` 302 to a plain curl
(the login gate, expected); the journal clean (no Traceback, no "NOT mounted").

### The spine (step 9, the spine first)
`spine_build.py` and `selftest_spine.py` placed; the live build by the cron command (`spine_evidence.py` then `spine_build.py`, `flock -w 300`)
swapped at 12:13:19 IST: `spine_state.json` passed, gate **13/13**; `sp_close_name` **22,315 rows over 55 captures**; `sp_close` **unchanged**
(14,211 rows, content hash `99973eda2d40` before and after the build) and **equal to a build of the same readings by the OLD builder** (the
backup's `spine_build.py`, run on a fresh copy of the live readings: R3-C13). The selftest on the new builder: `SELFTEST OK 50 checks` (45 + 5).

### Charter 1b — the dependency's state at install
The spine: passed, gate 13/13, last success 12:00:45 IST (9 minutes before the lock). The order-rules tick (`*/10 5-21`, the writer of the gap
sets) runs as before; `record_gaps` writes nothing until `stock_figure.ready()` is True, which it is since the live build. The collector was not a
dependency of this kit. **3.3 E:** no `stock_shelf_fix`, `stock_sales_test` or `stock_diff_lane` row written by the system on or after 2026-10-18
(the desk's 09:52 opening wrote nothing) — checked by the installer and the walk; the four system rows on record are the two of 27-09 and their two
`stock_sales_test` rows, untouched.

### The install-day state (printed BEFORE with the live files, as the NEW files read the same copy, and AFTER placing)
- **Count #1:** stage C, lot 3; A total 7, entered 7, open 0, **pending 0**; C entered 30/30, released 30, wrong 4 (FOLITRAX 15 MG TAB, KT ROS
  DT, VINBACTUM DS, OSTOVAXL DM — "do not agree with Marg's closing of 16-10-2026": unchanged by this kit; stages A and C give identical verdicts
  on the old and the new files, control 8).
- **Voucher lines:** pending (unfrozen) lines offered 0, held 0, unread 0 on both files; frozen batches not entered 0 (all 37 non-void batches
  are entered). **No line flips; `A["pending"]` stands at 0** — before, as the new files read it, and after placing. Nothing on Amir's card moved.
- **Shelf figures (the count's 373 names):** old 373 with a figure (22 approx, 2 below zero), on Marg's closing of **18-10** (the 09:37 shop-hours
  capture); new 373 with a figure (23 approx, 2 below zero), on the usable closing of **16-10**. Counted items whose figure moves: **3** —
  KNEE IMMOBILIZER UNISON L 1 → 0, KNEE IMMOBILIZER UNISON XL 2 → 0, KNEE SUPPORT HINGED L 4 → 1 (the usable capture instead of the 18-10 one;
  the family's movements split by counted share through `key_of`). **21 renamed items reach their count under the old name** (no shelf figure
  before, one now: the ankle binders, pelvic belts, knee immobilisers, knee supports, LS belts, shoulder immobilisers, wrist splints) — their lines on
  the ordering pages now stand on the shelf figure instead of Marg's. The 18 items with no count on either side are equal before and after on the
  order plan (control 7).
- **Gap flags:** old newest set 2026-10-18 (judged on the 09:37 capture), **22 flagged**: CAST SHOE M TYNOR, CEECIT MZ, CHYMORAL AP, CROCAL, DECA
  INSTABOLIN 50, ENZOMAC PLUS, FOLITRAX 15 MG TAB, INTACOXIA-60, KT ROS DT, LACTOVAX SYP, MET4MIN GL 1, NEWTEL H 40, PANOPLUS GEL, PANSPED L,
  PANTOCID DSR, PARI CR 12.5, PRETOL 8, PROTICO CHOCOLATE, ROSIKA FORTE, THIO Q AP, VINBACTUM DS, ZIBON EXTRA. New: no set yet at install (the
  tick writes the first one); on the walk's copy the first pass wrote **one set of 368 live rows for the end of 16-10** (capture 7f4d5832, judged
  against the usable capture of the end of 15-10, taken 16-10 05:17) with **0 of the 22 old flags carried** and **0 live items flagged** (the
  one flag was the walk's own item). `s454_shelf_gap`: 4,574 rows, content hash unchanged.
- **The spot roster's reasons:** latest live day 17-10 — ANKLE BINDER L BAMBOO *"you asked for it · carried from 14-10-2026"* (unanswered),
  PRETOL-4 *"the shelf figure and Marg moved apart · received 08-10-2026, not counted since · short at the last count (10 strips + 6 tabs)"*
  (unanswered) — unchanged by the install (rows already written). A forced roster for tomorrow on the copy: XQ10 *"received 15-10-2026, not
  counted since · short at the last count (8 tabs) · sells 1 tab a day"*, ROSIKA FORTE *"received 15-10-2026, not counted since · short at the
  last count (17 strips) · sells 4 strips + 3 tabs a day"* — no gap reason (no s577 set yet).
- **Items absent from the newest capture but counted (27):** 22 are the renamed items' old names (their spot count is now judged as **approx** —
  no verdict); 5 read **0 by 'absent'** and are judged on the shelf basis (ANKLE BINDER FLAMINGO M → 0, ANKLE BINDER TYNOR XL → 2, KNEE
  IMMOBILIZER 14 M TYNOR → 0, PREDNOSIS 8 → 0, KNEE IMMOBILISER UNISON M → approx). Before, a spot count of any of them read *"Marg mein yeh item
  nahi mila -- ginti likh li"*.
- **Staff words that changed (read as each login on the installed bytes):** amir `/finance/amir`, steps 1 and 7, `/api/pad/amir/1`: unchanged;
  darpan `/finance/stockmatch`, its state API, `/finance/darpan/kal`: unchanged; shavez `/finance/reports/aaj`: unchanged; reception
  `/finance/porders`: unchanged; manoj: the hub page unchanged, the hub API gains `not_shelf: 0` twice (A and C), the Loss desk API carries the
  kit's version and `system_closed`, `/api/now` and `/api/drift` carry the new figures of record (as on 16-10-2026, the capture of 17-10 09:20),
  Needs-you loses the 22-item gap line (no set yet) and the 01-10 Yuvika line (the walk had blanked that tie on its copy; live it is tied).

### The walk (the installer's run, on backup-API copies of the live finance.db, assets.db, the readings and a scratch spine built by the new builder; the real app; the walk's own session)
`WALK OK S577: 82 checks, 39 controls green on the new files` · negative control: `27 controls red on the old files` (every control that ran went
red; two sections crashed on the old files — the guard has no `pack` argument, `stock_point` has no `basis` column — each counted as one red). Per
control (red on the old files → green on the new):
1. KNEE SUPPORT HINGED L (the voucher's old name) is judged by the guard, a closing read (old: `unread=True`, "not readable"); approx with the four
   sizes under its key; VINTAZ P 4500 INJ (renamed, alone under its key) is not approx, its closing read by name.
2. The 01-Oct Yuvika KNEE IMMOBILIZER UNISON L line with its tie blanked is NOT "bill entry baaki" (old: *"bill entry pending: YUVIKA SURGICALS,
   arrival tapped 01-10-2026"*).
3. The walk's own item (closing 90 at the end of 16-10; Marg 140; shelf 160; tol 10): an ISSUE of −40 is held `past_shelf` (after 100); +15 is
   offered (155, judged); a frozen line already inside unkeyed landing on 160 is not held; a RECEIVE of +40 is held (180); the residual 30 = the
   purchase of 15-10 → "not judged against the shelf". Old: `_voucher_guard()` has no shelf test (TypeError).
4. The capture rule, unchanged on both files: printed 17-10 taken 18-10 05:17 → the end of 17-10; printed 18-10 taken 09:37 → unusable; taken
   22:30 → the end of 18-10; 08-10's captures → the 06:00 one stands for the end of 07-10; four captures stand for the end of 10-10 and the newest
   by stamp (10:35) is chosen; today's newest usable capture is 7f4d5832 (printed 16-10, taken 17-10 09:20).
5. Two reads of `/api/loss/1/piles` across a same-inputs spine rebuild: one build (`built=full` then `built=cache`), nothing written outside
   `stock_pile_cache` / `stock_pile_cache_meta` (every table's row count compared); a new export forces one build, again with no outside write
   (old: rebuilt twice). The desk carries the `system_closed` line. An open shortage that sold more since the count than counted + bought (ONKET
   DT, the walk's own sale of 500 strips) stays OPEN in its pile with *"sold after count: 592 strips + 9 tabs sold since 06-09-2026 against 5 strips
   counted + 90 strips bought -- …"* (old: `writeoff` with no such words — `sales_test` would have closed it); a full rebuild writes no
   `stock_shelf_fix` / `stock_sales_test` row.
6. A shelf-basis provisional point is settled on the shelf basis against the base before it (expected 160, gap −10); a corrected spot count keeps
   its basis; an approx point (KNEE SUPPORT L HINGED) stores NULL expected and NULL gap, its receipt is *"Likh liya: KNEE SUPPORT L HINGED — 1 nag."*
   with no verdict, no loss line, no trace, absent from `month_leak`; corrected it stays approx (*"Badal diya: … — 2 nag."*); *Kuchh gadbad hai* on it
   records the text and opens no trace; the owner's watch card carries *"counted N against a family figure (approximate) — not judged"*.
7. 18 items with no count → `shelf=None` (old: Marg's figure); the plan's lines for them equal; the 3 moved figures and the 21 renamed items printed.
8. `key_of` = the old `_s524_key_of` for all 198 items of the 207 voucher lines (37 non-void batches); stages A and C identical on both files.
9. The first pass writes ONE `s577_shelf_gap` set for the newest covered end day (16-10) from its usable capture, judged against the usable capture
   before it; a second pass writes nothing; `s454_shelf_gap` unchanged (4,574 rows, hash `5aa683dabf0c`); the roster's reasons before and after printed.
10. A `past_shelf` held line prints *"… the count-day sum asks -4 strips; it would take Marg to 10 strips against the shelf figure 16 strips (closing of
    16-10, taken 09:20): not given to Amir"* (old: the below-zero sentence); the summary gains *"not judged against the shelf for 3 item(s) (…)"*
    beside *"closing not readable for 1 item(s)"*; a `not_ready` line prints *"held: the spine's closing table is not ready yet"*.
11. With `sp_close_name` absent (the OLD builder's spine): `ready()` False; every lowering line HELD `not_ready`, a raising line not held;
    `record_gaps` writes nothing.
12. PREDNOSIS 8 (counted, not printed, known to `sp_item`) reads units=0 by 'absent'; the 27 absent items printed with what a spot count of each is judged against now.
13. The grep tests on the built files: no `def latest_snapshot`; no `stock_snapshot` inside the moved readers; no `sp.key(` in `bill_pending_lines`,
    `_arrivals`, `scan_arrivals`; the capture rule and the stamp parser defined in `stock_figure.py` only; no `sales_test(` call; no `_s524_capture`;
    no `s454_shelf_gap` read; `_voucher_held` and `latest_close_day` gone; `_voucher_void` kept; no file outside the kit reads `s454_shelf_gap`
    or `shelf_figure.latest_snapshot`.
14. Staff-eye: every login's portal home renders its tiles (amir 3, darpan 8, shavez 18, reception 10); the pages above answer 200.
15. Amir's card 1.34 s / 6,607 bytes; his pad 1.19 s / 28,727 bytes; no run of ten digits in the output.

### §7 — what only the live spine could confirm (read at the open, 11:05 IST, on backup-API copies)
1. Accepted full closing captures: **55** (56 STOCK_CLOSING exports, all ok; one category-filtered print is not full); **43 usable**, 12 unusable
   (shop-hours captures). End days with more than one usable capture: **7** — 31-03 (3), 05-09 (4), 17-09 (2), 21-09 (2), 25-09 (2), 06-10 (2),
   10-10 (4: 07:11, 09:39, 09:52, 10:35 on 11-10 — the 10:35 one, 76eb46af, is chosen, as `sp_close` already does).
2. `sp_close_name` names against `stock_count_item` / `stock_snapshot`: every capture name is a `stock_snapshot` name (the one exception was an
   empty name, which `sp_close_name` now skips); the count's names not printed in the newest capture are the 22 renamed items' old names and 5
   zero-stock items (ANKLE BINDER FLAMINGO M, ANKLE BINDER TYNOR XL, KNEE IMMOBILISER UNISON M, KNEE IMMOBILIZER 14 M TYNOR, PREDNOSIS 8).
3. Names printed with two packings in one capture: **0** (and no name printed twice in the newest capture).
4. Families in the newest capture (8 keys, renamed pairs folded): ANKLE BINDER BAMBOO (L, M); BLING PELVIC TRACTIO (L, XL); KNEE IMMOBILI?ER UNI
   (family) (L, XL); KNEE SUPPORT HINGED (L, M, XL, XXL); L S BELT CONT GRAY U (L, M, XL, XXL, XXXL); SHOULDER IMMOBILISE (L, M, XL); TYNOR WRIST
   SPLINT L (LF L, LF M); TYNOR WRIST SPLINT R (RT L, RT M).
5. `sp_item` holds every one of the 199 voucher items by exact name (198 in non-void batches) — `key_of` equals the old key for all.
6. The gate stays **13/13** with the new table (the scratch build and the live build).

### The first witness file — `/root/finance/spine/stock_figure_witness_Sun.txt` (12:14:13 IST, 98,724 bytes)
Newest usable capture: printed 2026-10-16, taken 2026-10-17 09:20:35 (7f4d5832). The PC's newest push_expected: day 17-10-2026, received 09:51:08
today, 395 items; marg_shadow's newest run: as on 16-10-2026, 111 lines. **`marg()` against `expected_units`: 20 items a pack or more apart** — every
one is a family member (the knee supports, LS belts, shoulder immobilisers, wrist splints, pelvic belts, ankle binders: `expected_units` gives the
whole family's `sp_close` figure to each size) or FOLITRAX 15 MG TAB (126 vs 120), and for every item the two read different closings (16-10 by
name vs 18-10 by `sp_close`, the shop-hours capture the old way takes by its printed day). `marg()` against the PC's push: 165 items apart;
marg_shadow (server vs PC): 102 lines apart — the PC's base and reach, for 4b-2. The nightly line for the parent's crontab:
`58 23 * * * cd /root/finance && /root/wa/venv/bin/python3 -B stock_figure.py witness >> /root/finance/spine/stock_figure_witness.log 2>&1 # S577_WITNESS`
(without the spine lock: read only).

### Calls made (no question was put to the owner)
- **The HTML pages are outside the brief** (`stock_now.html`, `stock_drift.html`, `stock_loss.html`, the watch card in it): the new fields ride in the
  JSON only. The *stock now* page's three columns now show the shelf figure (None where no count), Marg's figure on the usable capture, and the gap;
  the PC's old estimate reaches the JSON for the doctor role as `pc_old` headed *"PC's old estimate (retiring)"*; the Loss desk's line is
  `system_closed.text`; the watch card's line is `approx_lines`. **Charter: left out** — the headings on the pages themselves (a template kit).
- **A provisional point is re-judged against the base before it** (`exclude_id`): the point itself is the newest count, so without this the shelf
  figure would be its own quantity and every settlement would read gap 0.
- **`movements` and `boundary_purchases` inside `shelf_figure.py`** also key the spine by `key_of` (the brief named `bill_pending_lines`, `_arrivals`
  and `scan_arrivals`; these two live in the same file and feed the same figure — a second identity there would be a second answer, charter 2).
- **`s454_shelf_gap`'s DDL went with its last reader** (the table stays untouched as a record; nothing creates or reads it now).
- **The nightly witness line is not added to the crontab** (the brief: "the crontab is the parent's: one line in the README"); the installer wrote
  the first file by hand.
- **The guard's tolerance setting has no row** (`seed=None`): the default 1 pack is read, so the desk's stamp did not move at install.

## Charter
- **Retired:** `sales_test`; `shelf_figure.latest_snapshot`; `_s524_capture` / `_s524_captures` / `_S524_CAPTURES` (the stock_feed moment lookups);
  `_voucher_held`; `Spine.latest_close_day`; the bare-clip spine keys of `bill_pending_lines`, `_arrivals`, `scan_arrivals` (and `movements` /
  `boundary_purchases`); `s454_shelf_gap` as a read; the second copies in `stock_app` of the capture rule, the stamp parser, the reach and the
  residual match (one-line wrappers now).
- **Left for later, with its rung (§3.4):** `/api/snapshot` and `reconcile` (rung 5 / 4f); the count's own figures (`_three_way`, `_r_stock`,
  `_newest_snapshot`, `_snapshot_qty_map`, `_item_life`, `_pad_report_data`, `stock_statement.build`, `full_count_points`, `loss_piles.fixes`,
  `porders.shelf` / `ortho_items`) — rung 4f; the order engine (`_s470_snap`, `_s454_shelf_snap`, `purchase_app._latest_snapshot`, `kedar_review`)
  — S486 B / rungs 4a, 4c; the list readers of `stock_snapshot` and `marg_spine.py`'s identity — rung 5; `stock_spot_check` — rung 4d;
  `expected_units`, push_expected, marg_shadow — 4b-2 after seven explained nights; the stage proof's own table onto `captures()` — the morning-flow
  kit; at count #2 `_s454_store_shelf` stores NULL for an uncounted item (announced).
- **Named limits:** R2-C18 — a voucher typed in Marg before the capture but recorded here after it is counted twice in `unkeyed`; no grace.
  R3-C5 — two absence rules stand (`closing()`: 0 when `first_seen <= as_on`; `_s524_table`: 0 only when `first_seen > R.as_on`, else
  `absent_before`) until the morning-flow kit makes them one. The accepted `seen_name` read (`marg_item_rename_event`, event `accepted`, for
  `done_rows`' ids only) is a read `item_alias` should own at its next kit.
- **Seen, not touched (charter 12):** the order lines in `_arrivals` / `scan_arrivals` are still matched by `pad_norm(name[:27])`. `stock_snapshot` is
  still written by `/api/snapshot` and read by the list readers (rung 5) and the count's own figures (rung 4f). The witness shows the old
  `expected_units` reading the 18-10 shop-hours capture by its printed day for every item — the very thing 4b-2 retires.
- **Dependency at install (rule 1b):** the spine, green and 9 minutes old at the lock; `sp_close_name` filled by the live build before the five files
  were placed; the order-rules tick writes the first gap set. **DUTY_MAP:** no duty added, moved or removed — not changed.

### Not done, and why
- The HTML column heading *"PC's old estimate (retiring)"* is not drawn by the page: the templates are not in the brief (named above; the heading is in the JSON).
- The crontab line for the witness is not added (the crontab is the parent's; the line is in the README and above).
- The 27-09 system rows are not marked; the 18-10 desk check found nothing to stop on.

### Publish and the lock
`PUBLISH_ALL.bat` is run after this report is written; the commit, the server clone's pull, `md5sum -c SUMS.md5` there and the lock's release are
written below in the line added after the publish, and the report is published once more after it.

### Undo (if the owner says "undo")
`\cp -p` each `.bak_S577_<from8>` back over the six files (four in `/root/finance`, two in `/root/finance/spine`), `rm -f /root/finance/stock_figure.py`,
`systemctl restart clinic-finance`, healthz 200, read the md5s back (the FROM pins). `sp_close_name`, `s577_shelf_gap` and `stock_point.basis` stay
(additive; nothing old reads them). `finance.db.bak_S577_20261018_121036` is the full copy from just before placing and is not needed for the undo
(the kit writes no data).
