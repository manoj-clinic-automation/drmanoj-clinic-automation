# S603_AMIR_CALENDAR_SAFE — Amir's flow off the calendar: the export fact, the covering export, the owner's 48-hour line, the answered salt

**Brief:** `claude_code_briefs/S603_AMIR_CALENDAR_SAFE.md` (v2, Sanjeevni session 333, 20-Oct-2026), step 5's first half of the restructuring
plan, at the owner's word of 18:09 IST 19-Oct ("Darpan, amir and f 943 now") and his deadline (live before 1 November). The independent read R1
(`03_WORKING_PAPERS/S333/S603_R1_REVIEW.md`: six blockers, fifteen corrections) is folded in. Repairs **F-952** (the tap clears the band),
**F-953** (the start-capture judge reachable from `/api/readiness`), **F-769** (the stock-ahead sentence), **F-786** (the waiting words),
**F-726 a** (the answered salt). No D-number: every rule is the owner's existing one (rule (c) of 05-Oct, D737/D740, D708, D712, D648).
**Charter:** `SANJEEVNI_BUILD_CHARTER.md` v1.1. Four Sanjeevni files and the duty map; no new file placed, no new table, no new setting,
no data step. Kit shape: S602's. One restart.

## What it does

- **`amir_day.py` (3.1–3.3).** One export fact, in one place: `_export_fact(cx, day)` → `(lo, fact, t2)` — `lo` the day's oldest step-2 tap
  ("Sab bill daal diye"), `t2` the newest, `fact` the newest moment the SERVER received a purchase export after `lo` (a VERIFIED `mi_file` of the
  pair's families, or a `purchase_export` row of them, superseded or not; any day). `_reexport_due` reads it: due when `t2 > fact`; `(False, None)`
  while no fact exists (no band before the visit's first file; R1-B1). **His step-3 tap is no longer a mark (F-952):** on 18-Oct it cleared the
  band and no file ever came. `_export_state` reads the export that COVERS the 1st..today first, then the newest (bound `(kind, day, first, day)`,
  R1-B3): a month-end export taken second no longer hides the covering one; a pair that did not arrive says since when ("hh:mm baje se nahi
  aayi", `since` = his tap's hh:mm). New `_s603_export_lines`: the owner's one line per OPEN visit day of the last 7 days whose step-3 tap is
  `amir.proof_wait_hours` (48) old or more — "never reached the server" when no fact exists, "re-export owed" when a bill was entered after the
  fact — appended in `needs_you_lines` after D712's lines; it reads the same fact, never `_export_state` (a past day's live pair is superseded by
  the next export, R1-B2). `S488_WHYS` gains `absent`; `_s488_ending` says "N item(s) not printed under their name in it: … (still wrong in Marg
  — the hub's correction list; Amir)". `KIT = "S603_AMIR_CALENDAR_SAFE"`.
- **`stock_app.py` (3.4).** `readiness()`: the purchase "days behind" sentence is gone (F-769: a quiet day is not "behind"); the stock-ahead
  sentence is one rule, `_s603_purchase_wait` — `stock_figure.purchase_cover_how` over the newest usable capture (the one `_r_stock` names) with
  a **read-only Ctx** (F-953): "No purchase export has been taken since the closing stock of D was captured (dd-mm hh:mm); the newest purchase
  exports reach dd-mm hh:mm (bill-wise) and dd-mm hh:mm (item-wise). Amir's next export settles it — count after it, not before." — no sentence
  when a clause covers it. `_r_stock` builds a read-only Ctx too (one word, F-953). `_s488_why(…, unseen=None)`: when a clean closing came, its
  purchase half is not short and EVERY unseen row is `absent_at_try`, the reason is `absent` and `out["absent"]` names the items (only
  `absent_at_try`: `absent_before` is R's lack, R1-C9); `_s524_verdict` passes `unseen=unseen`. `_s488_purchase_reach` deleted (no other caller).
- **`stock_watch.py` (3.5).** `start_capture_lines`: the SELECT carries `md5, end_day`; a PENDING capture past its sale gate is judged by the one
  rule, `purchase_cover_how` over the capture as the judge builds it (`capture_of(md5)` with `end_day` from the row — a pending start capture's
  own dict carries none, R1-B4), a read-only Ctx; the line is "Closing stock printed dd-mm hh:mm waits for a purchase export taken after it
  (newest: bill-wise dd-mm hh:mm, item-wise dd-mm hh:mm)"; no line once an export covers it. The day count ("waits for Amir's purchase export")
  is gone.
- **`amir_salts.py` (3.6).** `SECTIONS` gains `"waiting": ("Item ka salt badliye — Dr sahab ka jawab", "answer")`; `_open_tasks` lists an
  answered waiting row last (its exact text = the owner's answer); `_waiting` (tab 2) keeps only the unanswered; tab 1's "ABHI KYA HAI" shows
  the Marg salt for `change` and `waiting`; `_apply`'s SELECT carries `answer`. Step 6's `saltsdoor` card shows by itself (it counts
  `_open_tasks`).
- **`DUTY_MAP.json` v15 → v16, one dated line in `DUTY_MAP.md`:** duty `amir.salt_tasks` (person amir, tile "Amir ka kaam", door
  `/finance/amir/step/6`, marker "Salt aur naye item: list kholiye, Marg mein sudhaar kijiye, tick lagaiye", `due_sql` the sheet's open rows
  including the answered salts, `allowed_days` 10 mirroring `amir.marg_jobs`, `coded` null — no owner line is raised today: door, no raise; the
  owner's salts page counts them). Run on the live database at the open: `(0, None)`. Placed by the PUBLISH (the clone's pull), never by the
  installer; the kit ships the v16 copy its walk ran with (the `.gitignore` line added with the kit, F-300's rule).

## Pins (FROM → TO; TO is `PINS.sh`)

| file | FROM | TO |
|---|---|---|
| `/root/finance/amir_day.py` | 3af992d9e6b6c6050b1427e34757ca78 | 1169a3d6ae451ebb4c9806052de0856c |
| `/root/finance/stock_app.py` | 4f73d0b02a167289d9439af7a35b5fa0 | 40f2c92260ae6b6715d49729fef464ff |
| `/root/finance/stock_watch.py` | 299c3ef76b73a10e4af1cd15974c7a3f | f0d9092a051c4cd043645e4510ef4cee |
| `/root/finance/amir_salts.py` | d8d9ba772650a4d804add6953790d14d | fc5c1d169cf971deb6b59010141a4550 |
| `claude_code_briefs/DUTY_MAP.json` (the clone, by the publish) | c2ef9c6c5adb8c930b21bff5441cc017 (v15) | b75ea78ea5c65005d2a6420960bad19c (v16) |
| `claude_code_briefs/DUTY_MAP.md` (the clone, by the publish) | — | 59c6bf9896aeb818fd9d4a54fe6e8b8b |

Read only, never edited — the installer prints their live md5 and STOPS if one moved: `stock_figure.py` 51e1fc63, `purchase_app.py` 60f2d846,
`export_watch.py` f6845ec5, `shelf_figure.py` 23b2394a, `order_rules.py` 8d078dbe, `porders.py` e5a5c4d4, `darpan_kal.py` b28d7342,
`spine/spine_read.py` 10697b38; proved unmoved: `finance_app.py`, `portal.py`, `tile_grants.json`, the crontab (84 lines, `# S577_WITNESS` once),
`spine.db`'s schema. Service `clinic-finance`, restarted once. Window 08:00–23:49 IST, the spine green and under 30 minutes old;
`DOCTOR_AUTO_OFF` around the restart.

## The install (`install_S603_AMIR_CALENDAR_SAFE.sh`)

Gates (window, lock, SUMS, KIT_ID, PINS, S602's and S598's kits present and whole) → the FROM pins, the clone's `DUTY_MAP.json`, the read-only
md5s, the crontab → the spine green → **the live facts printed (F-510):** the 18-Oct `amir_step_log` rows, the receipts after 09:35:24 (expected
0 0), the newest receipt, the `stock_start_capture` rows, the salt counts by section, the settings, the new duty's `due_sql` on the live database
→ build from the live bytes (26 anchored edits, each anchor exactly once; the built `DUTY_MAP.json` = the kit's copy) → compile on both pythons →
scratch (the finance folder twice, a portal copy per side — never the live secret or user store, finance.db / assets.db / spine.db by the backup
API) → the walk on the OLD files (every control red) then on the NEW files → S602's walk whole on the NEW files (green) → S598's walk on both
sides, its check lines identical → DRY stops → the install-day state BEFORE and as the NEW files read the same copy → backups
(`finance.db.bak_S603_<stamp>`, `<file>.bak_S603_<from8>` ×4) → `DOCTOR_AUTO_OFF` → the four files staged and renamed in ONE command → one
restart → healthz 200, the pages 302 → journal clean → the state AFTER (the live files on a fresh copy: `readiness` without the purchase "days
behind"; the 18-Oct line present or not, with the box's clock) → nothing else moved → md5 read-back → the off-switch removed. Red after placing:
the four files back in one command, one restart, healthz. The lock is released after the report (`rm -f …/owner; rmdir …`).

## The walk (`walk_s603.py`)

On scratch copies only (the real finance app and the real portal in one process; the walk's own header session for the finance pages and its own
portal sign-in; its own rows by key `W603 / w603 …`; the live rows by key: 18-Oct's visit, the 18-10 09:37 start capture, the answered salts of
04-Oct; the spine copy never written by the code under test — the synthetic spines are second copies). Controls as the brief's §4, in this
order: (10, first) Amir's seven steps and salts page on the quiet copy, the owner's amir/day, Shavez's, Darpan's, reception's pages, stock-now,
api/day, api/readiness (the purchase sentences masked) and needs-you (the S603 lines and the count masked) dumped and byte-equal OLD vs NEW;
(1) the 18-Oct replay `(True, '2026-10-18 09:35:24')` on NEW, `(False, …)` on OLD; a synthetic `mi_file` receipt of 20-Oct clears it, a
`purchase_export` receipt too; the morning case (R1-B1); (2) a synthetic day with two live rows per family — the covering one is taken; the
non-covering one alone is bad on both; 1-Oct printed; (3) a step-3 tap 10 min ago → "hh:mm baje se nahi aayi" in the state and in the step-4
head rendered as amir (the walk patches `_today` to the synthetic day); the wait state byte-equal; (4) the owner's line: six synthetic open days
laid and read one at a time (one fact for all days — a receipt laid for one case answers every visit before it, so the cases are staggered and
cleaned between) — (i) never reached, (ii) re-export owed, (iii) a receipt after the last tap, (iv) 10 h, (v) closed, (vi) the real 15-Oct; both
lines through `needs_you_lines`; (5) F-786: a batch of the real count whose items are all proven, one item's rows removed from every capture
after the vouchers on a second spine copy → `absent`, the ending and `_s524_english_ending`; a mixed set and `absent_before` stay `no_figure`;
the live lot stays `pur_behind`; (6) readiness: no purchase "days behind", the stock-ahead sentence per `purchase_cover_how`, the forced case
(a spine copy without purchase exports and the visit's step-2 taps removed), the judge did not run (rows byte-equal; OLD moves `checked_at`),
the other keys equal; (7) the 18-10 pending capture's line in its new words on a spine copy with any export after it removed; none with both
families stamped today; the judge did not run; (8) one answered salt set `done = 0` on the copy: `_open_tasks` last with section `waiting`,
`_exact` = the answer, `_waiting` empty, tab 1 carries it and tab 2 is absent, an upload with Y ticks it by id, an unanswered row stays on tab 2;
(9) the duty's `due_sql` `(0, None)` → `(1, '2026-10-04')`, the map v16, S533's byte-equal check of `DUTY_SQL`, the staff-eye walk (the portal
home's tile, the door's marker with the row open, gone when restored); (11) the greps of §3.7, every `_sf.Ctx(` in stock_app listed, no
ten-digit run, no spine write, `stock_figure.py` untouched, the copy's rows as they were. `--expect-red` is the negative control; `--state`
prints the install-day state (the brief's §5).

## Charter

- **One fact, one place:** the export fact = the server's receipts after the visit's first bill-entry tap, read in `_export_fact` only, by the
  band and by the owner's line; purchase cover = `stock_figure.purchase_cover_how` (S587), now read by `readiness` and `start_capture_lines`
  instead of their own date arithmetic; a read path says `read_only=True` (F-943's rule, now F-953's); the waiting reason = `_s488_why` →
  `_s488_ending` (one wording, the owner's); the salt task's exact string = `_exact` through `SECTIONS`.
- **Rule (c) of 05-Oct on the owner's side:** since-when and for-what on his lines; the 48-hour escalation for the export wait and the owed
  re-export. On Amir's side only the "do this" line gains the moment (D708 kept).
- **Seen, not touched (named):** `stock_gate` / `purchase_due` / the frozen feed (4b-2; the "COUNT GATE" sentence keeps its calendar words);
  `visit_cover`'s no-tap rule (R1-B3); the sale "days behind" sentence; `export_watch`'s 1st-of-month rule; the words sweep of Kit 3; Amir's
  stage line (D708); the day's pages' writable Ctx (R2-B2: `_s577_record` 2316, `_voucher_guard_base` 5260, `amir_stage` 7994, `_s488_why`
  8302/8322, `_s524_table` 8747 — named, not touched); the two helpers that read the per-family newest stamps (`stock_app._s603_newest_stamps`,
  `stock_watch._s603_newest`) repeat clause (b)'s two queries of `stock_figure.purchase_cover_how` — stock_watch cannot import stock_app, and
  stock_figure is not in this kit; a later kit may give stock_figure one `newest_stamps()` door.
- **Retired:** `_s488_purchase_reach` (dead), the purchase "days behind" sentence, the pending capture's day count, the step-3 tap as a mark.
  **Left for later:** nothing new.
- **Behaviour changes (rule 4, 7):** the band stays until a file lands and never shows before the visit's first file; step 4 prefers a covering
  export; one owner line after 48 h; three owner sentences reworded by a fact; the drift page's two reads never judge; an answered salt becomes a
  tickable line on Amir's sheet; one duty row. No figure, no order, no verdict changes.
- **Dependency state at install:** S587, S598, S602 live (the FROM pins); the 18-10 09:37 capture `pending / pur_short`; 0 open salt tasks; the
  spine green.

## Undo

`\cp -p /root/finance/amir_day.py.bak_S603_3af992d9 /root/finance/amir_day.py && \cp -p /root/finance/stock_app.py.bak_S603_4f73d0b0 /root/finance/stock_app.py && \cp -p /root/finance/stock_watch.py.bak_S603_299c3ef7 /root/finance/stock_watch.py && \cp -p /root/finance/amir_salts.py.bak_S603_d8d9ba77 /root/finance/amir_salts.py && systemctl restart clinic-finance` — then healthz 200 and the four md5s read back as the FROM pins. The duty map's v16 stays (a duty row with a door raises nothing).
