# REPORT_S570 — S570_PROOF_MORNING_WINDOW (16-Oct-2026)

**For Dr Manoj (plain English):**
- **The rule is fixed.** The check of Amir's stock vouchers now accepts the morning sale report (05:10) for the closing that comes a few minutes later (05:17). Both stand for the end of the same day. A normal morning no longer blocks the check. Live since 12:11 IST.
- **Your waiting line now tells the truth:** *"Marg's closing of 15-10 arrived 16-10 05:17; waiting for a purchase export that reaches that day (Amir)"*. Before, it named a mid-day 10:11 snapshot and waited for a sale report that had already arrived.
- **Today's verdict: still waiting, on Amir's purchase report.** As of 12:12 IST no purchase report has arrived since 15-10 09:11. The one you expected at about 11:10 has not reached the server. The check will give its verdict as soon as that report arrives. Nobody needs to do anything else.
- **What it will probably say:** a trial on a copy, with a made-up purchase report, flags 4 voucher lines: **KT ROS DT** and **VINBACTUM DS** (as the chat found), plus **FOLITRAX 15 MG TAB** and **OSTOVAXL DM**. The real purchase report may still clear those last two. This is not yet the verdict.
- **Amir's card:** no new screen and no verdict words. While the check waits on his purchase report, his card adds its existing reminder *"· Purchase report nikaaliye"* after *"Dawa ke voucher daal diye ✓"*.

---

## 1. Live files, FROM → TO (md5 read back on the box)
| file | FROM (read at the open, 11:49 IST) | TO (read back 12:11 and 12:12 IST) |
|---|---|---|
| `/root/finance/stock_app.py` | `f58e09dbb273e8b1470aa7220da70015` | `050587dfb5951da65f95937615ddf144` |

Read only, never edited: `amir_day.py` `73882a8391fde24f31e07b0191c5bd89` (same before and after), `/root/finance/spine/*`. The installer
recorded the md5s of `amir_day.py`, `finance_app.py`, `stock_watch.py`, `shelf_figure.py`, `stockmatch.py`, `sanjeevni_approvals.py`, `stock_hub.html`,
`stock_amir.html`, `qty_words.py`, `portal.py`, `tile_grants.json`, `spine_build.py`, `spine_read.py`, `marg_read.py`, `spine_rules.json` and the crontab
before placing. All of them were the same after placing. No data was written to `finance.db`.

## 2. The edits (`make_s570.py`, 4 anchored edits, each anchor found exactly once in the live bytes)
- **E1 F-905:** `_s524_tryable` now calls the new `_s570_covers(day, stamp, c, d)` = `stamp > c["stamp"]` **or**
  `_s524_end_day(day, _s524_stamp_iso(stamp)) >= d` (None never covers). `day` = `reach['last_sale']` / `reach['last_pur']`. The helpers are the ones
  REPORT_S569 named (`_s524_end_day`, `_s524_stamp_iso`), and their names and signatures are unchanged. `last_sale >= end_day` and `last_pur >= end_day` are kept.
- **E2 F-906:** `_s488_why` sets `closing_at` = the spine closing's own capture (`c["stamp_iso"]`), never a `stock_feed` push.
- **E3 F-906:** `_s488_why` handles the case where the spine has no clean closing after the vouchers. A push the capture rule skips (a mid-day capture) is never named, each
  push is read by its own capture (not the day's MIN), and when `_s524_tryable` reports the purchase side short the reason is `pur_behind`.
- **E4 F-906:** `_s488_first_push` skips mid-day captures the same way.
- **What it does not change:** the proof's cache key, its verdict, the pairing, and S528's "the newest capture says wrong" rule (W3c proves the tables are identical).

## 3. The walk (`walk_s570.py`, run by the installer on the box 12:09:43–12:11 IST; the same as the dry run at 11:59 and the first attempt at 12:07)
```
GREEN W1a function: _s524_tryable -> (True, '') on the NEW file
CONTROL RED (as it must) W1a on the OLD file -> [False, 'sale']
GREEN W1b the spine copy: the made-up closing read by _s524_closings (end_day 2027-03-10), the reach by _s524_reach (sale 2027-03-10, pur 2027-03-10) -> tryable [True, '']
CONTROL RED (as it must) W1b on the OLD file -> [False, 'sale']
GREEN W2a function: NEW (False, 'pur'), OLD (False, 'pur')
GREEN W2b the spine copy: NEW [False, 'pur'], OLD [False, 'pur']
GREEN W2c purchase to D+1 captured D+1 11:10 (after the closing) [True, '']; a sale captured D 15:00 [False, 'sale']; a sale report short of D [False, 'sale']
   closing 2026-10-10 / 10-12 / 10-13  OLD [True, '']  NEW [True, '']   (every closing on the copy, 2026-03-31 .. 2026-10-13: identical)
   closing 2026-10-15@20261016-051700  OLD [False, 'sale']  NEW [False, 'pur']
GREEN W3a the earlier closings 2026-10-10, 2026-10-12, 2026-10-13 give the same answer on both files ((True, ''))
GREEN W3b the only closing whose answer moves is 2026-10-15
GREEN W3c the proof table (R, after, tries, N, every key's tries and verdict) is the same on both files for 6 windows (the lots' and one before each earlier closing)
W4 as on the copy (NEW): hub 200 state wait stage C; 3 lots: export · why pur_behind · closing_day 15-10-2026 · closing_at 2026-10-16T05:17:00
   as on the copy (OLD): 3 lots: export · why no_figure · closing_at 2026-10-15T10:11:28
   with a made-up purchase export captured 16-10 11:00 covering 1-16 Oct (NEW): state now; "Stage C: lot 3 — 4 voucher(s) do not agree with Marg's closing of 15-10-2026"
     WRONG ROW: FOLITRAX 15 MG TAB · need -6 (-1 patte + 1 goli) · Marg moved 0 · Marg at 15-10 28 patte + 2 goli          (voucher 8, STOCK ISSUE)
     WRONG ROW: KT ROS DT · need -101 (-6 patte + 11 goli) · Marg moved 0 · Marg at 15-10 28 patte + 10 goli               (voucher 9, STOCK ISSUE)
     WRONG ROW: VINBACTUM DS · need -25 (-25 nag) · Marg moved 0 · Marg at 15-10 25 nag                                    (voucher 18, STOCK ISSUE)
     WRONG ROW: OSTOVAXL DM · need +21 (+2 patte + 1 goli) · Marg moved +25 (+2 patte + 5 goli) · Marg at 15-10 37 patte + 1 goli (voucher 6, STOCK RECEIVE)
GREEN W4a with the made-up purchase export the NEW file gives a verdict (state now; lots waiting 0; wrong rows 4)
CONTROL RED (as it must) W4a on the OLD file with the same made-up purchase export: state wait, lots waiting 3, wrong rows 0
GREEN W5a the 15-10 sale report is in; the NEW sentence has no '10:11' and no 'made when its sale report lands'
GREEN W5b the purchase side short -> the purchase words and 'arrived 16-10 05:17'
CONTROL RED (as it must) W5 on the OLD file the sentence carries both '10:11' and 'made when its sale report lands'
GREEN W5c Amir's card: the OLD words, plus S528's own tail ' · Purchase report nikaaliye'; no verdict word
GREEN W7a a mid-day push is never named (NEW: why no_closing)      CONTROL RED (as it must) W7a on the OLD file the mid-day push is named
GREEN W7b the clean push (22-03 05:17) is the one named (NEW)       CONTROL RED (as it must) W7b on the OLD file the mid-day 10:11 is named
GREEN W6 no run of ten digits in the walk's own output
WALK_S570 GREEN (20 checks, every control red on the old file)
```
**W4, what it shows (not asserted):** KT ROS DT and VINBACTUM DS are among the wrong rows, as in REPORT_S569's trial. FOLITRAX and OSTOVAXL are the
same two extra lines S569 found. Because the made-up purchase export carries no purchase lines, a purchase keyed after 15-10 09:11 would not show here.
W7 is an extra test of E3/E4 that the brief did not list. Each probe ran in a fresh process on its own backup-API copies, with its own rows found by key (md5 `W570…`, the day
2027-03-10, the feed day 21-03-2027).

**"S524/S528 walks (read-only) stay green" (brief §3.3): they cannot be green on today's estate. S570 moves none of their checks.** I ran both
walks twice on scratch copies (12:01–12:07 IST). First with NEW = the box as it is (f58e09db), then with NEW = the box + the S570 build; OLD = the box both times.
`walk_s528`: **RED 2 of 7 on both runs, the same two checks**. Its function probe dies on `stock_app._S444_RENAMES_CACHE`, a name a later
kit retired, and its amir_day grep predates S533. `walk_s524`: **RED 24 of 43 on both runs, the same 24 checks**. It needs the S524 Part-0 spine builds and
the v10 duty map. **diff base → s570: no difference for either walk.** These walks are tied to the code of their own time. W3 in `walk_s570.py` takes their place
for the proof logic.

## 4. Install (`install_S570_PROOF_MORNING_WINDOW.sh`)
- **First attempt, 12:07:27 IST: red after placing, restored.** The walk was green and the file was placed (md5 read back 050587df) and restarted once.
  Then the kit's own read-back script stopped on a wrong column name (`mi_file.family`; the column is `type`). The installer restored
  `stock_app.py` byte-identically (read back `f58e09db…`), restarted, and healthz was 200. The code change was not at fault. I fixed `state_s570.py` (the kit
  was not yet published), tested it alone on the box, and ran the installer again.
- **Second run, 12:09:43 IST, the lock already held by S570:** gates green (spine 13/13 passed, last success 12:00:52; collector ran 3 min before) → FROM pin →
  build = TO pin → compile on both pythons → walk green → state BEFORE → backups → placed by rename → md5 read back `050587dfb5951da65f95937615ddf144`
  = TO and byte-identical to the walked copy → `clinic-finance` restarted once (12:11:15) → healthz 200; `/finance/stock/page/amir`, `/finance/amir`,
  `/finance/sanjeevni/api/needs-you` 302 (the login gate, as expected); no error in the journal → read-back green → nothing else moved → `S570_PROOF_MORNING_WINDOW: DONE`.
- **Restarts of `clinic-finance`: three in total.** The brief names one. Two came from the first attempt (place, then the restore) and one from the second run.
- **Backups:** `/root/finance/stock_app.py.bak_S570_f58e09db` (md5 f58e09db…; the second run copied it again with the same bytes);
  `/root/finance/finance.db.bak_S570_20261016_120727` and `/root/finance/finance.db.bak_S570_20261016_120943` (38465536 bytes each, backup API).

## 5. The owner's proof on the box (`/api/pad/hub/1` `proof`, the app's test client on backup-API copies, 12:12:15–12:12:25 IST)
```
reach: sale to 2026-10-15 @ 20261016-051010 · purchase to 2026-10-15 @ 20261015-091029
purchase files received 16-10 after 11:00 IST: none
proof: hub 200 · state wait · stage C · total 30, entered 30, released 30, lots 3, verified 0
text: Stage C: lot 3 entered on 15-10-2026 — waiting: Marg's closing of 15-10 arrived 16-10 05:17; waiting for a purchase export that reaches that day (Amir)
  lot released 12-10 08:08 (12 vouchers): export · why pur_behind · closing_day 15-10-2026 · closing_at 2026-10-16T05:17:00 · since 2026-10-15T09:32:02
  lot released 15-10 08:43 (12 vouchers): export · why pur_behind · closing_day 15-10-2026 · closing_at 2026-10-16T05:17:00 · since 2026-10-15T09:50:38
  lot released 15-10 09:50 (6 vouchers):  export · why pur_behind · closing_day 15-10-2026 · closing_at 2026-10-16T05:17:00 · since 2026-10-15T10:00:49
Amir's card: Dawa ke voucher daal diye ✓ · Purchase report nikaaliye
```
Before placing (the old file, 12:09): the same lots read `why no_figure · closing_at 2026-10-15T10:11:28`, and the text read "… arrived 15-10 10:11; waiting for our own
figure for that day (made when its sale report lands — Shavez; …)". **The owner's ~11:10 purchase export had not landed by 12:12 IST** (no
`mi_file` PURCHASE_* received after 11:00), so there is no verdict to read. Once that file arrives and the spine's next build (every 10 min) reads it,
the hub will give the verdict on its own.

## 6. Did not do, and why
- **The brief's exact words "a purchase report that reaches dd-mm (Amir)" were not used.** The English ending lives in `amir_day._s488_ending`, and amir_day is
  read only in this brief (§1). Its existing `pur_behind` words appear instead: "…arrived 16-10 05:17; waiting for a purchase export that reaches that day (Amir)".
  The head of the sentence already names the day (15-10). If the chat wants "dd-mm" in the tail, that is a small amir_day edit for a later kit.
- **No DUTY_MAP change.** No duty was added, moved or removed. "Purchase report nikaaliye" is S528's existing tail on `[amir.count_vouchers]`, and the
  purchase export is already the duty `[amir.purchase_exports]`. That is why there is no portal staff-eye sign-in. W5c reads Amir's card words through
  `_s521_stage_words`, the same source his card uses, on both files.
- Board `_numbers` v453 → v454: not reachable from Claude Code. **The chat should append S570's DONE line.**

## 7. Charter
- **Retired:** the clock-only comparison in `_s524_tryable` (a second, narrower capture rule beside charter 11's); the day's-MIN read of `stock_feed`
  in `_s488_why` / `_s488_first_push`. **Left for later:** the amir_day tail words (above). **Left out:** nothing.
- **Seen, not touched (outside the brief):**
  1. **Amir's card changes even though the brief says it would not.** While the proof waits on the purchase side, S528's `pur()` in `_s521_stage_words` now adds
     "· Purchase report nikaaliye". The old file never reached `pur_behind` on a normal morning, so that tail almost never showed. It is a do-this line,
     not a verdict (D708), so I kept it. If the chat wants his card unchanged, that is an S528-words decision.
  2. Older closings still read (False, 'sale') on both files: 2026-09-02 (captured the same day at 17:23), 2026-09-19 (10:13), 2026-10-01 (21:39), 2026-10-04 (10:22) and
     2026-10-08 (09:54). All are captures made inside shop hours, so they have no end_day and are skipped as before. The spine keeps one of them per printed day
     even when a clean capture of that day might exist. Not investigated.
  3. The live sentence's tail reads "that day" where the head names 15-10. That is fine as English but less exact than the brief's wording.
- **Dependency state at install (charter 1b):** `spine_state.json` passed, gate 13/13, last success 2026-10-16T12:00:52 IST; the collector's last run 1–3 min before, 0 failed.

## 8. Lock, publish, scratch
- Build lock `/root/deploy/.claude_code_build.lock` taken at 12:07:27 IST (owner S570_PROOF_MORNING_WINDOW). It was held through both runs and released after this report (see the end).
- Published with `PUBLISH_ALL.bat`: commit `b38364f` (NO_PHONE_NUMBERS clean, 23 files). That commit also carried other pending files: the S571 brief and two S568 walk
  files from the other chat. `/root/deploy/repo` was pulled to `b38364f`, and `md5sum -c SUMS.md5` there gave OK for all 7 files; its SUMS.md5 is identical to the folder that ran
  (`568dc5c4…`). This report is published by a second `PUBLISH_ALL.bat`.
- Box scratch: every database copy I made in /tmp was removed (118 files under `/tmp/s570probe` and `/tmp/s570prior_20261016_120114`). Code copies and logs
  remain in `/tmp/s570kit1..3`, `/tmp/s570probe`, `/tmp/s570prior_20261016_120114`. They hold no database, but `rm -rf` is refused by the permission list, so they stay.
  The installer's own `/tmp/s570_walk_*` folders were removed by the installer.
- **Lock released at 2026-10-16 12:13:31 IST** (read on the box) with `rm …/owner; rmdir …`; afterwards the lock directory no longer exists.
- **Undo:** put back `/root/finance/stock_app.py.bak_S570_f58e09db`, restart `clinic-finance`, healthz 200, read the md5 back (f58e09db…). No data to reverse.
