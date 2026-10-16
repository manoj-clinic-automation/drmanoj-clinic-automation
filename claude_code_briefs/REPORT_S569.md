# REPORT_S569 — S569_PROOF_REACH_AND_TWO_LINES (16-Oct-2026)

**For Dr Manoj (plain English):**
- **Why the stock check of Amir's 6-Sep vouchers says "waiting":** nothing is broken on the server — it holds the 15-10 sale report
  and the 15-10 closing. Two things hold it back: (1) the check only trusts a sale report taken *after* the closing, and this morning
  the sale report came at 05:10, seven minutes *before* the closing (05:17); (2) no purchase report has come since 15-10, 09:11.
- **Fixed?** No. The first needs a small program change and the second needs the next purchase report from Marg. Rerunning the
  stock data build would not help, so nothing was changed. The fix is written below for the chat.
- **What the check will find:** a trial run on a copy shows KT ROS DT and VINBACTUM DS did not move in Marg, as the chat found. It also
  shows two more lines that may be wrong: FOLITRAX 15 MG TAB (voucher 8) and OSTOVAXL DM (voucher 6). Those two may still clear when the
  purchases come in. This is not yet the system's verdict.
- **Amir's card:** the two jobs are now on it, under *Ek baar ke kaam*, each with a *Kar diya* button: "KT ROS DT — Marg mein STOCK ISSUE
  kijiye: 6 patte + 11 goli" and "VINBACTUM DS — Marg mein STOCK ISSUE kijiye: 25 nag". Nothing else on his card changed. Tested first on
  a copy of the database, then added to the live one after a backup.

---

## Part A — why the proof has no figure

### A1. `spine_read.py status` (run 10:48 IST on the box, whole output)
```
spine built 2026-10-16T10:40 · gate 13/13 blocking checks green · stock = Marg at 2026-10-15 EXCEPT 189 item(s): ACILOC 300 -62, AKLAVE 1000 -10, ALCOXIB 120 +197, ANKLE BINDER BAMBOO -4, ANKLE BINDER L TYNOR +2, ANKLE BINDER M TYNOR +1 · pending closings: none
```
`spine_state.json`: `at 2026-10-16T10:40:53+05:30, gate 13/13, passed true, failed [], last_success 2026-10-16T10:40:53, last_failure
2026-10-15T10:10:48` (yesterday's; `spine.db.failed` 15-10 10:10 is that one). The gate is **13/13 blocking** (the brief asked "14/14?";
this build version `S524.1` has 13 blocking checks). Re-read at 10:57: built 10:50, 13/13 green.

### A2. The build's runs (cron `*/10 8-23`, `spine_evidence.py && spine_build.py`, log `/root/finance/spine/spine.log`)
Every run from 08:00 to 10:50 IST on 16-Oct finished `SPINE BUILT AND SWAPPED: spine.db`, all gates ok; `spine_evidence`: "listed 282,
read 0, failed 0, store now 282 readings" (nothing new to read — both 05:1x files had already been read). No run failed, no lock, no cap.
(The cron starts at 08:00, so there were no runs between 05:00 and 08:00. The first run at 08:00 read the files.)

**The spine holds the 15-10 files:**
| file | md5 (mi_file) | received | in the spine (`sp_export`) |
|---|---|---|---|
| SALE_BILLWISE_DETAIL 15-10 | `e7d68e2c2c344e01db17d3491f41b4a5` | 2026-10-16T05:11:41 (VERIFIED, 64 lines) | yes, ok=1, stamp `20261016-051010` |
| STOCK_CLOSING_TOTALS 15-10 | `22a035ab6a79579591a016fd6ab1d4fe` | 2026-10-16T05:17:03 (VERIFIED) | yes, ok=1, stamp `20261016-051700`, in `sp_close` as 2026-10-15 |

### A3. The reach as `stock_app` reads it (`_s524_reach(_s524_spine())`, in-process on backup-API copies; `stock_app.py f58e09db…`)
```
reach: last_sale 2026-10-15  sale_stamp 20261016-051010 | last_pur 2026-10-15  pur_stamp 20261015-091029
       (PURCHASE_BILLWISE 2026-10-01..15 @ 20261015-091029, PURCHASE_ITEMWISE 2026-10-01..15 @ 20261015-091122)
closings after the vouchers (last voucher 2026-10-15T10:00:49), clean ones:
  as_on 2026-10-15  stamp 20261016-051700  end_day 2026-10-15  _s524_tryable -> (False, 'sale')
(earlier: 10-10, 12-10, 13-10 -> (True, ''); the spine holds no 14-10 closing)
```

### A4. The cause
`_s524_tryable` (stock_app 8530–8540) requires `sale_stamp > closing.stamp` **and** `pur_stamp > closing.stamp`.
- **Sale side (what `no_figure` names):** the 15-10 sale report was captured at 05:10:10 on 16-Oct, the 15-10 closing at 05:17:00. Both
  are pre-09:00 captures of the same morning, and charter 11 places both at the end of 15-10, so they cover the same day. The rule
  compares only the two clock times, so it refuses. The same order happened on 14-Oct (sale 09:21:24, closing 09:23:21).
- **Purchase side (behind it):** the newest purchase exports were captured 15-10 09:10–09:11, *before* 15-10 ended. They really do not
  cover the day (purchases keyed later on 15-10 are not in them). This is a true "not yet" (charter 1b).

**The decision, by the brief's rule (§2.3):** neither (a) nor (b). The build ran and is green, and every file is read. The sale side
needs a code change. The purchase side is a real data reason, which only a new Marg purchase export can satisfy. **Nothing was changed,
and no runbook command was run.**

**F-new (for the chat to number) — the reach rule refuses a sale report taken in the same morning window as the closing.**
The morning order is: sale report first (~05:10), closing second (~05:17). With that order the newest closing is never "in reach"
except in the minutes between the next morning's sale report and the next closing. `wrong` is said only by the newest capture
(S528, F-851). So a lot whose items did not move stays `export`/waiting, and moves to `pending_reach` once an older closing is tried.
It reaches `wrong` only in that window.
**Smallest repair (stock_app only, one function):** in `_s524_tryable`, an export also covers a closing when its own capture, read by the
estate's one capture rule, stands for the end of a day at or after the closing's `end_day`:
`_s524_end_day(reach["last_sale"], _s524_stamp_iso(reach["sale_stamp"])) >= end_day` (and the same for the purchase pair), kept as an
**or** beside the existing stamp comparison. Walk it with the S524/S528 walks and a control on the old file.
What-if, in-process on the copy, never placed: with that repair alone, today's three lots read `export / why: pur_behind` ("waiting for
a purchase export that reaches that day (Amir)"). So the honest state today is "waiting for Amir's purchase export".

**F-new (words, for the chat) — the waiting sentence names the wrong closing time.** The hub says "Marg's closing of 15-10 arrived
15-10 10:11". 10:11:28 on 15-10 is a mid-day `push_snapshot` in `stock_feed` (as_on 15-10-2026). The closing the spine uses arrived
16-10 05:17:03. `_s488_first_push` takes the earliest Marg push of that printed day after the vouchers, including a mid-day capture that
`_s524_end_day` skips. The same sentence also says "made when its sale report lands — Shavez", but that report had landed at 05:11.

### A5. The verdict — `/finance/stock/api/pad/hub/1`, `proof` (read 10:5x and again 10:57 IST; the app's test client on backup-API copies of finance.db and spine.db, owner by header on the copy, not the owner's session)
```
proof.state 'wait'; stage 'C'
text "Stage C: lot 3 entered on 15-10-2026 — waiting: Marg's closing of 15-10 arrived 15-10 10:11; waiting for our own figure for that day (made when its sale report lands — Shavez; on a no-sale day, the empty report)"
C: total 30, entered 30, released 30, lots 3, verified 0, waiting_export 3, wrong 0
lot 1 (released 12-10 08:08, 12 vouchers): export · why no_figure · closing_day 15-10-2026 · closing_at 2026-10-15T10:11:28 · since 15-10 09:32:02
lot 2 (released 15-10 08:43, 12 vouchers): export · why no_figure · closing_day 15-10-2026 · closing_at 2026-10-15T10:11:28 · since 15-10 09:50:38
lot 3 (released 15-10 09:50, 6 vouchers):  export · why no_figure · closing_day 15-10-2026 · closing_at 2026-10-15T10:11:28 · since 15-10 10:00:49
rows [] · lines []
```
**What the system found:** no verdict. All three lots are waiting, with no wrong rows and nothing proven. So the expected
"KT ROS DT and VINBACTUM DS wrong, the other 168 proven" is **not** what the system says today.

**What-if only** (same copy, `_s524_tryable` swapped in-process to ignore the purchase side; this shows what the 15-10 closing would
give; it is not the system's verdict): state `now`, 4 voucher lines that do not agree, by Marg's closing of 15-10 (base: Marg's
closing of 13-10, the newest clean one before the first entry):
| voucher | item | need (the voucher) | Marg moved (net of the spine's sales/purchases) | Marg at 15-10 |
|---|---|---|---|---|
| 9 STOCK ISSUE | KT ROS DT | −101 (6 patte + 11 goli) | 0 | 430 (28 patte + 10 goli) |
| 18 STOCK ISSUE | VINBACTUM DS | −25 (25 nag) | 0 | 25 |
| 8 STOCK ISSUE | FOLITRAX 15 MG TAB | −6 (−1 patta + 1 goli) | 0 | 142 (13-10: 150; sales 14–15-10: −8) |
| 6 STOCK RECEIVE | OSTOVAXL DM | +21 (+2 patte + 1 goli) | +25 | 371 (13-10: 386; sales −40) |
The other voucher lines agree in that what-if. KT ROS DT and VINBACTUM DS match the chat's finding. **FOLITRAX and OSTOVAXL are two more
the chat did not name.** Each could still be a purchase keyed after 15-10 09:11, which the next purchase export would show (FOLITRAX +6
or OSTOVAXL +4 would square them). No card line was added for them because they are outside the brief; the chat decides.

**On the brief's note (§3):** the stage-C judgment tries the first closing after the vouchers **and the newest closing the reach covers**
(S520 / S524 `tries`), and an item is proven if either agrees. So once Amir enters the two lines today and a later closing (16-10 or
after) is within reach, the code as read would **prove** KT ROS DT and VINBACTUM DS on that newer closing. It would not keep naming them
wrong. This is from reading the code, not a run.

## Part B — the two lines on Amir's card

### B1. The voucher words, asserted before inserting (`/finance/stock/api/pad/amir/1` as amir, on a copy)
- voucher seq 9, `STOCK ISSUE — voucher 9`, KT ROS DT, `qty_hi '6 patte + 11 goli'`, change_sign −1 ✔
- voucher seq 18, `STOCK ISSUE — voucher 18`, VINBACTUM DS, `qty_hi '25 nag'`, change_sign −1 ✔

### B2. The walk (`add_jobs_s569.py walk`, box, 10:56:38–10:57:06 IST; the same file as in the kit, `md5sum -c SUMS.md5` OK)
Backup-API copies of finance.db and spine.db; a **walk-only portal** (a random secret and its own user store in the scratch folder;
the live `portal_config.py` and user store never copied); amir signs in through the portal and his cookie is the only auth the card sees.
```
GREEN W1  voucher 9 / 18 still say '6 patte + 11 goli' / '25 nag' (STOCK ISSUE)
GREEN W4  amir signs in as 'amir'; the tile 'Amir ka kaam' is on his home
GREEN W5  /finance/amir -> 303 -> /finance/amir/step/1 200
GREEN W6  the door /finance/amir/step/6: 'Ek baar ke kaam' shown
GREEN W7  'KT ROS DT — Marg mein STOCK ISSUE kijiye: 6 patte + 11 goli' / '6 Sep ki stock ginti · voucher 9 ki line' / Kar diya (tap:9)
GREEN W7  'VINBACTUM DS — Marg mein STOCK ISSUE kijiye: 25 nag' / '6 Sep ki stock ginti · voucher 18 ki line' / Kar diya (tap:10)
GREEN W8  DUTY_MAP amir.marg_jobs due_sql: n 0 -> 2
GREEN W9  nothing else on his card changed: 7 segments added (the header + 2 x line, sub-line, Kar diya), none removed
GREEN W9b /finance/amir: no other change
GREEN W2  two rows, the brief's shape;  GREEN W3  two job_added by system {"kit": "S569", "owner_word": "16-Oct 09:33"}
GREEN W10 a second run: ALREADY x2, rows and audits unchanged;  GREEN W11 no verdict / "check" / "chhoot" words (D708)
CONTROL (the same card checks on the card without the two rows = the old state): W6 RED, W7 RED, W7 RED, W8 RED -> RED as it must
WALK GREEN: 0 red; control ok
```
(The first walk run at 10:55:33–10:56:00 gave the same.)

### B3. Live (`add_jobs_s569.py live`, 10:57:12–10:57:25 IST, under the build lock)
```
backup: /root/finance/finance.db.bak_S569_20261016_105712 (38453248 bytes, integrity ok)
before: amir_job rows 8; DUTY_MAP amir.marg_jobs due [0, None]
row id 9  key 'fix:S569:KT ROS DT'    kind tap subject 'KT ROS DT'    created_at = show_from 2026-10-16 10:57:18 created_by S569
          text_hi 'KT ROS DT — Marg mein STOCK ISSUE kijiye: 6 patte + 11 goli' | sub_hi '6 Sep ki stock ginti · voucher 9 ki line'
row id 10 key 'fix:S569:VINBACTUM DS' kind tap subject 'VINBACTUM DS' created_at = show_from 2026-10-16 10:57:18 created_by S569
          text_hi 'VINBACTUM DS — Marg mein STOCK ISSUE kijiye: 25 nag' | sub_hi '6 Sep ki stock ginti · voucher 18 ki line'
audit 888 / 889  at 2026-10-16 10:57:18  who system  action job_added  detail {"kit": "S569", "owner_word": "16-Oct 09:33"}
after: amir_job rows 10; DUTY_MAP amir.marg_jobs due [2, '2026-10-16']
read-back (a copy taken after the insert), amir's door /finance/amir/step/6 200: 'Ek baar ke kaam', the two lines, each with 'Kar diya'
LIVE DONE
```
All other fields of the two rows are NULL. Afterwards: `/finance/healthz` 200; `stock_app.py f58e09dbb273e8b1470aa7220da70015` and
`amir_day.py 73882a8391fde24f31e07b0191c5bd89`, the same as at the open. **No `.py` changed, no service restarted.**
**The DUTY_MAP is not changed**: the duty is `amir.marg_jobs` ("Ek baar ke Marg ke kaam", tile *Amir ka kaam*, door
`/finance/amir/step/6`, marker *Ek baar ke kaam*). Its owner line names them after `amir.job_wait_days` (10) days.

## Charter
- Retired: nothing. Left for later: the two F-new above (code). Left out: nothing.
- Dependency state at install: spine `spine_state.json` passed, 13/13, built 10:40 and 10:50 IST; cron pass green all morning.
- Seen, not touched: Amir's four `category` jobs (ids 1–4, created 07-Oct) still have `show_from` NULL although the stage is C.
  `_s494_refresh` is meant to show them in stage B/C/done, but renders during this walk did not show them. Not investigated (outside the brief).

## Numbers, lock, scratch, gates
- Board `_numbers` (v451 → v452 with its PLANNED line): **not reachable from Claude Code** (a claude.ai artifact). **The chat should append
  S569's DONE line**: data only, amir_job ids 9 and 10, audit 888–889, backup `finance.db.bak_S569_20261016_105712`, live 16-Oct 10:57 IST.
- Build lock `/root/deploy/.claude_code_build.lock` taken 10:56:38 IST (owner S569). Released at 10:59:44 IST (read on the box) after
  this report was written and published, using `rm …/owner; rmdir …`. The first attempt, joined with `rm -rf` in one ssh line, was
  refused by the permission list, so the narrower command was used. After publishing, `/root/deploy/repo` pulled to `29fbcab`, and
  `md5sum -c SUMS.md5` there gave OK for every file.
- Box scratch removed: `/tmp/s569probe` (it held backup-API copies of the databases), `/tmp/s569kit`, `/tmp/s569walk`, `/tmp/s569live`.
- Kit `deploy_kits/S569_PROOF_REACH_AND_TWO_LINES/`: `add_jobs_s569.py f8963062…`, `README.md`, `KIT_ID.txt`, `SUMS.md5`.
