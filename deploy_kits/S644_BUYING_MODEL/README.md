# S644_BUYING_MODEL — Kit II, the buying model (D678 built) · project Sanjeevni · session 350 · 25-Oct-2026

**For the owner, in four lines.** Behind one setting (*How the list is made*, on your approvals page under *Buying rules for medicines*) the system's own order list is now made the new way: each supplier at its own learnt rhythm (Kedar stays Monday + Friday), the shop's usual lots, yesterday's sales in the list, the shelf kept for the largest single sale of the last four weeks, an extra order between reviews only when the stock will not last. **Nothing changes for the staff** — Darpan's Marg sheet stays the order (`order.source` is read, never written); the new list is made and scored every night in the background. After three good weeks of score (D673's bar) the switch to the system's list is brought to you for your word. *Old (fixed days)* is one button away and is proved line-for-line equal to today's engine.

## What this kit is
Brief `claude_code_briefs/S486_BUYING_MODEL.md` **Part B** (S295, 05-Oct), as corrected by `claude/S308_S486_CHARTER_REREAD.md` (the nine changes) and planned in `claude/S350_KIT_II_PLAN.md` (the owner: *"you do for kit 2 what you consider to be best for now"*, 07:01 IST 25-Oct). Part A's fixes were already live (F-738 `not_confirmed`, S593) or are folded in here (the owner's door). Kit I (S593, 19-Oct) put the engine on the one stock source; this kit builds the model on it.

The arithmetic is **pure** — eight functions in `order_rules.py` (`model_rate`, `model_big_day`, `model_lot`, `model_interval`, `model_cap_days`, `model_level`, `model_qty`, `model_interim_due`), no database, no clock — unit-tested in `selftest_spine.py` (`test_s644`, made to fail on purpose) and run by the kit's own replay (`replay_s644.py`) over the shop's months: **0.0 % from the reference** on the 25-Oct database copy (04-May … 22-Oct: lost sale 0.69 %, 84 empty-shelf item-days against the shop's 231, Rs 1.70 L average stock, 20.4 supplier orders a week).

## Files — FROM → TO (every edit anchored; `make_s644.py` rebuilds the TO bytes from the live FROM bytes and stops on any other md5)
| live file | FROM | TO | what |
|---|---|---|---|
| `/root/finance/order_rules.py` | 8d078dbe | 8a116cbd | 7 anchored edits (KIT; `rhythm()` → `model_interval`; the plan hook after `plan_line`; the interim hook; the interim keys; the stamp after `prepare_day`; the relist in `tick`) + the S644 block before `if __name__` |
| `/root/finance/porders_s454.py` | 673883e8 | 438714b8 | `S470_LIMITS` + `S644_CHOICE`; `_s470_valid` (a word, a clock); `_s470_set` (min ≤ max cross-check); `_s470_score_line` per model; `_s644_model_line` on the old page's card |
| `/root/finance/spine/spine_read.py` | 10697b38 | ad441b1d | one read: `last_sale_day()` |
| `/root/finance/spine/order_rehearsal.py` | 104d366d | c5d019ef | B.8: `keep()` stores `model`, `held`, `added`, `qty_engine`, `made_through`; `proposed()` skips added lines and scores the engine's quantity; `weekly()` writes `by_model` (when a week carried two models) and `darpan` |
| `/root/finance/spine/selftest_spine.py` | 7d0edb4a | a05229e1 | `test_s644()` — 20 checks on the pure functions and B.8 |
| `/root/finance/finance_ui/finance_approvals.html` | a7016a4e | 885f6f31 | **the parent's template** (served by `finance_app.py`, which is NOT touched): `poModelHTML` in the *Buying rules* fold (the line, the button, the score, the inputs, each supplier's rhythm, the eleven settings); two fields on the supplier form (Rhythm, Review every N days) |

Read, not edited: `stock_figure.py`, `shelf_figure.py`, `stock_watch.py`, `purchase_app.py` (`plan_line` is called, never edited), `darpan_kal.py` / `.html` (no change — his tab is unused on `marg_sheet`; the one header line of B.2a waits for the kit that moves the source), `porders.py`. **No crontab change** (the relist rides the existing ten-minute tick; the rehearsal line is S341's). **The medical PC and manojz: nothing.**

## What the model does (levels), rule by rule — and what `fixed` keeps
| | fixed (today) | levels |
|---|---|---|
| when a supplier is reviewed | its calendar (weekly Mon / fortnightly / monthly / Kedar Mon + Fri) | `rhythm_mode learnt`: due when today − last buy ≥ its interval (median gap of its bill days in 90 days, half-up, clamped 2–30; default 7 under 3 bill days; the owner's `review_days` overrides). `rhythm_mode fixed` (Kedar, owner-set days): the calendar as before |
| last buy | — | a sent/received purchase order that is not interim-only · a sent fixed/darpan proposal · only when neither is within 30 days, the newest bill day the spine holds; strictly before the day |
| the rate | sales of today − 28 … today ÷ 28 | long (28) and short (7) windows ending on the spine's **last sale day**, never today; the short rate counts when sold on ≥ 3 of 7 days, capped at 200 % of the long |
| the level | rate × cover | max(rate × cover, the largest single day's sale of 28 days) — a line plan_line left out is listed when the shelf is under that day's sale |
| the quantity | box-rounded, then 10-then-tens | the usual lot (median purchase units of 180 days) rounded up, the cover cap as a limit (never below one lot — `confirm` and a line when one lot is more than the cap); a new medicine (first bought ≤ 28 days) one lot; **no 10-then-tens on a lot-based line**; no lot → today's rails |
| cover cap | the row's cap | the row's cap when the owner set it, else by the interval: ≤ 7 → weekly cap, ≤ 14 → fortnightly, else monthly |
| between-review orders | fire when cover < days to next + lead + safety | fire only when stock ÷ rate < days to next review + lead + 1 (`interim_margin_days`); sized to the horizon with safety, through the lot |
| on the way | sent orders of 4 days count as stock | within max(4, interval + lead) of the order's own supplier |
| the list made again | never | before 13:00, when the sales day, the closing day or the spine build moved and nobody touched the list: rows UPDATED in place by (day, supplier, kind), ids kept, nothing deleted; a touched list is marked *stale* for the owner's fold |

**Not built, by the charter (S308):** B.6 "count it" (`shelf_figure` already judges Marg vs shelf once); B.5 on Darpan's tab (the not-known list stays on the owner's fold — a medicine never bought has no supplier and its first bill names it). **Nothing of `why`, the rates or the lots reaches a staff screen**; `_s485_line` names its fields.

## Settings (eleven, on the approvals fold and the old page's card; validated and audited through `/finance/porders/api/s454/setting`)
`order.model` fixed → **levels at install if `order.source = marg_sheet`** · `order.rate_short_days` 7 · `order.rate_short_cap_pct` 200 · `order.rate_short_min_sell_days` 3 · `order.big_day_days` 28 (0 = off) · `order.interim_margin_days` 1 · `order.relist_until` 13:00 · `order.new_item_days` 28 · `order.review_min_days` 2 · `order.review_max_days` 30 · `order.review_default_days` 7. Per supplier: `rhythm_mode` (learnt | fixed — seeded ONCE at the columns' creation: fixed for a `custom` cadence or owner-set `order_days` / `cadence`, learnt for the rest), `review_days` (blank = learnt). `bill_days90` / `rhythm_at` are display-only (the interval is computed at read; refreshed by the installer and by the 1st-of-month reseed).

## The walk (`walk_s644.py`, 46 checks, on scratch copies by the backup API; `walk_run.py` is its per-step child) and the replay
1 **fixed is today** — old bytes vs new on `plan()` + `interim_plan()` + `prepare_day` on today, a Monday and a Thursday: every old key equal, the rows equal, no stamp. 2 **rhythm** — the table for every supplier; Kedar fixed; clamps; default under 3 bill days; cap by interval; the words; `last_buy` (a) (b) (c) on the walk's own supplier (an interim-only order does not move it; today is not before today); the owner's override; the mode switch; bad values refused. 3 **relist** on a Monday (10 rows): same → nothing; moved + untouched → made again once, ids kept, count kept; touched → stale; after 13:00 → nothing; fixed → off. 4 **on the way** within the supplier's window, not beyond; fixed as before. 5 **the owner's fold** — `owner_state()['model']`; the settings route (word, clock, clamp cross-check, 17 keys on the card). 6 **the real day, both models** — counts and the fifteen largest quantity differences (in REPORT). 7 **the selftest** (71 checks). 8 **the cron commands** as scripts. **N** the negative control on the OLD bytes. `replay_s644.py` — the kit's functions against the reference arithmetic on one read-only copy: within 10 % (measured 0.0 %).

Built and walked in the Sanjeevni chat (the cloud workspace) against the 25-Oct 01:35 IST bundle and database copy, with the spine rebuilt offline from `D:\Downloads\margsync\MargArchive` (`spine_evidence.py` → `spine_build.py`); the installer repeats the build, the walk and the replay on the box's own live bytes, database copy and spine before anything is placed.

## Install (the owner's one line, after his publish)
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S644_BUYING_MODEL/install_S644_BUYING_MODEL.sh
```
Gates → the build lock → pins → build → compile (both pythons) → the walk → the replay → backups (`*.bak_S644_<from8>`, `finance.db.bak_S644_<stamp>`) → place → md5 read back → ONE restart of `clinic-finance` → healthz 200 → the data step (columns, settings, display columns, `order.model = levels` only on `marg_sheet`) → the owner's lines (F-740: the source and model in force, today's proposals by status, what staff see — nothing) → lock released. `DRY=1` rehearses everything and places nothing. Red after placing: every file back, one restart, healthz.

**Undo:** the installer prints the one line (`\cp -p` each backup back, restart). The columns and settings are harmless to the old bytes.

## For the chat (the close)
- Charter: one lot (`_s470_purch` → `model_lot`), one interval (`rhythm()` → `model_interval`), one days_left (S593); the interval computed at read; `inputs` stamped on the day and the relist on any moved input; B.6 dropped; B.5 read-only on the fold; the spine gate on `spine_state.json` (passed, ≤ 36 h); `first_seen` not read (new = the spine's earliest purchase line); every unit figure in a `why` through `_qw`; `_line_out` adds `model` to every row (fixed rows say `fixed`) — the one new key on a fixed line.
- Retire later, named: `fixed` after four scored `levels` weeks (`by_model` is the evidence); `order.engine_source = tables` (rung 4b). Dead code OR `lead_learned`'s loop is as it was (not this kit's lines).
- F-1024 (the parent's, 07:2x IST 25-Oct) names S619's DUTY_MAP rewrite — this kit touches no duty and no DUTY_MAP row (no staff duty added, moved or removed).
