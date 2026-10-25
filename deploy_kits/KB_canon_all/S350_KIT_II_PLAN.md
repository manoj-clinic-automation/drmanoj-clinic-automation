# S350 · KIT II — THE BUYING MODEL · FINAL PLAN (for the owner's yes)
*Written 25-Oct-2026, 07:0x IST, by the Sanjeevni chat (S350) on claude-fable-5-1, at the owner's word "Rerun this kit plan with fable, and give the final." Replaces the 06:4x draft. Brief of record: `claude/S486_BUYING_MODEL.md` Part B (S295) as corrected by `claude/S308_S486_CHARTER_REREAD.md` (nine changes); step 4 of `claude/S327_SANJEEVNI_RESTRUCTURING_PLAN.md`. Read for this plan: the 25-Oct bundle's `order_rules.py` 8d078dbe whole at the lines the kit edits, `spine_read.py`, `spine_build.py`, `order_rehearsal.py`, the 25-Oct database copy; the replay re-run twice (`S350_replay_final2.py`, `S350_replay_final3.py` beside this file).*

## 1 · What it is, in five rules
The system makes its own order list every morning and judges it every night against what was actually bought. Kit II changes how that list is made:
1. **Each supplier at its own rhythm** — the review interval is the median gap between its bill days over 90 days (clamped 2–30 days); Kedar stays Monday + Friday (your ruling of 26-Sep). Due = today − last buy ≥ interval, never on a blocked day, Sunday or holiday.
2. **The shop's own lots** — the quantity is rounded up to the item's usual purchase lot (median of the last 180 days), at least one lot, capped by cover days; a new medicine (first bought within 28 days) gets one lot.
3. **Yesterday's sales in the list** — the rate windows (28 days and 7 days) end on the spine's last sale day, never today; the short rate counts when the item sold on 3 of the 7 days and is capped at 2× the long rate. If the sale report lands after 09:00, an untouched list is made again once, before 13:00.
4. **The shelf keeps one large sale** — the level is never below the largest single day's sale of the last 28 days.
5. **Between-review orders only when the stock will not last** to the next review + lead + 1 day (today's engine adds the full safety and fires three times as often).

## 2 · What changes for the staff — nothing
`order.source = marg_sheet` stays: Darpan's Marg sheet is the order. The new list is made and scored in the background (the proposals already exist every day — 128 since 28-Sep — and the nightly rehearsal already scores them). No staff screen changes; no count is asked of anyone; nothing of the model's reasons is served to Darpan's tab (charter rule 14).

## 3 · What you will see
On your approvals page, inside **Buying rules for medicines**: one line **How the list is made — New (each supplier's rhythm, the shop's lots) / Old (fixed days)** with one button; under it the weekly score, split by model once the first new week is scored (seven nights after the switch-on); the thirteen new settings in the same table as today's, each at the replay's value; and the "stock stood on" line the engine already returns (`inputs`) — the closing day, the sales day, counted / Marg / absent.

## 4 · The evidence — re-run this morning on the 25-Oct database
Replay re-anchored on Marg's closing as on 23-10 (anchor day 22-10); 199 medicines sold, 100 like-for-like (books that add up). Each "empty-shelf day" = one medicine at zero for one day.

| window | | empty-shelf item-days | avg stock | supplier orders / week | lost sale |
|---|---|---|---|---|---|
| **04-Oct … 22-Oct — 19 days the model never saw** | the shop (Darpan's sheets) | 27 | Rs 1.83 L | 15.1 | — |
| | today's engine (fixed days) | 26 | Rs 1.25 L | 25.4 | 2.23 % |
| | **Kit II** | **10** | **Rs 1.75 L** | **18.8** | **1.47 %** |
| 04-May … 22-Oct — whole | the shop | 231 | Rs 1.81 L | 18.2 | — |
| | today's engine | 195 | Rs 1.29 L | 24.3 | 1.35 % |
| | **Kit II** | **84** | **Rs 1.70 L** | **20.4** | **0.69 %** |

**Every rule still earns its place on the longer data** (whole window, Kit II with one rule taken out → empty-shelf days): without the lots 123 · without between-review orders 187 · list made before the sale report 100 · without the 7-day rate 103 · without the largest-day floor 94 (over 56 days instead of 28: 78 — a setting, left at 28). Safety 2 → 91, safety 4 → 87 (more stock, little gain): 3 stays. Minimum order Rs 2,000 → 104 with fewer orders: your Rs 500 stays. Kedar learnt → 85: your fixed days cost nothing. If goods take two days, not one: 127 (the shop 231).

**Honest cost:** about 3 more supplier orders a week than Darpan places (20.4 vs 18.2; on the new days 18.8 vs 15.1). **Honest limits:** the replay re-implements the rules on the tables and reads 100 of 199 medicines; the engine itself stands on the spine's stock figure, which today differs from Marg's own printed closing on 191 items — if that figure is off, any model's quantities are off, and the nightly score is what shows it. That is why the score, not the replay, decides the switch.

## 5 · What has already been built since the brief, and what this kit carries (the S308 nine, settled)
Done by S593 (19-Oct) and S577/S583: (i) one stock source — `_s470_snap` reads `stock_figure.marg()` + taps + scans, counted items the shelf figure, `plan()` returns `inputs`; (ii) `rhythm()` reads the spine's bills by `supkey`; (iii) one `days_left` on every row; F-738 is closed (`not_confirmed` live). **This kit carries:** one lot (`_s470_purch` → `model_lot`), one interval (`rhythm()` → `model_interval`), `review_interval` computed at read (the stored columns display-only, stamped); the `inputs` stamp on every proposal and the relist when ANY input moves (sales day, closing day or spine build), the fold saying "stale" for a touched list; B.6 ("count it") DROPPED; B.5 (supplier not known) stays on your fold as a read-only list — a medicine never bought has no supplier and its first bill names it, no door; the install gate on `spine_state.json` (passed, fresh) and the "not yet" answer when the closing is older than the sales; "new medicine" = the spine's earliest purchase line within 28 days (the replay's own test — `first_seen`'s shape is not guessed at); every unit figure in a `why` through `_qw`; the README's retirement list (`_s485_days_left` already gone; `fixed` retired after four scored `levels` weeks; `engine_source = tables` named to rung 4b); dead code OR `lead_learned`'s empty loop removed. The pure arithmetic (eight `model_*` functions, no database, no clock) is unit-tested in `selftest_spine.py` and is the same code the kit's replay runs.

## 6 · How it is proven before install (the walk, on scratch copies)
1. **`fixed` is today, line for line** — `plan()` and `prepare_day` with the kit's files against the live bytes on today, a Monday and a Thursday; any difference = stop.
2. The rhythm table for every supplier (bill days, median, interval, cap); Kedar fixed; the override and both clamps; `last_buy` from orders first, bills only when no order within 30 days; an interim order never moves the review.
3. Rate, floor and lot arithmetic on invented series (the pure functions); the relist once and only once, never on a touched list, never after 13:00, never on `fixed`.
4. **The real day, both models, on the live copies** — suppliers due, lines, value, the fifteen largest quantity differences item by item: the table goes in the report whole.
5. **The replay inside the kit** on the spine rebuilt offline from `D:\Downloads\margsync\MargArchive` (the S339/S348 road; `spine.db` is in no bundle) — the kit's own functions must land within 10 % of the reference's five figures; a larger gap is found and named, never tuned away.
6. Staff-eye: Darpan's tab and `api/order` on `fixed` equal the live bytes; on `levels` the one header line "बिक्री dd-mm तक · गिनती/क्लोज़िंग dd-mm" and nothing else new.
7. Every cron command the kit's files serve run once on scratch (F-711).
Install: gates → pins (the 25-Oct bundle's) → build → compile → walk (red = nothing placed) → backups → place → the columns and settings seeded (audited) → `order.model = levels` only because `order.source = marg_sheet` (else `fixed`, said) → one restart of `clinic-finance` → healthz → read back as you, printing what staff see next (nothing) and when.

## 7 · After the install — the shadow weeks and the bar
The new list runs beside Darpan's sheet. From the seventh night the weekly score reads per model: of what was bought, how much was on the list in time · of what was listed, how much was bought within 14 days · medicines that ran out, how many were listed in time. **D673's bar — three weeks running at least 85 % / 80 % / no more stock-outs than Darpan's sheet — brings the switch (K4, `order.source = system`) to you for your word.** Not before, never by itself. `fixed` stays one tap away throughout; Darpan's Marg sheet stays the fallback before and after.

## 8 · Decided by Claude, not put to you
One kit (Part B alone; Part A's fixes are live or folded in); the owner door is the existing *Buying rules* fold, no fourth fold; B.6 dropped and B.5 read-only on your fold (charter rules 2, 3, 7 and your ruling of 11-Oct); the replay runs on the offline-rebuilt spine; the kit number is claimed on the board when the build starts (F-515), not now; the build road is the chat itself (your word).

## 9 · Your part
**"Yes"** to this page. Then, after the build and your publish double-click, one paste line on the VPS. Nothing else — no diagnostics, no checks, no staff instruction.

*Evidence beside this file: `S350_replay_load.py` (the S295 loader re-anchored), `S350_replay_final2.py` (the three windows), `S350_replay_final3.py` (every rule taken out, both windows). Data: `D:\Downloads\_kbtools\vps_code\finance_nightly.db.gz` of 25-Oct 01:35 IST; the bundle of the same hour. No person's name or number read or written.*
