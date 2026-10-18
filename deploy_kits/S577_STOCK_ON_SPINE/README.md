# S577_STOCK_ON_SPINE — one place works out stock; the voucher check gains its second half; the Loss desk only reads

**Brief:** `claude_code_briefs/S577_STOCK_ON_SPINE.md` (v4, Sanjeevni session 324, 18-Oct-2026) — rung 4b of the spine plan (Book §4A,
§15F.1). **Charter:** `claude_code_briefs/SANJEEVNI_BUILD_CHARTER.md` v1.1. **Faults closed:** F-874 (a renamed item "not readable" by the
voucher check), F-873 (a Yuvika bill lost by "bill entry baaki"), F-841 (opening the Loss desk changed the count), F-862 for the readers moved
(`stock_snapshot` never pruned), D715 a's second half (a voucher line never takes Marg past the shelf). Kit shape: S574's.

## What it does

- **`stock_figure.py` (NEW) — THE one stock function.** For an item it gives two answers, each carrying the closing it stands on:
  - `marg()` — Marg's figure: the newest USABLE closing capture (charter 11's capture rule, moved here verbatim from `stock_app._s524_end_day` /
    `_s524_stamp_iso`; the one choice rule: for a given end day the newest usable capture by stamp), read BY PRINTED NAME over the spine's new
    `sp_close_name` (every accepted full capture, by name and packing) and carried forward by the spine's own movements (`sp_move`, the proof's
    five kinds, never OPENING). `approx=True` whenever the item's key has more than one printed name in the capture (a family).
  - `shelf()` — the shelf figure: the newest physical count (the count family with the desk's corrections laid over, or a stock point that is
    not the full count's own copy and not superseded), carried forward the same way, split by counted share among the family's members, plus
    boundary purchases, tapped arrivals not in Marg and scan arrivals. **No count → `shelf=None`, `named='no_count'`, never Marg's figure.**
  - `key_of()` — the one identity (charter 12): `sp_item.k20` for the printed name (spacing and case ignored), else through the ticked renames
    (`item_alias.done_rows`: the partner name and the owner's ACCEPTED seen_names), else the spine's alias key. Never a bare clip.
  - `closing()`, `captures()`, `capture_for()`, `capture_at()`, `family()`, `printed_forms()`, `base()`, `expect_for_point()`, `late_match()`,
    `late_purchase()`, `early_bill()`, `reach()`, `covers()`, `tryable()`, `witness()`. Read only; no table of its own; no Flask (it runs in
    the `order_rules tick` process too). One per-request `Ctx`, built by the caller, never module-global.
- **The spine (`spine_build.py`, `selftest_spine.py`):** one new table `sp_close_name (md5, name, packing, k20, units)` — every accepted full
  closing capture by printed name and packing, a name printed twice with one packing summed, `k20 = Z(name)`. The capture's printed day and
  stamp are `sp_export.as_on` / `stamp` (one copy). `sp_close` and every gate check are exactly as they were (the walk and the installer prove
  the same `sp_close` from the new and the old builder on the same readings). `BUILD_VERSION` S524.1 → S577.1. The selftest gains five checks.
- **The voucher guard (`stock_app.py`, F-874, D715 a):** `_voucher_guard_base` / `_voucher_guard` read `stock_figure.closing / marg / shelf` by
  every printed form of the name — a renamed item is judged. The below-zero test is unchanged in meaning (`m + unk + ch < 0`, `m` =
  `closing().units`; a closing read by key counts as unread). NEW, the past-the-shelf test on ANY line: `after = marg.figure + unk + ch`; held
  (`why='past_shelf'`) when `ch < 0 and after < shelf − tol` or `ch > 0 and after > shelf + tol`, `tol` = `stock.voucher_shelf_tol_packs` × pack
  (default 1, read, no row written); applied only when the shelf is known, neither figure is approximate, no arrival is open, no late-keyed bill
  explains the residual and the capture is not an early-morning one holding a bill of its own day — the rest are "not judged against the shelf".
  While `stock_figure.ready()` is False (no `sp_close_name` yet) every lowering line is HELD (`why='not_ready'`), never offered.
  `_voucher_lines` tests every line; `_voucher_held_batches` drops its `ch >= 0` skip and passes `frozen=True`; `amir_stage` builds one
  `Ctx` and passes it down; `A["not_shelf"]` / `C["not_shelf"]` count the unjudged. `_voucher_held` (dead) is removed; `_voucher_void` is KEPT
  (the kit-only void door: S537 `data_s537.py` and S539 `data_s539.py` wrote the two `stock_voucher_void` rows through it).
- **The owner's words, built once in `_s521_stage_words`:** `below_zero` keeps today's sentence; `not_ready`: *"Count #N: ITEM (voucher …) — held:
  the spine's closing table is not ready yet"*; `past_shelf`: *"Count #N: ITEM (voucher …) — the count-day sum asks X; it would take Marg to Y
  against the shelf figure Z (closing of dd-mm, taken HH:MM): not given to Amir"*; the summary gains *"not judged against the shelf for N item(s)
  (a family figure, no count, goods not yet billed, or a bill keyed after the closing)"* beside *"closing not readable"*.
- **The stage proof's helpers** `_s524_stamp_iso`, `_s524_end_day`, `_s524_reach`, `_s570_covers`, `_s524_tryable`, `_s524_key_of` are one-line
  wrappers onto `stock_figure` (identical verdicts: the walk proves stages A and C the same on both files); `_s524_table`'s residual match is
  `stock_figure.late_match`. The proof's own table (`_s524_closings` / `_s524_table` / `close_of` reading `sp_close` by printed day) moves onto
  `captures()` in the morning-flow kit, which changes the proof anyway.
- **Points, settling, traces (`stock_watch.py`):** `_s454_expected` → `stock_figure.expect_for_point` (basis `shelf` | `marg` | `approx`).
  New column `stock_point.basis` (additive, healed in `ensure()`; NULL on old rows = `marg`). An **approx point** (a size that shares a family
  figure) stores NULL expected and NULL gap: no verdict (`verdict_hi=""` before the empty-gap branch, so *"Marg mein yeh item nahi mila"* never
  prints), no loss line, no trace; Darpan sees the plain receipt *"Likh liya: X — q."*; `gadbad` on it records the text and opens no trace;
  the NULL gap keeps it out of the month's leakage and the watch trend; the owner's watch card gets `approx_lines` (*"ITEM: counted N against a
  family figure (approximate) — not judged"*). `correct_roster` carries the old point's basis; `settle_provisional` re-judges a provisional
  point on its STORED basis against the base before it (NULL → `marg`; never an approx point); `open_trace` receives the point's E and starts
  its window at that base. `_arrivals` and `bill_pending_lines` key the spine by `key_of` (F-873). `expected_units` stays for the witness only;
  `Spine.latest_close_day` (dead) is removed.
- **The shelf figure and the gap sets (`shelf_figure.py`):** `figures()` reads both figures from `stock_figure` (its output keeps its keys; `marg`
  = `marg().figure`, `marg_as_on` = the capture's printed as_on; `pack_size` / `packing` from `sp_close_name` through `qty_words.pack_of`, else
  `sp_item` — `pack_src` names the one used). `count_family` / `points` call into `stock_figure` (the one change: a superseded point is
  excluded; a retired fix, `count_id < 0`, is never read). `latest_snapshot`, `_s524_capture`, `_s524_captures`, `_S524_CAPTURES` are REMOVED;
  `filed_vouchers` takes its two moments from `captures()`. NEW table `s577_shelf_gap (end_day, item, capture_md5, …)`: `record_gaps` writes one
  set per END DAY, from the newest usable capture the sale and purchase reach covers (`tryable`), judged against the usable capture before it
  (`closing()`, never a stored row); only the newest covered end day per pass; nothing while `ready()` is False; `rejudge`, `gap_flags`,
  `gap_flag` (matched under every printed form), `gap_line` read `s577_shelf_gap`. **`s454_shelf_gap` is untouched** — a record, read by nothing
  (its DDL is gone with its last reader; the table stays). No seed: judging starts fresh (R3-C1..C3).
- **The Loss desk only reads (`loss_piles.py`, F-841):** `rebuild` no longer calls `sales_test`; the full build writes `stock_pile_cache` and
  `_meta` and nothing else; `sales_test` is removed. `_classify_one` marks an open shortage whose sales since the count day exceed counted +
  bought with `why` *"sold after count: N sold since dd-mm against M counted + B bought -- …"* (English; it stays for his existing doors).
  The stamp's `spine` part = md5 of the spine's INPUTS (its ok exports, `rules_version`, its aliases) — a rebuild of the same inputs no longer
  rebuilds the desk. The desk's JSON gains `system_closed` (*"2 lines were closed by the system on 27-09 as 'sold after count' (DOLOGESIC SP,
  TYCOB 1500); from now on such lines are yours to decide."*). The two 27-09 rows are NOT marked (R3 blocker 1). One new setting
  `stock.voucher_shelf_tol_packs` (int, default 1, lo 0, hi 5, `seed=None`: no row written at install).
- **The owner's *stock now* and *drift* pages (`api_now`, `api_drift` only):** the figures of record are `stock_figure`'s (`ours` = the shelf
  figure, None for an item no count has reached; `marg` = Marg's figure on the newest usable capture; `gap`; `capture`); the PC's push_expected
  figure rides beside them to the DOCTOR role only (`pc_old`, headed *"PC's old estimate (retiring)"*). `_three_way` and `_r_stock` untouched.
- **The side-by-side week:** `python3 stock_figure.py witness` writes `/root/finance/spine/stock_figure_witness_<Mon…Sun>.txt`: every item of the
  newest usable capture — `stock_figure.marg` against `stock_watch.expected_units` against the PC's newest push_expected row, marg_shadow's
  line where `sh_diff` has one, per pair the items a pack or more apart, the named reason. It honours `/root/finance/_off/ALL_OFF` and reads
  finance.db read-only. The installer writes the first file. **The crontab is the parent's — the line to add (not added by this kit):**
  `58 23 * * * cd /root/finance && /root/wa/venv/bin/python3 -B stock_figure.py witness >> /root/finance/spine/stock_figure_witness.log 2>&1 # S577_WITNESS`
  (without the spine lock: read only; spine.db is replaced by rename). Seven explained nights = 4b-2's start condition.

## Pins (FROM → TO; TO is `PINS.sh`)

| file | FROM | TO |
|---|---|---|
| `/root/finance/stock_figure.py` | absent | cb5f24aacf7748752206619ce8bbb1e3 |
| `/root/finance/stock_app.py` | 050587dfb5951da65f95937615ddf144 | f279a3be440878bb30e418c20a5cf608 |
| `/root/finance/shelf_figure.py` | 183c70fabb64ed1e5a43c645a225c560 | a544afda07b4632e9bc05e97c256dde6 |
| `/root/finance/stock_watch.py` | 0e6a42c4c7ae51eb8f8a0869fce2d101 | bc6885217a9f7ca7d8273021fcf6315a |
| `/root/finance/loss_piles.py` | 81ae481e4480a12fead3016515037214 | 2b9023fd06aadc0ddaef30e2f26eccb3 |
| `/root/finance/spine/spine_build.py` | 5d8b1f94d80189c16b2ee5b1e093429c | e3d3ed85973eab2df0326dc9621e230e |
| `/root/finance/spine/selftest_spine.py` | fc63d2c683a1970c58f60502302187a9 | 7d0edb4aafb17c83cf07be1052623f76 |

Read only, never edited (the installer checks their md5 and proves none moved): `item_alias.py` 111a8e48, `stockmatch.py` 10e30d28,
`amir_day.py` 73882a83, `order_rules.py` 79f21c1e, `qty_words.py` 706db7cc, `spine/spine_read.py` 712a1e4e, `purchase_app.py` 98f7d9f0,
`order_sheet.py` f00f0163, `porders_s454.py` 83079763, `porders.py`, `darpan_kal.py`, `finance_app.py`, `portal.py`, `tile_grants.json`,
`DUTY_MAP.json` (no duty added, moved or removed), the crontab. `finance.db`: no data step; `stock_point.basis` is added by `ensure()` on the
first read; `s577_shelf_gap` is created by `record_gaps` (the order_rules tick) — both additive. The spine: `sp_close_name`, additive.
Service: `clinic-finance`, restarted once. The install window is 08:00–23:59 IST (the spine builds `*/10 8-23`).

## The install (`install_S577_STOCK_ON_SPINE.sh`)

Gates (the window, the lock, SUMS, KIT_ID, PINS; the spine green and under 30 minutes old; no system-written desk row on or after 18-10) →
pins → build from the live bytes → compile on both pythons → scratch (the finance folder twice, the databases by the backup API, the readings;
the spine by the NEW and the OLD builder on the same readings: equal `sp_close`, gate 13/13; the selftest; the walk on the OLD files — every
control red — then on the NEW files) → DRY stops → the install-day state on the OLD and the NEW files (a flipped voucher line or a moved
`A.pending` = STOP) → backups → THE SPINE FIRST (two files, the live build by the cron command with `flock -w 300`, `sp_close_name` filled,
gate 13/13, `sp_close` = the old builder's on the same readings) → `/root/deploy/_off/DOCTOR_AUTO_OFF` → the five files staged and renamed in
ONE command → one restart → healthz 200, the pages 302 → journal clean → the state AFTER (no flip) → nothing else moved → the first witness
file → the off-switch removed → md5 read-back. Red after placing: the seven files put back in one command, one restart, healthz; the additive
tables and column stay.

## The walk (`walk_s577.py`)

On scratch copies only, the real app in one process (the walk's own header session), its own rows by key (`W577 FIX TAB` on the scratch spine and
the finance copy; a made-up export md5). Sections 0–15 as the brief's section 4: the live state; a renamed item judged (approx; VINTAZ P 4500
not); the Yuvika immobilizer line not "bill missing" with its tie blanked; the past-the-shelf test (held by two packs, offered within tol, a
frozen line on the shelf not held, a RECEIVE held, a late bill not judged); the capture rule (printed, the same on both files); the desk only
reads (one build across a same-inputs rebuild, no write outside the two cache tables, a new export forces one build, the owner's line, a line
sold after count stays open); settling and correcting on the basis (a provisional shelf point against the base before it; an approx point:
NULL gap, the receipt alone, no loss line, no trace, out of `month_leak`, stays approx when corrected, `gadbad` opens no trace, the owner's
line); shelf figures (no count → None; the plan's no-count lines equal; every moved figure printed; the 21 renamed items that now reach their
count); identity (key_of = the old key for all 198 voucher items; stages A and C identical); the gap sets (one set, judged against the usable
capture before it, a second pass writes nothing, `s454_shelf_gap` unchanged, the roster's reasons before and after); the owner's sentences;
install order (`ready()` False → held `not_ready`, `record_gaps` writes nothing); absence (PREDNOSIS 8 reads 0); the grep tests; staff-eye
(every login's tiles and pages, the lines whose words changed); Amir's card and pad under 2 s and 100 KB; no ten-digit run. `--state` prints
the install-day state (the installer runs it before and after). `--expect-red` is the negative control.

## Charter

- **Retired:** `sales_test`; `shelf_figure.latest_snapshot`; `_s524_capture` / `_s524_captures` / `_S524_CAPTURES` (the stock_feed moment lookups
  — the 22:30 re-send moved them); `_voucher_held`; `Spine.latest_close_day`; the bare-clip keys of `bill_pending_lines`, `_arrivals`,
  `scan_arrivals` (and `movements` / `boundary_purchases` inside shelf_figure, the same file); `s454_shelf_gap` as a read (and its DDL);
  the second copies of the capture rule, the stamp parser, the reach and the residual match in `stock_app` (wrappers now).
- **Left for later, with its rung:** `stock_snapshot`'s writer `/api/snapshot` and `reconcile` (rung 5 / 4f); the count's own figures
  (`_three_way`, `_r_stock`, `_newest_snapshot`, `_snapshot_qty_map`, `_item_life`, `_pad_report_data`, `stock_statement.build`,
  `full_count_points`, `loss_piles.fixes`, `porders.shelf` / `ortho_items`) — rung 4f; the order engine (`order_rules._s470_snap`,
  `_s454_shelf_snap`, `purchase_app._latest_snapshot`, `kedar_review`) — S486 B / rungs 4a, 4c; the list readers of `stock_snapshot` (§2.1 b)
  and `marg_spine.py`'s identity — rung 5; `stock_spot_check` — rung 4d; `expected_units`, push_expected, marg_shadow — 4b-2; the stage proof's
  own table onto `captures()` — the morning-flow kit; at count #2 `_s454_store_shelf` stores NULL for an uncounted item (announced).
- **Named limits (the brief's):** R2-C18 — a voucher typed in Marg before the capture but recorded on the page after it is counted twice in
  `unkeyed`; no grace is applied. R3-C5 — two absence rules stand: `closing()` reads a key absent from a full capture as 0 when
  `first_seen <= as_on`, `_s524_table` as 0 only when `first_seen > R.as_on` (else `absent_before`); the morning-flow kit makes them one.
  The accepted `seen_name` read (`marg_item_rename_event`, event `accepted`, for `done_rows`' ids only) is a read `item_alias` should own at
  its next kit. The order lines in `_arrivals` / `scan_arrivals` are still matched by `pad_norm(name[:27])` — seen, not touched (charter 12).
- **Charter: left out.** Nothing of the brief. The stock-now, drift, Loss-desk and watch-card HTML pages are not named by the brief, so the new
  fields ride in the JSON only: `api_now`'s `columns` / `pc_old_head`, `api_drift`'s per-item `marg` / `shelf` / `pc_old_head`, the desk's
  `system_closed.text`, the watch card's `approx_lines`. The page templates draw their old columns (Ours / Marg / Gap, now the shelf figure /
  Marg's figure / the gap) — the chat may give the templates the new heading in a later kit.
- **Charter: seen, not touched.** `stock_snapshot` is still written by `/api/snapshot` and read by the list readers (rung 5); the count's own
  figures still read it (rung 4f).

## Files

`KIT_ID.txt`, `PINS.sh`, `SUMS.md5`, `README.md`, `stock_figure.py` (the new module, placed byte for byte), `make_s577.py` (the builder: 59
anchored edits on five live files), `walk_s577.py` (the walk and the install-day state), `install_S577_STOCK_ON_SPINE.sh` (the installer).
No `.json` in the kit folder.

## The undo

`\cp -p /root/finance/stock_app.py.bak_S577_050587df /root/finance/stock_app.py` and the same for `shelf_figure.py.bak_S577_183c70fa`,
`stock_watch.py.bak_S577_0e6a42c4`, `loss_piles.py.bak_S577_81ae481e`, `spine/spine_build.py.bak_S577_5d8b1f94`,
`spine/selftest_spine.py.bak_S577_fc63d2c6`; `rm -f /root/finance/stock_figure.py`; `systemctl restart clinic-finance`; healthz 200; read the
md5s back. `sp_close_name`, `s577_shelf_gap` and `stock_point.basis` stay (additive; nothing old reads them). `finance.db.bak_S577_<stamp>`
is kept but never needed for the undo (the kit writes no data).
