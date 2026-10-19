# S593_ORDER_ENGINE_ONE_SOURCE — the order engine on the one stock function and the one arrivals rule (D743)

**Brief:** `claude_code_briefs/S593_ORDER_ENGINE_ONE_SOURCE.md` (v2, Sanjeevni session 328, 18-Oct-2026) under **D743** (the owner, "Yes" 21:21 IST,
to the mock-up `S328_F916_ORDER_PAGE_MOCK.html`): step 4, Kit I of the plan of record (`S327_SANJEEVNI_RESTRUCTURING_PLAN.md`) — the engine put on
the one stock function and the one arrivals rule, the supplier rhythm read from the spine, S486 Part A's switch-safety fixes, F-717 and F-916.
The independent read R1 (`03_WORKING_PAPERS/S328/S593_R1_REVIEW.md`: six blockers, sixteen corrections) is folded in. **No new buying model**
(Kit II). Closes **F-916, F-717, F-738, F-739**. **Charter:** `SANJEEVNI_BUILD_CHARTER.md` v1.1. Six Sanjeevni files, no new file, no new table,
no new setting, no data step; `DUTY_MAP.json` v14 → v15 and one row of `DUTY_MAP.md` (the clone, by the publish). Kit shape: S587's. One restart.

## What it does

- **3.1 `order_rules.py` — the stock base from the one function (S308 i; charter 1, 2, 3; R1-B1, C1–C6).** `_s470_inputs` opens TWO handles:
  `_s470_spine()` (spine_read's `Spine`, for `_s470_pace` / `_s470_purch`, as before) and `stock_watch.Spine()` — the handle `stock_figure` is
  written for (it carries `.ok`; R1-B1) — inside ONE `stock_figure.Ctx` shared with `_s454_shelf_snap`, so every item is figured once per `plan()`.
  `_s470_snap(con, pa, sw, ctx, today)` takes every master item's figure from `stock_figure.marg()` (Marg's newest usable closing carried by the
  spine's movements to today) `+ taps() + scan_arrivals()` since that closing's capture stamp (one moment for both arrival kinds, R1-C4), never
  below 0; the key grouping stays only for `n` = the number of MASTER names under the key (`_s470_pace` divides by the same `n`, R1-C2). An item no
  capture holds is left out and named; an item the closing did not print but the spine knew (`by='absent'`) stands at 0 AND is named — the engine
  may now list it (a deliberate change; the walk counts them). `as_on` is the capture's end day (was the printed day of the newest `sp_close` row —
  on 18/19-Oct the unusable 09:37 start capture). `_s454_shelf_snap(con, snap, ctx)`: the engine's context rides into `shelf_figure.figures`;
  `marg_qty` is Marg's PURE figure (`_s470.marg`), not the figure with arrivals (R1-C5). **Retired:** `_s470_arrivals` (the engine's own arrivals
  rule), `_s470_snap`'s `sp.closing()` read and equal-share split, `ON_ORDER_DAYS`, the dead loop in `lead_learned` (the function stays). `transit`
  holds the sent-and-unanswered lines only (`_on_order_units`). **`days_left(on_hand, per_day)`** — ONE module function (the arithmetic
  `darpan_kal._s485_days_left` had): `_line_out` adds `days_left` to every row; the carried-short row carries `days_left=None`. **`plan()` returns
  `inputs`** (`sales_through` = the spine's sale reach, `capture` {md5, as_on, end_day, stamp}, `spine_built`, `counted` / `marg` / `absent`,
  `made_at`), kept per thread in `_S470` and per process in `_S593_INPUTS`; the owner's `/finance/porders/api/day` serves the process's last
  (`None` until a plan was made in that process); nothing of it on Darpan's tab. `KIT = "S593_ORDER_ENGINE_ONE_SOURCE"`.
- **3.3 `rhythm()` from the spine (S308 ii; R1-C15).** The two `purchase_bill` reads are one `spine_read.purchases_by_supplier(since, today)`
  (**3.4**, one method added after `purchase_lines`: `sp_purchase_bill`, direction PURCHASE, grouped by supplier key and day, the printed name
  beside); `sn = pa.supplier_key(supplier)`. **The money basis moved:** `amount90_p` is now the report's bill amount (the tables gave the NET
  amount per bill). On the 19-Oct copy: 25 suppliers (the tables had 26 — "BASS PHARMA DISTRIBUTORS PVT" and "… PVT LTD" are one key in the spine);
  L.K. DRUG HOUSE moves `bills90 24→19, gap 4→5, amount90_p 4079800→4528300`; **no supplier's cadence moved.** The three other `purchase_bill` reads of
  order_rules.py (the supplier names, the owner's spend alert, Kedar's big four) stay — rung 5's, SEEN.
- **3.2 `porders.py` — `detect_supplies` asks the one rule (S583's "two copies" closed; R1-B1, B2, C9, C10).** For every open line (`billed_qty`
  NULL, order sent / received) it asks `stock_figure.carried()` on `stock_watch.Spine()` with a FRESH `Ctx` per row (rule (b) sees each write);
  accepts only `how in ("c", "d")` — the order's own vendor's bill, dated up to `arrival.back_days` before the order day (c) or on/after it (d); (e),
  another supplier's bill, counts for stock only and never marks this line billed. **Packs, not units:** `q = SUM(qty) + SUM(free)` of
  `sp_purchase_line` for that bill and the spine's key (`stock_figure.key_of`, the identity `carried()` used — never `units / pack_size`). Then the
  write as before (`billed_qty`, `billed_bill_no`, `billed_date`, `detected_at`; `supplied` / `short` / `arrived_by='marg'` when nobody tapped; the
  audit; `_close_complete_orders`). The spine unread (`sw.ok` False): nothing written, one stderr line. The table read (`purchase_line`, `EFF_LINE`)
  and the 20-letter `ia.clip` match are gone from this function. A rule-(c) hit may carry `billed_date < created_at` (`lead_learned` clamps it at 0).
  **`api_send_med`:** on `order.source = darpan` the door is refused outright — `409 not_confirmed` ("Darpan ki pakki list se hi order jaata hai")
  — it bypasses Darpan's pakka (R1-C8, decided).
- **3.5 `send_proposal` (F-738):** on `darpan` an `open` proposal answers `409 not_confirmed` ("Darpan ne yeh list abhi pakka nahi ki."); `held` /
  `darpan_ok` unchanged. `_s470_purch`'s `statistics.median(lots)` stays — the ONE lot (Kit II's `model_lot` is to live there).
- **3.6 `porders_s454.py` — F-916 (D743) and F-739.** `done_all = _done_today(con)` stays what the page's CONDITIONS read (the "Abhi baaki: N"
  heading, the all-done line, the "WhatsApp chala gaya" banner — unchanged). Only the done BLOCK is filtered: `done = [d for d in done_all if d["sn"]
  not in {e["sn"] for e in pend}]` — a supplier with a card is not repeated under "Ho chuke"; a done line of an earlier day reads `✓ dd-mm · <word>`
  (`OS.ddmm(d["sent_at"]) != OS.ddmm(OS.now_iso())`), a line of today stays `✓ <word>`. No new string. **F-739:** the `system` and `darpan` headings
  count the cards' own list LESS a card that is only orthotic (`set(e["sources"]) != {"ortho"}` — `entries()` hands `sources` as a sorted LIST, not the
  set R1-C11 named) and the medicine lines only (`l["src"] != "ortho"`; a mixed card counts once). **`DUTY_MAP.json` (the clone, by the publish):**
  `reception.medicine_orders`' `due_sql` gains the `darpan` arm (`status = 'darpan_ok'`, distinct `supplier_norm`, in the shape of the `system` arm);
  `version` 15, `kit` S593, the `_note` and the duty's words. The arm's SELECT was run on the live database read-only at the open (CLAUDE.md "every duty
  has a door" rule 1: `n = 0` on 19-Oct, `order.source = marg_sheet`). `DUTY_MAP.md`: the dated paragraph and the row's "Due when".
- **3.7 `order_sheet.py` — F-717.** `load_pending`'s fallback `except` calls `con.rollback()` (inside `try / except sqlite3.Error`) before the print.
  `order_sheet_pdf.py` is not edited (R1-B5: its head line is S543's, source-less; the stale comment at 22 stays).
- **3.8 `darpan_kal.py` (S308 viii, charter 14; R1-B3).** `_s485_days_left` deleted; `_s485_line` serves `pid, item, packing, unit, qty, on_hand_text,
  days_left, held, added` — `why` and `cover_days` no longer served — with `days_left = l["days_left"]` when the engine wrote it, else
  `order_rules.days_left(on_hand, per_day)` (every proposal stored before this install, until its next `prepare_day`). Darpan's add door writes
  `days_left` on the line it stores. `darpan_kal.html` is not edited (it reads `on_hand_text` and `days_left`).

## Pins (FROM → TO; TO is `PINS.sh`)

| file | FROM | TO |
|---|---|---|
| `/root/finance/order_rules.py` | 79f21c1ee1f763b1ac06b370e3d77b79 | 8d078dbe1b63a4706dc6f35e3c31ac9a |
| `/root/finance/porders.py` | a5a823bf30661a4bf65ced39b2355500 | 78ea72be7d87a7c56c65de7d4c96a952 |
| `/root/finance/porders_s454.py` | 8307976393e6ea161f8d3a94bcb0692c | 40f1755a7655deb733765456b9a466fe |
| `/root/finance/order_sheet.py` | f00f0163bdd66a074c5af261c9b80a49 | 1f1e85c12c64521b50a10cea48220170 |
| `/root/finance/darpan_kal.py` | 8128598f745fca48a08472905f47da97 | 325d988c61e1c7408a2a4b687a4822bb |
| `/root/finance/spine/spine_read.py` | 712a1e4ef827f6be4e8b23415c3ceb62 | 827b00402add288d028c910128084b90 |
| `claude_code_briefs/DUTY_MAP.json` (the clone, by the publish) | 891defd8431e291b1a152f9e3c85f8c6 | c2ef9c6c5adb8c930b21bff5441cc017 |

Read only, never edited — the installer prints their live md5 and STOPS if one moved: `stock_figure.py` 92367a19, `shelf_figure.py` 23b2394a,
`stock_watch.py` c5f3ce21, `purchase_app.py` 60f2d846, `order_sheet_pdf.py` 7fca11db, `darpan_kal.html` 75d5a5b5, `finance_ui/finance_approvals.html`
b32da7ff, `porders.html` 7a6799ae, `aaj_kaam.py` cd232b1c, `amir_day.py` 3af992d9, `spine/spine_build.py` e3d3ed85, `spine/selftest_spine.py` 7d0edb4a,
`item_alias.py` 111a8e48, `qty_words.py` 706db7cc; and proved unmoved: `finance_app.py`, `spine/order_rehearsal.py`, `portal.py`, `tile_grants.json`,
the crontab, `spine.db`'s schema (no table added to the spine). `finance.db`: no new table, no new setting, no data step; backed up by the backup
API before placing. Service `clinic-finance`, restarted once. Install window 08:00–23:59 IST with the spine green and under 30 minutes old;
`DOCTOR_AUTO_OFF` set around the restart, removed after healthz 200.

## The install (`install_S593_ORDER_ENGINE_ONE_SOURCE.sh`)

Gates (window, lock, SUMS, KIT_ID, PINS) → the FROM pins and the read-only md5s → the clone's `DUTY_MAP.json` at FROM (the publish not yet landed:
the kit builds the new map in scratch for the walk) or at TO (landed) → the spine green → the settings and the darpan arm's SELECT printed → build
from the live bytes (35 anchored edits, each anchor exactly once) → compile on both pythons → scratch (the finance folder twice, finance.db /
assets.db / spine.db by the backup API) → the walk on the OLD files (every control red) then on the NEW files → DRY stops → the install-day state on
the OLD and the NEW files → backups (`finance.db.bak_S593_<stamp>`, `<file>.bak_S593_<from8>`) → `DOCTOR_AUTO_OFF` → the six files staged and renamed
in ONE command → one restart → healthz 200, the pages 302 → journal clean → `porders.detect_supplies` once on the live database (its writes quoted
by rule letter, in packs — what the page's every read and the ten-minute tick would do within minutes anyway) → the state AFTER → nothing else moved
→ md5 read-back → `DUTY_MAP.json` landed / not yet → the off-switch removed. Red after placing: the six files put back in one command, one restart,
healthz. Nothing of the database to reverse.

## The walk (`walk_s593.py`)

On scratch copies only (the spine copy is never written), the real app in one process (the walk's own header session), its own rows by key
(`W593 …`), the brief's thirteen controls: (11, first, with Marg's clearing held still so the WORDS are compared alone) the staff screens word for
word — reception's four pages, Darpan's page and two APIs, Amir's seven steps, Shavez's reports, the owner's api/day and Needs-you — the only
differences allowed: F-916's (a done line of a supplier with a card gone, an earlier day's date), Darpan's rows losing `why` / `cover_days`, the
owner's api/day gaining `inputs`; (1) the stock base: `plan()["engine"] == "spine"` with `inputs`; every uncounted item's qty == `int(round(marg +
taps + scans))` from a direct `stock_figure` call with `stock_watch.Spine()`, every counted item's `marg_qty` == Marg's pure figure and its qty ==
`shelf_figure.figures(...)["shelf"]`; the OLD `_s470_snap` replayed (printed day, equal split) and every uncounted item that moved printed; the
`absent` / `key` counts and the plan lines they produce; (2) `_s470_arrivals` gone, transit = on-the-way only, the items with arrivals since their
closing printed; (3) `detect_supplies`: every open line OLD (the tables' match) vs NEW (`carried()`: rule, bill, date, PACKS) side by side; the spine
made unreadable → 0, nothing written, one stderr line; the real run's writes, every one by (c) or (d) with the spine's packs; no rule-(e) write;
the visible effect (the orthotic card, the owner's arrival lines) before / after; two open lines of one key from one vendor carried by TWO bills
(fresh Ctx per row), a second run writes nothing; (4) `rhythm()` NEW vs the OLD `purchase_bill` read per supplier, the cadence moves named; (5) F-738:
`open` on darpan → 409 `not_confirmed`, `api/send_med` → 409, `darpan_ok` sends; (6) `days_left` on the engine's row == the OLD arithmetic, on a
proposal STORED before the install, on a line Darpan adds through his door; (7) F-916 on the copy: the done block must read exactly D743's list
(no supplier with a card, an earlier day's date, today's without), the real case when it stands, three constructed orders; (8) F-739 on darpan with a
mixed card and an orthotic-only card; the duty map's darpan arm equals the heading; (9) the greps (the retired things gone, the one lot, the one
median, `days_left`'s four call sites, the handle's type asserted on every `stock_figure` call); (10) F-717: two failing sheets → two rollbacks;
(12) the spine untouched (schema, bytes, no `sp_` write, selftest green); (13) `order_rehearsal.keep` on the copy, `/finance/health`, `plan()` under
the OLD time × 1.5. `--expect-red` is the negative control (34 controls, every one red on the old files); `--state` prints the install-day state.

## Charter

- **Retired:** `_s470_snap`'s own `sp.closing()` read and equal-share family split (→ `stock_figure.marg`); `_s470_arrivals` (→ the one rule inside
  `stock_figure`); `detect_supplies`' `purchase_line` read and `ia.clip` match (→ `carried()`, rules c / d, packs from the spine's line);
  `rhythm()`'s `purchase_bill` reads (→ the spine); `darpan_kal._s485_days_left` (→ `order_rules.days_left`, one function); `why` / `cover_days` on
  Darpan's API; `ON_ORDER_DAYS`; the dead loop in `lead_learned`.
- **Left (named, with their condition):** `order.engine_source = tables` and `purchase_app._latest_snapshot / _pace / _last_purchase / _in_transit`
  (4b-2's, after the witness week); the old page's `owner_cards` settings card (Kit II moves it to the owner's fold); `fixed` vs `levels` (Kit II);
  the three other `purchase_bill` reads in order_rules.py (rung 5); `_k20` for held sets (rule 12, SEEN); the second Spine class (`spine_read.Spine`
  for sales and purchase lines, `stock_watch.Spine` for the stock function — one class is rung 5's).
- **Seen, not touched:** `stock_watch.expected_units` (4b-2); `_s454_shelf_snap` (stays — the one function's door; two anchored edits only);
  `order_sheet.entries`' orthotic card (S403's); `porders.html ?old=1` English `why` lines (S410's, the owner's page); `order_sheet_pdf.py`'s stale
  comment at 22; **`porders._movements`' `purchase_line` fallback** (S403's orthotic shelf reads the tables when the spine is not fresh — the one
  other `FROM purchase_line` in porders.py; the brief's grep is scoped to `detect_supplies`); **the 20-letter key families** — sizes of one orthotic
  (KNEE SUPPORT HINGED XL / XXL; ANKLE BINDER BAMBOO M / L) share one spine key, so `carried()` + the bill's packs for the KEY marks the first open line
  with the whole family bill (XL ordered 2, billed 6) and rule (b) then keeps that bill from the sibling line (XXL stays open; the owner's arrival line
  "not in Marg's purchases" appears for it) — S583's "units-based matching (one bill line answers at most its own units)" is the fix, not this kit's.
- **Behaviour changes named (rule 4, 1b):** an item the closing did not print but the spine knew stands at 0 and may be listed (today dropped); the
  rhythm's money basis is the report's bill amount; a rule-(c) bill may date a line's `billed_date` before its order day; **`detect_supplies` lives
  again** — the OLD table rule matched none of the 17 open live lines (no effective `purchase_line` row matched by clip), the one rule carries 7 of
  them on the 19-Oct copy (4 of Yuvika's orthotic lines, CROCAL and PREGHYPE by rule c, BRUTAFLAM GEL by d), so on install day the orthotic shortage
  card and the owner's arrival lines move with those writes (quoted by the installer).
- **Dependency state at install:** `order.source = marg_sheet` (nothing here reaches reception's list); the spine green; the 18-10 09:37 start
  capture `pending` (the engine's `as_on` reads 16-10 — the 17-10 09:20 capture — until Amir's next export; `inputs` says so); count #1 at stage C.
