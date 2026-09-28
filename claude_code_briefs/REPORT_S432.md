# REPORT S432_DESK_GROUP_FLOW — the Loss desk made fast, and closed group by group your way (28-Sep-2026, installed 07:52 IST)

## For the owner
- **The desk opens fast now.** Measured on the server through the real program: the desk's figures used to take about **6.5 seconds**
  to arrive; now the totals arrive in about **0.4 s** and the whole desk in about **0.4 s** (the first open of a count computes the piles
  once and keeps them — 3.4 s, done for count #1 by the install). A tick or a move now takes about **0.4 s** and changes only that row and
  the totals — the page no longer redraws or re-reads everything.
- **Count #2 will close group by group, as you asked.** Above the piles there is a **Group** box: pick *Within the allowance*, *Small real
  gap*, *Old stock*, *Big losses*, *Clinic consumption*, *Owner's use* or *All*; tap **Tick all**; untick the lines that should not go — a
  small menu opens on each unticked line (With me / Write off / Big losses / Consumption / Owner's use / back to the system's choice / leave
  it here) and your choice moves that line to its pile at once; then tap **Clear this group (N ticked)** and confirm within 10 seconds. The
  ticked lines are written off as that group, Amir's vouchers are made, and they leave the list; the unticked stay open. When the last
  group is cleared the count closes by itself — one staff block for Darpan, the leakage line, the stock points — exactly as the single
  **Close the count** button does (that button is still there for a one-tap close).
- **The count statement's "impossible" excess is gone.** Marg holds a stock below zero on 12 items (PRIME CAST 4"/5", BELL CAST 5,
  ALCOXIB 120, NEWTEL 40 and the rest). The statement now prints them as Marg **-24 pcs**, tags each **"Marg negative — book correction,
  no goods: 24 pcs to correct"**, and counts none of it as excess money. The Consumables section's excess of Rs 88,650 was exactly
  PRIME CAST 4" and 5" — it now reads Rs 0 on 0 lines; Medicines' excess falls from Rs 49,426.82 to **Rs 15,001.91** (20 lines);
  Orthotics' from Rs 1,349.69 to Rs 1,120; the whole count's excess from Rs 1,39,426.51 to **Rs 16,121.91**. Every shortage figure is
  unchanged (Rs 1,19,749.26 in all). **BELL CAST 5** now sits in Consumables.
- The watch card on the desk (counts, traces, leakage) is scored by the 06:30 job and shown with its time; a **Refresh watch** button
  scores it again when you want it. Count #1's frozen close of 27-Sep is untouched. Installed and tested.

https://followup.dr-manoj.in/finance/stock/page/loss?count=1

## For the chat

**Kit** `deploy_kits/S432_DESK_GROUP_FLOW/` (KIT_ID `kit id S432_DESK_GROUP_FLOW`). Installed on srv1746119 from `/tmp/s432kit` (byte-identical to
the repository kit — SUMS.md5 checked both sides after the publish, `diff -r` clean) with `KITS=/root/deploy/repo/deploy_kits`; install log
`/tmp/s432_install4.log`; started 07:36:19, DONE 07:52:32 IST (read from `date` around the run). Build lock taken 06:10:28 IST
(`/root/deploy/.claude_code_build.lock/owner` = S432_DESK_GROUP_FLOW), released after this report.

### Where the time went (measured on the box before the build, a scratch copy, the test client — probe 28-Sep 05:2x IST)
A desk read took **6.5 s**: `_pad_report_data` (the S227 report composer, **2.8 s** — `_item_life` once per differing line, 1.9 s of it) ran
**twice** per read (once inside `loss_piles.sales_test`, once for the desk) and `stock_watch.owner_view` (the watch scoring, **0.9 s**) ran on
every read. `loss_piles.classify` itself takes **10 ms**. A move cost 2.2 s and the page then re-fetched the whole 276 KB JSON. The brief's
diagnosis (the allowance's per-line spine queries) was not where the time was; the build follows the brief's design (a stamped cache, one
recompute, the traces and the watch off the read path, in-place patches) and it is that design that removes the report composer and the
scoring from every read.

### Live files — FROM → TO, md5 read back on the box after placing
| file | FROM (pin in the brief, re-read live 05:28) | TO (read back 07:52) |
|---|---|---|
| /root/finance/loss_piles.py (whole, v2.1 → v2.2) | 3720b2e1261fd83932b07e2a319a0687 | 2501b55ad8334bf10c0c19a254d40a02 |
| /root/finance/stock_watch.py (whole, v1.1 → v1.2) | 6a51e47b891b717fbb51b030d4a29f02 | 5114e01f5dc70bd3f90dea3b040f8f02 |
| /root/finance/stock_loss.html (whole) | ab60c341336c8c897699db18e830211d | 5ead2a32949ec6e77e95b8645db350e2 |
| /root/finance/qty_words.py (whole, v1.0 → v1.1) | 1e67a3e35ce815798ef6ebd606e5b972 | f4c15d7e88c84b14c7686d5b28148877 |
| /root/finance/stock_app.py (anchored, make_s432.py) | 2a95e2543330b3efbdb0dc0106892bea | 02ad3d6ac3390dcf940d7a443557ac7c |
| /root/finance/stock_statement.py (anchored, v1.0 → v1.1) | 85ec7619d79c7a9f311f7bed91eeabae | 05c63235a9f78c9f0f6969c683548880 |
| /root/finance/stock_statement.html (anchored) | 175f4654a88e6bb81d0fd724be6d93c4 | b6bb8056821b8d3417868cb08b57cb75 |

Pinned and read, **not changed**: `stock_hub.html` 38e0537c (no label changes). Read only: `section_map.py` 9bf9b98f, `stockmatch.py` df5501ea,
`pad_receipt.py`, `padwriter.py`, `finance_app.py`, the spine. Restarted `clinic-finance` only; the crontab is unchanged (the 06:30 line still
runs `stock_watch.py job`, which now also stores the watch).

### What changed
- **`loss_piles.py` v2.2** — `stock_pile_cache` (count_id, item; diff_id beside it, indexed) + `stock_pile_cache_meta` (the stamp). `stamp()`:
  full parts = the stock.* settings (md5), the spine file (mtime + size), the count's rows (count, max id, sums), the swap answers, the prices
  (`stock_mrp_manual`, `stock_rate`), the renames, the section map, the snapshot, the close/parts; per-line parts = the newest id of
  `stock_pile_move` / `stock_shelf_fix` / `stock_diff_lane` / `stock_sales_test` / `stock_writeoff_run` / `stock_loss_share`. `cached()` →
  `rebuild()` (the report once; `sales_test` on it — a hit re-reads the report once; `classify` with `Spine.prefetch`: every item's sales,
  first sale and first purchase in three queries; every row + the stamp in one transaction) or `refresh_items()` (the touched items only:
  the stored post-swap line under today's word and shelf fix, `_classify_one`) or the rows as they are. `classify()` is now `_ctx()` +
  `_classify_one()` + the loop (the same rule, byte-for-byte in effect; the hub's `totals()` and the statement still call it).
  `desk_cached()` (`lite`, `pile`, `force`), `_light_d()`, `patch_of()`. `move_patch` / `accept_patch` recompute their lines at once and
  return the patch; `_run()` gains `clear=True` (kind `clear:<group>`, exactly the armed items, each still open in the group), `arm_clear()`,
  `clear()`, `CLEAR_GROUPS`; the last clear → `_freeze_block(how='auto')` from `_union_groups()` (every run since the previous block); a tap
  close's block unions the clears too; `block_preview` counts them (`cleared_runs`). `runs()` carries `kind` / `kind_text`; `closes()` lists
  the blocks with `how`; the record and the PDF show both. Two guarded columns: `stock_writeoff_run.kind`, `stock_staff_block.how`.
  **A bug found by the walk and fixed:** the arm token was an md5 of the second-resolution time + the items, so two arms of the same lines
  within one second shared a token and the confirm found the older (expired) row; the token now carries a random salt and the lookup takes
  the newest row.
- **`stock_watch.py` v1.2** — `stock_watch_view`; `refresh_owner_view()` (the traces on the given / cached Big-loss lines, then `owner_view`,
  stored with its time, audited `watch_refresh`); `stored_owner_view()` (built once, without traces, if nothing is stored); `cached_big_lines()`;
  `job()` stores the watch at the end and prints it.
- **`stock_app.py`** (anchored, every anchor once): `/api/loss/<cid>/piles` serves `desk_cached` + `stored_owner_view` (no `sales_test`, no
  report, no `trace_big_losses`, no `owner_view`; `?lite=1`, `?pile=`, `?rebuild=1`); `/pile/move` and `/pile/accept` return `patch`; the close
  opens `trace_big_losses` on the closed Big-loss lines; NEW `POST /api/loss/<cid>/pile/clear` (arm / confirm; the auto-close writes the S428
  points and the traces) and `POST /api/watch/refresh`.
- **`stock_loss.html`** — two reads (`?lite=1` first); collapsed pile cards drawn on open; `applyPatch()` for moves, accepts, clears and the
  close; the group card (`#grp`, Tick all / Untick all, the untick menu, Clear this group with its own 10-s countdown); the watch card with its
  time and **Refresh watch**; the cache's times under the tally. Every string the S427/S428/S430 walks look for is kept.
- **`qty_words.py` v1.1** — `words()` carries the minus of a negative quantity; `signed()` unchanged in effect; `stock_app._qw` (abs) unchanged.
- **`stock_statement.py` v1.1 / `.html`** — the Marg-negative rule (3.4): `neg_marg`, `correct_units`, `correct_text`, no short / over / money,
  not 'unpriced'; `neg_lines` / `neg_items` / `neg_text` per section, `neg_lines` overall; the PDF (head line + a kv under each section's
  totals), the XLSX (a Totals column, the row flagged), the page (a totals cell, the row's "to correct" tag, the section line).
- **The data (seed_s432, audited, idempotent):** `stock_item_section` BELL CAST 5 → Consumables (source owner, by "S432, cast material";
  `audit_log` `stock_item_section` / `section_set`); the tables and the two columns; the cache and the stored watch warmed for count #1.

### Calls I made (the brief left these open; each reason in one line)
- **The cache key is `(count_id, item)` with `diff_id` as a column** — every other desk table (moves, fixes, words, tests, runs) is keyed by
  item, and a crafted or re-imported line may have no diff row yet; the brief's `diff_id` is stored and indexed beside it.
- **The sales-after-count test runs inside the full build**, not on every read — its only input that changes without a desk write is the
  spine, and a spine rebuild changes the stamp; a hit re-reads the report once and the cache holds the closed line.
- **The spine's stamp is its file's mtime + size** (a rebuild rewrites the file), not a scan of its rows.
- **The first read after the install builds the stored watch once, without traces**, so the card is never empty; the traces come from the
  06:30 job, Refresh watch, a close or a clear.
- **Clear on "All"** is the one-tap close through the clear door (the same `_run`).
- **A tap close after clears unions the clears into its block** (the brief asks one block of the auto-close; a tap close in between would
  otherwise leave the earlier clears out of the staff block).
- **The block preview counts the clears already made** ("N clears already in it").
- **S431's and S428's walks are re-run from adjusted copies inside this kit** (a published kit is frozen): `walk_s431_s432.py` — two named
  adjustments (a Marg-negative line is neither short nor over; it carries no excess money and is not 'unpriced'); `walk_s428_s432.py` — two
  named adjustments (Refresh watch before the Big-loss traces are looked for; the crafted confirmed-Sunday count pinned a week back — see
  "outside the brief"). `walk_s427_s432.py` is S430's copy unchanged but for its docstring; `walk_s430.py` and `walk_s404.py` ran from their kits.

### The walk (install run 4, on scratch copies of the live database and the spine; crafted rows W432*, count W432 = #2)
```
   -- scratch: crafted W432 rows on count #1 and the crafted count W432 (#2, ~150 lines) on both copies, the spine; the S432 seed ran on the new copy
   -- NEW (the kit's files) on the scratch copies
     ok   count #1: the FIRST read builds the cache -- the report composed (2), the sales test once (1), no trace (0), no watch scoring by the read itself; 6106 ms
     ok   the sales-after-count test ran in that build: W432 SOLD TAB (counted 5, 20 strips sold after 06-09) is closed by the system, listed under 'sold after the count'
     ok   the crafted open lines sit in the piles: W432 LATE TAB and W432 LATE2 PC -> Write off, small real gap
     ok   the stored watch card came with it (built once on the first read), with its time; the piles are still the four of S427
     ok   the SECOND read is served from the cache: no report, no sales test, no trace, no watch scoring -- 331 ms (target under 1,000)
     ok   the stamp is stored and unchanged between the two reads; the cached rows carry every desk line (count_id, item, diff_id)
     ok   the two reads give the same lines and totals
     ok   the light read (?lite=1): the totals, the piles' headers with their counts, the close and the block -- no lines; 350 ms
     ok   one pile's lines (?pile=writeoff): that pile carries its lines, the others none
     ok   a move (W432 LATE TAB -> Big losses) answers in 436 ms (target under 500) with the PATCH: that line (bucket bigloss, group big), the totals, the close
     ok   the read after the move is a plain read again (the tap brought the stamp up to date): 381 ms, no report
     ok   the move recomputed ONE line (the cache's last partial refresh: 1)
     ok   a stale stamp on the moves part recomputes only the touched line (W432 LATE2 PC -> With me), no report
     ok   a setting change recomputes EVERYTHING once (the report composed once, no second sales test hit): built=full
     ok   a spine rebuild (its file's stamp changed) recomputes everything and re-runs the sales test once
     ok   and the read after that is a plain read: 330 ms
     ok   the hub's status card reads THE SAME totals as the desk (classify on the report = the cache)
     ok   two reads open no trace and score no watch (counters 0 / 0)
     ok   Refresh watch: the traces on the cached Big-loss lines (W432 LATE TAB gets one) and the watch scored once, stored with its time (851 ms)
     ok   the desk's watch card is the stored one, refreshed by manoj, and the refresh is audited
     ok   a second refresh opens no second trace on the same line (once per item per 30 days)
     ok   the job (cron) stores the watch: 'watch stored for count #' in its line, the row made by cron
     ok   count W432 (#2): the light read gives the groups with their open counts, the full read the lines; allowance / small / old / big / consume all present
     ok   W432 BIG TAB is a Big loss; BLADE is consumption; GLOCREPE is old stock; TYRO BR within the allowance
     ok   Clear with nothing ticked is refused (400); an unknown group refused; a line of another group refused (409)
     ok   the untick menu's choice writes the move (audited 'manoj'), the line leaves the allowance list for Big losses; the patch says so; no word written
     ok   the page's group list: ticks are local -- nothing in the database changes on a tick or an untick (no door exists for it)
     ok   Clear this group (18 ticked) arms: n = the ticked lines, a 10-second confirm, the group in the arm
     ok   the 10-second gate: a confirm after 11 s is refused and writes nothing
     ok   a ticked line that moved after the tap: the confirm is refused (409), nothing written
     ok   Clear writes off EXACTLY the ticked lines as that group (18, WRITE_OFF + closed), the unticked stay open; 2752 ms
     ok   ONE stock_writeoff_run for the clear, kind clear:allowance, its lines all under 'allowance', Amir's vouchers in a new round (<= voucher batch a voucher)
     ok   the voucher round is in batches of at most stock.voucher_batch lines
     ok   after the clear: the unticked line (W432 HOME TAB) and the moved one are still open; the cleared ones read 'written off -- Within the allowance'; the patch carried the new totals and group counts
     ok   the clear is in the record as its own run with its time and kind ('Clear this group -- Within the allowance'); no staff block yet (the count is still open)
     ok   the block preview counts the cleared run already ('1 clear already in it')
     ok   every group cleared in turn (clear:small, clear:old, clear:consume, clear:owner_use, clear:big): one run each, 5 runs in all; the LAST clear (big) closed the count by itself
     ok   ONE staff block (how 'auto'), frozen from the UNION of every clear: total = allowance + small + big of all the runs (734233), big by name (W432 BIG TAB first)
     ok   the desk shows the frozen block 'closed by itself after the last clear'; the record lists every clear and the close with their times; the piles are empty; W432 HOME TAB went as owner's use
     ok   the S428 full-count points were written ONCE for count W432 (one point per counted line), the leakage period line 06-Sep -> 20-Sep is there
     ok   W432 BIG TAB carries exactly ONE Big-loss trace -- opened by the job / the clear (once per item per 30 days), never by a read
     ok   the auto-close is audited; 'Close the count' on the empty desk is refused (400)
     ok   Amir's board carries every clear's round; the owner's-use line in its own round
     ok   the block is pinned on Stock milaan in Hindi (the S427 wording: 'Ginti 20-09-2026 · kul kami', 'Chhoti kami, likh di gayi', 'Badi kami')
     ok   the record PDF lists each clear as its own run ('Clear this group -- ...') and the close of the count
     ok   Close the count still works as one tap (count #1: 2 lines): kind 'close', a block (how 'tap'), the patch, the Big-loss trace opened once
     ok   count #1's frozen run of 27-Sep is untouched (md5, groups and lines equal before / after)
     ok   PRIME CAST 4" (Marg -24, shelf 0): tagged Marg negative -- book correction, no goods; Marg reads "-24 pcs"; 24 pcs to correct; no excess money
     ok   the Consumables section: PRIME CAST 4"/5" and BELL CAST 5 (moved there by the seed) are its Marg-negative lines; its excess money is Rs 0 on 0 lines; short unchanged (Rs 6,109)
     ok   BELL CAST 5 sits in Consumables in the section map, source owner, by 'S432, cast material', audited
     ok   the Medicines section: 8 Marg-negative lines (ALCOXIB 120, DECA INSTABOLIN 50, NEWTEL 40, FLUPIVAMP 100, TRAMEF P, GLI-ME SR1, PRIME PAD 4"/6") carry no excess money; its excess is the other lines' sum
     ok   the Orthotics section: CERVICAL COLLAR SOFT HOPE L (Marg -1) is its Marg-negative line; the overall carries 12 such lines and its excess money excludes them all
     ok   the section totals name the Marg-negative lines with their quantities to correct; the count line (S431's 373 + 3 crafted: Medicines 287, Consumables 20, Orthotics 69)
     ok   every other S431 figure stands: Medicines short on the real lines unchanged, Orthotics short Rs 6,860 on 13 lines; the real excess lines still read 'never a loss'
     ok   the PDF carries the Marg-negative line under the section totals and '-24 pcs' in the Marg column; no 'unit(s)'
     ok   the XLSX: the Totals sheet has the 'Marg negative' column; a Marg-negative row is flagged
     ok   the statement page carries the Marg-negative cell and the 'to correct' tag
     ok   qty_words carries the sign: words(-24, '1*1') = '-24 pcs', Hindi '-24 nag'; words(-13, '1*10') = '-1 strip + 3 tabs'; a positive figure unchanged; signed() unchanged
     ok   the frozen-copy list and the close line still answer (S431 stands)
     ok   bhati is refused on the desk, the clear door, Refresh watch and the page ([302, 302, 302, 302])
     ok   darpan is refused on the desk, the clear door, Refresh watch and the page ([403, 403, 403, 403])
     ok   shavez is refused on the desk, the clear door, Refresh watch and the page ([403, 403, 403, 403])
     ok   the page: the group card ('Close the count group by group', 'Tick all', 'Clear this group'), the light read first (?lite=1), the in-place patch (applyPatch), 'Refresh watch', the collapsed piles, the S430 strings kept
     ok   no 'unit(s)' on the desk JSON (both counts), the statement JSON or the page
     ok   the pile cache table exists on the new copy
      MEASURED (the test client, in-process, this box): first read 6106 ms (the cache built) · second read 331 ms · light read 350 ms · a move 436 ms · targets: piles < 1,000 ms, a move < 500 ms
   -- NEGATIVE CONTROL: the same scenario on the box as it is (must go red)
     ok   NEGATIVE: the old files go red (17 of 21 checks red): no cache (the report on every read), no clear door, the traces on the read path, no Marg-negative rule, no sign in qty_words
     ok   NEGATIVE: the old box has no stock_pile_cache table
     ok   NEGATIVE: on the old files a read composed the report and scored the watch (counters > 0)   [{'report': 30, 'sales_test': 14, 'trace': 12, 'owner_view': 12}]
   WALK_S432 GREEN -- 68 of 68 passed
```
(The walk's first read of 6.1 s composes the report twice because its crafted W432 SOLD TAB is a sales-test hit; on the live count #1 the
first read is one composition — 3.4 s in the figures below. The "18 ticked" clear took 2.75 s: a clear composes the report once for Amir's
vouchers, as the close always did.)

### The earlier walks re-run on the patched files (same install run, each against its own pre-kit control)
- **S430** `walk_s430.py` (S430 kit) — on `finance.db.bak_S430_20260927_121728`: **GREEN 42 of 42**.
- **S427** `walk_s427_s432.py` (S430's copy, unchanged) — on `finance.db.bak_S428_20260927_103804`: **GREEN 82 of 82**.
- **S428** `walk_s428_s432.py` (two named adjustments) — on the 12:17 backup: **GREEN 73 of 73**.
- **S431** `walk_s431_s432.py` (two named adjustments) — on a copy of the live database: **GREEN 56 of 56**.
- **S404** `walk_s404_s432.py` (one named adjustment: the four crafted verification-export days are today-relative) — on
  `finance.db.bak_S412_20260926_140429`: **GREEN 65 of 65**.
Runs before the green one (each stopped by its own gate, nothing placed): dry run 1 — my pin filler had overwritten the FROM pins (stopped
at [2/10]); dry run 2 — 68/68 own, S430 42/42, S427 82/82, S428 **red 7/73** (the calendar: the walk's "last Sunday" is the day before a
Monday run; fixed by pinning it a week back); install run 1 — own walk **red** on the clear confirm (the arm-token collision above; fixed);
install run 2 — own 68/68, S430, S427, S428 green, S431 **red 1/56** (I had marked a Marg-negative orthotic line 'not open' though the
section still awaits the owner's word on it; the override removed — the statement mirrors the section); install run 3 — own, S430, S427,
S428, S431 green, S404 **red 3/65** on its rename-verification checks — S404's walk hardcodes its crafted export days (2026-09-27..30) and
`item_alias.verify_closing` skips an export dated before the tick day, so from 28-Sep it goes red on ANY files: **run on the live files as
they are (no S432 file), 07:2x IST, the same 3 checks went red** (`/tmp/s432probe/run404.sh`); the adjusted copy makes the days
today-relative and nothing else; install run 4 — all green, placed.

### The seed on the live database and the figures (figures_s432.py, read 07:52 IST on a fresh scratch copy through the live files)
```
   BELL CAST 5: Medicines -> Consumables (set to Consumables)
   warmed count #1: 142 desk lines + 20 over in 3266 ms (full); the watch stored in 850 ms
   stamp: moves=5/5, runs=1/1, spine=1790533233457:9138176, v=S432.1, words=175/175
count #1 -- the desk read through the live files (the test client, this box):
  first read (the cache built from the report, the sales test once)    3385 ms  status 200  278770 bytes  built=full in 3009 ms, 142 lines
  second read (served from the cache)                                     366 ms  status 200  278769 bytes  built=cache
  light read (?lite=1: the totals first)                                 366 ms  status 200  35373 bytes
  a setting saved (no change) 350 ms; the read after it 3283 ms built=full
  the watch card: stored, as at 28-09-2026 07:52 IST (first read), 0 traces shown, first-count 28
  totals: open Rs 0 (0 lines) · back Rs 20,556.75 · written off Rs 64,678.78 · short at the count Rs 85,235.53 (142 lines)
the statement of count #1 (S431, with the S432 Marg-negative rule):
  ALL SECTIONS   373 lines (187 differ, 186 matched)  short Rs 1,19,749.26  excess   Rs 16,121.91  net Rs 1,03,627.35  without a price 3  Marg-negative 12
  MEDICINES      284 lines (162 differ, 122 matched)  short Rs 1,06,780.26 (134 lines)  excess   Rs 15,001.91 (20 lines)  net   Rs 91,778.35  without a price 1  Marg-negative 8
     Marg negative -- book correction, no goods: ALCOXIB 120 19 strips + 7 tabs; DECA INSTABOLIN 50 5 pcs; FLUPIVAMP 100 1 strip + 1 tab; GLI-ME SR1 7 tabs; NEWTEL 40 4 strips + 8 tabs; PRIME PAD 4" 12 pcs; PRIME PAD 6" 23 pcs; TRAMEF P 1 strip + 5 tabs
     no price -- name it: CORTIRI
  CONSUMABLES     20 lines (10 differ, 10 matched)  short       Rs 6,109 (7 lines)  excess           Rs 0 (0 lines)  net       Rs 6,109  without a price 0  Marg-negative 3
     Marg negative -- book correction, no goods: BELL CAST 5 14 pcs; PRIME CAST 4" 24 pcs; PRIME CAST 5" 45 pcs
  ORTHOTICS       69 lines (15 differ, 54 matched)  short       Rs 6,860 (13 lines)  excess       Rs 1,120 (1 lines)  net       Rs 5,740  without a price 2  Marg-negative 1
     Marg negative -- book correction, no goods: CERVICAL COLLAR SOFT HOPE L 1 pc
     no price -- name it: FINGER COT SPILNT REMEDE, SOFT COLLAR BODY AID S
the section map (stock_item_section) against the name rule (section_map.classify): 6 of 373 lines sit in a section their name contradicts
  BLING ELASTIC SHOULDER IMMOB (stored Orthotics, by name Medicines) · DISPO SYRINGE NIPRO 3ML · G DRESS 10 · G DRESS 20 · LEUKOBAND 4 INCH · TAPEASE NS SPRAY (stored Medicines, by name Consumables) -- all set by the owner (manoj)
```
(The figures' "a setting saved (no change) ... the read after it 3283 ms built=full": S427's setting door normalises a percentage — the
stored "1.0" was rewritten as "1", audited — so to the stamp it WAS a setting change and the piles were rebuilt once, as designed; on the
scratch copy only. The statement's Medicines count reads 284 because BELL CAST 5 moved out; S431's 285 / 19 / 69 are now 284 / 20 / 69.)

### Backups made
- `/root/finance/finance.db.bak_S432_20260928_073619` (sqlite backup API) — stays.
- `.bak_S432_<from8>` beside the seven files: loss_piles 3720b2e1, stock_watch 6a51e47b, stock_loss ab60c341, qty_words 1e67a3e3, stock_app
  2a95e254, stock_statement 85ec7619, stock_statement.html 175f4654.
- Service restarted: `clinic-finance` only. After: active; `/finance/healthz` 200 (local and public); `/finance/stock/page/loss` and
  `/finance/stock/page/statement` 302 to a plain curl (login gate, expected); journal since 07:36: 16 lines, all the restart's own
  (workers stopped and started), 0 tracebacks, nothing "NOT mounted". Read back independently at 07:58: `stock_pile_cache_meta` count #1
  built 07:52:19 (142 lines + 20 over, 3,254 ms), `stock_watch_view` 'owner' stored 07:52:20 (846 ms), BELL CAST 5 Consumables / owner /
  "S432, cast material" 07:52:16 with its audit row, count #1's one run (122 lines, 12:58 of 27-Sep) and one block unchanged, the two new
  columns present, no walk folder left under /tmp, the crontab's one stock_watch line as before.
- **Data written by the install:** the seed's one section row (BELL CAST 5), the new tables (`stock_pile_cache`, `stock_pile_cache_meta`,
  `stock_watch_view`) and two columns, the warmed cache and watch for count #1. No line, no word, no run of any count was touched.

### Not done, and why
- **A cosmetic slip in the watch card's time:** `stored_text` reads "28-09-2026 07:52 IST IST" (stock_watch's own `stamp()` already appends
  " IST" and I appended it again) — on the desk's watch card and in the "Watch refreshed …" message. One string in `stock_watch.py`
  (`refresh_owner_view` / `stored_owner_view`); found in the figures after placing, left as is because a published kit is frozen and the
  live file must stay byte-identical to it — a one-line fix for the next kit.
- **The memory note** on the walks' calendar trap could not be saved: the memory folder is denied to Claude Code's file tools here (as
  REPORT_S428 noted). The note is in this report instead (below).
- **`stock_hub.html` untouched** — no label on it changes (the brief: only if a label changes).
- **The job's 06:30 run of today (28-Sep) ran on the old stock_watch** (before the install); the first stored watch came from the seed's
  warm-up; the cron takes over tomorrow. No cron line changed.
- **A `__pycache__` folder** was written under the git-ignored `_scratch\S432_DESK_GROUP_FLOW\kit\` by a local compile check; the command to
  remove it (`Remove-Item -Recurse -Force`) is refused on this PC, so it stays there (never copied into `deploy_kits`, never published).

### Outside the brief, noticed
- **The section map has six more lines in a section their name contradicts** (stored vs `section_map.classify`, listed as the brief asked;
  no change made): BLING ELASTIC SHOULDER IMMOB — stored Orthotics, by name Medicines (the name rule misses it; the stored is right);
  DISPO SYRINGE NIPRO 3ML — stored Medicines, by name Consumables; G DRESS 10 and G DRESS 20 — stored Medicines, by name Consumables (the
  owner ruled on 27-Sep that G Dress is sold on bills — stock, not consumption — so Medicines may be his intent); LEUKOBAND 4 INCH — stored
  Medicines, by name Consumables; TAPEASE NS SPRAY — stored Medicines, by name Consumables. BELL CAST 5 was the seventh and is moved.
- **The arm token collision** (above) existed since S418 for every armed tap (write-off, close): two arms of the same lines within one
  second shared a token. Fixed here for all of them.
- **S428's walk assumes a Sunday run:** `walk_s428_s430.py` (the S430 kit) crafts its confirmed-Sunday count as the most recent Sunday and
  its trace bills 3–6 days back; on a Monday the Sunday is yesterday and seven trace checks read `first_count`. Later kits re-running
  S428's walk should start from `walk_s428_s432.py`.
- **The orthotic Marg-negative line** (CERVICAL COLLAR SOFT HOPE L, Marg -1, shelf 0) is still among the ten awaiting the owner's word on
  the hub / Stock milaan; the statement shows it as a book correction and open.
- **Count #1's 12 Marg-negative lines** are already on Amir's vouchers (the RECEIVE side, as before); nothing here changes a voucher.

### Publish
Published with `PUBLISH_ALL.bat` (kit + brief + this report); the commit is named in the "After publish" section below.

### After publish (07:59–08:00 IST)
- Commit `d49191a` "publish: pending kits and files (PUBLISH_ALL)" — 25 files: this kit (16), the S432 brief, this report — **and the
  clinic chat's `deploy_kits/S433_YES_BRANCH_READ/` (7 files), which was sitting uncommitted in the folder; PUBLISH_ALL publishes everything
  pending by design.** I did not touch, run or read that kit. The phone gate was clean (25 files); origin verified (07d1335 → d49191a).
- On the box: `/root/deploy/repo` pulled to `d49191a` (07:59:51); `md5sum -c SUMS.md5` in the repository kit: 15 of 15 OK; `diff -r` of the
  repository kit against `/tmp/s432kit` (what ran): identical; no `__pycache__` in the kit. The repository installer answered
  **ALREADY INSTALLED: the seven files are at the kit's pins; clinic-finance active; healthz 200**. Two `__pycache__` folders found under
  the clone's `deploy_kits/S413_SLIP_PICKER` and `S416_BUNDLE_ALLOWLIST` (earlier kits' compile runs, git-ignored) were removed; the clone is clean.
- Build lock released 08:00:15 IST. Public `/finance/healthz` 200 after everything.
- This section is published in a second commit.
