# REPORT — S484_SPINE_BILL_TIES (05-Oct-2026)

Brief: `claude_code_briefs/S484_SPINE_BILL_TIES.md` · kit `deploy_kits/S484_SPINE_BILL_TIES/` · faults F-734, F-735, F-736 repaired ·
F-737 recorded and measured, not repaired · no D-number. Built, walked, installed, published and read back by Claude Code on
manojz, 05-Oct-2026. Every clock time below is read (IST).

## For the owner

- **The spine is building again since 11:37 today** (it had been refused since about 08:10; its last good build was 08:00). Its own
  ten-minute job built it again by itself at 11:40. All 13 of its checks pass.
- **Two things had frozen it:** in one of this morning's purchase reports the date sat in the wrong column, so no line had a date;
  and on 01-Sep two different suppliers each have a bill numbered 160, which the spine could not tell apart. Both are mended, and
  the category list that also failed this morning reads clean now.
- Nothing changed on any screen. The finance service was restarted once (11:36) and is healthy. **One thing is left for the chat,
  not urgent:** a purchase report printed for one supplier only can still be mistaken for a whole one (see "F-737" below).

## For the chat

### 1 · Every pin, FROM → TO, read back on the box (11:40:49)

| file | FROM (read before the first edit) | TO (read back after placing) | backup beside it |
|---|---|---|---|
| `/root/finance/spine/spine_build.py` | `ce99bedf60194a84fe93455927a336e2` | `11f8acb05c46aeaa72e1771d5c89922c` | `.bak_S484_ce99bedf` (reads `ce99bedf…`) |
| `/root/finance/spine/marg_read.py` | `099d621315f3bf9297a9b4626a5caee5` | `96f565a8d138d9ce75c0ed228b471495` — S483's TO, as required | `.bak_S484_099d6213` (reads `099d6213…`) |
| `readings/de92f5d5185646d4de563e30d5464f6e.json` | `0af44311254ecad7603e243faff743f8` — ok True, **0 of 208** lines dated, read 08:10:58 | `279570f0fb8b1d89fa344f1e78a9fc8c` — ok True, **208 of 208** dated, written again 11:37:08 | `.bak_S484_0af44311` (reads `0af44311…`) |
| `readings/f62cc9e3d93c692f1795229be9e7cfe1.json` | `b054e6c826902234c0af98524de29450` — **ok False**, 3 failures, read 08:11:06 | `802b77174d8e963c859648d46f51e60a` — **ok True**, 341 items, `code {'OTHERS': 'D98'}`, written again 11:37:09 | `.bak_S484_b054e6c8` (reads `b054e6c8…`) |

Read only, md5 the same before and after: `spine_evidence.py` `0fcf6c6419d5a69d7314e152421a2aa7` · `spine_read.py`
`712a1e4ef827f6be4e8b23415c3ceb62` · `selftest_spine.py` `fc63d2c683a1970c58f60502302187a9` · `spine_rules.json`
`dd6c761665ce38fe4ec65d25b6102265` · `reports_tile.py` `ea15aacb…` · `finance_app.py` · the crontab.
`make_s484_reader.py` is S483's `make_s483.py` byte for byte (`5b9b19e0…`, `cmp` on the server); S483's folder matches its own
`SUMS.md5` — untouched.

**Data.** `finance.db.bak_S484_20261005_113547` (backup API, 31,313,920 bytes) — the kit writes no row. `spine.db` was never
written by the kit: the spine's own build swapped it in.

**Service.** `clinic-finance` restarted once, 11:36:17; `/finance/healthz` 200 after, at the end, and at 11:40:49;
`/finance/reports/aaj` 302 (the login gate, expected); no Traceback / "NOT mounted" in its journal since.

**The lock.** `/root/deploy/.claude_code_build.lock` taken 11:35:47 (owner `S484_SPINE_BILL_TIES`), released after this report
was written (11:42:32; healthz 200 and spine_state 13/13 passed at that moment).

**Publish.** `PUBLISH_ALL.bat`: the number gate clean, commit `6b26051`, origin HEAD verified. On the server `git pull --ff-only`
→ `6b26051`; `md5sum -c SUMS.md5` in the repository's kit: every file OK; `diff -r` against the copy that ran: no difference
(SUMS.md5 `703e8b4c0ed6c4cbaa9828c43a3cbdc6`). The owner's line of the brief's §4, run from the repository at 11:41, says
`ALREADY INSTALLED … healthz 200 … gate=13/13 passed=True`. This report went up with a second `PUBLISH_ALL.bat` run.

### 2 · The gate's line from `spine.log`

The installer ran the spine's job once, as the crontab spells it, under `flock -n /tmp/spine.lock` (first try):

```
  ok    PURCHASE_BILLITEMWISE    PURCHASE_BILLITEMWISE_DEFAULT__2026-09-01_to_2026-10-03__20261005-0759        (de92f5d5 -- the log cuts a name at 70 letters)
  ok    CATEGORY_WISE_ITEM_LIST  CATEGORY_WISE_ITEM_LIST_DEFAULT__2026-10-05__20261005-075955__f62cc9e3
spine_evidence 2026-10-05 11:37:09: listed 228, read 2 (0 not a report the spine uses), failed 0, store now 228 readings
  note every purchase bill: its lines re-add to the bill (net, within Rs 1)  -- 1 of 554 bills off: [(('KEDARPHA', '195', '2026-09-27'), 1771600, 1795900)]
SPINE BUILT AND SWAPPED: spine.db
```

`spine_state.json` after it: `at 2026-10-05T11:37:11+05:30 · gate 13/13 · passed True · failed []`. **The ten-minute job then built
it by itself:** `spine_evidence 2026-10-05 11:40:40 … SPINE BUILT AND SWAPPED: spine.db`; `spine_state.json`
`at 2026-10-05T11:40:42 · gate 13/13 · passed True · last_success_iso 2026-10-05T11:40:42 · last_failure_iso 2026-10-05T11:30:48`;
`spine.db` 2026-10-05 11:40:42, `sp_meta.build_version S484.1`. No FAIL line in either run.

### 3 · The figures the brief asks for

| | the 08:00 spine (S331.1) | the spine now (S484.1) |
|---|---|---|
| purchase lines of September (`sp_purchase_line`, 01–30 Sep) | **186** | **186** |
| purchase lines 01-Sep … 03-Oct, and whose | 208 — `d63bd4a8` 186 + `a5581a9b` 22 (SUPPLIER-grouped exports of 01-Oct and 04-Oct) | 208 — **all from `957b473f`**, the SUPPLIER-grouped sheet of 07:59:55; none from `de92f5d5` |
| the five lines of bill 160 of 01-Sep | 1 line ₹5,376.68 under one supplier, 4 lines ₹12,400.00 under the other | the same: 1 line ₹5,376.68 → the ₹5,377.00 bill; 4 lines ₹12,400.00 → the ₹12,400.00 bill |
| exports in `sp_export` | 212 | 228 |
| gate | 13/13 | 13/13 |

- **The re-add line** (*every purchase bill: its lines re-add to the bill*, non-blocking): **1 of 554 bills off** — bill 195 of
  27-Sep (supplier key `KEDARPHA`): the bill ₹17,716.00, its lines ₹17,959.00.
- **F-737, measured (walk §5), not mended.** On a scratch store with the one-supplier print `15b48bc5` stamped one second after
  the whole one (`20261005-075955` → `20261005-075956`), the new order makes it the authority for all 33 days of 01-Sep … 03-Oct:
  the build's purchase lines of that period fall **from 208 to 5**, the re-add line counts **87 of 554 bills off** — and **the gate
  still passes, 13/13, swapped** (on the scratch copy). A filtered purchase-lines print exported after the whole one would do
  this for real.
- **How the tie is used today.** In the true store the SUPPLIER-grouped sheet is the authority, so the five lines reach the spine
  through it. The tie itself is exercised twice in the true build — the same five lines in `de92f5d5` and in Marg's own BILL-grouped
  sheet of 06-Sep (`7aab826f`), both superseded — and the walk runs it end to end on a store without the two SUPPLIER sheets,
  where `de92f5d5` is the authority: gate passes, the five lines land under their two suppliers; the OLD file fails there.

### 4 · The two notes S483 left

- **For the next medical-PC kit (F-734's root):** in the text cutter (`marg_txt.page_to_sheet`, rule A — "a word belongs to the
  column in which it ends"), a line that is ONE token starting at column 0 belongs to column 0. The day's date of the BILL/ITEM
  WISE statement lands in column 1 today because it is wider than the `BILL` head; Marg's own Excel has it in column 0. The
  spine's reader now takes it wherever it sits.
- **Equal stamps from a one-second batch conversion:** S480's install converted the waiting texts in one second, so three
  purchase-lines sheets carry `20261005-075955`. The spine now gives equal stamps a stated order; the converter could still
  give each text its own capture second (the stamp is otherwise the only thing that says which export is newer).

### 5 · Calls made while building (the kit's README lists them too)

1. **`itertools` is imported inside `cut_shared_bill`**, not at the top of the file — five edit sites, "nothing else in the file".
2. **`tol` is handed over as a function of the bill** (`lambda b: 100 + 0.002 * abs(b["amount_p"])`): the tolerance depends on each
   bill's amount, so "the same expression, not a new constant" can only be passed as one.
3. **An untied line of a shared number records how many bills carry that number** (the pre-filter count, as the brief asks); the
   old code recorded how many survived the whole-sum test (0). Only the wording of the gate's detail changes.
4. **Section 3 also runs the tie end to end** on a scratch store without the two SUPPLIER sheets (see §3 above).
5. **Section 6 is two comparisons.** Sixteen readings arrived after the 08:00 build, not two (1 sale, 3 SUPPLIER/ITEM WISE,
   1 BILL/ITEM WISE, 1 bill-wise, 1 item list, 2 salt lists, 1 category list, 6 the spine does not use), so one diff could not
   show "nothing else moved". 6a builds the 08:00 evidence again (212 readings) with the OLD and the NEW file: the OLD gives the
   08:00 spine row for row in all 15 tables; the NEW gives the same rows as the OLD — on what the spine held at 08:00 the new
   rules move no row. 6b explains every added and removed row of the true new spine by the readings that arrived since.
6. **Gate details are compared by verdict, not wording, across builds:** two STOCK lines print a dictionary whose order changes
   from run to run, under the old file too (found when my first dry run failed 6a on wording alone; nothing was placed).
7. **The spine's job is run under `flock -n` and tried again every 15 s** while the ten-minute job holds the lock (it ran at the
   first try).
8. **No staff-eye walk section, no duty-map change:** no page, tile, duty or door changes.

### 6 · Not done, and why

- **F-737** — by the brief: recorded and measured, not mended.
- Nothing on manojz, the medical PC, the crontab, or any parent file. S483's kit folder is as it was published.

### 7 · The installer's run, whole (the walk is its lines between [5/12] and [6/12]; scratch copies; 11:35:47–11:37:12)

```
[1/12] kit gates green (SUMS, KIT_ID, the venv's flask, the database, the spine's files; spine_evidence.py, spine_read.py and selftest_spine.py at the brief's pins; no OFF switch)
[2/12] spine_build.py, marg_read.py and the two readings at their FROM pins
   built spine_build.py  ce99bedf -> 11f8acb0  (36809 bytes)
   built marg_read.py  099d6213 -> 96f565a8  (27934 bytes)
[3/12] live bytes + anchored edits give the two pinned files (marg_read.py comes out S483's 96f565a8, as the brief requires)
[4/12] compiles on /usr/bin/python3 and the venv python (a scratch copy)
[5/12] scratch copies: the spine folder twice (NEW with the two built files, OLD as it is), finance.db by the backup API
     ok   no OFF switch is set (spine_build.py would exit 0 as 'switched off' and read like a pass): /root/finance/_off/ALL_OFF absent, no OFF file beside either scratch copy; spine_read.py sits beside both   [[]]
     ok   the store holds the two readings and the two SUPPLIER-grouped sheets of the same second; the server keeps both mended sheets   [{'957b473f': 1, '15b48bc5': 1}]
   -- 1  the reader (S483's two edits, built by make_s484_reader.py): the two readings rewritten on a scratch copy
     ok   de92f5d5: 208 of 208 lines dated, every one inside 2026-09-01 .. 2026-10-03; ok True (the stored reading: 0 of 208)
     ok   f62cc9e3: ok False -> True; 341 items; data['code'] == {'OTHERS': 'D98'}
     ok   114 kept readings re-read by the NEW reader: 112 the same family, ok and data as stored; the only two that differ are these two (not re-read here: {'SALE_BILLWISE': 67, 'CATEGORY_WISE_ITEM_LIST': 2}; 45 the spine does not use)   [['de92f5d5', 'f62cc9e3']]
     ok   the two files' source, statement by statement: marg_read.py differs in read_purchase_lines and read_grouped_list only; spine_build.py in build, the new cut_shared_bill and BUILD_VERSION only   [['build', 'cut_shared_bill', 'stmt:BUILD_VERSION = "S331.1"', 'stmt:BUILD_VERSION = "S484.1"']]
     ok   selftest_spine.py beside the built reader AND the built spine_build.py: SELFTEST OK  45 checks -- every check passes (the box as it is: SELFTEST OK  45 checks)
   -- 2  the order of same-second exports (the three sheets stamped 20261005-075955: {'957b473f': ('20261005-075955', 'SUPPLIER', 208), '15b48bc5': ('20261005-075955', 'SUPPLIER', 5), 'de92f5d5': ('20261005-075955', 'BILL', 208)})
     ok   NEW order (stamp, SUPPLIER-grouped, number of lines, md5): the authority of every day 2026-09-01 .. 2026-10-03 for purchase lines -- 33 days -> 957b473f, 0 -> de92f5d5, 0 -> 15b48bc5; and the NEW build's own purchase lines of that period all come from 957b473f ({'957b473f': 208})   [({'957b473f': 33}, {'957b473f': 208})]
     ok   negative control, OLD spine_build.py (ce99bedf, stamp alone -> the store's md5 order) on the same store: {'de92f5d5': 33} for the same 33 days; its build takes that period's lines from de92f5d5 ({'de92f5d5': 203})   [({'de92f5d5': 33}, {'de92f5d5': 203})]
     ok   days whose authority moved under the new keys: purchase lines 33 (exactly the 33 days above, nothing outside them); bill-wise exports 0 (expected 0 -- 0 bill-wise stamps are shared by two exports)   [(['2026-09-01', '2026-09-02'], [])]
   -- 3  the tie of a shared bill number (bill 160 of 01-Sep in de92f5d5)
            run: 1 line(s), net 5376.68 = Rs 5376.68  ->  the bill of Rs 5377.00 (supplier DAAN..., PURCHASE)   ['DENGEN PLUS']
            run: 4 line(s), net 2400.00 + 880.00 + 3200.00 + 5920.00 = Rs 12400.00  ->  the bill of Rs 12400.00 (supplier KEDA..., PURCHASE)   ['MEG QCS', 'ASTOFEN SP', 'PATOPAN DSR', 'TYRO BR']
     ok   cut_shared_bill on the five lines and the two bills numbered 160 of 01-Sep: exactly one cutting fits -- run 1 = 5,376.68 -> the Rs 5,377.00 bill; run 2 = 2,400.00 + 880.00 + 3,200.00 + 5,920.00 = 12,400.00 -> the Rs 12,400.00 bill (the whole sum, Rs 17776.68, is no bill's)   [[(1, 537668, 537700), (4, 1240000, 1240000)]]
     ok   negative control, OLD: no cut_shared_bill; its build leaves those five lines tied to no bill and its gate line fails (5 lines: )
     ok   end to end, a scratch store WITHOUT the two SUPPLIER sheets (so de92f5d5 is the authority of the period, as a BILL-grouped sheet may be): the NEW build ties all its lines -- the gate line passes, the whole gate passes, and the five lines are purchase lines under their two suppliers [('DAAN', 1), ('KEDA', 4)]; the OLD build on that store fails the line on 5 lines   [('0 lines: [] | lines of superseded exports not tied (informat', "5 lines: [('PURCHASE_BILLITEMWISE_DEFAUL")]
     ok   (c) a group with ONE candidate bill never reaches the helper: 284 such groups in the BILL-grouped sheets of the store, 2 groups with two or more bills, 2 calls in the whole build -- every one with two or more bills ([(('160', '2026-09-01'), 2, True)])   [2]
     ok   (d) a SUPPLIER-grouped line never reaches it: 2818 lines in the SUPPLIER-grouped sheets, 0 calls carried a line with a supplier
     ok       the cap: no group of the store has more than 24 lines or more than 4 bills (largest call: 5 lines, 2 bills)
     ok   invented rows through cut_shared_bill itself: the shape of today's five lines ties 1 + 4; the bills given in the other order tie the same way; the bigger bill's lines printed first tie 4 + 1
     ok   (a) two candidate bills of EQUAL amount, lines that fit either way -> two fits -> None: every line stays untied
     ok   (b) lines whose runs fit no cutting -> None: untied
     ok   (e) the cap: 25 lines, or 5 bills -> None at once (0.0000 s; both groups WOULD fit exactly one way, so it is the cap that answers, not the search); 24 lines and 4 bills are still cut
   -- 4  the gate: spine_build.py's own main() on scratch stores, to scratch --out files
     ok   NEW spine_build.py + NEW readings: 13/13 of the blocking lines, 'SPINE BUILT AND SWAPPED' (exit 0) -- on the scratch copy   [(0, [], 'SPINE BUILT AND SWAPPED: /tmp/s484_walk_20261005_1')]
            the non-blocking line 'every purchase bill: its lines re-add to the bill (net, within Rs 1)': 1 of 554 bills off: [(('KEDARPHA', '195', '2026-09-27'), 1771600, 1795900)]
     ok   negative control, OLD build + NEW readings: GATE FAILED (exit 3) on the purchase-lines line alone -- 5 lines, bill number ['160'] (REPORT_S483's finding, reproduced)   [(3, ['every purchase line of an export that is the authority for its whole period belongs to exactly one bill'])]
     ok   negative control, NEW build + OLD readings: GATE FAILED (exit 3) on the category-list line alone -- E.2 is still needed   [(3, ['every CATEGORY_WISE_ITEM_LIST export passes its own witness'])]
     ok   the box as it is, OLD build + OLD readings: GATE FAILED on both lines (208 lines on the purchase line), as spine.log says today   [(3, ['every CATEGORY_WISE_ITEM_LIST export passes its own witness', 'every purchase line of an export that is the authority for its whole period belongs to exactly one bill'])]
     ok   every other gate line reads the same in all four builds (19 lines); none was 'switched off'   [[]]
   -- 5  F-737 measured, not mended: a one-supplier print exported AFTER the whole one
     ok   with 15b48bc5's stamp moved one second after 957b473f's (20261005-075955 -> 20261005-075956; a copy of the store, the reading's file replaced): the NEW order makes the one-supplier print the authority for all 33 days, the build's purchase lines of 2026-09-01 .. 2026-10-03 fall from 208 to 5 -- and the gate STILL PASSES (13/13, swapped on the scratch copy). F-737 is real and is not mended by this kit   [({'15b48bc5': 33}, 208, 5, 0)]
            the non-blocking re-add line in that build: 87 of 554 bills off: [(('DAANSHIP', '160', '2026-09-01'), 53   (in the true build: 1 of 554 bills off: [(('KEDARPHA', '195', '2026-09-27'), 177)
     ok   the stores of the other sections were never changed by this one (the F-737 store is its own copy; 15b48bc5's reading in the walk's main store is the live one, byte for byte)
   -- 6  the new spine.db (scratch) against the last good one (2026-10-05 08:00:44, opened read only)
     ok   6a  the evidence the last good build had (212 readings of the store's 228), built again on scratch by the OLD file: that spine, row for row, in every table -- sp_alias 51, sp_check 23209, sp_close 10286, sp_export 212, sp_finding 377, sp_gate 21, sp_item 1019, sp_item_fact 20120, sp_meta 6, sp_move 23483, sp_purchase_bill 554, sp_purchase_line 1157, sp_recon 34, sp_sale_bill 4230, sp_sale_line 21312 -- so the scratch store IS that evidence   [(0, [])]
     ok       the NEW spine_build.py on the same evidence: it builds 13/13 and every table is the same rows as the OLD file's -- on what the spine held at 08:00 the new rules move no row. One gate detail differs, as it should: lines of superseded exports tied to no bill (information) 6 -> 1 -- the five lines of bill 160 in Marg's own BILL-grouped sheet of 06-Sep now find their two bills   [(0, [], [])]
     ok   6b  sp_export: 212 rows then, 228 now -- 16 readings arrived since that build ({'(not used)': 6, 'SALE_BILLWISE': 1, 'PURCHASE_ITEMWISE': 3, 'ITEM_MASTER': 1, 'SALT_WISE_ITEM_LIST': 2, 'PURCHASE_BILLWISE': 1, 'PURCHASE_BILLITEMWISE': 1, 'CATEGORY_WISE_ITEM_LIST': 1}); no export left; the `ok` of every export both hold is the same   [([], [])]
     ok       the tables that carry their source (rows then -> now, +added, -removed): sp_purchase_line 1157 -> 1157 (+208, -208), sp_purchase_bill 554 -> 554 (+12, -12), sp_sale_bill 4230 -> 4230 (+0, -0), sp_close 10286 -> 10286 (+0, -0) -- every added row comes from a reading that arrived since; every removed row is a purchase line or bill of a period a newer export of its kind now covers, or the same bill / closing figure printed again by a newer export   [[]]
            sp_purchase_line by month, then: {'2026-04': 185, '2026-05': 185, '2026-06': 211, '2026-07': 217, '2026-08': 151, '2026-09': 186, '2026-10': 22}
            sp_purchase_line by month, now : {'2026-04': 185, '2026-05': 185, '2026-06': 211, '2026-07': 217, '2026-08': 151, '2026-09': 186, '2026-10': 22}
     ok       the purchase lines of 2026-09-01 .. 2026-10-03: then 208, from {'d63bd4a8': 186, 'a5581a9b': 22}; now 208, every one from 957b473f (the SUPPLIER-grouped sheet's 208 lines) -- none from de92f5d5; the months before September are the same, month for month   [({'957b473f': 208}, {'d63bd4a8': 186, 'a5581a9b': 22})]
     ok       the five lines of bill 160 of 01-Sep are in sp_purchase_line under their two bills: [('DAAN', 1, '5376.68'), ('KEDA', 4, '12400.00')] against the bills ['5377.00', '12400.00']
     ok       sp_alias and sp_recon (the rules' own tables) are the same; the items: sp_item 1019 -> 1019. The tables worked out from the above (rows then -> now): sp_check 23209 -> 24142, sp_finding 377 -> 397, sp_gate 21 -> 21, sp_item_fact 20120 -> 23881, sp_meta 6 -> 6, sp_move 23483 -> 23483, sp_sale_line 21312 -> 21312
     ok       sp_meta records the build: build_version S484.1 (then: S331.1)
     ok   the walk wrote nothing live: every reading it read at its start is byte for byte as it was; spine.db is the same file (md5 b0918f47)
   WALK_S484 GREEN -- 36 checks
[6/12] walk_s484 sections 1-6 green on scratch copies; every named control red on the old file (above)
   before: de92f5d5185646d4de563e30d5464f6e.json  ok=True failed=0 lines=208 dated=0 items=- code=None read_at=2026-10-05 08:10:58
   before: f62cc9e3d93c692f1795229be9e7cfe1.json  ok=False failed=3 lines=- dated=- items=341 code=None read_at=2026-10-05 08:11:06
   before: spine_state.json  at=2026-10-05T11:30:48+05:30 gate=11/13 passed=False last_success=2026-10-05T08:00:44+05:30 failed=['every purchase line of an export that is the authority for its whole period belongs to exactly one bill', 'every CATEGORY_WISE_ITEM_LIST export passes its own witness']
   before: spine.db  2026-10-05 08:00:44  built=2026-10-05T08:00:44+05:30 build_version=S331.1 gate=13/13 exports=212 | purchase lines 01-Sep..03-Oct: 208 by source {'d63bd4a8': 186, 'a5581a9b': 22}; September: 186 | bill 160 of 01-Sep: [('DAAN', 1, 537668), ('KEDA', 4, 1240000)]
[7/12] the lock is held by S484_SPINE_BILL_TIES; finance.db.bak_S484_20261005_113547 made (backup API; the kit writes no row); a .bak_S484_<from8> beside each of the two files and each of the two readings, read back
[8/12] both files placed, each by a rename; md5 read back = the two TO pins
[9/12] the two readings removed from the store (their .bak_S484 copies are not read by anything: they do not end in .json)
health : finance healthz 200
         /finance/reports/aaj 302 (302/401 = the login gate, expected)
[10/12] clinic-finance active (restarted once, 2026-10-05 11:36:17); healthz 200; the gated page answers the gate
   spine.log:   ok    CATEGORY_WISE_ITEM_LIST  CATEGORY_WISE_ITEM_LIST_DEFAULT__2026-10-05__20261005-075955__f62cc9e3
   spine.log: spine_evidence 2026-10-05 11:37:09: listed 228, read 2 (0 not a report the spine uses), failed 0, store now 228 readings
   spine.log:   note every purchase bill: its lines re-add to the bill (net, within Rs 1)  -- 1 of 554 bills off: [(('KEDARPHA', '195', '2026-09-27'), 1771600, 1795900)]
   spine.log: SPINE BUILT AND SWAPPED: spine.db
   exit 0 after 1 try(s) · spine_state.json  at=2026-10-05T11:37:11+05:30 gate=13/13 passed=True last_success=2026-10-05T11:37:11+05:30 failed=[]
   after : de92f5d5185646d4de563e30d5464f6e.json 279570f0fb8b1d89fa344f1e78a9fc8c  ok=True failed=0 lines=208 dated=208 items=- code=None read_at=2026-10-05 11:37:08
   after : f62cc9e3d93c692f1795229be9e7cfe1.json 802b77174d8e963c859648d46f51e60a  ok=True failed=0 lines=- dated=- items=341 code={'OTHERS': 'D98'} read_at=2026-10-05 11:37:09
   after : spine.db  2026-10-05 11:37:11  built=2026-10-05T11:37:11+05:30 build_version=S484.1 gate=13/13 exports=228 | purchase lines 01-Sep..03-Oct: 208 by source {'957b473f': 208}; September: 186 | bill 160 of 01-Sep: [('DAAN', 1, 537668), ('KEDA', 4, 1240000)]
[11/12] THE GATE PASSES AND spine.db IS SWAPPED -- the spine builds again (its own line, the state file's clock time and the new spine's own figures are above)
11f8acb05c46aeaa72e1771d5c89922c  /root/finance/spine/spine_build.py
ce99bedf60194a84fe93455927a336e2  /root/finance/spine/spine_build.py.bak_S484_ce99bedf
96f565a8d138d9ce75c0ed228b471495  /root/finance/spine/marg_read.py
099d621315f3bf9297a9b4626a5caee5  /root/finance/spine/marg_read.py.bak_S484_099d6213
[12/12] done · healthz 200 · nothing else moved (spine_evidence.py, spine_read.py, selftest_spine.py, spine_rules.json, reports_tile.py, the crontab) · backups: a .bak_S484_<from8> beside both files and both readings, /root/finance/finance.db.bak_S484_20261005_113547
S484_SPINE_BILL_TIES: DONE
```

### 8 · Outside the brief, noticed

1. **The spine's own status line now reads** *"stock = Marg at 2026-10-04 EXCEPT 20 item(s): ANKLE BINDER BAMBOO -3, ANKLE BINDER L
   TYNOR +2, …"* — the latest checkable closing moved from 02-Oct to 04-Oct with this morning's exports. It is the spine's
   non-blocking STOCK line doing its work, not a fault of this kit; named because it is new on the health page since 11:37.
2. **Bill 195 of 27-Sep** (supplier key `KEDARPHA`): bill ₹17,716.00, lines ₹17,959.00 — the one bill the re-add line counts off.
   It was off at 08:00 too (the line is non-blocking).
3. **Two walks were needed to get section 6 right** (see call 6): the first dry run, 11:32:48–11:33:16, was red on one check of
   mine; the second, 11:34:56–11:35:30, green. Both dry; the kit that ran and was published is the second.
4. My read-only probes and the kit's copy are left in the server's `/tmp/s484probe` and `/tmp/s484kit` (scripts and logs; the one
   probe folder that held a copy of `finance.db` removed itself).

### 9 · Undo

Put back `spine_build.py.bak_S484_ce99bedf` and `marg_read.py.bak_S484_099d6213`, copy the two readings' `.bak_S484_<md5-8>` over
them, restart `clinic-finance`, healthz 200, read the md5s back. The spine's gate then refuses again on the two lines of this
morning; the `spine.db` now in place stays until a later build passes.
