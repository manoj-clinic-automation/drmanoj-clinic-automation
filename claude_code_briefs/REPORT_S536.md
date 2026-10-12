# REPORT S536 — Amir's board drops the reception-tap line; "ordering can start" waits for stage C (kit S536_AMIR_BOARD_D712)

**For the owner (12-Oct-2026, installed 06:36 IST — read from the installer's log):**

1. Amir's board, section 4 *Baaki kaam*, no longer shows *"KNEE IMMOBILIZER UNISON L — bill entry baaki: YUVIKA SURGICALS 01-10-2026 — maal aa gaya, Marg mein bill abhi nahi"*. This morning it reads *"Aaj kuch nahi — sab upar hai."*
2. The Yuvika arrival stays on **your** Needs-you only: *"Goods tapped as arrived on 01-10 from YUVIKA SURGICALS: no bill scanned, nothing in Marg (11 days)"*.
3. Your Needs-you no longer says *"live orthotic ordering can start"* while voucher 29 holds stage A open. It will appear on its own once the count passes the orthotic stages, dated that day, for two days.
4. Tested on copies first, then installed and read back on the live box; healthz 200.

---

## For the chat

### What ran, when (clock times read from `/root/deploy/kits/S536_install.log` and the box)
- Live pins read at 06:21 IST (all three at the brief's FROM). Built in `_scratch\S536_AMIR_BOARD_D712\` (`make_s536.py --print-to` against copies of the live files) → walk on the server in DRY from `/tmp/s536kit` (two DRY runs: the first was red on one control only — see *Decisions* 1; the second **WALK_S536 GREEN (38 checks)**) → **published** (PUBLISH_ALL, origin HEAD af9ec23; it also carried the brief file itself) → kit folder copied by scp to `/root/deploy/kits/S536_AMIR_BOARD_D712/` (SUMS.md5 7/7 OK) → installed → this report → published again.
- Build lock taken **06:34:45** IST by `S536_AMIR_BOARD_D712` (none held before); `clinic-finance` restarted once at **06:36:10**; installer finished `S536_AMIR_BOARD_D712: DONE`, log written **06:36:34**.
- `/root/deploy/repo` was **not pulled** (the brief). The clone's DUTY_MAP.json read 69b8f56b before and after (v11, no duty moves).

### Live files FROM → TO (md5 read back on the box after placing, 06:36:51)
| file | FROM | TO (read back) |
|---|---|---|
| `/root/finance/stock_app.py` | c626a46acf371b3a767756dc35743d57 | **8d55637c3ab59a323cff1a0efb021527** |
| `/root/finance/stock_amir.html` | 8dd65e64aa2315da6c74909fe50c31c7 | **72034c2e1be4ce1ff4b357841bc28bb9** |
| `/root/finance/amir_day.py` | 262b0b814ec2b840012cd1988e420097 | **73882a8391fde24f31e07b0191c5bd89** |

Every placed file byte-identical to the walk's NEW copy (`cmp`). Must-not-move (stock_watch c960f6c8, purchase_app 147201dd, stockmatch 10e30d28, item_alias, stock_hub.html, qty_words, sanjeevni_approvals, aaj_seed, aaj_kaam, owner_console, amir_salts, reports_tile, finance_approvals.html, finance_app, portal.py, tile_grants.json, spine_build, spine_read, marg_take) and the crontab: unchanged across the install. Greps on the placed bytes: `stock_app.py` bill_pending 0 · `stock_amir.html` bill_pending 0, "bill entry baaki" 0.

### The edits
- **2.1 `stock_app._amir_board_light`:** `rest = dict(plan=None, fixes=[])` and `rest = dict(plan=W.get("plan"), fixes=[…])` (the two-line form anchored together, R1-1); one comment line says the arrival is the owner's Needs-you line. Nothing else moved.
- **2.2 `stock_amir.html`:** restCard's arrival line removed whole; the header comment's section 4 reworded (R1-2). The rest of restCard is the old function less that one line (walk-checked).
- **2.3 `amir_day.needs_you_lines`:** the line only at stage C / done; moment = `MIN(at)` of the root's stage-C release, else `B.verified_at`; shown while ≤ 2 days; text unchanged; its own try (R1-3); read-only.

### Gates at install (charter 1b)
Spine passed 13/13 (last success 2026-10-11T23:50:41, built after the collector's newest take); the collector's last run 4 min before (0 failed), newest take 19 h before.

### The walk (`walk_s536.py`; scratch copies; NEW = the three built files, OLD = the box as it was; signed in through a walk-only portal secret and user store)
**WALK_S536 GREEN (38 checks), 8 controls red on the old files.**
- **4 greps:** NEW `stock_amir.html` bill_pending / "bill entry baaki" / "maal aa gaya" 0/0/0 — **RED:** OLD 1/1/1. NEW `stock_app.py` bill_pending 0 — **RED:** OLD on 2 lines (3 occurrences). New amir_day writes no stage event and still reads the arrival for the owner's D712 line. Both new .py compile on the venv python (the installer compiled them on both pythons).
- **1 the board, D712** (a walk arrival `W536 VENDOR` tapped 5 days ago, no spine purchase): the board API as amir and as the owner 200, `rest` keys `['fixes','plan']` — **RED:** OLD payload carries `['KNEE IMMOBILIZER UNISON L', 'W536 ITEM']` for both logins. The page as amir has no arrival loop and no "maal aa gaya" — **RED:** the OLD page loops `W.bill_pending` and the payload holds the row, so it prints *"maal aa gaya, Marg mein bill abhi nahi"*. The owner's Needs-you still carries *"Goods tapped as arrived on 07-10 from W536 VENDOR: no bill scanned, nothing in Marg (5 days)"*.
- **2 the ordering line** (each case on its own copy; made-up roots 9536001–9536005 are the newest count_id, so the root amir_stage and amir_day read):
  - (a) the install-day copy: count #1 stage A, 7 of 8, B verified 2026-10-12T05:49:01 → no line — **RED:** OLD prints *"… ordering can start (count #1, 12-10)"*. (a′) a made-up root at stage A (one orthotic voucher open after an A-verified, B an hour ago) → no line — **RED:** OLD prints it.
  - (b) orthotics entered and proven, B verified yesterday → no release before; the first read reaches C, writes the release (12-10 06:3x) and the line reads *"(count #9536002, 12-10)"* — the OLD prints it dated B's day (11-10). R1-3: a fault injected into the line's own query drops that line only (8 of 9 lines, the other 8 identical).
  - (c) the same copy, the earliest release back-dated three days → no line; asserted on `MIN(at)` = the back-dated moment — **RED:** OLD still prints it (B yesterday).
  - (d) no medicine batch → stage done, no release row, the line from `B.verified_at`; with B three days back → no line (the accepted edge, R1-6).
  - (b′) a root with no orthotic batch at all (no stand-in, the real path) → C on the first read, release written, the line dated it.
  - *The made-up roots' orthotic proof is a walk stand-in that answers "done" once every orthotic batch is entered — this walk tests amir_day's line, not the spine proof (S524/S528 walked that). The live root and (b′) run the real path.*
- **3 not broken:** the light board JSON as amir and as the owner equal old vs new on the same copy, the dropped key aside (stamps dropped); the board page 200 as amir and the owner (sections, `#rest`, the Sunday buttons' code); restCard otherwise unchanged; Needs-you lines carry `cls/target/text` both sides; `stock_watch.amir_view` still returns `bill_pending` with the walk's arrival; the hub API and page 200; Amir's steps 1–7 200.
- **Weight:** the board payload as amir 5,891 bytes (old 6,077), as the owner 32,318 (old 32,504). Time as amir 4,673 ms new / 4,730 ms old — the first board read of a fresh process builds the stage's report (the same in the old file; S533 saw the same ~4.4 s); the owner's second read 1,072 / 1,082 ms.

### The install-day state (charter 7), printed by the installer on scratch copies of the live database
- **Before** (old files): count #1 stage A, 7 of 8 entered, 1 open; renames 23 of 23, B verified 2026-10-12T05:49:01; no stage-C release. Board section 4 (rest keys `bill_pending, fixes, plan`): *"KNEE IMMOBILIZER UNISON L -- bill entry baaki: YUVIKA SURGICALS 01-10-2026 — maal aa gaya, Marg mein bill abhi nahi"*. Needs-you: *Count #1: Stage A: 7 of 8 entered* · *Orthotics verified and renamed -- live orthotic ordering can start (count #1, 12-10)* · *Goods tapped as arrived on 01-10 from YUVIKA SURGICALS … (11 days)*.
- **After** (new files): the same stage. Board section 4 (rest keys `fixes, plan`): *"Aaj kuch nahi — sab upar hai."* Needs-you: *Count #1: Stage A: 7 of 8 entered* · *Goods tapped as arrived on 01-10 from YUVIKA SURGICALS … (11 days)*. Voucher 29 had not been entered — R1-4's other branch did not arise.
- **Read-back** (after the restart, the live board API through a walk-only portal session — the API records no board visit): as amir 200, 5,891 bytes, rest `['fixes','plan']`, *Aaj kuch nahi — sab upar hai.*; as the owner 200, the same; owner Needs-you 200, 21 lines, the two above. **READ_BACK OK.**

### Backups, restart
`/root/finance/stock_app.py.bak_S536_c626a46a`, `stock_amir.html.bak_S536_8dd65e64`, `amir_day.py.bak_S536_262b0b81` (read back = FROM); `/root/finance/finance.db.bak_S536_20261012_063445` (backup API, 35,917,824 bytes; no data was changed — kept by rule). Restarted `clinic-finance` only, once (06:36:10).

### Charter
- **Retired:** the board's arrival row (restCard's loop) and the `bill_pending` key of the board payload (`_amir_board_light`), for every login. F-864's last staff place.
- **Left for later / seen, not touched:** `stock_watch.py`'s three places that still call the arrival a line on Amir's board — the settings hint (101), the `bill_pending_lines` docstring (862), the header (22–23) (R1-1); `_amir_board_light` still calls `amir_view`, which computes `bill_pending` the board no longer sends (R1-11 — dead work on every board read, the spine queried per arrival); the release moment is the first read after the orthotics cleared, not the clearing itself (R1-7). The second line ("ordering can start") has no F-number.
- **Charter: left out** — nothing the brief ordered was left out.
- **Dependency state at install:** spine passed 13/13 (built 2026-10-11 23:50, after the newest take); collector alive (last run 4 min before, 0 failed).

### Decisions made by the builder (named)
1. The brief's grep control "the old `stock_app.py` has 2" counts **lines**: the old file has the word on 2 lines, 3 times (the two-line `rest` names it twice). The control asserts the 2 lines and prints the 3 occurrences. This was the first DRY run's only red.
2. The made-up roots' orthotic proof is a walk stand-in (see the walk); (b′), a root with no orthotic batch, proves the release path with no stand-in.
3. The installer's post-restart gate probes `/finance/stock/page/amir`, `/finance/amir` and `/finance/sanjeevni/api/needs-you` (all 302 to a plain curl, read before the install); the read-back uses the board's API, never its page (the page records a board visit, which would put a false "Amir opened his board" on your line d).
4. The permission list refused an `rm -rf` of the (not yet existing) kit folder on the server before the copy; the copy was made without it. Nothing else was refused.

### Seen, not touched (for the chat)
- The three `stock_watch.py` places and R1-11 above.
- The board's first read in a fresh process takes ~4.7 s as amir (the stage's report build) — over charter 14's 2 s on a cold process only; the same in the old file.
- The live stage shows A proof `None` while A is open (1 voucher open) — as designed (the proof is asked only once every orthotic voucher is entered).

### Undo
Put back the three `.bak_S536_<from8>` files, restart `clinic-finance`, healthz 200, read the md5s back. No data change to reverse.
