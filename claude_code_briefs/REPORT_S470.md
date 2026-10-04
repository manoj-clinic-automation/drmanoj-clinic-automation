# REPORT S470 — S470_ORDER_ON_SPINE · installed 04-Oct-2026 15:04 IST · published

## For the owner

- **The system's own medicine list now works from the one checked record of Marg's figures.** Until today it read its sales, stock and
  suppliers from older tables that nothing checks. It now reads them from the store that is compared with Marg every ten minutes.
- **No staff screen changed.** Reception still orders from Darpan's sheet. Nobody has anything new to do.
- **The nightly trial now scores the list the system really made.** Before, it scored a list nobody ever saw.
- **Your old Purchase-orders page has one new line a week**, under "Who decides the order". The first score is not ready: nothing is 7
  days old yet. The first week is scored on the night of 05-Oct; the "bought within 14 days" part from the night of 12-Oct. Today the line
  reads: "The weekly score is not ready yet. The first week is scored on the night of 05-10-2026."
- **On today's figures the new list is the old list plus one line** (ROSIKA FORTE, 10 strips, from Deepam). No line went and no quantity
  changed. The list's value reads about 4% higher (Rs 57,999 against Rs 55,753), because the cost now includes tax.
- **39 medicines were sold but never bought on any bill Marg has given the server.** The system orders them from nobody; your page now
  counts and lists them. Two need a look: RIFAVAX 550 (about 5 days of stock) and GLI-ME SR1 (none on the shelf figure).
  https://followup.dr-manoj.in/finance/porders?old=1

## For the chat

### The six files — FROM → TO, read back on the box (15:05:50 IST)

| file | FROM (the brief's pin, read live 13:42 IST) | TO (md5sum after placing) |
|---|---|---|
| /root/finance/order_rules.py | 734fc6bcd67bb23da1bea2a6e927fcad | dac12be4c4a537d7ad2e4584a3423e6a |
| /root/finance/purchase_app.py | 979391b6e191e0d2468f3db6fc57366e | 254b77939ca40d20e46509a678bcb5d8 |
| /root/finance/porders_s454.py | c3562c5bc5602ecdb32e416a231ba30c | 3681622b11043116f40bc0d4c3b557ad |
| /root/finance/spine/spine_read.py | ab55344ee280b0b4847a45cebe6d3843 | 712a1e4ef827f6be4e8b23415c3ceb62 |
| /root/finance/spine/selftest_spine.py | bfa607b980e4e838dfc7198f0bc7c9c9 (read live; no pin in the brief) | fc63d2c683a1970c58f60502302187a9 |
| /root/finance/spine/order_rehearsal.py | 02582fbea29f51606a6ba8bb8694d3fc | 104d366d2e284ccfedef46ca0a744230 (replaced whole) |

- **Read back at 15:05:50 IST** (`md5sum` on the box): the six TO pins above. The installer's own read-back after placing gave the same.
- **Health:** finance healthz 200. These answered 302 (the login gate, expected): `/finance/porders`, `/finance/porders?old=1`,
  `/finance/amir`, `/finance/stock/page/count`. The journal since the restart has no "NOT mounted", no Traceback, no NameError.
- **Restarted:** clinic-finance only, once (ActiveEnterTimestamp 15:04:48 IST).
- **Backups:** `finance.db.bak_S470_20261004_144048` (backup API, 30,859,264 bytes). Beside the files, each read back at its FROM pin:
  `order_rules.py.bak_S470_734fc6bc`, `purchase_app.py.bak_S470_979391b6`, `porders_s454.py.bak_S470_c3562c5b`,
  `spine/spine_read.py.bak_S470_ab55344e`, `spine/selftest_spine.py.bak_S470_bfa607b9`, `spine/order_rehearsal.py.bak_S470_02582fbe`.
- **The data step:**
  - six new rows in `setting`, each at its present value: `order.engine_source` spine · `order.pace_days` 28 ·
    `order.dead_after_days` 60 · `order.on_order_days` 4 · `order.in_transit_days` 14 · `order.lot_history_days` 180;
  - the trial kept 28-Sep to 03-Oct in `spine/orders/` (six files), after copying S341's six files of those nights to
    `spine/orders/before_S470/`. It wrote `order_score_latest.json`. `spine.db` was not written.
- **One live tick of `order_rules.py`** after placing (15:04:56 IST) exited 0.
- **The live engine, read once read-only after placing:** `engine=spine`, the closing of 04-10-2026, 376 items, 239 with a pace, 210 with
  a supplier, 6 with goods on the way, none missing from the spine's closing. `order.source` is still `marg_sheet`, `order.stock_basis`
  still `count`.
- **The owner's line as the live code builds it now:** "The weekly score is not ready yet. The first week is scored on the night of
  05-10-2026."
- **Untouched, md5s compared before and after by the installer:** finance_app.py, portal.py, tile_grants.json, shelf_figure.py
  (23c34ebb), stock_watch.py (6d4d660f), order_sheet.py (a5408df0), porders.py, packs.py, asset_register.py, spine/spine_build.py
  (ce99bedf), spine/marg_read.py, sanjeevni_approvals.py, supplier_msg.py, stock_app.py. The crontab is as it was (78 lines; the
  rehearsal's line and the order_rules line unchanged).
- **The crons' own commands as scripts** on the built files, on scratch copies, before placing: `order_rules.py tick`,
  `stock_watch.py job`, `purchase_app.py rematch` and `spine/order_rehearsal.py` each exit 0.

### What was built (kit `deploy_kits/S470_ORDER_ON_SPINE/`)

- **A — the read door** (`spine_read.py`, 3 anchored edits): `sales_daily`, `stock_series`, `purchase_lines`, `family`, `last_sale`,
  `closing`. Nothing existing changed. `selftest_spine.py` gains one check per method: 39 → 45 checks.
- **B — the engine** (`order_rules.py`, 6 anchored edits: one block above the `__main__` guard, five small edits inside `plan()` and
  `_on_order_units`). `_snapshot_inputs` is wrapped. On `order.engine_source = spine` it reads the spine; on `tables` the four old calls
  run as they did. `plan()`, `interim_plan()`, the rails, `_staff_qty`, the rules and the proposals are as they were.
- **`purchase_app.py`:** the one edit. The diff is 8 lines (2 out, 2 in): `plan_line(it, cad_days, dead_after=None)` and
  `> (dead_after or DEAD_AFTER_DAYS)`.
- **C — the trial** (`spine/order_rehearsal.py`, replaced whole): it keeps `order_proposal` and scores it. It opens `finance.db` with
  `mode=ro` and never calls `order_rules`.
- **D — the owner's card** (`porders_s454.py`, 4 anchored edits): the block `id="s470"` after "Who decides the order", outside the
  sheet's condition. The six settings are on the same settings card and go through the same route (`/api/s454/setting`, audited as
  `s454_setting`, the owner only).
- **The duty map is not edited** (v5). No duty is added, moved or removed. No staff screen changes.

### Calls I made beyond the brief's words, each with its reason

1. **The item list is still Marg's newest stock list (`stock_snapshot`): names, packings and pack sizes only. No figure is read from it.**
   - The brief's six methods give no list of items, and the spine cannot give a sound one. It keeps a closing by 20-letter key, not by
     item. Its item table (`sp_item`) holds a row for every packing an item ever had and for every way a report spells one.
   - My first build took the list from `sp_item` (rows seen at the latest closing). The walk caught it. At 13:47 IST today a salt-list
     export arrived that spells two packings differently, and DOLOGESIC SP ("1*10" and "1*10.") and TRAMAVIN GEL ("1" and "1.0") became
     "2 under one key". That halved their stock (242 → 121, 27 → 13) and would have halved their sale rate.
   - So the engine takes the item list from the stock list and every figure from the spine. Today the two agree on all 379 names and on
     every pack size.
2. **A family's members are counted in the stock list, not with `family()`** (the same reason). `family()` is built as the brief asks and
   also carries `last_seen`; its `n` counts rows. 47 keys have two or more rows in `sp_item`. Only 8 have two or more items in the stock
   list, and all 8 are orthotics.
3. **On the Marg basis a family shares its stock equally, as it shares its rate.** The spine knows only the family's stock and the
   family's sales. Each member is planned on the family's cover, and its line carries `family = n`. No medicine is in a family today.
4. **If the spine cannot be read, that plan is made from the old tables and says so** (`engine`, and a red line on the owner's card).
   Ordering never stops for the spine. The install reads the live engine once after placing: `engine=spine`.
5. **`plan()` returns three new keys:** `no_supplier` (B.7), `engine`, and `no_closing` (a medicine of the stock list that the spine's
   latest closing does not hold; empty today).
6. **`purchase_lines(supplier=…)` filters on the spine's own supplier key** (the first eight letters). The engine does not use that
   filter: it compares `supplier_key` of the printed name, as the brief asks, because a short name with and without its city has two
   different eight-letter keys.
7. **`lot` is in units** (the median of quantity × pack size per line). **`free` is a ratio** (the median of free ÷ bought).
8. **Arrivals:** an order tied to a scan with `arrived = 1` is dated by `received_at`, else the scan's time, else its own day, for the
   `order.in_transit_days` window.
9. **The weekly line, as scored:**
   - "Bought on list" and stock-outs are over the days 7 to 13 nights ago. "Listed and bought within 14 days" and the money are over the
     days 14 to 20 nights ago.
   - Percentages count items (keys), not units or rupees.
   - **"Bought on list" leaves the Orthotics section out of what was bought.** The engine never lists an orthotic (S403 orders those),
     so they would always count against it. The night's own three scores (`score`, S341's) still count every key, as before.
   - A stock-out is a medicine with a sale in that week whose spine stock ended a day of it at or below zero, on a day a list was kept.
     "Listed in time" looks at the kept lists of the seven days before its first such day.
   - A day with no proposal, and a day with no kept list, is in no denominator.
10. **Where a part of the line cannot be scored yet, the card says so** in place of a figure ("not known yet (14 days are needed)"), and
    in the first week it adds when the first score comes.
11. **The settings' ranges** on the card: pace 7–90 days, dead-after 1–365, on-order 1–30, in-transit 1–60, lot history 30–730;
    `order.engine_source` takes `spine` or `tables`.
12. **S341's files of 28-Sep to 03-Oct were copied to `spine/orders/before_S470/`** before the new ones took their names. S341's files
    of 20 to 27-Sep stay as they are and are never scored: they are not the engine's lists.
13. **The files are placed in an order that is safe mid-way:** `purchase_app.py` first (its new argument is optional), the read door
    before the engine, `order_rules.py` last.

### The install-day compare (scratch copies, 14:40 IST; `compare_s470.py`)

**Marg's stock from the spine against `stock_snapshot`.** Both are the closing of 04-10-2026.

- 376 of the 379 items are read, and every item alone under its key has the same figure in both stores.
- **12 items differ, all orthotics in a family** (the key's figure shared equally):
  ANKLE BINDER BAMBOO L 0 → 1, M 1 → 0 · KNEE SUPPORT HINGED L 6 → 3, M 4 → 3, XL 1 → 3, XXL UNISO 1 → 3 ·
  L S BELT CONT GRAY UNISON L 3 → 2, XL 1 → 2, XXL 2 → 1, XXX 0 → 1 · SHOULDER IMMOBILISE UNISON L 1 → 2, M 3 → 2.
- **3 items are not read at all:** KNEE IMMOBILISER UNISON M, KNEE IMMOBILIZER UNISON L and XL. They are a family declared in the
  spine's rules, filed under a key the 20-letter clip does not reach (F-719). They are orthotics, which this engine never orders.
- Pack sizes that differ: 0.

**The sale units of the 28-day window, item by item** (on `count`). Medicines that differ: one.

- **LINTIDE 145 MCG 1*1: the old store reads 3, the spine 30.** Marg prints a plain "3" on a loose item; the spine reads it as 3 packs.
  The spine's reading is the record.
- The other nine are orthotics or consumables: three knee immobilisers (above), FINGER EXTENSION SPLINT (the old store had no pace),
  and five with no sale in the window on either side.
- RIFAGUT 550: 160 days since its last sale on the old tables, 130 on the spine. The spine joins a ticked rename to its old name's sales.

**The plan of 04-Oct on `spine` against the plan on `tables`**, the same copy, the same day:

| basis | tables | spine | added | gone | quantity changed | same quantity, other value |
|---|---|---|---|---|---|---|
| count (as it is set) | 28 lines, 12 suppliers, Rs 55,753 | 29 lines, 13 suppliers, Rs 57,999 | 1 | 0 | 0 | 23 |
| marg | 20 lines, 11 suppliers, Rs 41,605 | 20 lines, 11 suppliers, Rs 41,738 | 0 | 0 | 0 | 17 |

- **The one line added: ROSIKA FORTE, Deepam Pharma, 10 strips.** The old table holds a second supplier for it (Mannat Pharma); the
  spine holds only Deepam. One supplier means three more days of cover, and that brings the line in.
- **The values move because the cost does.** The spine's cost per pack is the bill's net amount ÷ quantity, with tax (the brief's B.5).
  The old table's is the purchase rate. No supplier moved across the minimum order (2 held on both, on count).
- No line is there because of a returned sale, a missing bill or a family: today the two stores hold the same 607 sale bills of the
  window, and no medicine is in a family.
- The interim plan: 0 lines on both. One plan takes 0.26 s on either source.

**`no_supplier` (39):** CARTILOX SACHET · CETAPHIL REST MOIST · CIXCEF O · CRX 100 INJ · DOPACEF 1.5 · DROZIN MF · ETOBONE P · ETOZOX 90 ·
EXLAIN A · FELBATE · FLUPIVAMP 100 · GLI-ME SR1 · KT ROS DT · LEUKOCREPE 6 CM · LEUKOCREPE 8 CM · MAGMAG · MET4MIN GL 1 ·
MYOTOP SR 450 · NERVIJEN D3 TAB · NEXPAR LA · NIMREX P · PANO OIL · PANTOCID L CAP · PANUM L · POWERGESIC 100 PATCH · PREGABA D 50/20 ·
PRIME CAST 4" · PRIME CAST 5" · PRIME PAD 6" · QBACK 1.5 · REDIMARD 25 · RIFAVAX 550 · RISTRYL · SERADIC GEL · STUGERON FORTE ·
TRAMEF P · ZERODOL P · ZUBOGESIC TAB · ZYLORIC.

- Eight of them sold in the last 28 days: RIFAVAX 550 (4.64 a day, 23 on hand), ZYLORIC (2.71, 95), ETOZOX 90 (1.68, 501),
  KT ROS DT (1.18, 329), GLI-ME SR1 (0.96, 0), DROZIN MF (0.86, 85), MET4MIN GL 1 and NIMREX P (0.36 each).
- The old plan dropped all 39 without a word; it reads no supplier for them either (133 stock items have no purchase line in the old
  table, 132 in the spine).

**The trial's first week.** Kept from `order_proposal`: 28-Sep 9 fixed proposals, 26 lines, Rs 53,125 · 29-Sep, 30-Sep, 01-Oct none ·
02-Oct 1 fixed, 2 lines, Rs 9,000 · 03-Oct 6 interim, 10 lines, Rs 16,378. Nothing is 7 days old, so nothing is scored: days scored at
7: 0, at 14: 0. The first 7-day score falls on the night of 05-Oct, the first 14-day score on 12-Oct.

### The walk — `walk_s470.py`: WALK_S470 GREEN — 46 of 46 (in the installer, on backup-API copies; NEW = the box + S470, OLD = the box as it is)

1. **A, the read door.** The spine's selftest: 45 checks (the box: 39). On the scratch spine, 10 sold and a credit note of 3 read 10 and
   −3 by the day. **NEGATIVE:** the box's read door has none of the six, and its `sales()` counts the credit note as a sale (13, not 7).
2. **B, equality on `tables`.** NEW's plan equals the box's line for line, on count (28 lines) and on marg (20), and so does the interim
   plan. **NEGATIVE:** the box's plan has no `engine` and no `no_supplier`.
3. **B, the spine source.**
   - Every item's rate equals the one worked out in the walk from `sp_sale_line` / `sp_sale_bill`: 239 items, 158 with a sale in the
     window, 0 off. Every line of the plan (29) prints that rate.
   - Marg's stock: as in the compare above.
   - The count-basis figures (`shelf_figure.figures`, every item) are identical on both sides (one md5).
   - A sale bill only the spine holds (28 units): NEW's rate is 2.5 a day and its stock the spine's 500.
     **NEGATIVE:** the box's rate is lower by exactly 28 ÷ 28 = 1 a day (1.5), and its stock is `stock_snapshot`'s 480.
4. **B.4, arrivals.**
   - Received and no bill yet: 30 and 20 units count as stock, on both bases, on both sides.
   - The bill is entered, dated the day before the receipt: NEW drops the 30 units on both bases.
     **NEGATIVE:** the box still counts them (twice, once Marg's stock has them).
   - With no bill the goods leave on day 15, on both sides.
5. **B.7 / B.5.** NEW names the never-bought item under `no_supplier` with its stock and rate, and the owner's card counts it.
   **NEGATIVE:** the box's plan drops it silently. A line carries its lot (100 units) and free (0.2), its supplier as the normalised key.
6. **B.8.**
   - The six settings are rows of the table at their present values.
   - `order.pace_days` 28 → 14 moves the rate (2.5 → 3.0). `order.dead_after_days` = 1 zeroes the line whose last sale is 2 days old.
     **NEGATIVE:** the box, with the same rows, reads neither.
   - The owner sets one from the card (200, audited, 28 → 21). A value out of range and a wrong word get 400. A staff login gets 403.
     **NEGATIVE:** the box's route does not know the key (400 bad_key).
   - `purchase_app.py` differs from the box's by the one edit (the diff printed, 8 lines).
7. **C, the trial.** Made-up proposals around a far-off "today", where the copies hold nothing of their own.
   - It exits 0, and `finance.db`'s md5 is the same before and after.
   - The kept file holds every line (3, the same key twice) with its kind and `source: "order_proposal"`. The blocked day is kept with
     no proposal.
   - The three old scores by hand: [2, 1, 1, 0] with the merged key at 120 units, then [2, 1, 1, 2].
   - The week by hand: 50% · 50% · 2 ran out, 1 listed in time · Rs 500 not bought · 1 day scored at 7, 1 at 14.
   - **NEGATIVE:** the box's trial keeps none of the proposals and scores nothing of them. Tonight for real, on the copies as they are,
     it writes 41 lines, all 41 in no proposal of today; NEW keeps exactly today's proposals (none: Sunday).
8. **D, the card.** The line as the brief words it. "The weekly score is not ready yet." with no file and with a file three days old.
   In the first week it adds the night the first score comes. Reception's old page has no such card.
   **NEGATIVE:** the box's owner page has none.
9. **E, the staff-eye walk** (DUTY_MAP v5). Every tile is on its home and every due duty's marker on its door. **32 pages** (the homes
   and every door of reception, darpan, shavez, amir and the owner) **are the same on both sides**, clock times and tokens apart. The one
   that differs is the owner's `/finance/porders?old=1`, which gains the card.
10. **The crons' commands as scripts.** `order_rules.py tick` exits 0 on the built file with `ORDER_TICK=prepare` and `=remind17`.
    **NEGATIVE:** the same file with the S470 block moved below its `__main__` guard fails with `NameError: name '_s470_days' is not
    defined`. Every added block sits above its file's guard.

### The earlier walks — `walks_old_s470.py`: WALKS_OLD_S470 GREEN (in the installer, before placing)

Each walk is copied to scratch and run twice: on the box as it is, and on the patched files.

| walk | reds, both runs |
|---|---|
| S403 | 13 of 52 |
| S407 | 5 of 27 |
| S410 | 3 of 32 |
| S414 | 1 of 8 |
| S417 | 5 of 25 |
| S428 | 9 of 64 |
| S439 | 23 of 55 |
| S440 | 27 of 66 |
| S441 | 6 of 27 |
| S444 | 18 of 60 |
| S446 | 17 of 41 |
| S452 | 16 of 54 |
| S454 P1C | 7 of 33 |
| S454 P1D | 1 of 3 on the box as it is; 2 of 3 on the patched files (I7, below) |
| S454 P2 | 7 of 44 |
| S454 P3 | 1 of 26 |
| S454 P3B | 10 of 26 |
| S454 P5 | 2 of 15 |

- **P9, one adjustment, on both runs:** `order.engine_source = tables` on each walk's scratch copy. Every earlier walk makes up its
  items, sales and purchases in the old tables only, never in the spine. On `spine` those rows do not exist for the engine. S470 keeps
  the old engine line for line behind this setting, and step 2 of the walk proves that equality on today's data.
  (`walk_s410.py` clears the `order.*` settings itself, so the row is written again right after its own clearing.)
- **I7, one intended red, on the patched run only:** S454 P1D's check "imported in-process, the module exposes exactly the same names
  as the live one". S470 adds names to `order_rules.py`, so a kit that adds a block cannot pass it. P1D's other check, the cron's own
  command exits 0, is green on the patched file. **The brief says "none new"; this one is new, and it is the kit's own doing.**
- **Not run, and why:**
  - S454 P1's walk no longer runs on the box as it is. Part 1C changed the printed sheet's layout that its probe reads
    (`KeyError: 'old'`), on both runs alike. P1C's walk, which took its place, is run.
  - P1B's needs the owner's real order sheet, which is not in the repository.
  - P4A's and P4C's are the medical PC's refusal note; they touch nothing S470 changes.
- The other adjustments (P0 … Q6) and S454 part 2's intended reds (I1 … I6) are S454's own, carried as they were. The box has S454 on
  it, so they apply to both runs.

### Not done, and why

- **The line for the parent, not done:** `/root/finance/spine/orders/` into the state backup (`/root/state_backup/clinic_state_backup.py`),
  so that the scores leave the box.
- **Not in this kit, as the brief says:** the buying model (levels, review intervals, the 7/28 rate, lots and schemes in the quantity,
  the family share by stock); the shelf figure's reader onto `spine_read`; Darpan's screen; the switch of `order.source`; F-719's repair
  in the spine; the earlier walks' known reds.
- **Still constants inside `purchase_app.plan_line`, for the next kit:** `DEFAULT_BOX`, `MIN_LINE_P`, `MAX_COVER_DAYS`,
  `PEAK_SHARE_SPIKE`, `THIN_SELL_DAYS`, `CONFIRM_LINE_P`, `BOX_STRETCH_ASK`. `PACE_DAYS` survives there only in a reason string; that
  string still says "in 28" if `order.pace_days` is changed.
- **Still on the old tables, as the brief names them:** the orthotic keep-in-stock list (S403), and `order_rules`' side reads
  (`candidates`, `oos_both_ends`, `new_items`, `rhythm`, `lead_learned`, `_month_spend`, `kedar_review`, `item_names`).
  `_carried_shorts` and the `stock_rate` fallback for a cost are as they were.
- **The first week's score is not measured: nothing is old enough.** It comes by itself on the night of 05-Oct.

### Noticed outside the brief

- **The spine's item table holds one item twice where two reports spell its packing differently.** Since the salt list of 13:47 IST
  today, 12 keys have two or more rows seen on 04-Oct: DOLOGESIC SP "1*10" and "1*10.", TRAMAVIN GEL "1" and "1.0", ANKLE BINDER BAMBOO M
  "1" and "1.0", DEPOMEDROL INJ, QFEB 40 and others. Anything that counts `sp_item` rows as items is wrong by them. `stock_watch.Spine`
  and the shelf figure do not count rows; I did not check other readers.
- **A family declared in the spine's rules cannot be reached through the read door by an item's name.** `key()` gives the 20-letter clip
  ('KNEE IMMOBILISER UNI'); the rows are filed under 'KNEE IMMOBILI?ER UNI (family)'. Three orthotics today. It is F-719's and is left.
- **ROSIKA FORTE has a Mannat Pharma purchase in the old table that the spine does not hold.** I did not trace which export carried it.
- **RIFAVAX 550 sells 4.64 a day, has 23 on the shelf figure, and has no supplier on record.** GLI-ME SR1 sells about 1 a day and reads
  0. Neither can be on the system's list. Staff order from Darpan's sheet, so this harms nothing today; it would on `order.source = system`.
- **Every future walk that makes up an item must make it up in the spine too**, or set `order.engine_source = tables` as P9 does. An
  item that exists only in the old tables is not planned on `spine`.
- **`/tmp` on the box holds this run's scratch folders:** `/tmp/s470dev_135755` (the dev runs; it holds scratch copies of `finance.db`,
  `assets.db` and the spine), `/tmp/s470kit_142936` and `/tmp/s470kit_144034` (the kit copies and the install log), and
  `/tmp/s470probe_134244` (read-only probe scripts). The permission list refuses `rm -rf` and I did not look for another way. The chat
  may want them cleared. The installer removed its own walk folder.

```
https://followup.dr-manoj.in/finance/porders?old=1
```
