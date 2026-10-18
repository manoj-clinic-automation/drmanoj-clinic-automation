# S587_MORNING_FLOW — the start-of-day closing (D740), the morning flow (D737), visit cover, "agrees = right at once"

**Brief:** `claude_code_briefs/S587_MORNING_FLOW.md` (v2, Sanjeevni session 327, 18-Oct-2026) under **D740** (a closing printed as on today and
taken before the day's first sale counts as the START of that day — the end of yesterday plus the morning's Marg work; amends charter rule 11)
and D737 (the morning flow); the design is the second independent read of S577 (`S577_R2_REVIEW.md` B2, B3, B4, B5, C6). Repairs F-926, F-927,
F-933, F-936. **Charter:** `claude_code_briefs/SANJEEVNI_BUILD_CHARTER.md` v1.1. Six Sanjeevni files, no new file, **one new table**
(`stock_start_capture` in finance.db, additive, created by `stock_figure` on first use), no data step (the first verdicts are written by the
installer's `verify-start`, quoted in the report), no staff duty added, moved or removed (DUTY_MAP.json unchanged; one wording line in
DUTY_MAP.md). Kit shape: S584's. One restart.

## What it does

- **3.1 `stock_figure.py` — the start capture (D740; R2-B2).** `captures()` marks a same-day print taken between 09:00 and 22:00 as a START
  capture (`start=True`, `start_day=D-1`) and a same-day print before 09:00 as `early=True`. A start capture is usable, with `end_day=D-1`,
  **only when its verdict is `accepted`**; the verdict is a record in `stock_start_capture` (one row per md5; `pending` → a final verdict once;
  never re-judged — `built` records which spine judged). `captures()` judges lazily (`_start_apply`) when the context's finance connection may
  write (present, not inside the caller's transaction — `_may_write`) and the capture is within `LATE_DAYS` with no final verdict; a read-only
  or absent connection only reads the record (fail-soft: the old rule). `start_ready`: the spine's sale reach has D **and** `purchase_cover`
  holds for the closing as it would stand — until then `pending` (`sale_short` / `pur_short`), never set aside. `verify_start`: P = the newest
  usable (clean or accepted) capture with `end_day ≤ D-1` and an earlier stamp (none → `pending` / `no_prev`); per key
  `change = (units_S − bal(D-1)) − (units_P − bal(P.end_day))` (`bal` = Σ sp_move.units to the day, OPENING included); excluded by cause
  (`_start_excluded`): count-voucher batches first entered in `(P, S]`, `amir_job` `fix:` rows done in the window, the consumption list
  (`loss_piles.settings`), keys with a purchase dated D, keys of a purchase bill first seen on or after P's own day (`purchase_bill.first_seen_day`
  → `sp_purchase_line` by supplier key, bill and date); an unexcluded key with `change < 0` and `|change| ≤` its SALE units dated D →
  `set_aside` / `sale_before`; more than `count.start_unexplained_max` other unexcluded keys with `|change| ≥ 0.5` → `set_aside` / `unexplained`;
  else `accepted` (the unexplained keys listed, approx on that capture). `detail` (JSON) carries the previous capture, the deciding keys with
  their printed names and the excluded keys by cause. The switch `count.start_capture` off → every start capture unusable, nothing written
  (`verdict='off'`). `python3 stock_figure.py verify-start` judges the last 21 days and prints every start capture with its verdict, reason,
  deciding and excluded keys (`verify_start_cli`, `start_report`).
- **3.2 `stock_figure.py` — purchase cover (R2-B4) and the one `tryable`.** `purchase_cover(con, sp, c, reach_, ctx)` (and `purchase_cover_how`,
  which names the clause): (a) the spine's purchase reach as before; (b) the newest purchase export of each family (`reach()['pur_newest']`,
  new) stamped after the closing; (c) **visit cover** (`visit_cover`): V = Amir's visit day on or before the closing's day; T2 = his last step-2
  tap on V before the closing (re-taps after the close included); E = the newest purchase export of EACH family (anyone's — `purchase_export`
  rows; an export identical in rows and amount to the visit's own continues it, flagged `identical`) stamped at or after T2 and before the
  closing; cover when no `self` answer and no open `amir_self_wait` fall between E and the closing. A closing on V before he opened his day or
  tapped bill entry is judged by the previous visit's cover (the bound: the next visit's first step-2 tap or its `opened_at`); a visit day
  with no step-2 tap gives no cover. `tryable(c, reach_, con=None, ctx=None)`: the sale half as before, the purchase half `purchase_cover`
  (with `con` None only (a) and (b)). Both callers pass `con` / `ctx`: `stock_app._s524_tryable` (and the two `_s488_why` calls, the bare dict
  too) and **`shelf_figure.record_gaps` — the kit's one edit to shelf_figure**.
- **3.1 R2-B3 — `marg()` on a start / early capture.** The purchases dated D are inside the capture: `marg()` never adds them again (only D's
  sales, returns and reconciliations, and every kind after D); such a key is approx with `approx_reason='purchase_on_start'` (also at
  `at == end_day`); an accepted start capture's unexplained keys are `start_unexplained`, its excluded keys with a sale dated D
  `start_excluded` (`start_marks`). The base side: when the figure is asked exactly at the capture's end day (record_gaps' pattern) and the
  previous end day's capture is a morning one holding this key's purchase, the key is approx too. `shelf()` takes no boundary purchase on such
  a key. `early_bill()` is retired: its one caller, the voucher guard (stock_app), reads `marg()['approx_reason']`.
- **3.3 `stock_app.py` — the proof on `captures()` (R2-C1/C2, R2-B5, F-933).** `_s524_closings` retired; `_s524_table` reads
  `stock_figure.captures()` (usable only; an accepted start capture included), `close_of(c)` = the capture's own rows by key (`_cn_rows` over
  its md5, the `''` key dropped), never `sp_close` by printed day. R as before; `after` = usable captures after the last entry; **`tries` =
  every usable capture the SALE reach covers, whatever its purchase cover** (R2-B5: an agreeing voucher is proven at once); `N = after[-1]`
  and `wrong` only when N is inside **both** reaches (`N_ok`) and disagrees; `pending_reach` while N is not. Keys with a morning mark on R or on
  a try (`morning_skip_keys`: `purchase_on_start` / `start_excluded`) are skipped for that try (`why`). **F-933:** a `wrong` key whose item has an
  `amir_job` `fix:` row with `done_at` after N's stamp is `pending_fix` (unseen, `why='pending_fix'`; `_s524_verdict` returns `pending_fix[]`;
  `amir_stage`'s C carries the lots' rows); the owner's line (`_s521_stage_words`, cls info): *"ITEM: Amir marked it done dd-mm hh:mm — judged
  on the next closing taken after it"*. A proof whose every unseen row is `pending_fix` says `why='pending_fix'` with the judged closing's
  day, and the stage's English reads *"Stage C: lot N entered on dd-mm-yyyy — N item(s) Amir marked done after Marg's closing of dd-mm-yyyy —
  judged on the next closing taken after it"* (`fix_en`; found at the first install's state step, where the S488 fallback said *"waiting for
  our own figure"* — wrong text, charter 8). The staff words do not change (D708). On the live copy the four corrected items (KT ROS DT,
  VINBACTUM DS, FOLITRAX 15 MG TAB, OSTOVAXL DM; done 18-10 09:23–09:25 by his tap, after the 17-10 09:20 capture) move from `wrong` to
  `pending_fix` — the only verdicts that change (the walk's control 1).
- **3.4 `stock_watch.py`.** Two rows under *Counts & watch*: `count.start_capture` (choice on/off, default 1, no seed) and
  `count.start_unexplained_max` (int, default 3, lo 0, hi 50, no seed); `settings()` returns `start_capture` and `start_unexplained_max`
  (stock_figure reads them through `_sw().settings`, as `arrival.*`); `needs_you_lines` gains `start_capture_lines`: one English line per
  start capture set aside in the last 7 days — *"Closing stock printed dd-mm hh:mm set aside — a sale came before it (ITEM, …)"* /
  *"— N items changed with no Marg reason (ITEM, …)"* — and *"Closing stock of dd-mm hh:mm waits for Amir's purchase export"* while pending
  more than a day after its day's sale report landed (`stock_figure.sale_landed`). Darpan and Shavez see nothing new.
- **3.5 `amir_day.py` — the export step last (fix D; the approved mock-up).** Ids never change. `ORDER = (1, 2, 6, 3, 4, 5, 7)`, `pos(id)`,
  `id_at(pos)`, `LABEL_OF`; the banner prints positions in `ORDER`; `_page`'s *"Step N of 7"* prints the position; `_next_step` walks `ORDER`;
  the POST redirect compares positions and steps to `id_at(pos(n) + 1)`; the visit summary marks *skipped* by position (R1-B1). Routes,
  `S.done`, `GATE_STEPS (2, 4, 5, 6)`, `amir_step_log.step` and the duty map's `due_sql` keep the ids. **F-926 / D737 D:** `_reexport_due` —
  the day's newest step-2 tap later than the newest export fact of the day (his newest step-3 tap, or the newest VERIFIED purchase export
  landed in `mi_file` that day); then the gate gains `(3, "Purchase report dobara nikaalni hai — bill entry export ke baad hui hai", "re-export
  due: a bill was entered after the export")`, `_ready_to_close` refuses, a red band on every position ≥ 4 (*"Purchase report dobara nikaaliye —
  bill entry export ke baad hui hai. Kholiye"* → the export step), the owner's `/finance/amir/day` says *"re-export due since hh:mm"*; a fresh
  step-3 tap or a fresh export landing clears it (the fact, not the tap — S584's E). `KIT = "S587_MORNING_FLOW"`.
- **3.6 `stock_now.html` — F-936.** The items table gets `id="itemtbl"`; the doctor's fifth heading is appended to `#itemtbl thead tr`, never to
  the first `<thead>` on the page (the readiness block's bills table).
- **`DUTY_MAP.md`** (repo only): the purchase-export row's wording names the step ids and their positions since S587 and the re-export line.
  `DUTY_MAP.json` is unchanged (door `/finance/amir/step/3` is the route id; `door_marker` "Do report nikaaliye" is still on that screen).

## Pins (FROM → TO; TO is `PINS.sh`)

| file | FROM | TO |
|---|---|---|
| `/root/finance/stock_figure.py` | 72b9135ab00db0af2fe8e54091147bb5 | see PINS.sh |
| `/root/finance/shelf_figure.py` | 14ef2c24e272ae8ea684615ae82b6cb5 | see PINS.sh |
| `/root/finance/stock_app.py` | 1883807d7c0872b805f6101e92206878 | see PINS.sh |
| `/root/finance/amir_day.py` | 3deca3b95380165d81ae4a8406a53d75 | see PINS.sh |
| `/root/finance/stock_watch.py` | 555202ce50b8df0b5111b5c56952efda | see PINS.sh |
| `/root/finance/stock_now.html` | ff415eb22ee1ad94a95f2c87365341a3 | see PINS.sh |

Read only, never edited — the installer prints their live md5 and STOPS if one moved: `loss_piles.py` 2b9023fd, `stockmatch.py` 623cb6f1,
`spine/spine_build.py` e3d3ed85, `spine/selftest_spine.py` 7d0edb4a, `spine/spine_read.py` 712a1e4e, `item_alias.py` 111a8e48,
`reports_tile.py` 535b5790, `qty_words.py` 706db7cc, `DUTY_MAP.json` 891defd8; and proved unmoved: `finance_app.py`, `purchase_app.py`,
`order_rules.py`, `porders_s454.py`, `portal.py`, `tile_grants.json`, the crontab, `spine.db`'s schema (no table added to the spine).
`finance.db`: one new table `stock_start_capture` (DDL `stock_figure.START_DDL`), created on first use; backed up by the backup API before
placing. Its reverse — never run by the installer, only if the chat orders the data change reversed: `DROP TABLE stock_start_capture;`.
Service `clinic-finance`, restarted once. Install window 08:00–23:59 IST with the spine green and under 30 minutes old; `DOCTOR_AUTO_OFF` set
around the restart, removed after healthz 200.

## The install (`install_S587_MORNING_FLOW.sh`)

Gates (window, lock, SUMS, KIT_ID, PINS) → the FROM pins and the read-only md5s → the spine green → build from the live bytes (50 anchored
edits, each anchor exactly once) → compile on both pythons → scratch (the finance folder twice, finance.db / assets.db / spine.db by the backup
API) → the walk on the OLD files (every control red) then on the NEW files → DRY stops → the install-day state on the OLD and the NEW files →
backups (`finance.db.bak_S587_<stamp>`, `<file>.bak_S587_<from8>`) → `DOCTOR_AUTO_OFF` → the six files staged and renamed in ONE command → one
restart → healthz 200, the pages 302 → journal clean → `stock_figure.py verify-start` once on the live database (the first verdicts; quoted in
the report) → the state AFTER → nothing else moved (the read-only files, the spine's files and schema, the crontab) → md5 read-back → the
off-switch removed. Red after placing: the six files put back in one command, one restart, healthz; the new table stays.

## The walk (`walk_s587.py`)

On scratch copies only (the spine copy written through a plain rw connection with `sp_meta.built` bumped), the real app in one process (the
walk's own header session), its own rows by key (`W587 …`, `w587…` md5s), the brief's fifteen controls: (1) the proof identical where
nothing changed — every differing verdict named by its rule (D740 start capture / R2-B5 / F-933 pending_fix), none unexplained; (2) the real
18-10 09:37 capture: pending with the sale report absent, pending with it present but no export after the 09:35 tap, then the verdict with the
deciding and excluded keys (the four `fix:` items excluded by cause, no sale_before on them); (3) a sale before the capture → set_aside; (4)
unexplained changes against the setting, accepted keys approx; (5) the switch; (6) the chooser (`capture_for(17-10)`, `closing()` of a corrected
item, `/stock/api/now` moving only for keys whose closing moved); (7) R2-B3 counted once, approx, skipped by the proof and the shelf-gap
flags; (8) visit cover replayed for 02 → 18-Oct with the reach as each day ended (15-10's export not cover after the re-taps; the owner's
16-10 export cover for 16-10 and 17-10; 04-10's same-day cover; 18-10's 09:37 waiting); (9) R2-B5 proven at once / waiting / wrong once N is
inside both reaches; (10) F-933 pending_fix, the owner's line, Amir's card unchanged, judged normally once a later capture exists; (11) the
banner, "Step N of 7", the ids under every tap, the visit summary's keys; (12) the re-export line (gate, band, the owner's view, cleared by a tap
or a landed export); (13) the staff screens word for word (the banner and the foot set apart); (14) the greps; (15) the spine untouched,
`selftest_spine.py` green. `--expect-red` is the negative control (every `C:` red on the old files); `--state` prints the install-day state.

## Charter

- **Retired:** `_s524_closings` and `close_of` by printed day (the proof reads captures by md5); `early_bill` (folded into `start_marks` /
  `marg()`); the single purchase-cover clause inside `tryable`; `_s524_table`'s first-or-newest tries.
- **Left (named):** the spine's own build and gate (untouched — a start capture is verified beside the spine, not inside it); an accepted start
  capture is not re-judged when the spine's nightly rebuild moves `bal()` under it (`built` records which spine judged; a re-judge rule is a
  later kit's); `amir_day` Kit 3 (`S528_KIT3_DEFERRED.md`); the D712 gap; `porders.detect_supplies` / `order_rules._s470_arrivals`.
- **Seen, not touched:** `shelf_figure.record_gaps` / `rejudge` (they follow `marg()`; the base side is approx through `marg()` at the end
  day); `_s488_ending` / `_s488_wait_line`; the sealed findings' frozen words; `stockmatch.KIT` (S502); `purchase_bill.first_seen_day` was
  backfilled by S533 on 11-10 to the export day of each bill's current bill-wise export, so on the start captures before 11-10 the `bill_new`
  exclusion covers most purchased keys (a data artifact, printed per capture by `verify-start`); the brief's "16 keys" of the visit summary
  are 17 on the live JSON (the walk asserts the set is unchanged).
- **Dependency state at install:** the spine green and fresh; `count.start_capture` on (default), `count.start_unexplained_max` 3; count #1
  at stage C (lot 3, four items corrected 18-10 and waiting — `pending_fix` from this kit on); Amir's next visit day unknown.
