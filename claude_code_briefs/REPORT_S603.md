# REPORT S603_AMIR_CALENDAR_SAFE — installed 20-Oct-2026, 08:05 IST

## For the owner

1. **Amir's "re-export" reminder now clears only when the fresh report really lands on the server** — not when he taps "Dono report nikaal di". On 18-Oct he entered a bill at 09:35 after exporting, tapped the two buttons at 09:37, and no new report ever came; the reminder went away anyway. From now the tap starts the six-minute clock and the reminder stays until the file is there. Checked on a copy of the live data: 18-Oct now reads "re-export due since 09:35"; the old file read "not due".
2. **His step 4 takes whichever of the day's exports covers "1st to today"** (the 1st of a month, a Sunday, a day with no purchase) instead of the newest one, and **when a report has not come his screen says since when** — "09:37 baje se nahi aayi".
3. **You get one line on Needs-you after 48 hours** if a visit's purchase report never reached the server, or a re-export is still owed. **At install (08:05 IST) the 18-Oct line was not yet on your list** — his tap was at 09:37:53 on 18-Oct, so the 48 hours run out at 09:37:53 today; from then your list says *"Amir entered a bill at 09:35 on 18-10 after that day's export and no purchase export has landed since — re-export owed (Amir)"* until his next export lands.
4. **Three of your English sentences stop blaming the calendar:** the drift page's "Purchases are 2 days behind today" is gone; the stock-ahead sentence is now a true sentence about whether a purchase export has been taken since the closing was captured — today it reads *"No purchase export has been taken since the closing stock of 18-10-2026 was captured (19-10 09:37); the newest purchase exports reach 18-10 09:25 (bill-wise) and 18-10 09:27 (item-wise). Amir's next export settles it — count after it, not before."*; the count's waiting line says "not printed under their name in it" when Marg's closing came and does not print the item; and "closing stock of D waits for Amir's purchase export" has become *"Closing stock printed 18-10 09:37 waits for a purchase export taken after it (newest: bill-wise 18-10 09:25, item-wise 18-10 09:27)"* — on your list from today (the old words would have waited until tomorrow). Opening your drift page no longer records a start-of-day verdict by itself (F-953): that page only reads now.
5. **A salt you answer reaches Amir's sheet:** it appears on his SALT KAAM tab as "Item ka salt badliye — Dr sahab ka jawab" with your answer as the exact text to copy, and he ticks it there like any other line; his step-6 "Salt aur naye item" card and your salts page count it with the rest. The seven you answered in October stay ticked (he ticked them on your page on 08-Oct); nothing is re-opened, so his sheet is empty today.

Nothing on Darpan's, Shavez's or reception's screens changes (their pages read the same bytes before and after on a copy). No figure changes. No new setting. **Installed and working:** `clinic-finance` restarted once at 08:05:53 IST, healthz 200, every page answering.

## For the chat

### Files, FROM → TO (read back on the box after placing, 08:06 IST; re-read 08:06:56 IST)

| file | FROM | TO |
|---|---|---|
| /root/finance/amir_day.py | 3af992d9e6b6c6050b1427e34757ca78 | 1169a3d6ae451ebb4c9806052de0856c |
| /root/finance/stock_app.py | 4f73d0b02a167289d9439af7a35b5fa0 | 40f2c92260ae6b6715d49729fef464ff |
| /root/finance/stock_watch.py | 299c3ef76b73a10e4af1cd15974c7a3f | f0d9092a051c4cd043645e4510ef4cee |
| /root/finance/amir_salts.py | d8d9ba772650a4d804add6953790d14d | fc5c1d169cf971deb6b59010141a4550 |
| claude_code_briefs/DUTY_MAP.json (the clone, by the publish) | c2ef9c6c5adb8c930b21bff5441cc017 (v15) | b75ea78ea5c65005d2a6420960bad19c (v16) |
| claude_code_briefs/DUTY_MAP.md (the clone, by the publish) | — | 59c6bf9896aeb818fd9d4a54fe6e8b8b |

Read-only pins printed at the open and unmoved: stock_figure 51e1fc63, purchase_app 60f2d846, export_watch f6845ec5, shelf_figure 23b2394a, order_rules 8d078dbe, porders e5a5c4d4, darpan_kal b28d7342, spine/spine_read 10697b38; the clone's DUTY_MAP.json c2ef9c6c (v15). Proved unmoved by the installer: finance_app, portal.py, tile_grants.json, the crontab (84 lines, `# S577_WITNESS` once), spine.db's schema (a66309303c25178a291ada6fb539fbe5 before and after). 26 anchored edits (amir_day 10, stock_app 7, stock_watch 3, amir_salts 6), each anchor exactly once, plus DUTY_MAP.json v15 → v16 and one dated line in DUTY_MAP.md; compiled on both pythons; the built DUTY_MAP.json byte-equal to the kit's shipped copy. The spine at install: passed 13/13, last success 2026-10-20T08:00:49+05:30 (2 min old). No DDL, no new table, no new setting, no data step.

**F-510, the clocks read, not estimated — the live facts the installer printed at 08:03:18 IST:** the 18-Oct `amir_step_log` rows: 51/52/53 step 2 at 09:22:55 / 09:22:58 / 09:25:06, 54 step 3 09:27:13 (export), 55 step 6 09:27:44, **56 step 2 09:35:24**, 57 step 6 09:36:42, **58 step 3 09:37:53 (export)**. Purchase receipts after 09:35:24: **0 mi_file, 0 purchase_export** (the newest receipts on the server: mi_file 2026-10-18 09:27:06, purchase_export 2026-10-18 09:31:59). `stock_start_capture` 6d718060 printed 2026-10-18 taken 09:37:08 → end 2026-10-17 **pending / pur_short** (checked 08:00:04 by the day's tick). `purchase_salt_task` by section (done): change 65 (1), cleanup 1 (1), create 38 (1), rename 2 (1), waiting 7 (1), parked_orthotic_S237 12 (0) — 0 open tasks. Settings: amir.proof_wait_hours 48, amir.job_wait_days 10. The new duty's `due_sql` on the live database: **(0, None)**.

### The install (one run, one placement)

- **07:39, 07:47 IST** two rehearsals of the walk alone on scratch copies (`/tmp/s603w`, the kit's two python files copied to `/tmp/s603kit`). The first found three faults in the walk itself, fixed before anything was placed: (1) the synthetic owner-line cases shared one export fact — a receipt laid for case (iii) answered the visits of cases (i) and (ii) too, exactly the one-fact rule — so the cases are now laid and read one at a time and the moments staggered; (2) the needs-you dump's `count` key moved with the masked lines; (3) a function-body regex that could not see the last function of a file. Two controls were relabelled plain checks because they are the same on both sides (the duty's SQL alone; the map file), and the F-953 control gained a one-second pause so a judge write inside `readiness()` cannot hide behind a same-second `checked_at`. The second rehearsal: 83 checks, 32 controls green on NEW, 32 red on OLD.
- **07:50 IST** the installer's DRY refused: outside the window (08:00). **08:00:01** DRY again: refused by the spine gate — last success 23:50 last night, 489 min old (the spine's cron builds `*/10 8-23`, so the first build of the day was running). **08:00:49** the spine built; the DRY ran green end to end (gates, pins, the facts, the build, both walks, S602's walk, S598's walk on both sides).
- **08:03:18** the build lock taken by S603; pins exact; the walk (08:03:52–08:04:5x) and the control; S602's walk whole on the NEW files `WALK OK S602: 50 checks, 18 controls green`; S598's walk `WALK RED` on BOTH sides with the same 5 FAIL lines (its data controls read the pre-re-judge rows and its own KIT line expects S598 in stock_figure — today's data, not this kit's doing, as at S602) and 62 check lines identical; the state BEFORE and as the NEW files read the same copy; backups; the four files placed by rename in one command (md5 read back = the TO pins, byte-identical to the walked files); **08:05:53** `clinic-finance` restarted — healthz 200; /finance/amir, /amir/day, /amir/salts, /stock/api/readiness, /reports/aaj, /porders, /darpan/kal all 302 without a login (the gate, expected); journal clean (0 error lines since the restart, re-read 08:06:56); the state AFTER; nothing else moved; `DOCTOR_AUTO_OFF` removed. DONE at 08:06.
- The kit ran from `/tmp/s603kit` (SUMS checked on the box); the kit in the repository is the same bytes (SUMS re-checked in the clone after the publish, below).

### The walk on the box (the install run, 08:03–08:05)

`WALK OK S603: 83 checks, 32 controls green on the new files` · negative control: `every control red on the old files (32)`. Every section green; the quiet-day page dumps (Amir's seven steps and salts page, the owner's amir/day, Shavez's, Darpan's tab and api/day, reception's porders, stock-now, api/readiness with the purchase sentences masked, needs-you with the S603 lines and the count masked) **byte-equal OLD vs NEW, 0 differ**.

**Control 1 (F-952) verbatim:**
```
18-Oct on the copy: taps {2: '2026-10-18 09:35:24', 3: '2026-10-18 09:37:53', 6: '2026-10-18 09:36:42'}; _reexport_due -> (True, '2026-10-18 09:35:24')
ok   C: (1) the 18-Oct replay: _reexport_due is (True, '2026-10-18 09:35:24') -- his step-3 tap of 09:37:53 clears nothing, no file came after 09:35:24
with a synthetic mi_file PURCHASE_BILLWISE receipt of 20-Oct 09:00 -> (False, '2026-10-18 09:35:24'); with a synthetic purchase_export BILLWISE receipt instead -> (False, '2026-10-18 09:35:24')
ok   C: (1) a VERIFIED mi_file receipt of ANOTHER day (20-Oct) after T2 clears the band (True -> False): the same-day cut is gone
ok   C: (1) a purchase_export receipt after T2 clears it too (the pusher's receipt is a receipt)
the morning case (synthetic day 2026-12-04): one step-2 tap at 10:00, nothing after -> (False, None); exports received 10:04, step 2 again 10:10, step 3 10:12 -> (True, '2026-12-04 10:10:00')
ok   (1) R1-B1: before the visit's first file nothing is expected -- (False, None)
ok   C: (1) a bill entered after the file landed, then 'nikaal di' tapped: due (True) -- the step-3 tap is no mark
```
OLD: `(False, '2026-10-18 09:35:24')` on the replay (his step-3 tap of 09:37:53 was the mark) and `(False, …)` on the morning case — red, as the brief said.

**Control 2:** a synthetic day with two live rows per family — A = 1st..day (stamp 09:00), B = last month (stamp 09:05, the newer) — NEW `ok` for both families with A's period "01-12-2026 se 06-12-2026"; OLD `bad` "tareekh galat hai -- 1 tareekh se aaj tak chahiye" (B chosen). With B alone: bad on both. The real 1-Oct rows as they stand: ITEMWISE `none` ("abhi nikaali nahi gayi" — all its 1-Oct ITEMWISE rows are superseded, R1-C6), BILLWISE `ok` — printed, not asserted, the same on both sides.

**Control 3:** a step-3 tap 10 min ago and no export → NEW `bad`, reason `07:53 baje se nahi aayi`, `since` 07:53 (OLD "aaj ki nahi aayi", since None); the step-4 head rendered as the walk's amir session on that day: *"Item-detail purchase report mein dikkat hai: 07:53 baje se nahi aayi — phir se nikaaliye"*; the wait state (tap 2 min ago) 34 lines, byte-equal OLD vs NEW with times masked.

**Control 4 verbatim (the cases laid and read one at a time; `lo` after the newest real receipt so no real receipt answers them):**
```
(i) 17-10: first tap 2026-10-18 09:52:59, step 3 2026-10-18 06:03:52, no receipt after the tap -> ["Amir's purchase export of 17-10 never reached the server — he tapped 'nikaal di' at 18-10 06:03; the day stays open until the pair lands (Amir)"]
(ii) 16-10: first tap 2026-10-18 09:32:59, a receipt 2026-10-18 09:34:59, a step-2 tap 2026-10-18 09:37:59, step 3 2026-10-18 06:03:52 -> ["Amir entered a bill at 09:37 on 16-10 after that day's export and no purchase export has landed since — re-export owed (Amir)"]
(iii) 14-10: as (ii) with a purchase_export receipt 2026-10-18 09:39:59 after the last step-2 tap -> no line
(iv) 13-10: as (i) with the step-3 tap only 10 h ago (2026-10-19 22:03:52) -> no line
(v) 19-10: as (i) but the day closed (a step-7 close row) -> no line
(vi) the real 2026-10-15 (closed; its pair superseded by the 16-Oct export; R1-B2) and 18-Oct as they stand -> no line
needs-you + Amir entered a bill at 09:37 on 16-10 after that day's export and no purchase export has landed since — re-export owed (Amir)
needs-you + Amir's purchase export of 17-10 never reached the server — he tapped 'nikaal di' at 18-10 06:03; the day stays open until the pair lands (Amir)
```
On the copy as it stood at 08:03:52 the S603 lines were none (18-Oct's 48 h run out at 09:37:53 today — printed, not asserted, R1-C12). OLD: no such line anywhere (red on i, ii and the needs-you check).

**Control 5 (F-786):** the real root count (stage C): R = the closing of 02-10 (20261003-072520), five tries after the vouchers (15-10 ×3, 16-10, 18-10), N = 18-10 not judgeable (short `pur`). Subject: batch 1|ISSUE|1, item ECONORM CAP, its 5 printed rows removed from every try capture on a second spine copy → NEW `_s524_verdict` state `export`, why **`absent`**, unseen `[('ECONORM CAP', 'absent_at_try')]`, absent `['ECONORM CAP']`; `_s488_ending`: *"Marg's closing of 15-10 arrived 15-10 10:05; 1 item(s) not printed under their name in it: ECONORM CAP (still wrong in Marg — the hub's correction list; Amir)"*; `_s524_english_ending` the same words. OLD: `no_figure` — *"waiting for our own figure for that day (made when its sale report lands — Shavez; on a no-sale day, the empty report)"* (red). A mixed unseen set (absent_at_try + no_verdict) → `no_figure`; one `absent_before` → `no_figure`; the live lot's proof `pur_behind` on both sides (a pur_short closing).

**Control 6 (F-769 / F-953) verbatim:**
```
the newest usable capture: printed 2026-10-18 taken 2026-10-19T09:37:51 -> end 2026-10-18; purchase_cover_how = None
readiness()['warnings']: ['The sale report is 2 days behind today.', "No purchase export has been taken since the closing stock of 18-10-2026 was captured (19-10 09:37); the newest purchase exports reach 18-10 09:25 (bill-wise) and 18-10 09:27 (item-wise). Amir's next export settles it — count after it, not before."]
stock_start_capture rows moved by readiness() + _r_stock(): False
ok   C: (6) F-769: no purchase 'days behind' sentence in readiness()['warnings']
ok   C: (6) the stock-ahead sentence follows purchase_cover_how of the newest usable capture (how None -> one sentence)
ok   C: (6) F-953: the judge did not run -- the stock_start_capture rows are byte-equal before and after readiness() and _r_stock()
forced (a second spine copy without its 77 purchase export rows; the copy's 4 step-2 tap(s) of visit day 2026-10-18 removed): [..., "No purchase export has been taken since the closing stock of 18-10-2026 was captured (19-10 09:37); the newest purchase exports reach none yet (bill-wise) and none yet (item-wise). ..."]
ok   (6) readiness()'s other keys equal OLD vs NEW (['gate', 'headline', 'lines', 'ok', 'purchase', 'returns', 'sale', 'stock'])
```
OLD: `'Purchases are 2 days behind today -- anything entered into Marg after 18-10-2026 is not in any figure on this page.'`, no stock-ahead sentence (reach = as_on today), and **the judge ran: the pending row's `checked_at` moved 08:03:47 → 08:03:48 under `readiness()`** — F-953 proven on this box.

**Control 7 verbatim:**
```
start_capture_lines: ['Closing stock printed 18-10 09:37 waits for a purchase export taken after it (newest: bill-wise 18-10 09:25, item-wise 18-10 09:27)']
ok   C: (7) the pending capture's line in its new words, verbatim
ok   (7) the judge did not run: the stock_start_capture rows are byte-equal before and after
with synthetic purchase exports of BOTH families stamped 20261020-080000: none
```
OLD printed nothing (the day count waits until 21-Oct) — red by text.

**Control 8:** the subject id 119 (answered 04-Oct, ticked by Amir on the owner's page 08-Oct) set `done = 0` on the copy → `_open_tasks` [(119, 'waiting')] last, `_exact` = the owner's answer, `_waiting` empty; the workbook's tabs ['SALT KAAM', 'NAYE ITEM', 'PADHIYE'] — tab 1 carries id 119, "Dr sahab ka jawab" and the answer, tab 2 absent; an upload with Y on that id → done 1 by amir at 08:04:20; a synthetic unanswered waiting row stays on tab 2 and off tab 1. OLD: `_open_tasks` empty, `_waiting` all 7, tab 2 present (red). **Control 9:** `due_sql` (0, None) → (1, '2026-10-04') with the row open; DUTY_MAP.json v16 loads; S533's byte-equal check of the three `DUTY_SQL` strings re-run green; **the staff-eye walk:** the real portal from a scratch copy with the walk's own secret and user store — Amir's home tiles ['Amir ka kaam', 'Aaj ki reports', 'Meri attendance']; the door /finance/amir/step/6 as amir shows the marker with the row open (OLD: no card, red) and not once the row is restored. **Control 11 (greps):** every proof of §3.7 green; `stock_figure.py` untouched; no ten-digit run; no spine write; the copy's rows as they were.

**The `_sf.Ctx(` list in stock_app.py (§3.4), as the walk printed it on the built file:** 1983 `_r_stock` **read-only (this kit)**; 2174 `_s603_purchase_wait` (readiness) **read-only (this kit)**; 2316 `_s577_record` (the stock-now / drift page's figures of record — a GET path that still judges, R2-B2, named, not touched); 5260 `_voucher_guard_base` (the guard, the day's pages); 7994 `amir_stage` (the day's pages); 8302 and 8322 `_s488_why` (the proof's reason, from the day's pages); 8747 `_s524_table` (the proof, by design). Only 1983 and `readiness` were changed, as the brief said.

### The state before / after (the installer's `--state`, fresh copies of the live database)

- **BEFORE (the OLD files, 08:05:38):** `_reexport_due(2026-10-18) = (False, '2026-10-18 09:35:24')`; `readiness` warnings: the sale sentence and *"Purchases are 2 days behind today …"*; `start_capture_lines`: none; salts: 0 open, 7 on tab 2. **As the NEW files read the same copy, and AFTER (the live files, 08:05:58):** `_reexport_due(2026-10-18) = (True, '2026-10-18 09:35:24')`, the day open, step 4 ok/ok; the S603 Needs-you lines none (the clock 08:05 < 09:37:53); `readiness` warnings: the sale sentence and *"No purchase export has been taken since the closing stock of 18-10-2026 was captured (19-10 09:37); …"*; `start_capture_lines`: *"Closing stock printed 18-10 09:37 waits for a purchase export taken after it (newest: bill-wise 18-10 09:25, item-wise 18-10 09:27)"*; the duty (0, None); salts 0 open, 0 on tab 2. The 7 other Needs-you lines identical before and after.
- **The capture rows:** eight within LATE_DAYS, verdicts unchanged throughout; 6d718060 `pending / pur_short`. Its `checked_at` moves on every `--state` read on both sides (08:05:45 / 08:05:51 / 08:06:04) because the state look also runs `needs_you_lines`, which reaches `amir_stage`'s proof judge through the day's writable Ctx (R2-B2, by design — the "moved by the reads above" flag in the STATE output counts that read too). The walk's control 6/7 isolate this kit's two reads: `readiness()`, `_r_stock()` and `start_capture_lines()` move nothing on NEW.

### Backups, restarts, lock

- `finance.db.bak_S603_20261020_080318` (40,894,464 bytes, the backup API, mode 600); `amir_day.py.bak_S603_3af992d9`, `stock_app.py.bak_S603_4f73d0b0`, `stock_watch.py.bak_S603_299c3ef7`, `amir_salts.py.bak_S603_d8d9ba77` beside the files.
- `clinic-finance` restarted once at 08:05:53 IST (`ActiveEnterTimestamp` read back). Nothing else restarted. `/root/deploy/_off/DOCTOR_AUTO_OFF` absent; the installer's `/tmp/s603_inst_*` scratch removed on exit.
- The build lock `/root/deploy/.claude_code_build.lock` taken 08:03:18 by S603; released after the publish (below) with `rm -f …/owner; rmdir …`.
- **After the publish:** <<AFTER_PUB>>

### Not done, decisions made, and findings outside the brief

- **Not done:** nothing of the brief was left out. The clone's DUTY_MAP.json / .md reach v16 by the publish and the clone's pull (the installer only pins and reads them; the after-publish check below confirms the Needs-you duty check reads v16).
- **Decided (the brief left it open or the box differed):**
  - **The per-family newest stamps are printed as `dd-mm hh:mm`** (through `stock_figure.stamp_iso`), not as Marg's raw `YYYYMMDD-HHMMSS` token — charter 11 (a moment on a screen in the owner's shape); the brief's sentence is otherwise verbatim.
  - **F-953's "judgeable pending capture":** the walk uses the real pending row (6d718060) instead of making a synthetic judgeable one — the judge re-checks a pending row on every read (`checked_at` moves), which is the write F-953 names; on OLD it moved under `readiness()` (08:03:47 → 08:03:48), on NEW nothing moved. A synthetic judgeable capture would need hundreds of `sp_close_name` rows on a spine copy; not built.
  - **Control 7 runs on a spine copy with any purchase export stamped after the capture removed** (today: none to remove) so the control stays deterministic after Amir's next export covers the row by clause (b); the live reading is printed by `--state`.
  - **Control 5's subject** is the first batch whose every item is proven on the copy (1|ISSUE|1, ECONORM CAP); the item's rows are removed from every capture after the vouchers (not only the newest) — removing them from the newest alone leaves the earlier tries proving it.
  - **The two helpers that read the per-family newest stamps** (`stock_app._s603_newest_stamps`, `stock_watch._s603_newest`) repeat clause (b)'s two queries of `stock_figure.purchase_cover_how` (stock_watch cannot import stock_app; stock_figure is not in this kit) — named under Charter below for a later kit to give stock_figure one door.
  - `S598`'s walk is red on today's data on both sides (as at S602); the installer gates on its check lines being identical (62) rather than green.
- **Finding — the 1-Oct ITEMWISE pair reads `none` today** ("abhi nikaali nahi gayi"), not `bad`: every 1-Oct ITEMWISE row is superseded (R1-C6), and a past day read without a step-3 moment falls in the `none` branch. Harmless (a past day), consistent with R1-B2's lesson: a past day's pair is never read from the live set — the owner's line reads the receipts.
- **Finding — the spine's first build of the day is at 08:00** (`*/10 8-23`): an installer run in the first minute of the window meets a spine 8 hours old and refuses (charter 1b, correctly). Worth a line in the next brief's window note (install from 08:02).
- **Finding — `deploy_kits/S444_STAFF_SAFE/__pycache__` exists in the working copy** (git-ignored, from an earlier run); not this kit's file, left alone and named.
- **Permissions:** nothing asked or refused on the server. On this PC: one PowerShell line with `Remove-Item -Recurse -Force` (to drop a `__pycache__` the local compile made) was refused by the permission list — not worked around: the compile now points `PYTHONPYCACHEPREFIX` at the session scratchpad. `git` is not on PowerShell's PATH (GitHub Desktop's copy was used for `diff --no-index`; PUBLISH_ALL finds its own). A memory note was not attempted (the memory folder was refused at S602).

### Charter

- **One fact, one place:** the export fact = the server's receipts (`mi_file.received_at` / `purchase_export.received_at`) after the visit's first bill-entry tap, read in `_export_fact` only, by the band and by the owner's line; purchase cover = `stock_figure.purchase_cover_how` (S587), now read by `readiness` and `start_capture_lines` instead of their own date arithmetic; a read path says `read_only=True` (F-943's rule, now F-953's); the waiting reason = `_s488_why` → `_s488_ending` (one wording, the owner's); the salt task's exact string = `_exact` through `SECTIONS`.
- **Rule (c) of 05-Oct on the owner's side:** since-when and for-what on his lines; the 48 h escalation for the export wait and the owed re-export. On Amir's side only the "do this" line gains the moment (D708 kept).
- **Seen, not touched (named):** `stock_gate` / `purchase_due` / the frozen feed (4b-2; the "COUNT GATE" sentence keeps its calendar words); `visit_cover`'s no-tap rule (R1-B3); the sale "days behind" sentence; `export_watch`'s 1st-of-month rule; the words sweep of Kit 3; Amir's stage line (D708); the day's pages' writable Ctx (R2-B2: `_s577_record` 2316 — a GET path that still judges — `_voucher_guard_base`, `amir_stage`, `_s488_why`, `_s524_table`); the two stamp helpers above.
- **Retired:** `_s488_purchase_reach` (dead), the purchase "days behind" sentence, the pending capture's day count, the step-3 tap as a mark. **Left for later:** one `newest_stamps()` door in stock_figure (the two helpers); `_s577_record`'s writable Ctx on a GET path.
- **Behaviour changes (rule 4, 7):** the band stays until a file lands and never shows before the visit's first file; step 4 prefers a covering export; one owner line after 48 h; three owner sentences reworded by a fact; the drift page's two reads never judge; an answered salt becomes a tickable line on Amir's sheet; one duty row. No figure, no order, no verdict changes (the page dumps byte-equal; `readiness`'s other keys equal; the capture verdicts unchanged).
- **Dependency state at install:** S587, S598, S602 live (the FROM pins); the 18-10 09:37 capture `pending / pur_short`; 0 open salt tasks; the spine 13/13 and 2 min old; `amir.proof_wait_hours` 48.
