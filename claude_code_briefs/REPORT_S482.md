# REPORT — S482_BILL_CHAIN (05-Oct-2026)

Brief: `claude_code_briefs/S482_BILL_CHAIN.md` · kit `deploy_kits/S482_BILL_CHAIN/` · decisions D675 b, D676 · faults F-731, F-732, F-733.
Built, walked, installed, published and read back by Claude Code on manojz, 05-Oct-2026. Every clock time below is read (IST).

## For the owner

- **The bill chain is now watched, and today it shows one gap.** Two Marg bills are missing from what the system holds: sale bill
  **A003478** and credit note **CN00203**, both between **08-Sep and 09-Sep**. Someone must make the sale report of **08-Sep and
  09-Sep** again in Marg (Bill Wise Statement, Detail, With Item Details Yes). The line goes away by itself when they arrive.
- **Where it shows:** on Shavez's *Aaj ki reports* page, one red line in Hindi — *"Bill A003478 aur CN00203 nahi mile (08-Sep se
  09-Sep ke beech) — 08-Sep aur 09-Sep ki bikri report dobara banaiye."* — and in your English reports line: *"Bill chain: A003478 and
  CN00203 missing between 08-Sep and 09-Sep — re-export both days."* Nothing else on any screen moved.
- **Amir's rename list carries the agreed names** (the seven belts: *L S BELT L CONT GRAY UNISON* … *BLING PELVIC XL TRACTION
  BELT*). He had ticked none of them, so nothing he did is lost. The list is still closed to him until the stock proof is green.
- **The empty day (Sunday 04-Oct) is accepted everywhere now:** the server's check gives it a tick instead of "jaanch me fail", and
  a no-sale day can never be mistaken for a missing one — the bill numbers decide, not the calendar.
- **The false "not ok" on your PC's ten-minute pull is gone** — it said "PROBLEM: send=1" every ten minutes from 08:51 to 09:40; the 09:50 pull says **ok**.
- It works: 54 checks on the server and 15 on your PC are green, each with its "must fail on the old file" control; the finance
  service is healthy. **One thing for the chat, not caused by this kit:** the spine's rebuild has been refused since about 08:10
  today by two of this morning's new reports (a purchase report and the category list) — see the last section.

## For the chat

### 1 · Every pin, FROM → TO, read back on the box

| where | file | FROM (read before the first edit) | TO (read back after placing) | backup beside it |
|---|---|---|---|---|
| server | `/root/marg_ingest/marg_take.py` | `3ac9bbe03abf5c01c4ebc1bfffd30da2` | `a86a0f26d4fc86a51e963b6a1b561323` | `.bak_S482_3ac9bbe0` (reads `3ac9bbe0…`) |
| server | `/root/marg_ingest/marg_ingest.py` | `7f6b4dc25d1c247c8b45f05108e600ca` | `828c4dad6b159207b034d8129aed3ab7` | `.bak_S482_7f6b4dc2` (reads `7f6b4dc2…`) |
| server | `/root/finance/reports_tile.py` | `406e452b2e3cf5991e89100ee867e1d6` | `ea15aacbb6a00131d3f02664b0c1df42` | `.bak_S482_406e452b` (reads `406e452b…`) |
| server | `/root/finance/spine/marg_read.py` | `7ec9b325687de465ea6942affb25dec1` | `099d621315f3bf9297a9b4626a5caee5` | `.bak_S482_7ec9b325` (reads `7ec9b325…`) |
| manojz | `D:\Downloads\margsync\MargPull\marg_gate.py` | `52f502d1ee1a59e37086fb3e514f7874` | `f5de9b4eb974052fd5773c270d1481b2` | `marg_gate.py.bak_S482_52f502d1` (reads `52f502d1…`) |
| server | `/root/finance/spine/readings/15495622be4e21b5daa8d1d7580fc6db.json` | `3dc6345bac0ad5db72df1dacb48bab5a` (ok False, two failed checks, read 09:01:00) | `4c78506000882aac501d54b8d16f1d8a` (ok True, written again by `spine_evidence.py` at 09:46:11) | `….json.bak_S482` (reads `3dc6345b…`) |

All five FROM pins were the brief's. Read only, md5 the same before and after: `stock_app.py` `7e159de737c0ec03cea890053f1bcd58` ·
`amir_day.py` `709f20c1078cbcb36fc1108e452c40c1` · `item_alias.py` `5168c3c05df63a674a8dcab59f74365f` · `marg_router.py`
`318086e36b0088f2da57b95d19a86b98` · `spine/spine_evidence.py` `0fcf6c6419d5a69d7314e152421a2aa7`. The installer also held
`purchase_app.py`, the three `marg_report.py`, `signatures.json`, `spine_build.py`, `finance_app.py`, `portal.py`,
`tile_grants.json` and the crontab to "md5 before = after".

**Data.** `finance.db.bak_S482_20261005_094406` (backup API, 31,293,440 bytes) was made before the first write. Then, in this order:
the seven `marg_item_rename` rows (the first live write, before any file was placed); after the service was healthy, the new table
`mi_bill_chain` (76 rows: 17-Aug → 04-Oct, two of them the EMPTY rows of 04-Oct).

**Service.** `clinic-finance` restarted once, 09:44:30; `/finance/healthz` 200; `/finance/reports/aaj`, `/finance/stock/page/amir`,
`/finance/clinic/marg/upload` answer 302 (the login gate, expected); no Traceback / "NOT mounted" in its journal since the restart.
Nothing else was restarted. The five-minute collector was run once as the crontab spells it: exit 0, nothing raised.

**The lock.** `/root/deploy/.claude_code_build.lock` taken 09:44:06 (owner `S482_BILL_CHAIN`), released after this report was
written (09:52:50; healthz 200 at that moment). The kit's scratch copies in the server's `/tmp/s482kit` and `/tmp/s482probe`
(the kit, its logs, read-only probes — no secret, no sheet) are left for the system to clear.

**Publish.** `PUBLISH_ALL.bat`: the number gate clean on 16 files, commit `783e89b`, origin HEAD verified. On the server
`git pull --ff-only` → `783e89b`; `md5sum -c SUMS.md5` in the repository's kit: every file OK; `diff -r` against the copy that ran
(`/tmp/s482kit`): no difference (SUMS.md5 `96caf7c5e1f709196565934aa8e8e2b9` both). The owner's line of the brief's §10, run from
the repository at 09:47, says `ALREADY INSTALLED … healthz 200 … the 04-10 reading: ok=True`. This report went up with a second `PUBLISH_ALL.bat` run; the kit folder was not touched again (frozen).

### 2 · The chain as measured live (A.5)

```
mi_bill_chain: 76 rows written; built True; complete False; last {'A': ['2026-10-03', 'A004000'], 'CN': ['2026-10-02', 'CN00234']}
gap: A missing A003478 between 2026-09-08 and 2026-09-09 (n 1)
gap: CN missing CN00203 between 2026-09-08 and 2026-09-09 (n 1)
TILE HI: Bill A003478 aur CN00203 nahi mile (08-Sep se 09-Sep ke beech) — 08-Sep aur 09-Sep ki bikri report dobara banaiye.
TILE EN: Bill chain: A003478 and CN00203 missing between 08-Sep and 09-Sep — re-export both days.
OWNER LINE: Today's reports: 5 of 5 arrived · Bill chain: A003478 and CN00203 missing between 08-Sep and 09-Sep — re-export both days.
CARD ON THE PAGE: yes
```

Exactly the one gap the chat measured, and nothing else from 17-Aug to the newest day. The rows that matter, read back:
`('A','2026-09-09', 3479, 3499, 21 bills, gap_before 'A003478')` · `('CN','2026-09-09', 204, 204, 1, gap_before 'CN00203')` ·
`('A','2026-10-04', empty 1)` · `('CN','2026-10-04', empty 1)`. The 04-Oct EMPTY day sits after the last numbered day and breaks
nothing. A re-export of 08-Sep and 09-Sep lands through the door, which rewrites the chain; the line then leaves by itself (the
walk shows this with its own rows: fixtures deleted → the state is the live state again).

### 3 · The seven rows, before → after (`marg_item_rename`, live)

| id | old_name (unchanged) | new_name before (S268) | new_name after (D676) | new20 after | new27 after |
|---|---|---|---|---|---|
| 5 | L S BELT CONT GRAY UNISON L | LS BELT L CONT GRAY UNISON | L S BELT L CONT GRAY UNISON | L S BELT L CONT GRAY | L S BELT L CONT GRAY UNISON |
| 6 | L S BELT CONT GRAY UNISON M | LS BELT M CONT GRAY UNISON | L S BELT M CONT GRAY UNISON | L S BELT M CONT GRAY | L S BELT M CONT GRAY UNISON |
| 7 | L S BELT CONT GRAY UNISON XL | LS BELT XL CONT GRAY UNISON | L S BELT XL CONT GRAY UNISON | L S BELT XL CONT GRA | L S BELT XL CONT GRAY UNISO |
| 8 | L S BELT CONT GRAY UNISON XXL | LS BELT XXL CONT GRAY UNISON | L S BELT XXL CONT GRAY UNISON | L S BELT XXL CONT GR | L S BELT XXL CONT GRAY UNIS |
| 9 | L S BELT CONT GRAY UNISON XXX | LS BELT XXXL CONT GRAY UNISON | L S BELT 3XL CONT GRAY UNISON | L S BELT 3XL CONT GR | L S BELT 3XL CONT GRAY UNIS |
| 21 | BLING PELVIC TRACTION BELT L | BLING PELVIC TRACT L BELT | BLING PELVIC L TRACTION BELT | BLING PELVIC L TRACT | BLING PELVIC L TRACTION BEL |
| 22 | BLING PELVIC TRACTION BELT XL | BLING PELVIC TRACT XL BELT | BLING PELVIC XL TRACTION BELT | BLING PELVIC XL TRAC | BLING PELVIC XL TRACTION BE |

`RENAMES_S482 OK -- 7 updated, 0 already so, 0 stopped; 23 rows in the table`. Read back live: 23 rows, 23 distinct `new20`, the
longest `new_name` 29; `done_by`, `done_at`, `verified_*` NULL on all seven (none stopped); each `note` ends
`· S482/D676: spelling per S295_ORTHOTIC_RENAMES_CHECKED (the search words kept)`; the other 16 rows equal the backup's, cell for
cell. On the live box Amir's list is not open yet (`renames_ready` False on the copy as it is); the walk opened it on a scratch
copy with the proof forced green there and read the seven D676 spellings from his board.

### 4 · The empty day, everywhere it touches

- **The spine's reader (F-732).** The 04-10 certificate written again: `ok True, failed [], classes {TITLE 1, COLHDR 1,
  EMPTY_FOOTER 1}, data {date_from 2026-10-04, date_to 2026-10-04, days [2026-10-04], empty True}`, seven checks.
  `reports_tile.certify` on it, live: `{'ok': True, 'failed': [], 'count': '0 bills', 'source': 'spine'}` — the tick, not *jaanch
  me fail*. On manojz, against MargArchive: the real EMPTY sheet OLD two failed checks / NEW none; all 56 DETAIL sheets read the
  same, record for record.
- **The collector (F-733).** On a scratch source folder: NEW takes the SUMMARY1 sheet (VERIFIED, lines 0, deleted) and the EMPTY
  sheet (lines 0, `EMPTY — no sale on <day>`, both dates) and rewrites the chain itself; OLD raises on the SUMMARY1 sheet, writes
  no row and **leaves the sale file at rest in the archive**, and gives the EMPTY sheet no reason.
- **The outbox (F-731), manojz.** Placed 09:46:24; `marg_gate.py send` run once, 09:46:30–09:46:31, exit 0:
  `skipping 15495622 (2026-10-04) -- an empty day: no bill to send; the server's door already has it` …
  `everything in the outbox is already on the server. Nothing to send.` `_outbox_state.json` now holds
  `15495622…: result empty_day, http null, business_date 2026-10-04, export_stamp 20261005-084914` (58 entries);
  `_NEEDS_ATTENTION.txt` is gone. The pull's status line, read from `MargPull\_logs\pull_0000-00.log`:

```
05-10-2026  9:31:33.60  PROBLEM: send=1
05-10-2026  9:40:51.25  PROBLEM: send=1
05-10-2026  9:50:44.08  ok
(_last_pull.txt: START 05-10-2026  9:50:01.65 / END 05-10-2026  9:50:44.08 -- ok ; _pull_facts.txt: rc_gate=0)
```

### 5 · The walk — server (run by the installer on scratch copies, before anything was placed) and the install

```
[1/13] kit gates green (SUMS, KIT_ID, the venv's flask, the duty map v6 of this kit, the databases, S480's marg_txt.py for the walk's made-up sheets, the five read-only files at the brief's pins)
[2/13] the four live files at their FROM pins (the brief's section 8)
built ingest/marg_take.py          3ac9bbe0 -> a86a0f26  (29242 bytes)
built ingest/marg_ingest.py        7f6b4dc2 -> 828c4dad  (21918 bytes)
built finance/reports_tile.py      406e452b -> ea15aacb  (64266 bytes)
built finance/spine/marg_read.py   7ec9b325 -> 099d6213  (26800 bytes)
[3/13] live bytes + anchored edits give the four pinned files
[4/13] compiles on /usr/bin/python3 and the venv python (a scratch copy)
new  the collector's, the door's, the shadow's and the rescan's imports  exit 0  imports ok: marg_ingest, marg_take, marg_shadow, marg_rescan_vps; chain: True
new  the spine's evidence job and its reader  exit 0  imports ok: spine_evidence -> marg_read S331.1
old  the collector's, the door's, the shadow's and the rescan's imports  exit 0  imports ok: marg_ingest, marg_take, marg_shadow, marg_rescan_vps; chain: False
old  the spine's evidence job and its reader  exit 0  imports ok: spine_evidence -> marg_read S331.1
[5/13] on scratch copies: the built files import as the crontab and the service import them; reports_tile.py's own selftest on the built file: reports_tile selftest: 40 checks, 0 failures (the same line as the box as it is)
     ok   the S480 kit's marg_txt.py is reachable (it makes the walk's made-up EMPTY and SUMMARY1 sheets)   [/root/deploy/repo/deploy_kits/S480_MARG_TEXT_READERS/marg_txt.py]
-- 1  the chain on the copy of the live table (rebuild_chain -> chain_state)
     ok   both chain probes ran to the end (NEW = the box + S482, OLD = the box as it is)
     ok   NEW marg_take has rebuild_chain and chain_state; NEW reports_tile words the lines
     ok   no table before the first rebuild; 76 rows written; the chain starts on 2026-08-17 (nothing earlier is read: first day per series {'A': '2026-08-17', 'CN': '2026-08-18'})
     ok   chain_state is the chain worked out a second way, straight from mi_sale_line: the same 2 missing number(s), each between the same two days; the same last bill per series   [([['A', 'A003478', '2026-09-08', '2026-09-09'], ['CN', 'CN00203', '2026-09-08', '2026-09-09']], {'A': ['2026-10-03', 'A004000'], 'CN': ['2026-10-02 ...]
     ok   complete = False on the live copy; every gap is between two numbered days of its own series (no gap is 'inside' a day today)
     ok   A.5 -- exactly the one gap the chat measured: A003478 and CN00203 between 2026-09-08 and 2026-09-09, and nothing else; complete = False   [[{'series': 'A', 'between': ['2026-09-08', '2026-09-09'], 'via_empty': [], 'missing': ['A003478'], 'n': 1}, {'series': 'CN', 'between': ['2026-09-08', '2026-09-09'], 'via_empty': [] ...]
     ok   last = the newest numbered day per series: {'A': ['2026-10-03', 'A004000'], 'CN': ['2026-10-02', 'CN00234']}; the copy's EMPTY day(s) ['2026-10-04'] carry no number and break nothing
     ok   the tile on this copy: status() carries bill_chain; ONE line per open gap, worded as A.4 -- Hindi on the card, English in the owner's line
            HI  Bill A003478 aur CN00203 nahi mile (08-Sep se 09-Sep ke beech) — 08-Sep aur 09-Sep ki bikri report dobara banaiye.
            EN  Bill chain: A003478 and CN00203 missing between 08-Sep and 09-Sep — re-export both days.   [(['Bill A003478 aur CN00203 nahi mile (08-Sep se 09-Sep ke beech) — 08-Sep aur 09-Sep ki bikri report dobara banaiye.'], "Today's reports: 0 of 2 arrived · Bill chain: A003478 and CN00203 missing between 08-Sep and 09-Sep ...]
     ok   negative control, the box as it is (marg_take 3ac9bbe0, reports_tile 406e452b): no rebuild_chain, no chain_state, no table before or after, no bill_chain in status(), no card, no 'Bill chain' in the owner's line   [(False, [])]
     ok   the owner's line with the gap clause taken out is the OLD line, letter for letter (the same far morning, before 10:00)   [("Today's reports: 0 of 2 arrived · OVERDUE: salt list 1625 days, category list 1625 days, item list 1625 days", "Today's reports: 0 of 2 arrived · OVERDUE: salt list 1625 days, category list 1625 d ...]
-- 2  invented fixtures (rows keyed w482; the numbers continue the copy's own chain on far days)
     ok   (a) one more number removed -> it is named: A004003 between 2031-03-03 and 2031-03-04, n 1; the copy's own gap list is untouched   [[{'series': 'A', 'between': ['2031-03-03', '2031-03-04'], 'via_empty': [], 'missing': ['A004003'], 'n': 1}]]
     ok   (b) an EMPTY row for a Sunday (2031-03-09) between two days whose numbers meet -> the gap list unchanged   [[{'series': 'A', 'between': ['2031-03-03', '2031-03-04'], 'via_empty': [], 'missing': ['A004003'], 'n': 1}]]
     ok   (b) the same three days on a table that holds nothing else: built, COMPLETE, no gap; an EMPTY row per series (['A', 'CN']); the tile renders NOTHING for a complete chain (no line, no card)   [(True, [], [])]
     ok   (c) an EMPTY row (2031-03-12) between two days whose numbers do NOT meet -> one gap per series naming all three dates: A004011, A004012 and CN00236 between 2031-03-11 and 2031-03-13 via 2031-03-12   [[{'series': 'A', 'between': ['2031-03-11', '2031-03-13'], 'via_empty': ['2031-03-12'], 'missing': ['A004011', 'A004012'] ...]
     ok   (d) a gap inside a day -> that day's gap_inside (A004015 on 2031-03-14; its gap_before is empty)   [([{'series': 'A', 'between': ['2031-03-14', '2031-03-14'], 'via_empty': [], 'missing': ['A004015'], 'n': 1}], ['', 'A004015'])]
     ok       a run of four missing numbers is one word, counted as four: A004019..A004022 between 2031-03-15 and 2031-03-17   [[{'series': 'A', 'between': ['2031-03-15', '2031-03-17'], 'via_empty': [], 'missing': ['A004019..A004022'], 'n': 4}]]
     ok   (e) the tile renders each case's Hindi and English line exactly as A.4 words them, one line per gap, oldest first:
            HI  Bill A004003 nahi mila (03-Mar se 04-Mar ke beech) — 03-Mar aur 04-Mar ki bikri report dobara banaiye.
            EN  Bill chain: A004003 missing between 03-Mar and 04-Mar — re-export both days.
            HI  Bill A004011, A004012 aur CN00236 nahi mile (11-Mar se 13-Mar ke beech, 12-Mar khali tha) — teen dinon ki bikri report dobara banaiye.
            EN  Bill chain: A004011, A004012 and CN00236 missing between 11-Mar and 13-Mar (12-Mar was empty) — re-export all three days.
            HI  Bill A004015 nahi mila (14-Mar ke andar) — 14-Mar ki bikri report dobara banaiye.
            EN  Bill chain: A004015 missing inside 14-Mar — re-export that day.
            HI  Bill A004019 se A004022 tak nahi mile (15-Mar se 17-Mar ke beech) — 15-Mar aur 17-Mar ki bikri report dobara banaiye.
            EN  Bill chain: A004019 to A004022 missing between 15-Mar and 17-Mar — re-export both days.   [['Bill A003478 aur CN00203 nahi mile (08-Sep se 09-Sep ke beech) — 08-Sep aur 09-Sep ki bikri report dobara banaiye.', 'Bill A004003 nahi mila (03-Mar se 04-Mar ke beech) — 03-Mar aur 04-Mar ki bikri report dobara banaiye.' ...]
     ok       no calendar word in any line (no Sunday, no Ravivaar, no holiday, no chhutti)
     ok       the fixtures deleted (md5 LIKE 'w482%') and the chain rebuilt: chain_state is the live state again -- a line leaves by itself when its numbers arrive
-- 4  the spine's reader on invented sheets (the real EMPTY sheet is read on manojz), and the Drive collector
     ok   the invented 3-row EMPTY sheet (title, heads, 'Total No. of | Bills: 0 | DAY TOTAL :'), OLD reader: exactly the two footer checks fail   [['GRAND TOTAL = sum of bill GROSS', 'footer bill count = bills read']]
     ok   NEW reader: no check fails; empty True; the day is the title's (2030-01-02); no bill   [([], {'date_from': '2030-01-02', 'date_to': '2030-01-02', 'days': ['2030-01-02'], 'empty': True})]
     ok   the same through the file door (reading_record on the made-up EMPTY .XLS, as spine_evidence calls it): OLD ok False, NEW ok True -- the certificate the tile reads   [(['GRAND TOTAL = sum of bill GROSS', 'footer bill count = bills read'], [])]
     ok   a sheet with no BILL row whose footer is NOT 'Bills: 0' keeps failing, the same on both (['GRAND TOTAL = sum of bill GROSS', 'footer bill count = bills read'])   [(['GRAND TOTAL = sum of bill GROSS', 'footer bill count = bills read', 'every DAY TOTAL = its bills'], ['GRAND TOTAL = sum of bill GROSS', 'footer bill count ...]
     ok   an invented DETAIL sheet (one bill, its own DAY TOTAL row, 'Bills: 1 | GRAND TOTAL :'): the same checks, the same result, no 'empty'   [([], [], {'TITLE': 1, 'COLHDR': 1, 'DATE': 1, 'BILL': 1, 'ITEM': 1, 'DAY_TOTAL': 1, 'GRAND_TOTAL': 1})]
     ok   the collector (marg_ingest.run on a scratch source folder), NEW: the SUMMARY1 sheet lands VERIFIED with lines 0 -- no sale_lines call -- and is deleted as every sale file is (not at rest)   [(0, {'row': {'type': 'SALE_BILLWISE', 'variant': 'SUMMARY1', 'verdict': 'VERIFIED', 'reason': 'structural', 'lines': 0, 'kept': 0 ...]
     ok   NEW: the EMPTY sheet lands VERIFIED, lines 0, reason 'EMPTY (em dash) no sale on 2030-01-02' -- the door's exact words -- and date_from = date_to = that day   [{'type': 'SALE_BILLWISE', 'variant': 'DETAIL', 'verdict': 'VERIFIED', 'reason': 'EMPTY -- no sale on 2030-01-02', 'lines': 0, 'kept': 0, 'date_from': '2030-01-0 ...]
     ok   NEW: the chain is rebuilt by the collector itself -- 2030-01-02 has an EMPTY row per series, pointing at that sheet   [[['A', 1, '92241de88124655e3df837b190b480e8'], ['CN', 1, '92241de88124655e3df837b190b480e8']]]
     ok   negative control, marg_ingest as it is (7f6b4dc2): the SUMMARY1 sheet is NOT taken (this is the 3-column 'Summary-1' report (BILL NO. | DESCRIPT) -- no mi_file row, and the file STAYS AT REST in the archive (1 file)   [(1, ['marg_ingest 05-10-2026 09:44  listed 2, new 2', '  VERIFIED SALE_BILLWISE          W482__203001 ...]
     ok   negative control: the EMPTY sheet gets no EMPTY reason from the OLD collector (reason '') and no chain exists   [{'type': 'SALE_BILLWISE', 'variant': 'DETAIL', 'verdict': 'VERIFIED', 'reason': '', 'lines': 0, 'kept': 0, 'date_from': '2030-01-02', 'date_to': '2030-01-02'}]
-- 3  the renames (D676): finance.db marg_item_rename, on a scratch copy
     ok   the seven rows (ids [5, 6, 7, 8, 9, 21, 22]) are updated by id AND old_name; none was ticked or seen before (done_by, done_at, verified_* NULL)   [([5, 6, 7, 8, 9, 21, 22], [], [])]
     ok   each carries the brief's spelling, new20 = clip(new_name, 20), new27 = clip(new_name, 27), and the note's S482/D676 words at its end   [{5: 'L S BELT L CONT GRAY', 6: 'L S BELT M CONT GRAY', 7: 'L S BELT XL CONT GRA', 8: 'L S BELT XXL CONT GR', 9: 'L S BELT 3XL CONT GR', 21: 'BLING PELVIC L TRACT', 22: 'BLING PELVIC XL ...]
             5  L S BELT CONT GRAY UNISON L    LS BELT L CONT GRAY UNISON   -> L S BELT L CONT GRAY UNISON    (20: L S BELT L CONT GRAY)
             6  L S BELT CONT GRAY UNISON M    LS BELT M CONT GRAY UNISON   -> L S BELT M CONT GRAY UNISON    (20: L S BELT M CONT GRAY)
             7  L S BELT CONT GRAY UNISON XL   LS BELT XL CONT GRAY UNISON  -> L S BELT XL CONT GRAY UNISON   (20: L S BELT XL CONT GRA)
             8  L S BELT CONT GRAY UNISON XXL  LS BELT XXL CONT GRAY UNISON -> L S BELT XXL CONT GRAY UNISON  (20: L S BELT XXL CONT GR)
             9  L S BELT CONT GRAY UNISON XXX  LS BELT XXXL CONT GRAY UNISON -> L S BELT 3XL CONT GRAY UNISON  (20: L S BELT 3XL CONT GR)
            21  BLING PELVIC TRACTION BELT L   BLING PELVIC TRACT L BELT    -> BLING PELVIC L TRACTION BELT   (20: BLING PELVIC L TRACT)
            22  BLING PELVIC TRACTION BELT XL  BLING PELVIC TRACT XL BELT   -> BLING PELVIC XL TRACTION BELT  (20: BLING PELVIC XL TRAC)
     ok   no two of the table's 23 rows share new20; no new_name is longer than 29; the other 16 rows are unchanged cell for cell; of the seven only new_name, new20, new27 and note moved
     ok   run again: nothing is written twice (7 already so; the note is not appended again)
     ok   negative control (one invented row, id 9482): the keyed update REFUSES a row whose old_name does not match -- nothing is written
     ok   a row already ticked is STOPPED and reported, never renamed under his feet   [[(9482, 'already ticked or seen under the old spelling (done_by, done_at)')]]
     ok   a spelling that would make two rows share their first 20 letters is refused whole (rolled back)
-- 3b + staff-eye (D648): shavez, darpan, amir and the owner on scratch copies, a walk-only login store and secret
     ok   both staff-eye probes ran to the end (NEW: the renames applied and the chain built on its own copy; OLD: the copy as it is)
     ok   Amir's rename list (his board, count #1) with the proof forced green ON THE COPY: the list is open to him and shows the seven D676 spellings   [{'code': 200, 'ready': True, 'n': 23, 'names': {'5': 'L S BELT L CONT GRAY UNISON', '6': 'L S BELT M CONT GRAY UNISON', '7': 'L S BELT XL CONT GRAY UNISON', '8': 'L S BELT XXL ...]
     ok   negative control, the copy without the update: the same list shows S268's spellings (LS BELT ..., ... TRACT L BELT)   [{'5': 'LS BELT L CONT GRAY UNISON', '6': 'LS BELT M CONT GRAY UNISON', '7': 'LS BELT XL CONT GRAY UNISON', '8': 'LS BELT XXL CONT GRAY UNISON', '9': 'LS BELT XXXL CONT GRAY UNISON', '21': 'BLING PELVIC ...]
            as the copy is (no forcing): the list is not open yet for Amir on both sides (renames_ready NEW False / OLD False)
     ok   shavez signs in; the home is byte-equal before and after (19 tiles); every door page too (4 pages) -- the reports tile compared with its gap card taken out   [[]]
     ok      shavez: the reports tile shows the gap line -- ['Bill A003478 aur CN00203 nahi mile (08-Sep se 09-Sep ke beech) — 08-Sep aur 09-Sep ki bikri report dobara banaiye.']; OLD shows no card   [(['Bill A003478 aur CN00203 nahi mile (08-Sep se 09-Sep ke beech) — 08-Sep aur 09-Sep ki bikri report dobara banaiye.'], [])]
     ok      shavez: 6 duties in the map, 2 due now -- each due one is visible (its tile on the home, its marker on its door); the same on both sides   [[]]
     ok   darpan signs in; the home is byte-equal before and after (8 tiles); every door page too (5 pages) -- the reports tile compared with its gap card taken out   [[]]
     ok      darpan: the reports tile shows the gap line -- ['Bill A003478 aur CN00203 nahi mile (08-Sep se 09-Sep ke beech) — 08-Sep aur 09-Sep ki bikri report dobara banaiye.']; OLD shows no card   [(['Bill A003478 aur CN00203 nahi mile (08-Sep se 09-Sep ke beech) — 08-Sep aur 09-Sep ki bikri report dobara banaiye.'], [])]
     ok      darpan: 8 duties in the map, 3 due now -- each due one is visible (its tile on the home, its marker on its door); the same on both sides   [[]]
     ok   amir signs in; the home is byte-equal before and after (3 tiles); every door page too (6 pages) -- the reports tile compared with its gap card taken out   [[]]
     ok      amir: the reports tile shows the gap line -- ['Bill A003478 aur CN00203 nahi mile (08-Sep se 09-Sep ke beech) — 08-Sep aur 09-Sep ki bikri report dobara banaiye.']; OLD shows no card   [(['Bill A003478 aur CN00203 nahi mile (08-Sep se 09-Sep ke beech) — 08-Sep aur 09-Sep ki bikri report dobara banaiye.'], [])]
     ok      amir: 9 duties in the map, 2 due now -- each due one is visible (its tile on the home, its marker on its door); the same on both sides   [[]]
     ok   manoj signs in; the home is byte-equal before and after (54 tiles); every door page too (10 pages) -- the reports tile compared with its gap card taken out   [[]]
     ok      manoj: the reports tile shows the gap line -- ['Bill A003478 aur CN00203 nahi mile (08-Sep se 09-Sep ke beech) — 08-Sep aur 09-Sep ki bikri report dobara banaiye.']; OLD shows no card   [(['Bill A003478 aur CN00203 nahi mile (08-Sep se 09-Sep ke beech) — 08-Sep aur 09-Sep ki bikri report dobara banaiye.'], [])]
     ok      manoj: 9 duties in the map, 7 due now -- each due one is visible (its tile on the home, its marker on its door); the same on both sides   [[]]
     ok   the duty this kit adds to the map (shavez.bill_chain_gap): due on the copy (n 1, since 2026-09-09), its tile 'Aaj ki reports' on Shavez's home, its marker on the door while due   [[{'id': 'shavez.bill_chain_gap', 'tile': 'Aaj ki reports', 'tile_seen': True, 'since': '2026-09-09', 'due_n': 1, 'door_seen': True}]]
     ok   the owner's English line (the page's own status API, signed in as the owner): ['Bill chain: A003478 and CN00203 missing between 08-Sep and 09-Sep — re-export both days.']   [("Today's reports: 5 of 5 arrived · Bill chain: A003478 and CN00203 missing between 08-Sep and 09-Sep — re-export both days.", "Today's reports: 5 ...]
WALK_S482 server GREEN -- 54 checks
[6/13] walk_s482 sections 1, 2, 3, 4 and the staff-eye walk green on scratch copies; every negative control red on the box as it is (above)
[7/13] the lock is held by S482_BILL_CHAIN; finance.db.bak_S482_20261005_094406 made (backup API)
      row  5  LS BELT L CONT GRAY UNISON    -> L S BELT L CONT GRAY UNISON    new20 L S BELT L CONT GRAY  updated
      row  6  LS BELT M CONT GRAY UNISON    -> L S BELT M CONT GRAY UNISON    new20 L S BELT M CONT GRAY  updated
      row  7  LS BELT XL CONT GRAY UNISON   -> L S BELT XL CONT GRAY UNISON   new20 L S BELT XL CONT GRA  updated
      row  8  LS BELT XXL CONT GRAY UNISON  -> L S BELT XXL CONT GRAY UNISON  new20 L S BELT XXL CONT GR  updated
      row  9  LS BELT XXXL CONT GRAY UNISON -> L S BELT 3XL CONT GRAY UNISON  new20 L S BELT 3XL CONT GR  updated
      row 21  BLING PELVIC TRACT L BELT     -> BLING PELVIC L TRACTION BELT   new20 BLING PELVIC L TRACT  updated
      row 22  BLING PELVIC TRACT XL BELT    -> BLING PELVIC XL TRACTION BELT  new20 BLING PELVIC XL TRAC  updated
RENAMES_S482 OK -- 7 updated, 0 already so, 0 stopped; 23 rows in the table, the others unchanged cell for cell
[8/13] Part B: marg_item_rename carries the D676 spellings (keyed by id AND old_name; the other rows unchanged cell for cell)
[9/13] a .bak_S482_<from8> beside each of the four files, read back; placed (each by a rename); md5 read back = the four TO pins
health : finance healthz 200
         /finance/reports/aaj 302 (302/401 = the login gate, expected)
         /finance/stock/page/amir 302 (302/401 = the login gate, expected)
         /finance/clinic/marg/upload 302 (302/401 = the login gate, expected)
[10/13] clinic-finance active (restarted 2026-10-05 09:44:30); healthz 200; the gated pages answer the gate; nothing else moved; the crontab is as it was
collector: 
[11/13] the five-minute collector run once as the crontab spells it: exit 0, nothing raised in the placed code (a quiet run prints nothing; a busy lock or a busy database is the next run's)
mi_bill_chain: 76 rows written; built True; complete False; last {'A': ['2026-10-03', 'A004000'], 'CN': ['2026-10-02', 'CN00234']}
gap: A missing A003478 between 2026-09-08 and 2026-09-09 (n 1)
gap: CN missing CN00203 between 2026-09-08 and 2026-09-09 (n 1)
TILE HI: Bill A003478 aur CN00203 nahi mile (08-Sep se 09-Sep ke beech) — 08-Sep aur 09-Sep ki bikri report dobara banaiye.
TILE EN: Bill chain: A003478 and CN00203 missing between 08-Sep and 09-Sep — re-export both days.
OWNER LINE: Today's reports: 5 of 5 arrived · Bill chain: A003478 and CN00203 missing between 08-Sep and 09-Sep — re-export both days.
CARD ON THE PAGE: yes
CHAIN_LIVE OK
[12/13] the chain lives in mi_bill_chain (built once here; from now on rewritten whenever a sale report or an EMPTY day lands); the tile's lines are above, as the placed page words them
the 04-10 reading before: ok=False failed=['GRAND TOTAL = sum of bill GROSS', 'footer bill count = bills read'] empty=None day= read_at=2026-10-05 09:01:00
its md5 before removal: 3dc6345bac0ad5db72df1dacb48bab5a
spine_evidence:   ok    SALE_BILLWISE            SALE_BILLWISE_DETAIL__2026-10-04__20261005-084914__15495622.XLS
spine_evidence: spine_evidence 2026-10-05 09:46:11: listed 228, read 1 (0 not a report the spine uses), failed 0, store now 228 readings
the 04-10 reading after : ok=True failed=[] empty=True day=2026-10-04 read_at=2026-10-05 09:46:11
a86a0f26d4fc86a51e963b6a1b561323  /root/marg_ingest/marg_take.py
828c4dad6b159207b034d8129aed3ab7  /root/marg_ingest/marg_ingest.py
ea15aacbb6a00131d3f02664b0c1df42  /root/finance/reports_tile.py
099d621315f3bf9297a9b4626a5caee5  /root/finance/spine/marg_read.py
[13/13] done · healthz 200 · backups: /root/finance/finance.db.bak_S482_20261005_094406, a .bak_S482_<from8> beside each file, /root/finance/spine/readings/15495622be4e21b5daa8d1d7580fc6db.json.bak_S482
S482_BILL_CHAIN: DONE
```

### 6 · The walk — manojz (build time; MargArchive read where it lies, the outbox dry on scratch copies)

```
-- 4  the spine's reader on the real sheets of MargArchive (verdicts only; no line of a sheet is printed)
  ok   the real EMPTY sheet of 04-10 is in MargArchive (1 file)
  ok   OLD reader (7ec9b325) on it: exactly two failed checks -- ['GRAND TOTAL = sum of bill GROSS', 'footer bill count = bills read']
  ok   NEW reader on it: no failed check; empty True; the day from the title (2026-10-04); no bill; the same md5 (15495622)   [([], {'TITLE': 1, 'COLHDR': 1, 'EMPTY_FOOTER': 1})]
  ok   every DETAIL sheet in the archive (56 files): the same checks, the same result, record for record (56 of them ok on both)   [[]]
-- 5  the outbox, DRY, on scratch copies of _outbox_state.json and index.csv (the outbox files are empty stand-ins of the same names)
  ok   the real EMPTY row is in index.csv: VERIFIED, rows = 3 (a string), date 2026-10-04
  ok   OLD marg_gate (52f502d1), send --dry-run: the EMPTY file of 04-10 (15495622) IS in the send list -- with the invented empty weekday (e482e482)   [['15495622', 'e482e482']]
  ok   NEW marg_gate, the same copies: both are told 'an empty day' and skipped; nothing is left to send   [([], ['15495622', 'e482e482'])]
  ok   its outbox entry: result empty_day, http null, business_date 2026-10-04, the export stamp, the brief's note   [{'business_date': '2026-10-04', 'export_stamp': '20261005-084914', 'http': None, 'note': '...', 'result': 'empty_day', 'when': '2026-10-05 09:38:08'}]
  ok   a dry run removes no file: the stand-in _NEEDS_ATTENTION.txt is still there
  ok   the same copy, send for real (nothing is left to send, so nothing is posted -- the URL given is a dead local port): exit 0 and the stale _NEEDS_ATTENTION.txt is gone   [(0, [])]
  ok   status (the picture, as of an invented 05-01-2030): OLD lists the empty weekday as NOT SENT; NEW no longer lists it (on server: yes) -- so _UPLOAD_NOW is not refilled with it   [(['2030-01-03   yes       NO         NOT SENT -- run SEND_OUTBOX.bat'], ['2030-01-03   yes       yes        '])]
  ok   refresh_upload_folder on the NEW picture copies nothing
  ok   with an invented DETAIL sheet (d482d482, 40 rows) waiting: NEW sends exactly that one -- a sheet with bill rows is never touched by the rule; OLD would send it and the two empty ones   [(['d482d482'], ['15495622', 'e482e482', 'd482d482'])]
  ok   an empty_day entry is NOT a delivery (delivered_stamps ignores it): a later real DETAIL sheet of that date is still sent   [{}]
  ok   marg_gate's own selftest: NEW selftest: 56/56 (three more checks than OLD selftest: 53/53)
WALK_S482 manojz GREEN -- 15 checks
```

**Negative controls, in one place.** OLD `marg_take` / `reports_tile`: no `rebuild_chain`, no table, no `bill_chain`, no card, no
clause · OLD `marg_read`: exactly the two footer checks fail on the EMPTY sheet (invented and real) · OLD `marg_ingest`: SUMMARY1
raises and stays at rest; EMPTY gets no reason · the copy without the update: Amir's list shows S268's spellings · the keyed update
refuses a wrong `old_name`, stops a ticked row, refuses a 20-letter clash · OLD `marg_gate`: the EMPTY file is in the send list and
the picture says NOT SENT.

### 7 · Calls made (each one mine; the brief's words first where they differ)

1. **A missing number = one no day of the series carries; named once, on the first day that carries a higher number.** With
   Marg's numbers in day order (measured: no bill on two days) this is the brief's rule exactly; it stays right if a bill is ever
   back-dated. The walk checks `chain_state` against a second, independent working-out from `mi_sale_line`.
2. **A run of three or more missing numbers is one word** — `A003481..A003499` in the column, *"A003481 se A003499 tak"* / *"A003481
   to A003499"* on the screen; `n` counts every number. One or two are written singly, as the brief words them. Reason: a lost week
   would be a line of ~150 numbers. Today's gap is unaffected.
3. **A gap inside a day has its own words** (the brief words only the between-days cases): *"Bill A… nahi mila (17-Sep ke andar) —
   17-Sep ki bikri report dobara banaiye."* / *"Bill chain: A… missing inside 17-Sep — re-export that day."* One number says
   *nahi mila*, more say *nahi mile*.
4. **`chain_state` also returns `built`.** No table yet = not known complete (`built False, complete False`, no gap).
5. **`mi_bill_chain` rows are generic in the series letters** (`^[A-Z]{1,3}\d+$`): only `A` and `CN` exist today; a new series
   would get its own chain instead of being silently ignored.
6. **The reader's empty day has one witness of its own** — *an empty day is named by its title (AS ON)* (a seventh check, only on
   an EMPTY sheet). `grand` is the footer's own figure (0.0 when blank), so *GRAND TOTAL = sum of bill GROSS* stays an honest check.
   `READER_VERSION` is not bumped ("nothing else in the file").
7. **The outbox rule needs a KNOWN row count, 1–3.** The brief writes `int(row["rows"] or 0) <= 3`; a blank count would read as an
   empty day and a real sheet would never be sent. It also holds under `--resend-all` (the route cannot take the sheet).
8. **`do_send` removes a stale `_NEEDS_ATTENTION.txt` when nothing is left to send** (never in a dry run) — a fourth small edit in
   `marg_gate.py`, plus three selftest checks. Without it the note of 09:40 would have stayed for ever: the old code removed it
   only after a send that had something to send.
9. **The duty map gains `shavez.bill_chain_gap` (v6)** — CLAUDE.md's "every duty has a door"; the brief does not name the map. Door:
   the tile's red line (marker *ki bikri report dobara banaiye*). Owner's line: the tile's own English line (`coded`), so the
   Needs-you list raises nothing new (a duty with a door never does). Its `due_sql`, run on the live database after the install:
   `(1, '2026-09-09')`. The kit carries the map it ran with (`.gitignore` line added, exact path).
10. **The installer runs `spine_evidence.py` once** (evidence only, under the cron's lock) after setting the old reading aside —
    so the clean certificate was read back in the same run. `spine_build.py` was not run by me.
11. **The five read-only files are gated at the brief's pins** before anything is built (the walk reads them).
12. **Part B stays if a later step had gone red** (it did not): the renames are right on their own; only the files would have
    been put back.

### 8 · Not done, and why

- **The re-export of 08-Sep and 09-Sep** — a person's work in Marg; the line asks for it.
- **The parent's line, not done here (the brief's own words):** the clinic's upload route (`finance_app.py` /
  `finance_returns.py` — the `no_item_detail` answer) should take an EMPTY day as a day with no bills, so the *Sale bills from
  Marg* freshness leg stops ageing over a no-sale day.
- Nothing in `stock_app.py`, `amir_day.py`, `purchase_app.py`, `item_alias.py` (its `THE_22` keeps S268's spellings on purpose —
  S483), no medical-PC file, no crontab, no parent file. S483 / S484 / S485 as the brief lists them.

### 9 · Outside the brief, noticed

1. **The spine has not rebuilt since 08:00 today.** `spine.log`: every ten-minute build since about 08:10 ends `GATE FAILED --
   nothing swapped`. Three reasons were listed at 09:20; this kit removes one (the 04-10 sale sheet's witness). **Two remain and
   are not this kit's:** (a) *every purchase line … belongs to exactly one bill* — 208 lines of
   `PURCHASE_BILLITEMWISE_DEFAULT__2026-09-01_to_2026-10-03__20261005-075955__de92f5d5.XLS`; (b) *every CATEGORY_WISE_ITEM_LIST
   export passes its own witness* — `CATEGORY_WISE_ITEM_LIST_DEFAULT__2026-10-05__20261005-075955__f62cc9e3.XLS`. Both files
   arrived at 07:59 with S480's text readers. Until they are settled `spine.db` stays the 08:00 build. The 09:50 run, after this install, shows exactly that: the sale-export line is gone from the list, (a) and (b) remain, and `spine.db` is still the 08:00 file.
2. **Who sees the gap line.** `/finance/reports/aaj` opens for darpan and amir too (the staff-eye walk rendered it for all four
   logins); the red line shows to whoever opens the page, not only Shavez. The tile itself is on Shavez's and the owner's homes.
3. **`marg_gate.business_days` still drops every Sunday** (`weekday() != 6`) from the PC's picture and from `covered_days` — a
   calendar rule that S484's list (the tile's banner, `spine_build`, `export_watch`, `darpan_kal`, the freshness legs) does not
   name. Today it only means the picture never listed 04-Oct at all.
4. **`/root/marg_ingest/logs/ingest.log` ends with a `database is locked` traceback** of an earlier collector run (it was there at
   09:27, before this install; the log carries no time). The run after it, and the one the installer made, were clean.
5. **The brief itself was untracked in git** until this publish (it went up with the kit).
6. `mi_sale_line` still holds the one June test day; the chain starts on 17-Aug by a constant with its reason in a comment
   (`CHAIN_FROM_DAY`), as the brief orders.

### 10 · Undo

Server: put back the four `<file>.bak_S482_<from8>`, restart `clinic-finance`, healthz 200, read the md5s back. `mi_bill_chain`
may stay (the old files do not read it). The old reading is `….json.bak_S482`. The seven renames come back only from
`finance.db.bak_S482_20261005_094406`, row by row, said first — and only while Amir has ticked none.
manojz: `python -B deploy_kits\S482_BILL_CHAIN\install_manojz_S482.py --undo`.
