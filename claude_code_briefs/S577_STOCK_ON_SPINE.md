# S577_STOCK_ON_SPINE — brief for Claude Code (v4)

*v4: written after three independent reads against the 18-Oct bytes, all kept in `03_WORKING_PAPERS\S324\`: R1 on v1, R2 on v2, R3 on v3. v4 takes R3's three blockers by simplifying: no seed of the old gap flags, no marking of the 27-09 rows, and the files placed in one move. Every finding is folded in below, and this text governs. The morning-flow rules of v2 (the owner's findings of 10:12 IST 18-Oct, A, B and F) move to their own kit after this one: R2 showed that the start-of-day test needs a charter amendment and a check of its own. Fix C (a closing's moment) stays here. Written 18-Oct-2026 by the Sanjeevni chat (session 324). Rung 4b of the spine plan (Book §4A, §15F.1).*

*Read `claude_code_briefs/SANJEEVNI_BUILD_CHARTER.md` (v1.1) first; nothing here relaxes it, `CLAUDE.md` or `BUILD_NORM_v1.md`. The map was made from the 18-Oct 01:35 bundle and the 01:40 database copy. **`spine.db` is in no bundle**: §7 lists what only the live spine can confirm. Read it at the open, before the first edit.*

## 0 · For the owner (what changes, in plain words)

1. **One place works out stock.** A new module, `stock_figure.py`, gives two answers for an item, each carrying the closing it stands on: **Marg's figure** and **the shelf figure**. Five checks ask it:
   - the voucher check for Amir;
   - Darpan's spot counts and their loss lines;
   - the shelf-gap flags on Darpan's spot list;
   - the "bill entry baaki" line;
   - your *stock now* and *drift* pages.
2. **One name for an item.** A renamed item is recognised under its old and new names. Two sizes that share Marg's short name are told apart at a closing and treated as one family between closings. Today the voucher check calls a renamed item "not readable" (F-874), and the bill check lost a Yuvika bill that was already in Marg (F-873).
3. **A closing's time is the time Marg made it,** never the time the PC re-sent it at 22:30.
4. **The voucher check gains its second half (D715 a).** A voucher line is never given to Amir when it would take Marg past the shelf figure. Such a line is yours, on Needs-you, with its own sentence.
5. **Opening the Loss desk no longer changes the count (F-841).** The desk only reads. A line that sold more than was counted is shown to you as *"sold after count"* for your decision, never closed by itself.
6. **No staff screen gains words.** Some things staff see can change, and the install prints each one for you first:
   - A voucher line on Amir's card can be held for you instead of given to him (only pending lines; every line already released stays as it is).
   - Darpan's spot-count answer can read differently for an item whose expected figure moves.
   - Darpan's spot list loses the shelf-gap reasons that were judged on closings taken in shop hours (41 of today's 42); judging starts again from two clean closings.
   - The ordering pages' stock figure moves for a counted item whose old reading was wrong.
   - A spot count on a size that shares a family figure is written down with the plain receipt only ("Likh liya: …"), with no verdict. It goes to you as an approximate line, never as a loss.
7. **The old ways run beside it for one week.** These are the PC's computed stock, the server's shadow of it, and the old expected-stock function. A nightly comparison shows every difference. After seven explained nights, a small kit (4b-2) removes them.
8. **Not in this kit (moved to the morning-flow kit, after this one, by your word):**
   - using Shavez's closing taken before the first sale whichever date is printed on it;
   - Amir's last export of a visit covering the days until his next;
   - "agrees = right at once";
   - your hub's *"Amir marked it done"* words;
   - Amir's page with the export step last.

   The first one changes a charter rule, so it needs your ruling. The independent read showed that it needs a careful check, built on its own.

## 1 · Numbers and pins

- Kit **S577_STOCK_ON_SPINE** (board `_numbers` v472 → v473, PLANNED line). Project: Sanjeevni. No D or F number of its own (they ride the close).
- **FROM pins** (full md5 at the open; if any differs, STOP and report):
  - `/root/finance/stock_app.py` **050587dfb5951da65f95937615ddf144**
  - `/root/finance/shelf_figure.py` **183c70fabb64ed1e5a43c645a225c560**
  - `/root/finance/stock_watch.py` **0e6a42c4c7ae51eb8f8a0869fce2d101**
  - `/root/finance/loss_piles.py` **81ae481e4480a12fead3016515037214**
  - `/root/finance/spine/spine_build.py` **5d8b1f94d80189c16b2ee5b1e093429c**
  - `/root/finance/spine/selftest_spine.py` **fc63d2c683a1970c58f60502302187a9**
  - NEW: `/root/finance/stock_figure.py` (absent)
- **Read only, must not change** (re-read their line numbers at the open):
  - `item_alias.py` 111a8e48 · `stockmatch.py` 10e30d28 · `amir_day.py` 73882a83 · `order_rules.py` 79f21c1e (S486 A/B own it) · `qty_words.py` 706db7cc · `spine/spine_read.py` 712a1e4e
  - **at S574's TO md5s, installed 07:03 IST 18-Oct, after the bundle, so the bundle's line numbers for them are stale:** `purchase_app.py` 98f7d9f05bc06ef6be80181dd9be4c8c · `order_sheet.py` f00f0163bdd66a074c5af261c9b80a49 · `porders_s454.py` 8307976393e6ea161f8d3a94bcb0692c
  - `porders.py`, `darpan_kal.py`, everything on manojz and the medical PC.
- Service `clinic-finance`, restarted once. The server build lock.
- **Install window:** 08:00–23:59 IST only. The spine builds `*/10 8-23` (crontab line 66), and the install refuses to place unless `spine_state.json` is green and its `last_success_iso` is under 30 minutes old (charter 1b).
- **`stock_app.py` drift 9:** read it whole before the first edit (section map §2.6).

## 2 · What is there now (the map of the 18-Oct bundle)

### 2.1 Readers of Marg's quantity — split into two lists

**(a) Quantity readers inside a judgment.** The STOP rule applies: a reader of this kind not listed here is STOP-and-report.

| # | where | what it does now | this kit |
|---|---|---|---|
| 1 | `shelf_figure.latest_snapshot` 63 (`stock_snapshot`, PK `(as_on, item)`, never pruned — F-862) | Marg's newest closing by full printed name | **removed**; its callers move to `stock_figure` |
| 1a | ← `shelf_figure.figures` 186/189 | | **moved** |
| 1b | ← `shelf_figure.record_gaps` 429 | | **moved** |
| 1c | ← `stock_app._voucher_guard_base` 5171–5189 | | **moved** |
| 2 | `stock_watch.Spine.close` 469 → `expected_units` 732 | raw `sp_close` carried by sales and purchases, plus taps; printed day = day-end | **kept for the witness week only** |
| 2a | ← `stock_watch._s454_expected` 1846 (fallback), `settle_provisional` def 830 (call 836), `open_trace` 1244 | | **moved** |
| 3 | `stock_app._s524_end_day` 8502, `_s524_stamp_iso` 8494, `_s524_closings` 8522, `_s524_reach` 8533, `_s570_covers`, `_s524_tryable`, `_s524_key_of` 8583, `_s524_table` def 8596 | the stage proof | **the rule and the key move to `stock_figure`** (one-line wrappers stay); the table logic stays |
| 4 | `shelf_figure._s524_capture` / `_s524_captures` / `_S524_CAPTURES` | a closing's moment = `MAX(stock_feed.received_at)` — the 22:30 re-send moves it | **retired** |
| 5 | `stock_app.api_now` 2209, `api_drift` 1669 (via `_feed_latest` 500) | the push_expected feed against the snapshot | **moved** (§3.3 F) |
| 6 | `stock_watch.bill_pending_lines` def 861 (`sp.key` at 877), `_arrivals` 708, `shelf_figure.scan_arrivals` | spine key by bare clip | **moved to `key_of`** |
| 7 | `shelf_figure.gap_flags` 473 ← `gap_flag` 486 (spot roster `stock_watch` 952) · `gap_line` (`order_sheet` ≈1710) · **`porders_s454.gap_flags` ≈1611** | the newest gap set | read the new sets (§3.3 D) |
| 8 | `order_rules._s470_snap` 1920, `_s454_shelf_snap` 1794, `purchase_app._latest_snapshot` (≈1295 pre-S574) + callers, `order_rules.kedar_review` (read 1379) | the order engine | **not here** — S486 B (re-briefed on `stock_figure`) / rung 4a, 4c |
| 9 | `stock_app._three_way` 696 (ONE caller: `_pad_report_data` 4202), `_r_stock` 1952 (frozen into sealed readiness, 857–866), `_newest_snapshot` 1029, `_snapshot_qty_map` 1054, `reconcile` 995, `_item_life` def 3501, `_pad_report_data` 4198/4208, `stock_statement.build` 237, `full_count_points`, `loss_piles.fixes`, `porders.shelf` 389 / `ortho_items` 211 | the count's own figures | **not here** — rung 4f |

**(b) Item-list, existence and feed-watch readers of `stock_snapshot`.** Listed here, not touched in this kit (rung 5):
- `stock_watch.item_info` 530 · `darpan_point` 1184 · `gadbad` 1197
- `darpan_app._stock` 980
- `order_sheet._snapshot_names` ≈326
- `order_rules._s470_master` 1909
- `porders._newest_as_on` 205
- `purchase_app._known_items` / `_log_new_items` / `_unit_word` (pre-S574 ≈4264 / 4298 / 3392)
- `owner_sheets.consumable_items` 269
- `section_map.snapshot_items` 161
- `loss_piles.stamp` 1131 · `round_items` 2209
- `reports_tile` 1578 · `reports_watch.closing_reference` 166
- `spine/spine_compare.compare` 80
- `stock_app._price_value_p` 468 · `_feed_kind` 661 · `_snapshot_source` 683 · `_pad_family` 2760 · `_pad_receipt_data` 3203 · `api_pad_item` 3711 · `_purchase_audit` 4676 · `_newest_snapshot.key` 1044

### 2.2 The shelf figure

- **The one merge** is `shelf_figure.figures` 180. It takes the newest of `count_family` 75 (`stock_count_item` with `stock_shelf_fix` laid over) and `points` 104 (`stock_point` other than `full_count` — it **includes superseded rows**, unlike `stock_watch.last_point` 763), carried by `sp_move` with the count-day boundary, `boundary_purchases`, `_arrivals` and `scan_arrivals`.
- **Its family defect (R1-B1).** `figures` builds a family only from the names it is asked for. `_s454_expected` asks for one name, so one size takes the whole family's sales, with `approx=False`.
- **Not moved here:** `full_count_points`, `loss_piles.fixes`, `stock_statement.build`, `porders.shelf` (rung 4f).

### 2.3 The count tables people write

- `stock_count_item`: 373 rows, count #1, 06-09. **These carry the OLD names of the renamed items.**
- `stock_point`: 383 rows — 373 `full_count`, 8 spot settled, 1 superseded (377), 1 darpan.
- `stock_shelf_fix`: 6 rows — 2 `sales_test` by `system`, 3 `accept_back`, 1 `recount`.
  - Row 6 has `count_id = −1`. S502's data step (`fix_s502.py:106`) wrote it under its marking convention, `count_id < 0` = a retired row.
- `stock_spot_check`: 80 rows (`darpan_app`), an older store merged nowhere. Rung 4d; not touched.

### 2.4 Identity

- `stock_watch._k20` 432 / `Spine.key` 449 and `spine_read.K` 32 / `Spine.key` 46 give the 20-letter clip through `sp_alias`.
- `spine_build.Z` 180–183 stores rows under the **families** (`spine_rules.json`, for example `KNEE IMMOBILI?ER UNI (family)`) and folds ticked renames back to the old clip (`rename_aliases` 93–108). **`sp_alias` does not carry the families.**
- `sp_move` carries only `k20`, so **every size that clips to one key shares one movement ledger**: the KNEE SUPPORT … HINGED sizes, the L S BELT sizes, the wrist splints, the knee immobilizers.
- Renames are read through `item_alias` (`done_rows` 307, `resolve_map` 312, `aliases_of` 330; ticked and not taken back only). For six renamed items, Marg's printed name is the accepted event's `seen_name` (`marg_item_rename_event`, event `accept`), not `new_name`.

### 2.5 Stored conclusions

- `stock_watch_loss_line`: 5 rows, 1 voided, no stamp.
- `s454_shelf_gap`: PK `(as_on, item)`; 4228 rows, 02-10 → 16-10. The 15-10 set was judged on a mid-day capture (written 15-10 10:20).
- `stock_trace`: 33 rows, insert-only.
- `stock_watch_view`: 1 row.
- **`stock_pile_cache` + `_meta` (F-841):**
  - It was built 29-09 21:03. `last_partial_at` is NULL; `full_ms` is 3141.
  - The stamp's `spine` part is `spine.db`'s mtime. A failing build leaves `spine.db` untouched (renamed `.failed`, 654–662), so the mtime moves on every **passing** build, about 96 times a day. Nearly every read or owner tap therefore takes `rebuild` 1207, which runs `sales_test`, which writes `stock_shelf_fix` (shelf = Marg's count-day figure), `stock_sales_test` and `stock_diff` words into count #1.
  - The 01:40 copy shows the desk was not opened between 29-09 and 18-Oct 01:40. The chat's read-only sub-agent opened it at about 09:5x IST on 18-Oct. **Read and print `stock_pile_cache_meta.built_at` and every `stock_sales_test` / `stock_shelf_fix` row dated 2026-10-18 at the open.**

### 2.6 `stock_app.py` sections (at 050587df)

- 1–303 setup and rename helpers
- 306–466 prices and lanes
- 467–651 feeds
- 654–776 three-way
- 813–1027 seals, reconcile, snapshots
- 1028–1648 count routes (`/api/snapshot` 1142)
- 1651–1790 drift and losses
- 1778–2258 readiness, gate, now
- 2261–3097 pad import
- 3097–3398 proof, receipts
- 3398–4475 finding report
- 4489–4975 sections, cleanup, tranches
- **4975–5310 the voucher flow** (`_voucher_lines` 5098, the RECEIVE skip at 5146, guard 5171–5223, the `_voucher_held_batches` skip at 5212)
- 5397–5740 voucher routes, renames
- 5743–7219 Loss desk and hub
- 7222–7609 archive and upload
- 7612–8087 Amir's stages (`amir_stage` 7846; A `held`/`pending` 7874–7876 and `a_is_open` 7883; C held batches 7912 and 7948–7951; `_s452_release` 8063)
- 8091–8905 shelf map, dates, **stage words `_s521_stage_words` 8381–8388**, the one judgment `_s524_*`

**Dead:** `_voucher_held` 5166 (callers only in S537's frozen walk) and `stock_watch.latest_close_day` 474 — remove both. **NOT dead:** `_voucher_void` 5040. It is the kit-only void door: S537 `data_s537.py:70` and S539 `data_s539.py:90/178` wrote the 2 `stock_voucher_void` rows through it. Keep it, and name it in the README.

## 3 · The edits

### 3.1 The spine keeps every closing capture, by name (additive; the gate unchanged)

- **`spine_build.py`:**
  - `build()` returns `B["captures"]`: every accepted full `STOCK_CLOSING` export (`CL` with `_full`, 344–351), not only the latest of each printed day.
  - `write()` fills ONE new table: `sp_close_name (md5 TEXT, name TEXT, packing TEXT, k20 TEXT, units REAL, PRIMARY KEY (md5, name, packing))`.
    - `name` and `packing` are as Marg printed them.
    - `k20 = Z(name)`.
    - A name printed twice with the same packing inside one capture is summed.
  - The capture's printed day and stamp are **`sp_export.as_on`** (written 558; R2-C17) **and `sp_export.stamp`**. There is no second copy and no second stamp parser.
  - `sp_close` and every gate check stay **exactly** as they are.
- **`selftest_spine.py`** gains one check: two captures of one printed day give two md5s in `sp_close_name`; `sp_close` keeps the later one; a name printed twice in one capture is summed.
- **`spine_read.py` is not changed.** `stock_figure` reads through `stock_watch.Spine.q`, which is `ok`-safe; `spine_read.Spine` raises when the spine is missing.
- **Known, answered (R2-C11):** `sp_move` carries `OPENING`, `SALE`, `SALE_RETURN`, `PURCHASE`, `PURCHASE_RETURN` and `RECONCILIATION` only (spine_build 383/391/396/409). **No stock voucher, stock-issue fix or consumption issue ever reaches it.** So `marg()` never counts a voucher twice through `sp_move`; vouchers enter only through `unkeyed`.

### 3.2 `stock_figure.py` — NEW: the one stock function (read only; no table of its own; imports cleanly without Flask, because `record_gaps` runs inside the `order_rules tick` process)

**One per-request context.** `Ctx` is built once by the caller and passed down; it is never module-global. **Every guard helper takes `ctx=None` and builds one when it is None:** `_voucher_guard_base`, `_voucher_lines`, `_voucher_held_batches` and `_voucher_pending`. Their other callers (`loss_piles.py:2129`, `_s452_release` 8063, the routes at 5460 and 5521) are unchanged (R3-C7). **`amir_stage` gains `ctx=None`:** when it is None, it builds one and passes it to every `_voucher_lines` / `_voucher_held_batches` / `_voucher_guard_base` call it makes (7874, 7912, 7948). Its callers are `_s524_hub_proof`, `_amir_board_light`, `amir_day.state` and `stockmatch`; none of them changes (R2 on R1-C25).

- **`stamp_iso(stamp)`:** moved verbatim from `stock_app._s524_stamp_iso` 8494. **`end_day(as_on, stamp_iso)`:** moved verbatim from `_s524_end_day` 8502. Each old name becomes a one-line wrapper. **The capture rule is unchanged** (charter 11).
- **`captures(con, sp, ctx)`:** every capture in `sp_close_name`'s md5s, with `sp_export.as_on`, `stamp`, `stamp_iso` and `end_day`. Only those with `end_day` not None are usable.
  - **The one choice rule, used everywhere (R2 on R1-B2): for any purpose, the capture standing for a given `end_day` is the NEWEST usable one by stamp.** That applies to `closing()`, `filed_vouchers`, the guard and `record_gaps`.
  - Example, 08-10: 06:00 printed 07-10 stands for the end of 07-10; 09:30 and 09:54 printed 08-10 are unusable. So the 06:00 capture is the end of 07-10.
- **`key_of(sp, name, ctx)`:** the one identity (charter 12).
  1. `sp_item.k20` for the printed name, spacing and case ignored.
  2. Else, through `item_alias.done_rows(con)` (ticked, not taken back): the partner name and the accepted `seen_name`s, each tried through step 1. If `item_alias` has no reader for an accepted `seen_name`, read `marg_item_rename_event` (event `accept`) **only for the rename ids `done_rows` returns**, and name it in the README as a read `item_alias` should own at its next kit.
  3. Else `sp.key(name)`.

  `stock_app._s524_key_of` becomes a call to it.
- **`printed_forms(con, name, ctx)`:** the name, its rename partner and the accepted `seen_name`s, by the same `item_alias` read.
- **`family(sp, k20, md5, ctx)`:** the printed names under the key **within that capture** (`sp_close_name`). Two forms of ONE renamed item are one member, not two (`printed_forms`).
  - When the key is absent from the capture: the members are taken from **the newest `sp_close_name` capture that prints the key**. Never from `sp_item`, whose `last_seen` the salt list moves for every item Marg holds (R3-C4).
  - More than one member → a family.
- **`closing(con, sp, name, at=None, ctx)`** → `dict(units, as_on, end_day, stamp_iso, md5, by, approx, packings)` or None.
  - The capture is the newest usable one with `end_day` ≤ `at` (default today).
  - **By name:** `sp_close_name` for any printed form, summed across packings (`packings` = the count; `approx=True` when more than 1).
  - **Fallback:** `SUM(units)` over `sp_close_name` of **the same md5** where `k20 = key_of(name)` → `by='key'`, `approx=True`. **Never `sp_close`.**
  - **Absent from a full capture (R2-C4).** If the key is known to `sp_item` with `first_seen` ≤ the capture's `as_on` (Marg prints only items with stock), the result is `units=0`, `by='absent'`. Otherwise None.
- **`marg(con, sp, name, at=None, ctx)`** → `dict(figure, closing{…}, sold, returned, bought, upto, approx, taps)`.
  - `figure` = `closing.units` + `sp_move` of `key_of(name)` over `(end_day, at]` (`incl_from=False`).
  - **`approx=True` whenever `family()` has more than one member**, whatever `by` is.
  - `taps` = tapped arrivals the spine does not carry (`_arrivals` with `in_spine` by `key_of`). They are reported beside the figure, never added to it.
- **`late_purchase(con, sp, name, cap, after, shelf, tol, ctx)`** → True when `|after − shelf|` equals, within `tol`, the units of a purchase of the key dated within 21 days on or before the capture's `end_day`. That is a bill that may have been keyed after the closing. It is the residual match `_s524_table` uses (8679–8693), moved here and called by both. `sp_purchase_line.source_md5` cannot say when a line first appeared (R3-C6).
- **The early-morning capture.** A capture printed day D and taken before 09:00 on D stands for the end of D−1, but it can hold a bill dated D keyed before it. For such a capture, an item with a purchase dated D is "not judged on this closing" (R3, the remainder of R2-B3).
- **`reach(sp)`, `covers(...)`, `tryable(...)`:** `_s524_reach` 8533, `_s570_covers` and `_s524_tryable` moved here verbatim, with one-line wrappers in `stock_app`. `record_gaps` runs in the `order_rules tick` process and must not import `stock_app`, which is a Flask Blueprint (R3-C9).
- **Absence, named (R3-C5).** `closing()` reads a key absent from a full capture as 0 when `first_seen ≤ as_on`, while `_s524_table` (8673–8678) reads it as 0 only when `first_seen > R.as_on`, else `absent_before`. Two rules exist; the morning-flow kit, which moves the proof onto `captures()`, makes them one. The README names it.
- **`base(con, name, ctx)`:** the one view of the three count tables, for the name **and every printed form of it** (the count holds old names). It returns `dict(qty, kind, day, at, count_id, fixed, marg0)` or None, taking the newest of:
  - the count family: `stock_count_item` with `stock_shelf_fix` laid over, `count_id` = the root or 0. **`count_id < 0` is a retired row, never read.**
  - `stock_point` rows other than `full_count` **and other than `superseded`**.

  `shelf_figure.count_family` and `points` become calls into it. Their shape is kept; the one change is that superseded points are excluded, and no figure moves today.
- **`shelf(con, sp, name, at=None, ctx)`:** base + `sp_move` after the base (the count day's sales in, its purchases out) + `boundary_purchases` + taps not in Marg + `scan_arrivals`.
  - **Family members come from `family()`**, never from the names passed in. Movements are split by counted share; `approx=True` when there is more than one member.
  - **No count → `dict(shelf=None, named='no_count')`. Never Marg's figure (rule 3).**
  - Below zero → shelf 0, `named='below_zero'`, as today (`shelf_figure.py:229–231`, R3-C10).
  - The boundary's `marg_now` comes from `closing()`.
  - It returns `arrived` (taps + scans) separately.
- **`figures(con, sp, names, at=None, ctx)`** → `{name: dict(marg=…, shelf=…)}`: both kept apart, one pass.
- **`expect_for_point(con, sp, name, ctx)`** → `dict(expected, basis, provisional, as_on, approx)`:
  - **approx (a family member)** → `basis='approx'`, `expected=None`;
  - counted → `basis='shelf'`, provisional = its `arrived`;
  - uncounted → `basis='marg'`, expected = `marg.figure` + taps, provisional = taps.
- **`ready(sp)`** → False when `sp_close_name` is missing or empty. Every judgment then answers "not yet", and **the guard holds** (an owner line) — never offers (R2-B7).
- **`witness(con, sp)`:** see §3.5.

### 3.3 The consumers moved

**A. The voucher guard (F-874; D715 a's second half), `stock_app.py` 5098–5223.**
- **`_voucher_guard_base(con, root, ctx)`** reads, per item, `stock_figure.closing()` through `printed_forms`. A renamed item is judged.
  - It keeps a **per-item** capture: day shown = the printed `as_on`, as the S524 header (8432) says.
  - **`by='key'` counts as unread for the below-zero test** (a family sum hides one size, R2-C5). So does `ready()` False, except that the line is then **held**, not offered.
- **`unkeyed`** = the frozen, non-void lines whose batch's **first non-empty entry** (`_s446_window`) is after that capture's `stamp_iso`, plus lines not entered at all. **Known limit (R2-C18):** a voucher typed in Marg before the capture but recorded on the page after it is counted twice. It is named in the README; no grace is applied.
- **The below-zero test** is unchanged in meaning: `m + unk + (0 if frozen else ch) < 0`, with `m` = `closing().units`.
- **The past-the-shelf test.**
  - **Applies only when** the shelf is not None, neither figure is `approx`, the item has no open arrival (`arrived == 0`), and `late_purchase()` is False.
  - `after = marg.figure + unk + (0 if frozen else ch)`.
  - **Held** when `(ch < 0 and after < shelf − tol)` or `(ch > 0 and after > shelf + tol)`.
  - `tol` = setting **`stock.voucher_shelf_tol_packs`** × pack. Default `1`, lo 0, hi 5, on `loss_piles.SETTINGS` (141). **No row is written at install;** the default is read, so the desk stamp does not move (R2 on R1-C12).
  - Items it cannot judge are counted as "not judged against the shelf".
- **Both call sites change:**
  - `_voucher_lines` keeps `ch < 0` for the below-zero test and adds **any `ch`** for the past-the-shelf test (5146).
  - `_voucher_held_batches` drops its `if int(ch) >= 0: continue` (5212) for the past-the-shelf test, passes `frozen=True`, and keeps below-zero for ISSUE lines only.
- **A held entry carries** `why='below_zero' | 'past_shelf' | 'not_ready'`, `marg_now` and its day, `shelf`, `after`.
- **The owner's words are built once, in `_s521_stage_words` 8381–8388:**
  - `below_zero` keeps today's sentence;
  - `not_ready`: *"Count #N: ITEM (voucher …) — held: the spine's closing table is not ready yet"* (R3-C8);
  - `past_shelf`: *"Count #N: ITEM (voucher …) — the count-day sum asks X; it would take Marg to Y against the shelf figure Z (closing of dd-mm, taken HH:MM): not given to Amir"*;
  - the summary line gains *"not judged against the shelf for N item(s) (a family figure, no count, goods not yet billed, or a bill keyed after the closing)"* beside the existing *"closing not readable"* line.
- **Install-day state.** Print, before and after placing, every pending (unfrozen) and frozen voucher line of count #1 with its old and new verdict.
  - **If any line flips** (offered ↔ held) **or `A["pending"]` changes** (it decides `a_is_open` 7883): **STOP before placing and report.**
  - In the 01:40 copy all 37 non-void batches are entered and all 30 stage-C batches are released, so `_voucher_held_batches` sees an empty key list today.
- **Remove `_voucher_held`. Keep `_voucher_void`** (the kit-only void door, §2.6). `DUTY_MAP` needs no change.

**B. Points, settling, traces (`stock_watch.py`).**
- `_s454_expected` → `stock_figure.expect_for_point`.
- New column `stock_point.basis TEXT` (additive, healed in `ensure()`; NULL on old rows). `write_point` stores it.
- **An approx point (R2-B8):** `basis='approx'`, `expected_units=NULL`, `gap_units=NULL`. No loss line, no trace, no verdict.
  - `verdict` and `verdict_hi` are set to `""` **before** `write_point`'s empty-gap branch (799), so its *"Marg mein yeh item nahi mila"* never prints (R3 blocker 2).
  - `gadbad` (1197–1207) records the text for an approx item and **opens no trace**, so no *"wajah mil gayi"* follows.
  - Darpan sees only the existing receipt *"Likh liya: X — q."* (`answer_roster` 1115), for short, surplus and match alike. **No new staff sentence.**
  - Print every renderer of `verdict_hi` on his pages (stockmatch, `darpan_view`) with what it shows for an approx point.
  - The NULL gap keeps it out of the month's leakage (1477) and the watch trend (1608).
  - The owner's watch card gets one English line: *"ITEM: counted N against a family figure (approximate) — not judged"*.
- **`correct_roster` 1143 carries the old point's `basis`** (approx included) with its `expected`.
- **`settle_provisional`** re-judges each provisional point **on its stored basis**. NULL → `'marg'`, judged by `expect_for_point`'s marg branch (today's `expected_units` meaning, read through the one capture rule). It never re-judges an approx point.
- **`open_trace`** receives the point's `E` (basis, expected) from `write_point` and judges its window on that same base.
- `expected_units` 732 stays for the witness only (its docstring says so). Remove `latest_close_day` 474.

**C. "Bill entry baaki" and arrivals (F-873's family-key half).**
- `bill_pending_lines` (877), `_arrivals` 708 (`in_spine`) and `shelf_figure.scan_arrivals` key the spine by `stock_figure.key_of`.
- The S537 tie stays.
- Seen, not touched (charter 12): `pad_norm(name[:27])` matching of order lines.

**D. The shelf figure and the shelf-gap flags (`shelf_figure.py`; F-862 for these readers).**
- **`figures`** reads both figures from `stock_figure`.
  - **`latest_snapshot` is removed.** So are `_s524_capture`, `_s524_captures` and `_S524_CAPTURES`.
  - **`filed_vouchers`** takes its two moments from `captures()`' `stamp_iso`.
  - Its output keeps its keys: `marg` = `marg().figure`; `marg_as_on` = the capture's printed `as_on`. `pack_size` / `packing` come from `sp_close_name` with `qty_words.pack_of` (or `sp_item`); name the one used.
  - **No count → `shelf=None, named='no_count'`.** `_s454_shelf_snap` (≈1806) already skips `no_count`.
- **A NEW table for the gap sets (R2-B6):** `s577_shelf_gap (end_day TEXT, item TEXT, capture_md5 TEXT, shelf REAL, marg REAL, gap REAL, marg_move REAL, voucher REAL, base_day TEXT, pack INTEGER, approx INTEGER, flagged INTEGER, why TEXT, at TEXT, PRIMARY KEY (end_day, item))`.
  - **`s454_shelf_gap` is left untouched.** It is a record, read by nothing after install.
  - **`record_gaps` and `rejudge`** read and write only `s577_shelf_gap`, every query included: the existence check, `prev`, `prow`, `origins`, both passes.
  - A set is written **once per `end_day`**: from the newest usable capture for that `end_day`, and only when the sale and purchase reach covers it (`_s524_tryable`; charter 1b). It records `capture_md5` (charter 4).
  - **Only the newest covered `end_day`** is written by a pass. `prev` is the newest earlier set.
  - **`gap_flags`, `gap_flag`, `gap_line` and `porders_s454.gap_flags`** read `s577_shelf_gap`.
- **No seed: judging starts fresh (R3-C1, C2, C3).** The old sets' flags rest mostly on shop-hours closings: 41 of the 42 flagged on 16-10, and all 22 of the 16-10 origins clear against the usable end-of-15-10 capture. They are not carried.
  - **`record_gaps` computes `prev` from the captures, not from stored rows.** Marg's figures at the previous usable capture come from `closing(md5)`. So the first pass judges the newest covered `end_day` against the usable capture before it. A flag carries forward only from an earlier `s577_shelf_gap` set.
  - `rejudge` works on `s577_shelf_gap` alone. Its window fills from the second pass.
  - **`record_gaps` writes nothing while `ready()` is False** ("not yet").
  - **The walk prints the install-day state (charter 7):** every item flagged in the newest old set, and which of them the first new set flags. The spot roster's reasons are printed before and after. That difference goes to the owner.

**E. The Loss desk only reads (F-841, `loss_piles.py`).**
- `rebuild` 1207 no longer calls `sales_test`. **The full build writes `stock_pile_cache` and `_meta`, and nothing else.**
- **`_classify_one`** (so `refresh_items` 1286 keeps it) marks a line that `sales_test` would have closed with `why` *"sold after count: N sold since dd-mm against M counted + B bought"* (owner, English). It stays for his existing doors. `sales_test` is removed.
- **The stamp's `spine` part (R2 on R1-C1)** = the md5 of: the sorted `sp_export.md5` list with `ok=1`, the `sp_meta` rules version, and the sorted `sp_alias` rows — all read from `spine.db`. A rebuild of the same inputs no longer rebuilds the desk; a new export, a rules change or a rename tick does.
- **System-written rows in `stock_shelf_fix` (R1-C23, R2-C9, R3 blocker 1).**
  - **The two of 27-09 (DOLOGESIC SP, TYCOB 1500) are not marked.** Their `stock_diff_lane` EXPLAINED words and closed `stock_diff` rows go with them. Un-marking them would bring the count-day differences back as ISSUE vouchers (−288 tabs and −7 vials, `_word_vouchers` 4132).
  - The Loss desk shows one English owner line: *"2 lines were closed by the system on 27-09 as 'sold after count' (DOLOGESIC SP, TYCOB 1500); from now on such lines are yours to decide."*
  - **If any `stock_shelf_fix`, `stock_sales_test` or `stock_diff_lane` row was written by `system` on or after 2026-10-18** (the desk opening at about 09:5x IST), **STOP before placing and report each one.** The owner decides what happens to them. Nothing is marked by the kit.

**F. The *stock now* and *drift* pages — `api_now` 2209 and `api_drift` 1669 only.**
- Their figures of record become `stock_figure.figures`, with the capture each stands on.
- The push_expected figure (`_feed_latest`) is shown beside them in a column headed *"PC's old estimate (retiring)"*, **to the doctor role only**. These routes also admit `viewer` and `maker` logins (2195, 2216).
- `_three_way` and `_r_stock` are untouched (rung 4f).

### 3.4 What stays, with its rung (the README's "left for later")

- `stock_snapshot`'s writer `/api/snapshot` 1142 and `reconcile` 995.
- **Rung 4f:** the count's own figures (§2.1 a row 9).
- **S486 B and rungs 4a/4c:** the order engine (§2.1 a row 8).
- **Rung 5:** the list readers (§2.1 b), and `marg_spine.py`'s identity.
- **Rung 4d:** `stock_spot_check`.
- **4b-2:** `expected_units`, push_expected, marg_shadow.
- **The stage proof's own table** (`_s524_closings` / `_s524_table` / `close_of` 8633 reading `sp_close` by printed day; R2-C1, C2) moves onto `captures()` in **the morning-flow kit**, which changes the proof anyway. In this kit it calls the wrapped capture rule and `key_of` only, with identical verdicts (control 8).
- **At count #2:** `_s454_store_shelf` stores `shelf_qty = NULL` for an uncounted item (`porders_s454` ≈1614 counts `IS NOT NULL`). Announced.
- **The morning-flow kit (next, by the owner's word):**
  - start-of-day captures (a charter rule-11 amendment, with R2-B2's offset test);
  - visit cover for purchase reports (R2-B4's rule);
  - "agrees = right at once" (R2-B5);
  - the hub's corrected-item words (R2-C6);
  - Amir's page with the export last (findings D, a mock-up first).

### 3.5 The side-by-side week (witness only)

- `python3 stock_figure.py witness` writes `/root/finance/spine/stock_figure_witness_<Mon…Sun>.txt` (the IST weekday; seven files, overwritten a week later; nothing deleted).
- For every item of the newest usable capture it lists:
  - `stock_figure.marg` against `expected_units` against the newest `push_expected` row (`stock_feed`), each with its day;
  - `marg_shadow`'s line where `sh_diff` has one;
  - per pair, the items that differ by a pack or more;
  - the named reason.
- **Crontab:** `# S577_WITNESS 58 23 * * *`, **without the spine lock** (read only; `spine.db` is replaced by rename). It honours `/root/finance/_off/ALL_OFF`. **The crontab is the parent's: one line in the README.**
- Seven explained nights = 4b-2's start condition.

## 4 · The walk (scratch copies of the live database and spine; never the live files)

**Read the live state first** (charter 7), and print:
- count #1's stage;
- every pending and frozen voucher line with its old verdict;
- provisional points;
- the newest three `s454_shelf_gap` sets;
- `stock_pile_cache_meta`;
- **every `stock_shelf_fix` / `stock_sales_test` / `stock_point` row by `system` or with source `sales_test`**, dated;
- the newest seven captures with `end_day`;
- the families of the newest capture;
- names printed with two packings.

**Controls** (each red on the old files and green on the new):

1. KNEE SUPPORT L HINGED (renamed) is judged by the guard, not "not readable", and is `approx=True`. A renamed item with no other size under its key is **not** approx.
2. The 01-Oct Yuvika immobilizer line, with its tie blanked, is not "bill missing".
3. The past-the-shelf test:
   - an ISSUE line overshooting the shelf by two packs is held, with the `past_shelf` words;
   - a line within `tol` is offered;
   - **a frozen batch line landing exactly on the shelf is NOT held;**
   - a RECEIVE line overshooting is held;
   - an item with a late-keyed bill is "not judged against the shelf".
4. The capture rule (unchanged):
   - printed 17-10, taken 18-10 05:17 → the end of 17-10;
   - printed 18-10, taken 09:37 → unusable;
   - printed 18-10, taken 22:30 → the end of 18-10;
   - 08-10's three captures → 06:00 is the end of 07-10.
5. Two reads of `/api/loss/1/piles` across a spine rebuild of the same inputs: one build, and **`total_changes()` shows no write outside the two cache tables**. A new export forces one build, again with no outside write.
6. Settling and correcting points:
   - a shelf-basis provisional point is settled on the shelf basis;
   - a corrected spot count keeps its basis;
   - **an approx point stores NULL gap, shows no verdict, and is absent from `month_leak`**;
   - a corrected approx point stays approx.
7. **Shelf figures and the order plan:**
   - an item with no count → `shelf=None`, and the plan's lines for no-count items are equal before and after;
   - every counted item whose shelf figure moves is printed (old, new, why).
8. Identity and stage verdicts: `key_of` = the old `_s524_key_of` for every item of all 37 non-void batches, and **stages A and C give identical verdicts.**
9. The gap sets:
   - the first pass writes one `s577_shelf_gap` set for the newest covered `end_day`, judged against the usable capture before it (a second pass writes nothing);
   - `s454_shelf_gap`'s row count and content hash are unchanged;
   - the roster's reasons before and after are printed.
10. A `past_shelf` held line prints the `past_shelf` sentence, not the below-zero one.
11. **Install order:** with `sp_close_name` absent, `ready()` is False, every lowering line is held with the `not_ready` words, and `record_gaps` writes nothing.
12. An item absent from a full capture but known to `sp_item` reads `units=0`. Print every item whose staff words would change because of it.

**Grep test (rule 2) — after the edits these are empty:**
- `def latest_snapshot`;
- `stock_snapshot` inside any function of §2.1 a rows 1–7;
- `sp.key(` in `bill_pending_lines`, `_arrivals`, `scan_arrivals`;
- a second definition of the capture rule or the stamp parser;
- `sales_test(`;
- `_s524_capture`;
- `s454_shelf_gap` outside its own DDL (it is read by nothing after install).

**Also:**
- `python -m py_compile` on every changed file (`/root/wa/venv/bin/python3` on the box); `selftest_spine.py` green.
- The scratch spine built by the new `spine_build.py` gives the same gate (13/13) and the same `sp_close` as the live one.
- **Amir's card** (`/finance/amir`) and `/api/pad/amir/1` stay **under 2 s and 100 KB.**

## 5 · Install (the owner's one line, then you) — **08:00–23:59 IST only**

1. Build lock. Check the FROM pins. Check that `spine_state.json` is green and under 30 minutes old. **Check the 18-10 desk rows (§3.3 E): any → STOP.**
2. Back up all seven files as `.bak_S577_<old8>`.
3. **The spine first.**
   - Place `spine_build.py` and `selftest_spine.py`.
   - Run the build by its cron command but with `flock -w 300`.
   - Check that `sp_close_name` is filled and the gate is 13/13.
   - Check that `sp_close` equals a build of the **same input md5 list** by the old builder (R3-C13).
   - On any failure: put the two files back and STOP.
4. Print the install-day state: §3.3 A, and §4 controls 7, 9 and 12. **If a voucher line flips or `A["pending"]` moves, STOP.**
5. **The parent's clinic-doctor (S578, live 10:46 IST 18-Oct) restarts a part it finds down.** Before the restart below, create its off-switch `/root/deploy/_off/DOCTOR_AUTO_OFF`. Remove it once `healthz` returns 200, and say so in the report.
6. **Place the rest in one move.** Stage `stock_figure.py`, `stock_app.py`, `shelf_figure.py`, `stock_watch.py` and `loss_piles.py` beside their targets under temporary names, then rename all five in ONE shell command. Restart `clinic-finance` once. `healthz` must return 200. (`record_gaps` writes nothing until `ready()`, so the `order_rules tick` cannot race a half-placed set.)
7. Print the state again. Read back every md5.
8. **Rollback, if anything after step 6 fails:**
   - restore all seven files from the backups in one command and restart once;
   - `sp_close_name`, `s577_shelf_gap` and `stock_point.basis` stay — they are additive and nothing old reads them;
   - say so in the report.

**Read after install, as each login,** the page they use, and print any line whose words changed:
- amir: his card and steps;
- darpan: Stock milaan and Kal ka hisaab;
- shavez: his reports tile;
- reception: the ordering page;
- manoj: the hub, the Loss desk, *stock now* and *drift*.

**Never run** `deploy_kits\S488_DATES_AND_WAITS\deliver_S488.ps1`. **Never add to** Amir's *Aaj ka kaam* list (D690).

## 6 · Report (`claude_code_briefs/REPORT_S577.md`)

- **The charter section:**
  - retired: `sales_test`, `latest_snapshot`, `_s524_capture` / `_s524_captures` / `_S524_CAPTURES`, `_voucher_held`, `latest_close_day`, the bare-clip keys of §3.3 C, and `s454_shelf_gap` as a read;
  - left, with its rung (§3.4);
  - anything left out or seen and not touched;
  - the spine's state at install.
- **The install-day tables:**
  - voucher lines;
  - shelf figures that moved;
  - the gap flags old and new;
  - the spot-roster reasons;
  - the 18-10 desk-row check (§3.3 E);
  - staff words that changed.
- **Also:**
  - the first witness file;
  - every control, red then green;
  - the md5s;
  - the answers to §7.

## 7 · What only the live spine can confirm (answer each in the report before the first edit)

1. The accepted full closing captures: how many, and how many share an `end_day`.
2. That `sp_close_name` names equal `stock_count_item` / `stock_snapshot` names for the same item.
3. Names printed with two packings in one capture, and their count.
4. The members per family key in the newest capture, with renamed pairs folded.
5. That `sp_item` holds the old names of the 15 voucher items (control 8).
6. That the gate stays 13/13 after the new table.

*S577 brief v4 · session 324 · 18-Oct-2026 · v1 → R1 (8 blockers, 27 corrections) → v2 → R2 (5 R1 items partly fixed, 8 new blockers, 18 corrections) → v3: the morning-flow rules moved to their own kit → R3 (3 blockers, 13 corrections) → v4: simplified (no seed, no marking, one move); every finding folded in · read from the 18-Oct 01:35 bundle and 01:40 database copy.*
