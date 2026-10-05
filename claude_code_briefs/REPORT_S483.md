# REPORT — S483_SPINE_READS_TEXT (05-Oct-2026)

Brief: `claude_code_briefs/S483_SPINE_READS_TEXT.md` · kit `deploy_kits/S483_SPINE_READS_TEXT/` · faults F-734, F-735 · no D-number.
Built and walked by Claude Code on manojz, 05-Oct-2026. **Not installed.** Every clock time below is read (IST).

## For the owner

- **The spine is not building again yet, and I changed nothing on the server.** I built the fix exactly as the brief describes and
  tested it on copies first. The test stopped the install, as it is meant to: with the fix, one of the two frozen reports reads
  clean and the other is nearly there, but the spine's own check would still refuse to build.
- **What froze it, and what is left:** this morning's purchase report now gets its dates (208 lines of 208) and the category list
  reads clean. But on 01-Sep two different suppliers each have a bill numbered **160**, and the spine cannot tell which of five
  medicine lines belongs to which of the two bills. That rule sits in a file this brief told me not to touch.
- Nothing is at risk: the spine keeps using its last good build (08:00 today), the finance service was not restarted and is
  healthy. **The chat needs to write one short follow-up brief** — everything it needs is below, with two ways I tried on a copy
  that both make the spine build.

## For the chat

### 1 · State of the box — nothing moved

| what | before the build | after (read back 10:49–10:50) |
|---|---|---|
| `/root/finance/spine/marg_read.py` | `099d621315f3bf9297a9b4626a5caee5` (the brief's pin) | `099d621315f3bf9297a9b4626a5caee5` — **not replaced**; the kit's TO, built on the box from the live bytes and not placed, is `96f565a8d138d9ce75c0ed228b471495` |
| `readings/de92f5d5185646d4de563e30d5464f6e.json` | `0af44311254ecad7603e243faff743f8` — ok True, 0 of 208 lines dated, read 08:10:58 | the same file |
| `readings/f62cc9e3d93c692f1795229be9e7cfe1.json` | `b054e6c826902234c0af98524de29450` — ok False (*serial restarts…*, UNCLASSIFIED at row 148, SERIAL at row 149), read 08:11:06 | the same file |
| `spine_build.py` (read only) | `ce99bedf60194a84fe93455927a336e2` | the same |
| `spine_evidence.py` · `spine_read.py` · `selftest_spine.py` (read only) | `0fcf6c64…` · `712a1e4e…` · `fc63d2c6…` | the same |
| `spine.db` | 2026-10-05 08:00:44 | 2026-10-05 08:00:44 — the last good build, still in place |
| `spine_state.json` | 10:30:47 — gate 11/13, passed False | 10:40:45 — gate 11/13, passed False, `last_success_iso 2026-10-05T08:00:44` |
| `clinic-finance` | active since 09:44:30 (S482's restart) | active since 09:44:30 — **not restarted**; `/finance/healthz` 200 at 10:50:14 |
| the build lock | free | never taken: the install step was not reached |
| backups | — | none made: nothing was placed (no `.bak_S483_*`, no `finance.db.bak_S483_*`) |

The installer ran twice with `DRY=1` on the server (10:44:04–10:44:16 and 10:49:33–10:49:42); both stopped at
`!! [6/12] walk_s483 (server) red - nothing installed`. A dry run places nothing and removes its own scratch folder.

### 2 · What the walk found

**The two edits do what the brief says** (manojz, MargArchive; and the server's kept sheets):

- **E.1** — `de92f5d5`: OLD dates on lines **0 of 208** (its 27 date rows read as supplier headings); NEW **208 of 208**, every one
  inside 01-Sep … 03-Oct, ok True; nothing else of the sheet moves (the lines are equal field for field but for `date`). Marg's
  own Excel of 06-Sep (`7aab826f`), 25 SUPPLIER/ITEM WISE and 5 other BILL/ITEM WISE sheets: OLD = NEW.
- **E.2** — `f62cc9e3`: OLD ok False; NEW **ok True**, group `OTHERS` with code `D98`, 341 items under 4 headings (COMMON 30, NEW SEPT
  2025 10, ORTHOTICS 81, OTHERS 220 — the 220 were filed under ORTHOTICS before). The two orthotics lists of 18-Sep (`f4a3406e`,
  `fe483146`) and all 14 salt lists: OLD = NEW.
- **Section 4** — 114 readings re-read on the server from their kept sheets: 112 the same family, ok and data as stored; the only
  two that differ are the two mended ones. The reader's source differs in `read_purchase_lines` and `read_grouped_list` only.
  `selftest_spine.py` on the built file: `SELFTEST OK  45 checks`.

**The gate does not pass (section 3, on a scratch copy of the store with both readings rewritten by the NEW reader):**

```
FAIL every purchase line of an export that is the authority for its whole period belongs to exactly one bill
     -- 5 lines: ('…de92f5d5.XLS', '160', 'DENGEN PLUS', 0, True), ('…', '160', 'MEG QCS', 0, True), … (ASTOFEN SP, PATOPAN DSR, TYRO BR)
GATE FAILED -- nothing swapped        (gate 12/13; the category line and the sale line are ok)
```

Down from 208 lines to 5 — and those 5 are not the reader's:

1. **Two suppliers share bill number 160 on 01-Sep.** The bill-wise exports hold two bills `160` dated 2026-09-01: one of
   ₹5,377.00 and one of ₹12,400.00. The BILL/ITEM WISE statement prints the lines of both under the one number, with no supplier:
   one line of net ₹5,376.68, then four lines of net ₹2,400.00 + ₹880.00 + ₹3,200.00 + ₹5,920.00 = ₹12,400.00.
   `spine_build.py` (~l.200–205) settles a shared number "by the money of its own lines" — it adds up **all** lines of that number
   on that day (₹17,776.68) and looks for one bill of that amount. Neither matches; the five lines tie to no bill.
2. **Marg's own Excel of 06-Sep reads the same five lines the same way** (`7aab826f`: 5 of its 43 lines tie to no bill, measured
   with the same test). It never blocked, because that sheet was never *the authority for its whole period*: until 07:59 today
   the authority for September was always a SUPPLIER-grouped export (`342b40d7` / `2b3949fe` / `d63bd4a8` of 01-Oct), and a
   supplier-grouped line ties by supplier.
3. **`de92f5d5` is the authority today by the accident of its md5.** Three purchase-lines exports for 01-Sep … 03-Oct carry the
   **same stamp `20261005-075955`** (S480's install converted the waiting texts in one second): `957b473f` SUPPLIER-grouped, 208
   lines · `15b48bc5` SUPPLIER-grouped, **5 lines** · `de92f5d5` BILL-grouped, 208 lines. `spine_build.py` sorts by stamp alone
   (~l.172), so equal stamps keep the store's file order — md5 order — and the last one, `de92f5d5`, wins every day of the period.

So F-734 has two halves. The brief measured the first (no dates); the second (the shared number, exposed because a BILL-grouped
sheet became the whole-period authority) only shows when the gate is run with the mended reading — which the walk did.

### 3 · Two experiments, on a scratch copy only (nothing of them is in the kit or on the box)

Both on `/tmp` copies — the store with the two readings rewritten by the NEW reader, a copy of `spine_build.py`, a backup-API copy
of `finance.db`; the folder was removed afterwards (10:50).

| experiment (one change in a COPY of `spine_build.py`) | the purchase line | the gate |
|---|---|---|
| **A · cut the shared number by money.** When no single bill matches the summed lines, cut that number's lines, in sheet order, into runs whose net matches each candidate bill (same tolerance: ₹1 + 0.2 %); tie only if exactly one cutting fits | ok | **13/13, `SPINE BUILT AND SWAPPED`** (on the copy) |
| **B · at an equal stamp the SUPPLIER-grouped export is the authority** (sort key `(stamp, family == PURCHASE_ITEMWISE)`) | ok | **13/13, `SPINE BUILT AND SWAPPED`** (on the copy) |
| B with the store **as it is** (old readings) | ok | GATE FAILED on the category list alone — E.2 is still needed |

B leaves a second accident in place: between the two SUPPLIER-grouped sheets of the same stamp it is again md5 order that
picks `957b473f` (208 lines) over `15b48bc5` (5 lines). If the 5-line sheet ever won, September would hold five purchase lines.
What `15b48bc5` is (a filtered print?) I did not open — the chat should look before ruling.

### 4 · The call I made, and why

**Nothing was installed — not even the two edits, which are right in themselves.** The brief's walk section 3 requires the gate to
pass with the rewritten readings; it does not, the installer is written to place nothing on a red walk, and I did not weaken the
walk to let it through. Two more reasons, beyond the rule:

- `spine_build.py` is read only in this brief, and the remaining fault is a ruling about money in the spine's heart (how two bills
  that share a number are told apart; which of three same-second exports is the authority). That is the chat's to rule.
- A part-install is not harmless here. With only the reader mended, the spine stays refused today — and could later be let through
  by any newer purchase export (the BILL sheet then stops being the whole-period authority and its untied lines turn into
  "information"), building with five purchase lines of 01-Sep tied to no bill. Today, with the old reader, the category line keeps
  the spine refused until the chat rules — the safer of the two.

**Not done, therefore:** the install; the two readings' removal; the restart of `clinic-finance` (nothing was placed, so there was
nothing for the running process to pick up); the hand-run of the spine's job; "the spine builds again" — it does not. The
owner's line of the brief's §4 would, today, print the same `[6/12] walk red - nothing installed`.

### 5 · For the next brief

- **The kit is published as it was walked** (status at the top of its README and in `KIT_ID.txt`): `make_s483.py` (E.1 and E.2,
  three anchors, each exactly once on `099d6213`), `walk_s483.py`, the installer. A follow-up can take the two edits as they are.
- **What the follow-up must add** is one ruling in `spine_build.py` — experiment A, or B, or both (A mends the tie itself; B keeps a
  BILL-grouped sheet from taking September from a SUPPLIER-grouped one made the same second) — and a rule for equal stamps that is
  not md5 order.
- **Without a kit, the spine will not unfreeze by itself** while `f62cc9e3`'s reading is `ok False` (the category line is
  blocking on its own).
- **The one line for the next medical-PC kit (F-734's root):** in the text cutter (`marg_txt.page_to_sheet`, rule A — "a word
  belongs to the column in which it ends"), a line that is ONE token starting at column 0 belongs to column 0: the day's date of
  the BILL/ITEM WISE statement lands in column 1 today because it is wider than the `BILL` head; Marg's own Excel has it in
  column 0.
- **Also for that kit or S480's owner:** three texts converted in one second get one stamp; whatever orders exports by stamp
  alone then orders them by md5.

### 6 · Calls made while building (the kit's README lists them too)

1. **The code lives in `data["code"]`, a `{group: code}` map, present only when a heading carried one** — the reader has no group
   object, and a key on every item or every reading would have changed the data of every list already in the store.
2. **A code must hold a letter** ("letters and digits" alone would take a bare number — a rate, as an `.xlsx` cell prints a whole
   one — for a code).
3. **Section 4 re-reads every reading whose sheet the server keeps (114) and counts the rest:** 67 sale readings (the sheets are
   never at rest on the server, S186; the walk does not pull them from Drive to prove a negative — the sale reader, the file door
   and `identify()` are the same text, statement by statement), the 2 category lists the server does not keep (read on manojz by
   the same walk: OLD = NEW), 45 the spine does not use.
4. **No staff-eye walk section** — no page, tile, duty or door changes; the duty map is untouched. The one page module that
   imports the reader (`reports_tile.py`) is exercised through its own `certify`: with the old reader the category list certifies
   `ok False`, with the new one `ok True, 341 items`.
5. **The installer would have backed up `finance.db`** (the rulebook's rule 6) although the kit writes no row; it never got there.

### 7 · The walk — manojz (build time, 10:42; MargArchive read where it lies; no sale sheet opened)

```
-- 1  read_purchase_lines (E.1, F-734) on MargArchive -- verdicts and counts only
  ok   the text-made BILL/ITEM WISE sheet de92f5d5 is in MargArchive, and its md5 is the reading's name
  ok   OLD (099d6213): dates on lines: 0 of 208 -- its 27 date rows are read as supplier headings
  ok   NEW: dates on lines: 208 of 208, every one inside 2026-09-01 .. 2026-10-03 (27 days, 2026-09-01 .. 2026-10-03); ok True; 27 DATE rows, no supplier heading
  ok   nothing else of that sheet moved: the same 208 lines, field for field, but for `date`; the same five checks
  ok   Marg's own Excel BILL/ITEM WISE of 06-Sep (7aab826f; the day in column 0): OLD = NEW, the same reading (43 lines, all dated)
  ok   every other purchase-lines sheet in the archive -- 25 SUPPLIER/ITEM WISE (no date rows) and 5 BILL/ITEM WISE: OLD = NEW, reading for reading   [[]]
-- 2  read_grouped_list (E.2, F-735) on MargArchive
  ok   the whole-shop category list f62cc9e3 is in MargArchive, and its md5 is the reading's name
  ok   OLD: ok False -- ['serial restarts at 1 under every heading and never skips', 'UNCLASSIFIED at row 148', 'SERIAL at row 149']
  ok   NEW: ok True, nothing failed; the group OTHERS with code D98 (data['code'] = {'OTHERS': 'D98'}); 341 items read under 4 headings {'COMMON': 30, 'NEW SEPT 2025': 10, 'ORTHOTICS': 81, 'OTHERS': 220}; serials clean under every heading
  ok   nothing else of that list moved: the same 341 items in the same order; only `group` differs, and only on the 220 items after the OTHERS row (they were filed under the heading before it)
  ok   every other grouped list in the archive -- the two orthotics-only category lists of 18-Sep (f4a3406e, fe483146) and 14 salt lists (235e9643 among them): OLD = NEW, reading for reading   [[]]
-- the two rules on invented rows
  ok   E.1 on invented rows: a date-only row is a DATE wherever its one cell sits -- column 1, column 3, column 0: NEW dates all three lines; OLD dates only the line under the column-0 date   [(['2030-01-01', '2030-01-01', '2030-01-01'], ['', '', '2030-01-01'])]
  ok   negative control: a date cell with a second non-empty cell in its row is still NOT a DATE under NEW (the line stays undated, as under OLD)   [{'TITLE': 1, 'COLHDR': 1, 'SUPPLIER_HEADING': 1, 'ITEM': 1, 'GRAND_TOTAL': 1}]
  ok   E.2 on invented rows: 'OTHERS | 0.0 | D98' is a HEADING under NEW (ok, two groups, data['code'] = {'OTHERS': 'D98'}); under OLD it is UNCLASSIFIED and the next serial breaks   [([], ['serial restarts at 1 under every heading and never skips', 'UNCLASSIFIED at row 2', 'SERIAL at row 3'])]
  ok   a heading with no code reads exactly as before: the same data, key for key (no 'code' key appears)
  ok   negative controls: a row with two codes, with a rate, with a packing, with a 7-character word, with a space in it, or with a bare number beside the name is still UNCLASSIFIED under NEW, exactly as under OLD   [{'two codes': True, 'a rate': True, 'a packing': True, 'seven characters': True, 'a space': True, 'a bare number': True}]
WALK_S483 manojz GREEN -- 16 checks
```

### 8 · The walk — server (the installer's second DRY run, 10:49:33–10:49:42; scratch copies; nothing placed)

```
[1/12] kit gates green (SUMS, KIT_ID, the venv's flask, the database, the spine's files; spine_evidence.py and spine_read.py at the brief's pins; spine_build.py is ce99bedf60194a84fe93455927a336e2, read only)
[2/12] marg_read.py at its FROM pin 099d621315f3bf9297a9b4626a5caee5 (the post-S482 bytes)
built marg_read.py  099d6213 -> 96f565a8  (27934 bytes)
[3/12] live bytes + anchored edits give the pinned file (96f565a8d138d9ce75c0ed228b471495)
[4/12] compiles on /usr/bin/python3 and the venv python (a scratch copy)
[5/12] selftest_spine.py with the built marg_read.py (a scratch copy of the spine folder): SELFTEST OK  45 checks -- every check passes, the same line as the box as it is
     ok   the two readings are in the store, and the server keeps both sheets (purchases and lists carry no person's detail)
-- 3  the gate: spine_build.py on scratch copies of the readings store (the live spine.db is never the --out)
     ok   negative control, the store as it is: GATE FAILED (exit 3) on exactly the two lines of this morning -- the purchase lines and the category list; nothing swapped   [(3, ['every CATEGORY_WISE_ITEM_LIST export passes its own witness', 'every purchase line of an export that is the authority for its whole period belongs to exactly on ...]
     ok   with the two readings rewritten by the NEW reader: the category-list line passes, and the sale-exports line (mended by S482) passes   [['ok', 'ok']]
     FAIL the purchase-lines line passes -- it failed on 208 lines with the old reading; with the new one it STILL FAILS, on 5 lines, bill number(s) ['160']   [5 lines: [('PURCHASE_BILLITEMWISE_DEFAULT__2026-09-01_to_2026-10-03__20261005-075955__de92f5d5.XLS', '160', 'DENGEN PLUS', 0, True), ('PURCHASE_BILLITEMWISE_DEFAULT__2026-09-01_to_ ...]
     FAIL the gate PASSES (12/13, exit 0) and the build swaps ON THE SCRATCH COPY -- 'GATE FAILED -- nothing swapped; the fail'   [(3, ['every purchase line of an export that is the authority for its whole period belongs to exactly one bill'], 'GATE FAILED -- nothing swapped; the failed build is /tmp/s48')]
     ok   every other gate line reads the same in both builds (21 lines)   [[]]
-- 4  every reading in the store, re-read by the NEW reader from the sheet the server keeps
     ok   114 readings re-read from their kept sheets: 112 give the same family, the same ok and the same data as the stored one; the ONLY two that differ are the two mended sheets (de92f5d5, f62cc9e3)   [['de92f5d5', 'f62cc9e3']]
     ok      de92f5d5: ok True -> True; its lines dated 0 of 208 -> 208 of 208; nothing else of it moved (the lines are equal field for field but for `date`)
     ok      f62cc9e3: ok False -> True (failed 3 -> []); 341 items both; data['code'] {'OTHERS': 'D98'}; only `group` moved, on the items after the OTHERS row
     ok   the reader's source, statement by statement (38 top-level statements): only read_purchase_lines and read_grouped_list differ -- every other function, the sale reader and the file door among them, is the same text   [['read_grouped_list', 'read_purchase_lines']]
     ok   the readings NOT re-read here, counted: 67 of sale sheets (never at rest on the server, S186 -- read_sale_detail is the same text, so they cannot move); 2 category lists the server does not keep (f4a3406e, fe483146 -- both read on manojz by this walk: OLD = NEW); 45 that the spine does not use (no family -- identify() is the sam ...]
-- the tile's own certificate of the two kept sheets while the store has no reading for them (why clinic-finance restarts)
     ok   reports_tile.certify, the reader of the scratch spine folder: NEW -- the category list ok (341 items), the purchase sheet ok (); OLD -- the category list NOT ok (['serial restarts at 1 under every heading and never skips', 'UNCLASSIFIED at row 148', 'SERIAL at row 149'])   [({'de92f5d5': {'ok': True, 'failed': [], 'count': '', ' ...]
     ok   the walk wrote nothing live: the readings it read at its start are byte for byte as they were, and spine.db is the same file (md5 b0918f47) unless the ten-minute job itself swapped it meanwhile
WALK_S483 server RED -- 2 of 13 checks failed:
      - the purchase-lines line passes -- it failed on 208 lines with the old reading; with the new one it STILL FAILS, on 5 lines, bill number(s) ['160']
      - the gate PASSES (12/13, exit 0) and the build swaps ON THE SCRATCH COPY -- 'GATE FAILED -- nothing swapped; the fail'
!! [6/12] walk_s483 (server) red - nothing installed
```

### 9 · Outside the brief, noticed

1. **Equal stamps are ordered by md5** in `spine_build.py` (bill-wise ~l.154 and purchase-lines ~l.172 both sort by stamp alone) —
   §2 (3) above. Three purchase-lines exports and several other texts of 07:59:55 share one stamp.
2. **`15b48bc5`** — a SUPPLIER/ITEM WISE reading for 01-Sep … 03-Oct with 5 lines, `ok True`, same stamp. Not opened.
3. **`reports_tile.certify` says `ok False` for today's category list** (from the store's reading) — wherever the tile shows that
   list, it shows it as failed until the reading is written again by a mended reader.
4. The store holds 3 `PURCHASE_ITEMWISE` and 3 `STOCK_CLOSING` readings with `ok False`; the gate passes them today (waived by
   `spine_rules.json` exceptions or superseded) — unchanged by anything here, named only because the count is in the walk's view.
5. My read-only probes and the kit's copy are left in the server's `/tmp/s483probe` and `/tmp/s483kit` (scripts and logs; the one
   experiment folder that held a copy of `finance.db` was removed at 10:50).
