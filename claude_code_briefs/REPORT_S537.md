# REPORT S537_VOUCHER_GUARD — installed 12-Oct-2026 08:08 IST, green

**For the owner**
1. Voucher 29 (ANKLE BINDER BAMBOO L −1) is voided. Amir no longer sees it, and ANKLE BINDER BAMBOO L is marked settled for count #1, so it will not be raised again.
2. Darpan has one spot count at the top of his next list: ANKLE BINDER L BAMBOO (the new Marg name of BAMBOO L).
3. From now on, Amir is never given a voucher that would take an item below zero in Marg. Today that holds back one voucher: NORTIMER TAB −10 (STOCK ISSUE voucher 11), because Marg's 10-10 closing holds 3 tabs. It shows on your Needs-you as "not given to Amir". **It stays waiting until you decide it.** The screen to settle or void it from the hub is not built yet (left for later), so tell the chat what you decide.
4. The Yuvika knee-immobilizer line is gone from your Needs-you: that arrival is already tied to Yuvika bill 672.
5. The orthotic stage passed at once. Amir's first 12 medicine vouchers (STOCK ISSUE 1–10, 12, 13) are on his board now. Everything was checked on copies first, and the live pages answer correctly.

---

## For the chat

### Live files FROM → TO (md5 read back on the box after placing)
| file | FROM | TO (read back) |
|---|---|---|
| `/root/finance/stock_app.py` | 8d55637c3ab59a323cff1a0efb021527 | f58e09dbb273e8b1470aa7220da70015 |
| `/root/finance/stock_watch.py` | c960f6c890e3e83c58b88d8a7f219752 | 0e6a42c4c7ae51eb8f8a0869fce2d101 |
| `/root/finance/shelf_figure.py` | 9be5eb88d1b1fc1fdb03b906c88a4265 | 183c70fabb64ed1e5a43c645a225c560 |
| `/root/finance/stock_statement.py` | 1a4f6c9ecb2546dae954c0414074f406 | a90f3413427841b7daea76b7730b2896 |
| `/root/finance/loss_piles.py` | 202bfc4e3fd798501c6db95373c2a7d4 | 81ae481e4480a12fead3016515037214 |
| `claude_code_briefs/DUTY_MAP.json` (clone, after the pull) | 69b8f56b17da263b932426b87a7abc1c (v11) | f499dd1fb53cb9b23422154aac41596e (v12) |
| `claude_code_briefs/DUTY_MAP.md` (clone, after the pull) | 553398f3a21541e688d3f3c72e585748 | 7b921305c9767782f99d228bf3749206 |

All pins matched the brief at 07:34 IST (read). The five files were placed by rename and read back equal to their TO pins, byte-identical to the walk's NEW copies.
The repository's kit folder was byte-identical to the one that ran: `SUMS.md5` checked in `/root/deploy/repo` after the pull, which was publish commit 89e85b1.

### Install order (the brief's §5, as run; times read from the log and the rows)
gates → FROM pins + clone at v11 → spine passed 13/13 (last success 08:00:45), collector last ran 4 min before → build → compile on both pythons → walk GREEN → state BEFORE → backups → place → read-back → greps (stock_app `_void_sql(` 8 = the def + seven readers; shelf_figure 1; stock_statement 1; stock_watch billed_bill_no test 1; loss_piles `_voucher_lines(` 1) → `data_s537.py --schema-only` (both tables laid) → `git pull --ff-only` (DUTY_MAP v12 at its TO pin) → `data_s537.py` (committed) → ONE restart of `clinic-finance` at 08:08:09 → healthz 200 → the gated pages 302 → no journal error → state AFTER → live read-back OK → nothing else moved (the 20 must-not-move files, crontab) → healthz 200.

### The data step (live, `DATA_S537:` lines)
- 1: voucher found by its shape: count #1, round 6, ISSUE batch 1, one line ANKLE BINDER BAMBOO L −1, made by manoj at 2026-10-11T17:40:50. It was not entered, so it was **VOIDED**: `stock_voucher_void` row (1, 6, ISSUE, 1, manoj, at 2026-10-12T08:08:05). Its number stays STOCK ISSUE voucher 29; the numbering never shifts.
- 2: ANKLE BINDER BAMBOO L **SETTLED** for count #1 (`stock_voucher_settle`, manoj, 08:08:05). Steps 1 and 2 committed together.
- 3: `stock_watch.ask` → "ANKLE BINDER L BAMBOO goes at the head of Darpan's next morning list." `ask` names the item as the spine does: Marg's renamed L (`marg_item_rename`: BAMBOO L → L BAMBOO). The row is by "S537 owner 12-Oct", at 08:08:05, still open.
- 4 (read on a scratch copy): orthotic pending 0, orthotic held 0 (L is settled), stage C, A 7 of 7 entered, open 0, pending 0, proof done. The first lot is 12; C held = NORTIMER TAB (voucher 11). Round 6 is no longer a batch.
- Rows: void 0 → 1, settle 0 → 1, stock_watch_ask 1 → 2, stock_stage_event 5 → 5.

### The install-day state (charter 7), printed by the installer
- **BEFORE** (old files): stage A; A 7 of 8 entered, open 1. The board as amir showed 8 vouchers, voucher 29 among them. His line: "Orthotic ke voucher: 1 baaki — board kholiye". Needs-you: "Count #1: Stage A: 7 of 8 entered" and the YUVIKA D712 line. Spot list head: TYRO BR.
- **AFTER** (new files): stage C; A 7 of 7, open 0, pending 0, proof done; C released 12 of 30, today 12, held NORTIMER TAB (11). The board as amir shows 12 vouchers: STOCK ISSUE 1–10, 12, 13. His line: "Dawa ke voucher: 12 — board kholiye". Needs-you:
  - "Count #1: Stage C: 0 of 30 entered · 12 released · 0 verified"
  - "Count #1: NORTIMER TAB (STOCK ISSUE voucher 11) — the count-day sum asks -1 strip; Marg's closing of 10-10 holds 3 tabs: not given to Amir"
  - S536's "Orthotics verified and renamed -- live orthotic ordering can start (count #1, 12-10)"
  - No YUVIKA line.
  
  Spot list: TYRO BR, ANKLE BINDER L BAMBOO.
- **Live read-back** (walk-only portal session): board as amir 200, 11,180 bytes, stage C, 12 vouchers, round 6 not shown. Board as the owner 200, 36,302 bytes, 37 vouchers. Needs-you 200, 22 lines. READ_BACK OK.
- **The live first stage-C release** is at 2026-10-12T08:08:28, written by that read-back's own board read. It covers 12 keys: 1|ISSUE|1, 2|ISSUE|1–9, 2|ISSUE|11, 2|ISSUE|12. **2|ISSUE|10 was not released** (read on the live rows). The duty map v12 `amir.count_vouchers` reads 12, since 08:08:28.

### The walk (`walk_s537.py`, on the box, in the installer): **WALK_S537 GREEN (76 checks)**
The first DRY gave 73 of 76. The three reds were all in the walk itself, and the kit was re-packed before publishing. Two were the grep classifier: it missed shelf_figure's filter, which is built two lines above its SQL. One was the spot-count check: it looked the ask up by the old name, but `ask` stores the spine's name. The second DRY and the real run were both 76/76.

Every named control went **RED on the old files**:
- 6 OLD: no voucher-line site honours a void (0 filtered of 13); stock_watch has no billed_bill_no test; the v11 map does not name the void table
- 1 OLD: `_voucher_state` still lists the voided made-up round 7; `_s446_batches` and the stage still carry it (A total 9 vs 8); the board shows it as amir and as the owner; its round's xlsx is served (200); the statement names it; entering it is accepted (200 "Likh liya …")
- 2 OLD: the count-day rule raises ANKLE BINDER BAMBOO L −1 again (the copy before round 6)
- 3 OLD: (a), (c), (d) offered; `_voucher_make` freezes the line that should be held
- 3c4 OLD: the stage-C release hands round 2 ISSUE batch 10 to Amir; "Aur voucher kholiye" releases it
- 4 OLD: an arrival tied to its bill is listed

NEW, in short:
- **Void:** voided through the door, absent from `_voucher_state`, `_s446_batches`, the stage/proof, `amir_vouchers_open` (one fewer), the board (amir, owner), the xlsx (404) and the statement. `_voucher_seq` is unchanged for every batch. v12 SQL 2 → 1 while v11 stays 2. `aaj_kaam.build_all` with v12 2 → 1. Entering it → 400 "Yeh voucher ab nahi hai.". Voiding an entered batch → refused; a missing batch → refused; a second void → already.
- **Settle:** before the settle row, L is held (Marg 0); with it, nothing.
- **Guard:**
  - (a) held
  - (b) offered
  - (c) held, the unentered frozen −1 counted
  - (c2) RECEIVE +7 on −34 offered
  - (c3) the newest closing by real date (2026-10-10), not `MAX(as_on)` (30-09-2026); a partial newer day reads "not readable", never an older figure
  - (c4) on the install-day copy: stage C; the first lot skips batch 10 and the next batch takes its place; C held = exactly batch 10 by key (NORTIMER TAB −10, Marg 3, voucher 11); over EVERY medicine batch the guard fails exactly that one; the owner line names voucher 11; `_s452_release` never releases it; the board's "more" count is 0
  - (d) two names on one 20-letter key, L held
  - (e) no closing row → offered, one summary line
  - the guard writes nothing (0 row changes)
  - `_voucher_make` froze only B, R, E
- **Arrival:** tied → not listed and no D712 line; untied → listed and the line. The Yuvika arrival is not listed on the install-day copy.
- **Data step on copies:**
  - `--dry` writes nothing (row counts, table list) and skips step 3
  - `--schema-only` lays the tables
  - the real run commits; a second run is idempotent
  - voucher 29 entered → STOP, exit 2, nothing written
  - an extra round 7 → STOP
  - the OLD folder is refused
- **Not broken:** after the data step, A open 0 and pending 0. Board 200 as amir and owner, round 6 absent, payload under 100 KB (11,180 / 36,302 bytes). Hub api/page 200. Needs-you 200, shapes intact. Amir's steps 1–7 200. xlsx: round 6 404, round 5 200, Amir's board xlsx 200. `loss_piles.receive_close` twice: the second writes nothing. `selftest_spine.py` SELFTEST OK (45 checks). `py_compile` on both pythons.

**Staff-eye check (CLAUDE.md "Every duty has a door" 2), run after the install from `_scratch` on a backup-API copy with its own portal secret and user store.** The kit's walk opened Amir's steps 1–7 (200) but did **not** assert the door marker; that is a gap in the walk, named here. The separate check, as amir with the live map v12:
- the home shows the "Amir ka kaam" tile
- `amir.count_vouchers` is due 12, and its door `/finance/amir/step/6` shows "Marg sudhar"
- every other amir duty is due 0 and its tile is on the home
- STAFF_EYE OK

### The voucher-line sites and their decision (§2.1; the walk prints them)
- **Filtered (`_void_sql`):** `_voucher_frozen`, the guard's own read (`_voucher_guard_base`), `_voucher_state`, the entered door, `_voucher_numbers`, `amir_vouchers_open`, `_s446_batches` (stock_app); `filed_vouchers` (shelf_figure, through `vf`); the statement's rounds (stock_statement).
- **Not filtered, by design:**
  - `_voucher_seq` (numbers never shift)
  - `_voucher_make`'s next round number (a voided number is never reused)
  - `_report_cached`'s stamp
  - `_s446_root`
  - `_voucher_void`'s own existence check
  - aaj_seed 470 (the parent's SQL, left for later by the brief)
- `/root/portal` has no site.

### Backups and services
- `/root/finance/{stock_app,stock_watch,shelf_figure,stock_statement,loss_piles}.py.bak_S537_<from8>` (8d55637c, c960f6c8, 9be5eb88, 1a4f6c9e, 202bfc4e).
- `/root/finance/finance.db.bak_S537_20261012_080518` (35,921,920 bytes, backup API).
- `clinic-finance` restarted once (08:08:09). No other service touched.
- The build lock was taken 08:05:18 and held until this report; removed after it.

### Calls made inside the brief (written here, per the rulebook)
- **"Aur voucher kholiye" gets the same guard.** `_s452_release` runs the same test as `amir_stage`'s release. Without it, a second door would hand the held batch to Amir (charter 6, 13). `C["unreleased"]` leaves held batches out, so the board's "more" count never promises one.
- **The Hindi refusal covers a missing batch too.** "Yeh voucher ab nahi hai." answers both a voided and a non-existent batch; it is the same branch.
- **The void has a door function but no route.** `_voucher_void` refuses an entered or missing batch, and the data step is its one caller. The owner's door is left for later, per the brief.
- **One sum per held line.** A held line's owner line quotes the count-day sum and Marg's closing figure, per the brief. When the hold comes from unentered vouchers already made (case c), the line does not show that sum.
- **The read-back released the first lot.** The live first stage-C lot was released by the installer's own read-back, not by Amir's visit. Any first read would have done the same, as in S536.

### Charter
- **Retired:** the hand-edit way of voiding a voucher (the brief's line 141 stays as history); the count-day-only pending rule (a settled item and a line that would take Marg below zero are no longer raised).
- **Left for later:**
  - an owner door to settle / void from the hub. **The NORTIMER batch (voucher 11) needs it, or a brief, to move.** Stage C cannot reach "done" while it is held.
  - the "never past the shelf figure" half of the guard, and the family-key miss behind the Yuvika line (rung 4b)
  - the guard moves with `stock_snapshot` when rung 4b retires it (F-862)
  - stockmatch c2's reading of a held orthotic line as done (275, R1-9c)
  - the aaj_seed voucher SQL at 470 (the parent's)
- **Left out:** nothing.
- **Seen, not touched:**
  - **Renamed items will read "not readable".** The 23 renames are verified, so Marg's next closings print the new names (e.g. ANKLE BINDER L BAMBOO), while the count's lines carry the old ones. Those old names will read "not readable" to the guard: offered, and counted in the owner's summary line. The identity read-back belongs to rung 4b (charter 12).
  - **Any stock_app call can commit an open transaction.** `_voucher_ensure` uses `executescript`, which commits whatever transaction is open; for example inside `_voucher_make`'s `BEGIN IMMEDIATE`, via `_voucher_pending → _voucher_frozen`. This is old behaviour. For the same reason, `data_s537.py --dry` lays its tables inside its own transaction from `VOUCHER_S537_SCHEMA` and calls no stock_app function before it.
  - **Owner count includes the held batch.** "Stage C: 0 of 30 entered" counts the held batch in the 30.
  - **A few-second window at install.** It lies between placing the files and laying the tables (the void row reads 08:08:05). A job that read `_void_sql` in that window would have met a missing table. The service itself was not restarted until 08:08:09.
- **The dependency's state at install:** the spine passed 13/13, last success 2026-10-12T08:00:45+05:30. The collector last ran 4 min before, with 0 failed; its newest take was 21 h old, inside the 72 h rule.

### Not done
Nothing in the brief is left undone. No command was refused.
