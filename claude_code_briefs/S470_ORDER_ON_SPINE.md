# Claude Code brief — S470_ORDER_ON_SPINE (the medicine order engine reads the spine; the trial scores the real list; one weekly line for the owner)

Written 04-Oct-2026 by the Sanjeevni chat (session 285) from `S285_ORDER_GENERATION_ANALYSIS.md` (project knowledge; also `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S285\`), the owner's word of 04-Oct ("every build to the designed architecture only; it's your call on these kits and when to start"). Read `CLAUDE.md` first.

**Kit S470 · decisions D672, D673 · faults F-718, F-719.** It finishes rung 4a of `S272_SPINE_ARCHITECTURE.md` §5 ("the order engine reads the spine — ordering is the first consumer on purpose"), which has stood HALF since 27-Sep (`S283_SPINE_READINESS_27SEP.md`). It serves D626 (the buying rules as settings), D666 (the order source switch, untouched here), D667 (the shelf figure), D570 (the nightly rehearsal and its score).

**What this kit is NOT.** It does not change which list the staff see (`order.source` stays `marg_sheet`), does not change the buying rules or their values, does not change any staff screen, and does not build the buying model (that is the next kit, after this one's report). It changes **where the engine's three numbers come from** — the sale rate, the stock, the supplier and lot — and makes the nightly trial score the list the engine actually makes.

**Runs on the 04-Oct 01:35 bundle's files** (pins in §6; read each live before its first edit).

**Touches — all Sanjeevni's, declared on the board (`_numbers` v250):**

- Server, `/root/finance/`: `order_rules.py`, `porders_s454.py` (the owner's card: one line added), `spine/spine_read.py`, `spine/selftest_spine.py`, `spine/order_rehearsal.py`.
- `purchase_app.py`: **one anchored edit only** — `plan_line(it, cad_days)` gains an optional third argument `dead_after=None` and reads `dead_after or DEAD_AFTER_DAYS` where it reads the constant today (line ~1249); nothing else in the file changes, and every other caller is unaffected. Its helpers `_pace`, `_latest_snapshot`, `_last_purchase`, `_in_transit` are not edited; `order_rules.py` stops calling them and reads `spine_read` instead. Every other caller of those helpers (the old `/finance/purchase/page/staff` page, the orthotic side) keeps them.
- `shelf_figure.py` and `stock_watch.py`: **read only, not touched.** The shelf figure's second spine reader (`stock_watch.Spine`) is recorded (analysis §2.7) and moves onto `spine_read` in the next kit, where its item-info shape is changed with it; not here.
- The crontab: **not touched.** The rehearsal's own line (`58 23 * * *`, S341) runs the file this kit replaces.

**No parent file:** not `finance_app.py`, `portal.py`, `tile_grants.json`, `packs.py`, `asset_register.py`, nothing under `/root/state_backup/`. One line for the parent is named in §8, not done here.

**READ ONLY:** `spine.db` (always; every reader opens it `mode=ro`), `finance.db`'s `order_proposal`, `purchase_order`, `purchase_order_line`, `order_scan_tie`, `stock_count_item`, `stock_point`, `stock_shelf_fix`, `s454_shelf_gap`.

---

## 0 · The rules this build stands on

1. **Marg is the book of record and the spine is the one store of what Marg said** (S272 §3.1). After this kit **the plan** — `_snapshot_inputs` and what `plan()` / `interim_plan()` make from it — reads no sale, stock or purchase figure from `sale_line_item`, `stock_snapshot`, `stock_feed`, `purchase_line` or `purchase_bill`. Out of scope and still on the old tables, named for the next kit: the orthotic keep-in-stock list (S403), and `order_rules`' own side reads — `candidates`, `oos_both_ends`, `new_items`, `rhythm`, `lead_learned`, `_month_spend`, `kedar_review`.
2. **One engine, never a second** (`order_rules.py` line 11). The rehearsal stops copying rules; it reads what the engine made.
3. **Settings, never constants.** Six numbers that shape the list are constants today; they become settings at their present values (B.8). Nothing changes on the day of install. They are edited where every `order.*` setting is edited today (the settings card of `/finance/porders?old=1`, `porders_s454.py` ~1317, `s454set`); the approvals page is a parent file and is not touched.
4. **Nothing live rebuilt.** Every edit is an anchored patch on the live bytes; the old path stays reachable behind one setting, `order.engine_source` (`spine` after install; `tables` brings back today's reads line for line — the fallback the owner's rule requires).
5. **The 20-letter key is the spine's, and it is kept here as it is** (F-719, recorded). An item that shares its first 20 letters with another is a *family*; the engine shows it as such (§2.6) and never splits it by guesswork.
6. **No number of any kind in the repository** (F-185): the walk's fixtures are made up at run time; no supplier phone, account or token anywhere. `python3 -B deploy_kits/NO_PHONE_NUMBERS.py --files-from <list> .` before the publish.
7. **Every test can fail**: each walk section has a negative control on the OLD file.
8. **Staff-eye walk** (D648): no staff duty moves and no staff screen changes in this kit; the walk still signs in as reception, darpan, shavez, amir and the owner on the scratch copy and shows each home byte for byte the same, and the owner's card with its one new line.

## 1 · PART A — the read door gains what the engine needs (`spine/spine_read.py`, `spine/selftest_spine.py`)

Add to class `Spine`, read-only, beside the methods that exist (`item`, `fact`, `stock`, `movements`, `sales`, `bills`, `purchases`); nothing existing changes.

- **A.1 `sales_daily(name, date_from, date_to)`** → `[{date, units, bills}]`, one row per day with a sale, **returns deducted**: `sp_sale_line` joined to `sp_sale_bill` on `(date, bill)`; a line of a bill with `credit_note = 1` counts negative. Keyed by `self.key(name)` (the alias map, as every method here).
- **A.2 `stock_series(name, date_from, date_to)`** → `[{date, units}]`, the spine's figure at the end of every day in the range (cumulative `sp_move` to that date; days with no movement repeat the previous figure). This is what "days the item was in stock" is read from.
- **A.3 `purchase_lines(name=None, supplier=None, date_from=None, date_to=None)`** → `[{supkey, supplier, bill, date, name27, qty, free, units, amount_p, net_amount_p, direction}]` from `sp_purchase_line` joined to `sp_purchase_bill` for the supplier's printed name; filters as given; `direction` as stored (PURCHASE / RETURN).
- **A.4 `family(name)`** → `{key, members: [{name, packing, unit_kind, first_seen}], n}` — the rows of `sp_item` under the key, reshaped from what the existing `item()` returns (`{key, items, family}`); `item()` itself is not changed.
- **A.7 `last_sale(name)`** → `{date}` of the latest `sp_sale_line` row for the key over all history, or `None` (used by B.2).
- **A.5 `closing(name, as_on=None)`** → `{as_on, units}` — Marg's own closing figure (`sp_close`) at or before the date; the existing `stock()` returns it inside a larger answer; this is the direct read the engine uses for the Marg basis.
- **A.6 `selftest_spine.py`** gains one check per new method on a made-up spine (a credit-note line counted negative; a day with no movement repeating; a RETURN line kept as RETURN; a family of two; `last_sale` on an item with one old sale; `closing` equal to `stock().marg_units`). The existing checks are untouched and still pass.

## 2 · PART B — the engine's three numbers come from the spine (`order_rules.py`; one anchored edit in `purchase_app.py`)

All inside `_snapshot_inputs` (`order_rules.py` 725–743) and the helpers it calls; `plan()`, `interim_plan()`, the rails in `plan_line`, `_staff_qty`, the item rules, the suppliers' rules, the days, the proposals — **unchanged**.

- **B.1 One setting decides the source:** `order.engine_source`, default **`spine`** at install. On `tables` the four old calls run exactly as today (the fallback; the walk proves the two lists equal on `tables`).
- **B.2 The sale rate (replaces `pa._pace`).** From `sales_daily` over the same window `_pace` uses — `today − order.pace_days` to today, both ends included (`purchase_app.py` 1320–1323) — `rate_per_day = max(0, sum of units) / order.pace_days`, `sell_days` and `peak_share` as `_pace` defines them; `days_since_sale` from a new read-door method **A.7 `last_sale(name)`** → the latest `sp_sale_line.date` for the key over all history (as `_pace` reads `MAX(business_date)`); **every item with any sale in the spine's history gets a pace entry** (rate 0 where nothing sold in the window), exactly as `_pace` seeds them (`purchase_app.py` 1346–1351), so a `keep` item with no recent sale is not dropped before its rule is read. **The formula is unchanged in this kit; only the source changes.** Returns deducted as today (the credit-note join). Units are the spine's (`sp_sale_line.units`, as `spine_build` reads Marg's quantity, pack and loose); where that differs from `_units()`'s reading of the old store (a plain number on a loose item), the walk lists the items and the report names them — the spine's reading is the record. The family split stays **equal among members** as S454 built it (`purchase_app.py` 7133–7181), now from the spine's `family()`; `approx_shared = n`. Sharing by stock is the next kit's.
- **B.3 Stock, both bases.**
  - Marg basis: `closing()` at the spine's latest accepted closing. Today's `_latest_snapshot` reads `stock_snapshot` (last write wins, `as_on` as dd-mm-yyyy); the spine's `sp_close` keeps accepted closings of 250 items or more (`spine_build.py` 275–278). The two are usually the same export but not always: the install compares them live before placing — dates converted, items matched by key — and prints the items where they differ and the two dates; a difference is a finding in the report, never hidden and never a reason to stop.
  - Count basis: `shelf_figure.figures()` **unchanged** in this kit (its reader moves in the next kit, §Touches). It is called as today.
- **B.4 Arrivals not yet in Marg — one rule, both bases** (replaces `pa._in_transit` and the `_s454_count_way` exception). An order's received lines (`purchase_order.status = 'received'` with `received_at` within the last `order.in_transit_days` (14) days, as today; `purchase_order_line.supplied`, else `packs`) and an order tied to a scan with `order_scan_tie.arrived = 1` count as stock **until** `purchase_lines(name, supplier)` shows a purchase line of that item from that supplier **dated on or after the order's own day (`purchase_order.created_at`'s date)** — not, as today, on or after the tap: Marg dates the bill by the supplier's date, which is often a day or two before the tap, so today's rule never sees the bill and counts the goods twice until the window ends. Matched by `spine_read.key` and by `supplier_key`, not by the exact printed name. On the count basis, a counted item's arrival is already inside its shelf figure and is not added again (as today).
- **B.5 The supplier and the lot (replaces `pa._last_purchase`).** From `purchase_lines(direction = PURCHASE)` **over all history, as `_last_purchase` reads today** (no window — the formula is unchanged), per item, **every field `plan()` reads today** (`order_rules.py` 788–801): `vendor` = `pa.supplier_key(printed supplier name)` of the latest line (the normalised key every rule, proposal and phone lookup is keyed by — never the spine's `supkey`); `vendor_disp` = the printed name from `sp_purchase_bill.supplier`; `suppliers` = the set of normalised keys; `rate_p` = cost per pack of the latest line (`net_amount_p ÷ qty`, else `amount_p ÷ qty`); `box` = the GCD of the quantities as today, 0 when none (`plan_line` then applies its own default for pack items and leaves a pieces item at 1, as today — `order.default_box` is **not** passed in; see B.8). **New, read and carried on the line but not yet used by the rails:** over the last `order.lot_history_days` (180) only, `lot_units` = the median quantity bought per line (units), `free_per_lot` = median free per bought. They are written into each proposal line (`lot`, `free`) for the next kit and the report; the quantity rails of this kit stay today's.
- **B.6 Families.** A line whose item is a family member carries `family = n` and the owner's view of the plan prints "(1 of 2 under this name)" after it; staff screens print nothing new (they do not show the system's list while `order.source = marg_sheet`).
- **B.7 A never-bought item is not dropped silently.** Today `plan()` skips an item with no supplier (`order_rules.py` 780–783) — an item with no purchase line in the spine's whole history. It still skips it from every supplier's proposal — but `plan()` returns it under a new key `no_supplier: [{item, on_hand, rate_per_day}]`, and the owner's card counts them in one line ("N medicines have no supplier on record"). Nothing is ordered for them.
- **B.8 Constants become settings**, defaults at their present values, on the settings card of `/finance/porders?old=1` like the other `order.*` keys (`SETTINGS`, with `ensure()` inserting them; the card's list of editable keys gains them): `order.pace_days` 28 (read by B.2) · `order.dead_after_days` 60 (passed to `plan_line` through the one `purchase_app.py` edit) · `order.on_order_days` 4 (replaces `ON_ORDER_DAYS`, `order_rules.py` 703) · `order.in_transit_days` 14 (B.4) · `order.lot_history_days` 180 (B.5) · `order.engine_source` spine (B.1, a word: `spine` / `tables`). **Still constants after this kit, named for the next:** inside `purchase_app.plan_line` — `DEFAULT_BOX`, `MIN_LINE_P`, `MAX_COVER_DAYS`, `PEAK_SHARE_SPIKE`, `THIN_SELL_DAYS`, `CONFIRM_LINE_P`, `BOX_STRETCH_ASK`; `PACE_DAYS` there survives only in a reason string.

## 3 · PART C — the rehearsal scores the real list (`spine/order_rehearsal.py`) — F-718

Replace the file's engine copy with a reader. The nightly line and the output folder stay.

- **C.1 What is kept each night.** The proposals the live engine made that day: every `order_proposal` row with `day = today` (`kind` fixed and interim), read **read-only** from `/root/finance/finance.db` (`?mode=ro`; the cron runs from `/root/finance/spine`, so the path is absolute), with their lines (JSON from `_line_out`: `item`, `qty`, `unit`, `pack_size`, `value_p`). Written to `orders/order_rehearsal_<date>.json` in the same shape as today's files: `lines[].key` = `Spine.key(item)` (the alias map), `order_units` = `qty × pack_size`, `value_p`, `vendor`, plus `kind` and `source: "order_proposal"`. **Nothing is computed, nothing is written to `finance.db`** — `order_rules.plan()` is never called from here (its `ensure()` writes settings).
- **C.2 The score, seven nights later** (`score()` as today): proposed and bought · proposed not bought · bought not proposed — against `sp_purchase_line` (direction PURCHASE), by key. A key proposed twice on one day (a fixed and an interim line, or two family members) is **one** proposed key with its units summed before scoring — today's `score()` keeps the last line it meets and silently drops the rest (`order_rehearsal.py` 281); the kept file keeps every line, the score merges them.
- **C.3 Two new scores, from the spine:**
  - **Stock-outs:** medicines (not orthotics; `stock_item_section`) with a sale in the scored week whose `stock_series` was at or below zero on any day of it; for each, whether it was on any kept list of the seven days before that day (`listed_in_time`).
  - **Money:** the value (`value_p`) of lines proposed on the scored day and not bought within 14 days.
- **C.4 The owner's one line a week** — written to `orders/order_score_latest.json` every night over the trailing 7 days that are old enough to score: a day is scored for "bought on list" and stock-outs when it is 7 days old, and for "listed, bought within 14 days" and the money when it is 14 days old; each percentage is over the days scored for it, and a day with no proposal counts in no denominator (no division by zero). Keys: `bought_on_list_pct`, `listed_bought_pct`, `stockouts`, `stockouts_listed_in_time`, `value_not_bought_p`, `days_scored_7`, `days_scored_14`.
- **C.5 The past is kept now.** `order_proposal` holds the engine's proposals since 28-Sep; on install the rehearsal keeps each day from 28-Sep to yesterday as if it had run that night, and scores whatever is already old enough (on 04-Oct nothing is 7 days old; the first 7-day score falls on 05-Oct, the first 14-day score on 12-Oct). The report says which days were kept and that the first score comes on its own night.
- **C.6 Negative control:** the old rehearsal's figures of the same day differ from the new (it scored a list nobody made); shown in the walk.

## 4 · PART D — one line on the owner's card (`porders_s454.py`, the `?old=1` page, English)

After the "Who decides the order" block and **outside** the `if ns and ns.get("cmp")` condition (the "agreed on X of Y" block, `id="s454cmp"` ~line 1390, shows only when a sheet exists; this line shows always), one line read from `orders/order_score_latest.json`: **"Last week: of what was bought, N% was on the list beforehand · of what was listed, P% was bought within 14 days · M medicines ran out, K of them listed in time."** When the file is missing or older than two days: "The weekly score is not ready yet." Nothing else on the page changes; the staff pages are untouched.

## 5 · Walk (`walk_s470.py`, scratch copies of `finance.db` and `spine.db` — backup API — rows keyed W470*; the walk-only portal secret and users; no phone number in any output)

1. **A** — each new read-door method on a made-up spine: credit note negative; no-movement day repeats; RETURN kept; family of two; `closing()` equals `stock().marg_units`. NEGATIVE: the OLD `spine_read.py` has no `sales_daily` and its `sales()` counts a credit-note line positive (shown).
2. **B, equality on `tables`:** with `order.engine_source = tables` and every new setting at its default, `plan()` on NEW equals `plan()` on OLD line for line (same scratch copy, same day) — the new fields `lot`, `free`, `family` left out of the comparison. This is the fallback proved.
3. **B, the spine source:** with `spine`, for every item in the plan, `rate_per_day` equals the rate computed independently in the walk from `sp_sale_line`/`sp_sale_bill`; the Marg-basis stock equals `stock_snapshot`'s figure for every item both stores carry on the same date (the items where they differ printed — a finding, not a failure); the count-basis figure byte-identical before and after (every item; `shelf_figure.py` is not edited, so this is a guard). NEGATIVE: a made-up sale bill present in the spine and absent from `sale_line_item` (the shape of the 72 missing bills): OLD's rate is lower than NEW's by exactly its units ÷ 28.
4. **B.4 arrivals:** a made-up order received on day D, its Marg bill dated D−1 and entered on D+2: OLD counts the goods twice from D+2 to D+14; NEW drops them on D+2. A received order with no bill within `order.in_transit_days` leaves the stock on day 15 in both.
5. **B.7:** a made-up item sold, never bought, in the Marg closing: OLD plan drops it silently; NEW returns it under `no_supplier` and the owner's card counts it.
6. **B.8:** each new setting read from the `setting` table; changing `order.pace_days` to 14 on the scratch copy changes the rate; changing `order.dead_after_days` to 1 zeroes a line whose last sale is 2 days old (through the one `purchase_app.py` edit). NEGATIVE: OLD `order_rules.py` with OLD `purchase_app.py` on the same copy with the same setting row — the line is not zeroed (the setting is read by nothing). `purchase_app.py` differs from its pin by that one anchored edit only (a diff of the two files printed in the walk, under 12 lines).
7. **C:** on the scratch copy with made-up proposals of 7 and 14 days ago, a blocked day with no proposal in between, and made-up purchases since: the three old scores plus the two new ones come out right by hand; the blocked day counts in no denominator; the kept file carries `kind` and `source: "order_proposal"`; `finance.db`'s md5 is unchanged after the rehearsal runs (it never writes). NEGATIVE: the OLD rehearsal on the same copy produces lines not in `order_proposal`.
8. **D:** the owner's card shows the line from a made-up `order_score_latest.json`; "not ready yet" when the file is absent; the card as a non-owner login (reception) — unchanged, no line.
9. **E, the staff-eye walk** (DUTY_MAP v5, unchanged): reception, darpan, shavez, amir, the owner — every home and door byte for byte the same as OLD except the owner's `?old=1` card. The duty map is not edited; say so in the report.
10. **The crons' own commands as scripts** (the lesson of F-711): `order_rules.py tick` exits 0 on the NEW file on the scratch copy with `ORDER_TICK=prepare` and `=remind`; `order_rehearsal.py` exits 0 on the scratch copies. Every added block sits above its file's `__main__` guard.
11. **Earlier walks** (S403, S407, S410, S414, S417, S428, S439, S440, S441, S444, S446, S452, S454's) run on the NEW files: the same reds word for word as on OLD (they have known reds; none new).

## 6 · Pins — the 04-Oct 01:35 bundle (`code_nightly.tar.gz` f241c3f6); read each live before its first edit; STOP that file if different

| file | FROM |
|---|---|
| `/root/finance/order_rules.py` | `734fc6bcd67bb23da1bea2a6e927fcad` |
| `/root/finance/purchase_app.py` (one anchored edit, §Touches) | `979391b6e191e0d2468f3db6fc57366e` |
| `/root/finance/porders_s454.py` | `c3562c5bc5602ecdb32e416a231ba30c` |
| `/root/finance/spine/spine_read.py` | `ab55344ee280b0b4847a45cebe6d3843` |
| `/root/finance/spine/order_rehearsal.py` | `02582fbea29f51606a6ba8bb8694d3fc` |
| `/root/finance/spine/selftest_spine.py` | read live; the bundle's copy is the pin |
| read only — `shelf_figure.py` `23c34ebb…` · `stock_watch.py` `6d4d660f…` · `order_sheet.py` `a5408df0…` · `spine/spine_build.py` (unchanged; md5 compared before and after) | |

Backups beside every file replaced (`<file>.bak_S470_<from8>`), `finance.db.bak_S470_<stamp>` by the backup API before the install's data step (the settings rows and the first-week scoring; `spine.db` is never written). Restart `clinic-finance` once; `/finance/healthz` 200; `/finance/porders`, `/finance/porders?old=1`, `/finance/amir`, `/finance/stock/page/count` answer 302 to a plain curl (the gate — expected). Red after placing: restore every file byte-identically, restart, healthz 200, report.

## 7 · Done means

- `order_rules.py` makes its plan from `spine_read` on `spine` and from the old tables on `tables`, and the walk shows the two equal on `tables` and explained item by item on `spine`.
- `shelf_figure.py` is untouched and its figures are unchanged to the unit (the guard of walk step 3).
- The arrivals rule is one rule on both bases; the double count of a bill dated before the tap is gone.
- `order_rehearsal.py` keeps and scores `order_proposal`, writes `order_score_latest.json`, never writes `finance.db`; the first week (28-Sep on) is scored on install.
- The owner's card shows the weekly line; no staff screen differs by a byte.
- Six settings exist at their present values and are editable on the `?old=1` settings card; the constants that remain inside `plan_line` are named in the report for the next kit.
- Every walk section green on NEW, its negative control red on OLD; healthz 200; the lock taken and released; the publish gate clean.

## 8 · Report — `claude_code_briefs\REPORT_S470.md`

For the owner (3–6 lines): what changed (the engine now reads the one corrected store; the nightly trial scores the real list; one line a week on his card), that no staff screen changed, and **the first week's score as measured** (N% · P% · M stock-outs · K listed in time · Rs X not bought).

For the chat: every pin FROM → TO read back on the box; the walk's output and its negative controls; **the items where the Marg-basis stock from the spine differed from `stock_snapshot`** (count and names); **the plan on `spine` against the plan on `tables` on install day** — lines added, lines gone, quantities changed, each with its reason (returns deducted; a missing bill now counted; a family; a never-bought item now named); the `no_supplier` list; backups; the service restarted; the lock; anything not done and why.

**One line for the parent, named here, not done:** `/root/finance/spine/orders/` into the state backup (`/root/state_backup/clinic_state_backup.py`), so the scores leave the box.

**Not in this kit, said plainly:** the buying model (levels, review intervals, the 7/28 rate, lots and schemes in the quantity, the family share by stock — the next kit, on this one's report); the shelf figure's reader onto `spine_read` (next kit); the five constants left in `plan_line` (next kit); Darpan's screen; the switch of `order.source`; F-719's repair in the spine; the earlier walks' known reds.

The owner's line, after the publish:

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S470_ORDER_ON_SPINE/install_S470_ORDER_ON_SPINE.sh
```

*S470_ORDER_ON_SPINE brief · 04-Oct-2026 · session 285 · the owner pastes one line into Claude Code; this file is the whole scope.*
