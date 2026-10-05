# REPORT — S480_MARG_TEXT_READERS (D675 · F-726 b, F-728, F-729, F-730)

Built, walked, installed (server), placed (manojz), packed (medical PC) and published by Claude Code on 05-Oct-2026 from
`claude_code_briefs/S480_MARG_TEXT_READERS.md`. Kit: `deploy_kits/S480_MARG_TEXT_READERS/`. All times IST, read from a clock.

## For Dr Manoj

- **Every report you export from Marg as text is now understood** — purchase (all four kinds), the salt, category and item lists, the
  short sale statement, sale return, stock valuation, expiry and the stock register. The server, your PC and — since your line at
  07:59 — the medical PC are all updated. Yesterday's reports that had been turned away were taken at once: all 15 reached the server
  and were accepted.
- **A day with no sale is now accepted as an answer**, not thrown out as a broken file. A blank report made for *today* is still refused,
  with the staff's own words ("aaj ki report — kal ki tareekh chun kar dobara banaiye").
- **The orthotic proof has not run yet.** It needs Sunday's empty day. The one thing left: **one sale report (with item detail) of
  04-10-2026 from Marg** — you or Shavez — and the proof runs by itself.
- **The salts page no longer treats the shop's name as a salt.** Tested on a copy, "Marg confirms" goes from 78 to 82; the corrected
  list is already in place on the live page.
- It works: 91 checks green (60 on your PC against the real reports, 31 on the server on a copy), the server is healthy, and every
  changed file has a backup beside it. One thing still open for the chat is marked **(1)** below: on a closed **weekday**, Shavez's
  screen would wrongly say "jaanch me fail" for a correct empty report. Sunday's is not affected.

---

## For the chat

### 0 · Added 08:15 — the medical PC's files were delivered (the owner's line, 07:59)

Everything below this section is the record as it stood at 07:30, when `deliver_S480.ps1` had not been run. At 07:59 the owner gave
the line in the Claude Code window and it was run from the kit folder (the kit's `SUMS.md5` checked first: 0 mismatches).

- **Drive `ToMedical\_kit`, 07:59:17:** all three at their FROM pins → placed → read back `marg_txt.py` `14b75012…`, `marg_watch.py`
  `58b54f37…`, `KIT_MANIFEST.txt` `ea2b437a…`; `marg_push.py` `566e189e` not changed. Backups beside them: `marg_txt_S454.py.superseded`,
  `marg_watch_S454P4C.py.superseded`, `KIT_MANIFEST_S454P4C.txt.superseded` (each read back at its FROM pin).
- **The medical PC, heartbeat of 07:59:51:** `WATCHER FILE … md5 58b54f37`, `marg_watch.py up to date (58b54f37)`, `marg_txt.py up to
  date (14b75012)`; the watcher alive under a new process. Its log, 07:59:52: `marg_watch S480 starting -- text reader S480, text route
  LIVE`.
- **Its first start (D.4), counted from its log:** every text refused in the last three days was offered again — 13 taken (`a text
  refused earlier is taken now`; the others were the same reports under their twin names), plus the two texts lying in the watched
  folder: 15 captured in all. **The 09:43:21 text of 04-10 stayed refused**, by the stamp in its name, with the staff's words — as B.1
  requires (the one "would not convert" line of the start).
- **The server, 08:00:45 → 08:01:51, 15 rows, all VERIFIED, all by push:** PURCHASE_BILLWISE, PURCHASE_ITEMWISE ×3,
  PURCHASE_BILLITEMWISE, SALT_WISE_ITEM_LIST ×2, CATEGORY_WISE_ITEM_LIST, ITEM_MASTER, STOCK_EXPIRY/NEAR, STOCK_VALUATION/BATCHWISE,
  SALE_BILLWISE/SUMMARY1, SALE_RETURN/SUMMARY, SALE_RETURN/DEFAULT, STOCK_ITEM_LEDGER/TEXT. The four patient-bearing ones (short sale,
  both returns, the register) are `kept 0` and **none is at rest** in the archive (looked for by name); `archive/SALE_BILLWISE` holds
  no file. No refusal today.
- **The reports tile, read on a read-only connection at 08:04:** sale `ok` (18 bills — the DETAIL report of 03-10; the short statement
  of the same day did **not** displace it), closing stock `ok`, valuation `ok`, expiry `ok`, salt list `ok` (380 items); no banner;
  the owner's three lists (salt, category, item) all fresh.
- **The salts job by itself, 08:10:** posted the text-made list (`6340e66b`, 380 rows, 242 salts) → `server 200`; the page's list:
  0 items under the firm's name.
- **The Drive collector:** 08:10:42, `listed 303, new 0, failed 0` — the 15 sheets reached Drive after the push had already recorded
  them, so finding (2) below did not bite. healthz 200 throughout; 0 error lines in the service's journal.

Two things seen in this, neither a fault of the day: a text taken at a re-offer carries **today's** capture stamp, so the lists
exported on 04-Oct are dated 05-Oct on the server (S397's rule, unchanged); and the salt list the page now holds is the text of 14:15,
which the analysis records as the same rows as the Excel of 17:55.

**Still open:** the EMPTY day of 04-10 (one DETAIL sale export of 04-10-2026 from Marg), and findings **(1)** and **(2)** of §8, which
the delivery makes live: (1) for the first closed weekday, (2) only if a push ever fails before Drive delivers.

### 1 · What ran, and when

| step | when (IST, 05-Oct-2026) | result |
|---|---|---|
| build lock `/root/deploy/.claude_code_build.lock` (owner `S480_MARG_TEXT_READERS`) | taken 07:25:06 | held until this report was written, then removed |
| server installer, real run (from `/tmp/S480kit`, `md5sum -c SUMS.md5` 17 of 17 OK — the repository's kit, byte for byte) | 07:25:06 → 07:25:24 | `S480_MARG_TEXT_READERS: DONE`, exit 0 |
| `clinic-finance` restarted (the only service restarted) | 07:25:15 | active · `/finance/healthz` 200 |
| manojz: `install_manojz_S480.py` | 07:25:53 | `S480 manojz: PLACED` |
| medical PC | — | **packed, not placed**; `deliver_S480.ps1` was **not run** (parsed for syntax only: 0 errors) |

A dry run of the same installer (`DRY=1`, nothing placed) ran green at 07:18 before the real one.

### 2 · Pins, FROM → TO, read back

**Server** (read back by the installer and again by a separate read-only pass at 07:25:44):

| file | FROM | TO (read back) | backup beside it (md5 = FROM, read back) |
|---|---|---|---|
| `/root/marg_ingest/signatures.json` | `64943ac6719a0f2ee06a15ef56d8c3d1` | `21604e0fa84f0403e1a86e7584c3a1bd` | `.bak_S480_64943ac6` |
| `/root/marg_ingest/marg_report.py` | `eeab56055be76fec9531399ce9a0556e` | `2bf284ba0c7f6bc4e6902e54379c8e12` | `.bak_S480_eeab5605` |
| `/root/marg_ingest/lib/marg_report.py` | `eeab56055be76fec9531399ce9a0556e` | `2bf284ba0c7f6bc4e6902e54379c8e12` | `.bak_S480_eeab5605` |
| `/root/marg_ingest/marg_take.py` | `b41195e4ce853272ecf25b06343e3e16` | `3ac9bbe03abf5c01c4ebc1bfffd30da2` | `.bak_S480_b41195e4` |
| `/root/marg_ingest/lib/push_expected.py` | `4b3b700c1640591a3723d4fce3de5603` | `1ba529851eed04973e4bd540547c447c` | `.bak_S480_4b3b700c` |
| `/root/finance/marg_report.py` (the copy the door runs) | `f9370dde648f629461d4efac2b4805af` | `d9c9a9b20ffd6ad35fe1564b0183680d` | `.bak_S480_f9370dde` |
| `/root/finance/marg_door.py` | `6a2366638234bf0ddf9c7d6c745c975b` | `dc5c1e36d2c8bee2cd556de5c5e4f018` | `.bak_S480_6a236663` |
| `/root/finance/salts_refresh.py` | `40cb26159c59d55d33d871abe36646ef` | `f002161807b700c664846a8af2873646` | `.bak_S480_40cb2615` |
| `/root/finance/reports_tile.py` | `9d2244a6d56d3791428982565f620a97` | `406e452b2e3cf5991e89100ee867e1d6` | `.bak_S480_9d2244a6` |

Database backup (backup API, before placing): `/root/finance/finance.db.bak_S480_20261005_072506` (31,014,912 bytes).
Read only, unchanged before and after: `/root/marg_ingest/marg_router.py` `318086e36b0088f2da57b95d19a86b98`; `marg_ingest.py`,
`marg_shadow.py`, `marg_rescan_vps.py`, `finance_app.py`, `portal.py`, `tile_grants.json`, `stock_app.py`, `amir_day.py`, `purchase_app.py`,
`order_sheet.py`, `item_check.py`, `shelf_figure.py` and the crontab (the installer compares each before and after, and undoes itself if
one moved). No table was created.

**manojz** (read back by `install_manojz_S480.py`, then by its `--check`):

| file | FROM | TO (read back) | backup beside it |
|---|---|---|---|
| `D:\Downloads\margsync\MargPull\signatures.json` | `7f72c572808218fbfc008373336beea8` | `21604e0fa84f0403e1a86e7584c3a1bd` — **the server's bytes** | `.bak_S480_7f72c572` |
| `D:\Downloads\margsync\MargPull\marg_report.py` | `28b47d447cfd966411742055717a5c56` | `2bf284ba0c7f6bc4e6902e54379c8e12` — the kit's file | `.bak_S480_28b47d44` |
| `D:\Downloads\margsync\PUSH_STOCK_DAILY.bat` (one line, `set KIT=`) | `5cbec862593e201884b8f372775c7db2` | `fe8b7f549d1ee1ba6c21431ce65d80e1` | `.bak_S480_5cbec862` |

Read only, unchanged: `MargPull\marg_router.py` `318086e3`, `MargPull\expected_on_capture.py` `bd8565d6`. In the kit folder, new:
`push_expected.py` `1ba529851eed04973e4bd540547c447c` and `marg_report.py` `2bf284ba…` — the copies the `.bat` now runs. Run from the kit
folder with `--dry-run`, the kit's `push_expected.py` printed the same 132 lines as `S208_STOCK_LEDGER`'s on today's archive (baseline
03-09-2026, 27 sale days to 03-10-2026; nothing sent).

So: **both `signatures.json` are the same bytes** (`21604e0f…`); **the four non-finance `marg_report.py` are the same bytes**
(`2bf284ba…`: two on the server, manojz's, the kit's), and the finance copy carries the same EMPTY rule at the same anchors, its extras kept.

**Medical PC — packed in the kit, not placed:**

| file | FROM (read from the mirror, and from Drive `ToMedical\_kit`) | TO (packed) |
|---|---|---|
| `marg_txt.py` | `ed17bb763c202f81cb8b3708fac61b52` | `14b750120233e349d713d9de1d1edb7a` |
| `marg_watch.py` | `297cc3d9ff5edddc894390426bdc463a` | `58b54f37865cb487720b95eaa4aedde5` |
| `KIT_MANIFEST.txt` | Drive holds `9e754e5c48407f0f08b72746e76a2bb2` (CRLF) | kit `c9681701ac23d4cbcf8ed39bc23e2b48` (LF) → Drive `ea2b437a79f4829790820773e4ba26a9` (CRLF) |

Both selftests pass on Python 3.14 (manojz) and Python 3.9 (the server): `marg_txt.py --selftest` and `marg_watch.py --selftest`,
`SELFTEST OK`. `make_s480.py --medical … --check` rebuilds both from the mirror's bytes and they are the kit's files, byte for byte
(marg_txt: 12 anchored edits, two of which add the cutter block and the selftest block; marg_watch: 11 anchored edits; every anchor
exactly once).

### 3 · The walk on manojz — sections 1, 2, 3, 4a, 5, 6, 7 (real samples; 60 checks, GREEN)

Counts, verdicts and titles only: **no line of a sale or register text is printed anywhere**, and the converted samples were deleted
when the walk ended.

```
  ok   the OLD files are the ones the medical PC runs (marg_txt ed17bb76, marg_watch 297cc3d9); the router is 318086e3, not edited
-- 1  byte equality of the three live kinds (every text the medical PC took since 24-Sep)
  ok   every captured text converts to the SAME BYTES by marg_txt S480 and by ed17bb76 (21 texts; 21 when the brief was written)   [(21, 21, [])]
  ok   S480's output is the kept conversion in MargArchive\_spool, paired by the capture stamp and slot in the spool name (21 pairs)   [(21, 21)]
  ok   negative control: one figure changed in a text -> other bytes (or the reader's own totals refuse it)
-- 2  the cutter against Marg's own Excel (the prototype's normalisation)
  ok   093801 text  =  Marg's own Excel of the same moment, cell for cell: 18 rows, 72 cells, 0 rows differ   [(18, 18, 72)]
  ok      negative control: one figure changed in that text -> exactly one cell differs   [1]
  ok   094002 text  =  Marg's own Excel of the same moment, cell for cell: 47 rows, 564 cells, 0 rows differ   [(47, 47, 564)]
  ok      negative control: one figure changed in that text -> exactly one cell differs   [1]
  ok   141519 text  =  Marg's own Excel of the same moment, cell for cell: 701 rows, 3505 cells, 0 rows differ   [(701, 701, 3505)]
  ok      negative control: one figure changed in that text -> exactly one cell differs   [1]
  ok   the three same-moment pairs come to 4,141 cells   [4141]
  ok   ITEM_MASTER (text 04-Oct, Excel 18-Sep): the spine's reader reads both as ITEM_MASTER; of the Excel's 375 items 374 are in the text identical at the reader's output (the rest changed in Marg between the two days)   [(381, 375, 374, 'text ok=True', 'excel ok=True', [])]
  ok      negative control: one figure changed on one item's line in that text -> one item fewer found
  ok   CATEGORY_WISE_ITEM_LIST (text 04-Oct, Excel 18-Sep): the spine's reader reads both as CATEGORY_WISE_ITEM_LIST; of the Excel's 81 items 74 are in the text identical at the reader's output (the rest changed in Marg between the two days)   [(341, 81, 74, 'text ok=False', 'excel ok=True', ['serial restarts at 1 under every he ...
  ok      negative control: one figure changed on one item's line in that text -> one item fewer found
   (the known nuance, named: a company name overrunning two column heads -- Marg's sheet puts its first word one cell further
    right than rule A; the item list is therefore proved at the reader's output: item, packing, company)
-- 3  landing: every sample of A.2 through the router (read_preamble -> identify -> verify) with the NEW signatures
  ok   093801  PURCHASE  -> NEW: VERIFIED PURCHASE_BILLWISE/DEFAULT   (OLD signatures: VERIFIED PURCHASE_BILLWISE/DEFAULT)   [structural]
  ok   094002  PURCHASE  -> NEW: VERIFIED PURCHASE_ITEMWISE/DEFAULT   (OLD signatures: VERIFIED PURCHASE_ITEMWISE/DEFAULT)   [structural]
  ok   183328  PURCHASE  -> NEW: VERIFIED PURCHASE_ITEMWISE/DEFAULT   (OLD signatures: VERIFIED PURCHASE_ITEMWISE/DEFAULT)   [structural]
  ok   090549  PURCHASE  -> NEW: VERIFIED PURCHASE_SUPPLIERWISE/DEFAULT   (OLD signatures: VERIFIED PURCHASE_SUPPLIERWISE/DEFAULT)   [structural]
  ok   183119  PURCHASE  -> NEW: VERIFIED PURCHASE_BILLITEMWISE/DEFAULT   (OLD signatures: VERIFIED PURCHASE_BILLITEMWISE/DEFAULT)   [structural]
  ok   141519  SALT      -> NEW: VERIFIED SALT_WISE_ITEM_LIST/DEFAULT   (OLD signatures: VERIFIED SALT_WISE_ITEM_LIST/DEFAULT)   [structural]
  ok   143140  CATEGORY  -> NEW: VERIFIED CATEGORY_WISE_ITEM_LIST/DEFAULT   (OLD signatures: UNKNOWN)   [structural]
  ok   155650  ITEMS     -> NEW: VERIFIED ITEM_MASTER/DEFAULT   (OLD signatures: VERIFIED ITEM_MASTER/DEFAULT)   [structural]
  ok   182159  SALE_SHORT -> NEW: VERIFIED SALE_BILLWISE/SUMMARY1   (OLD signatures: VERIFIED SALE_BILLWISE/SUMMARY1)   [structural]
  ok   182424  SALE_SHORT -> NEW: VERIFIED SALE_BILLWISE/SUMMARY1   (OLD signatures: VERIFIED SALE_BILLWISE/SUMMARY1)   [structural]
  ok   183024  RETURN    -> NEW: VERIFIED SALE_RETURN/SUMMARY   (OLD signatures: VERIFIED SALE_RETURN/SUMMARY)   [structural]
  ok   183541  RETURN    -> NEW: VERIFIED SALE_RETURN/DEFAULT   (OLD signatures: VERIFIED SALE_RETURN/DEFAULT)   [structural]
  ok   182137  VALUATION -> NEW: VERIFIED STOCK_VALUATION/BATCHWISE   (OLD signatures: REFUSED)   [structural]
  ok   EXPIRY  EXPIRY    -> NEW: VERIFIED STOCK_EXPIRY/DEFAULT   (OLD signatures: VERIFIED STOCK_EXPIRY/DEFAULT)   [structural]
  ok   183952  LEDGER    -> NEW: VERIFIED STOCK_ITEM_LEDGER/TEXT   (OLD signatures: REFUSED)   [structural]
  ok   all fifteen samples of A.2 land VERIFIED and typed with the NEW signatures   [15]
  ok   negative control, the server's OLD signatures (64943ac6): category UNKNOWN, valuation REFUSED, register REFUSED (its title is known there, its two-line heads are not -- the prototype's cut lost the title and so read UNKNOWN)   [{'CATEGORY_WISE_ITEM_LIST': 'UNKNOWN', 'STOCK_VALUATION': 'REFUSED', 'STOCK_ITEM_LEDGER': 'REFU ...
  ok   the register is a PHI type by its signature (STOCK_ITEM_LEDGER): the server deletes it at the door (walked there, section 4)
  ok   negative control: marg_txt ed17bb76 (the medical PC today) takes none of the fifteen
  ok   both signatures.json will be the same bytes: the kit's file is what manojz's own copy becomes (7f72c572 + the edits)   [21604e0fa84f0403e1a86e7584c3a1bd]
-- 4a the empty day, on the real zero-bill text of 04-Oct 09:43:21 (it carries no bill, so no patient)
  ok   the real text is, byte for byte, the made-up sample of the selftest with its date (so the server's section 4 walks the same shape)   [(885, 887)]
  ok   exported the NEXT day -> a no-sale day: title, heads, 'Total No. of | Bills: 0 | DAY TOTAL :' and six zeros; info empty, as_on 04-10-2026   [['Total No. of', 'Bills: 0', 'DAY TOTAL :']]
  ok   exported on its own day (as it was) -> refused in the staff's words
  ok   re-offered from refused by its stamp -> refused in the staff's words
  ok   the kit's marg_report (the four non-finance copies are these bytes) reads it ok / empty, one day, from the title   [(True, True, [])]
  ok   the EMPTY sheet through the router: NEW signatures VERIFIED SALE_BILLWISE/DETAIL; OLD signatures REFUSED (TRUNCATED: GRAND TOTAL)   [('VERIFIED', 'REFUSED')]
  ok   negative control: marg_txt ed17bb76 refuses the text ('no GRAND TOTAL line')
  ok   negative control: manojz's OLD marg_report (28b47d44) says TRUNCATED of the same sheet
-- 5  the marker: every SALE_BILLWISE sheet in MargArchive carries 'Total No. of' within its last 40 rows (B.3)
  ok   57 sale sheets read (56 when the brief was written): every one carries 'Total No. of' in its last 40 rows -- one that does not = STOP   [(57, 57, [], {'DETAIL': 57})]
  ok   with the NEW marker and the kit's reader every one of them still verifies exactly as with the OLD ones (57 of 57, was 57)   [(57, 57)]
  ok   negative control: a sale sheet cut before its footer is REFUSED by the router under the new marker (TRUNCATED)   [REFUSED]
-- 6  the watcher, in a scratch folder with a made-up marg_push.py (no key, no address: nothing can be sent)
  ok   both watcher probes ran to the end
  ok   a made-up salt list cut short, saved as user_1.txt, is KEPT and logged by S480 (kind SALT, a reason, a note waiting)   [NOT TAKEN: a salt-wise item list without the '*** End of Report ***' line at the]
  ok   negative control: the watcher of today (297cc3d9) drops it -- 'not a Marg report', nothing kept, no line in the log   [not a Marg report]
  ok   its report.txt twin with the same bytes is not kept twice (S480: one kept copy; before: none at all)   [(1, 0)]
  ok   the complete made-up salt list under user_2.txt is TAKEN by S480 as the reader's own .XLS
  ok   every kind word reaches note_of: CATEGORY, EXPIRY, ITEMS, LEDGER, ORDER, PURCHASE, RETURN, SALE, SALE_SHORT, SALT, STOCK, VALUATION   [['CATEGORY', 'EXPIRY', 'ITEMS', 'LEDGER', 'ORDER', 'PURCHASE', 'RETURN', 'SALE', 'SALE_SHORT', 'SALT', 'STOCK', 'VALUATION']]
  ok   negative control: before, every one of the nine new kinds had no word (the note said nothing of what it was)   [['', 'ORDER', 'SALE', 'STOCK']]
  ok   the census lists the kept text with its title (before: not listed)
  ok   a note never carries a line of the file
-- 7  the salts reader on the archive's list of 04-Oct 17:55 (235e9643)
  ok   the list 235e9643 is in MargArchive
  ok   NEW: 0 items under the firm's name, 380 items kept   [(0, 380)]
  ok   NEW: the four the brief names land on their salts (CALFLIP CQ -> CALCIUM + CISSUS, CROCAL EXTRA TAB -> CALCIUM + CISSUS, JARDIANCE 10 -> EMPAGLOFLIZON 10, NURVION LC TAB -> LEVOCARNITINE)
  ok   negative control, OLD (40cb2615): 12 items filed under the firm's name   [(12, 380)]
  ok   only those 12 items change salt between OLD and NEW; nothing else in the list moves   [12]
WALK_S480 manojz GREEN -- 60 checks
```

### 4 · The walk on the server — sections 4 and 8 (scratch copies; 31 checks, GREEN) — the real run's output

```
-- 4  the empty day (a made-up zero-bill text AS ON 02-01-2030 -- the real 09:43:21 text is the same bytes but for its date: section 4a)
  ok   marg_txt S480, exported the NEXT day -> the EMPTY sheet (3 rows; info empty, as_on 02-01-2030)
  ok   the same text exported on ITS OWN day -> refused with the staff's words: aaj ki report -- kal ki tareekh chun kar dobara banaiye
  ok   negative control: marg_txt ed17bb76 refuses it ('no GRAND TOTAL line')
  ok   both door probes ran to the end (NEW = the box + S480, OLD = the box as it is)
  ok   every patched read_report -- /root/marg_ingest, its lib copy, and /root/finance (the one the door runs) -- reads the EMPTY sheet ok / empty, one day, from the title (2030-01-02), no bills; day_totals gives that day with zeros   [{'ingest': (True, True, ['2030-01-02']), 'lib': (True, True, ['2030-01-02']), 'finance': (True ...
  ok   negative control: each OLD read_report says TRUNCATED of the same sheet (not ok, no empty)   [{'ingest': (False, True), 'lib': (False, True), 'finance': (False, True)}]
  ok   the door (marg_take.take) on the scratch copy: the EMPTY sale is TAKEN, VERIFIED SALE_BILLWISE/DETAIL, lines 0, date_from = date_to = 2030-01-02   [('TAKEN', 'VERIFIED', 'SALE_BILLWISE', 'DETAIL', '2030-01-02')]
  ok   its mi_file row: reason 'EMPTY (em dash) no sale on 2030-01-02' exactly as the brief words it, dates the title's, kept 0; mi_sale_line untouched for its md5; the file itself deleted as every sale file is (S186) -- nowhere at rest   [('EMPTY -- no sale on 2030-01-02', 0, [])]
  ok   the same bytes again: ALREADY, nothing counted twice
  ok   negative control, the door as it is: the same sheet is REFUSED (TRUNCATED) -- no EMPTY row   [('TAKEN', 'REFUSED', "TRUNCATED — the completeness marker 'GRAND TOTAL' is missing; the expo")]
  ok   the short sale statement (SUMMARY1) LANDS through the new door: TAKEN, VERIFIED SALE_BILLWISE/SUMMARY1, no line read, deleted (S186)   [('TAKEN', 'VERIFIED', 'SUMMARY1', [])]
  ok   negative control, the door as it is: the same sheet is NOT taken ('could not be read here: this is the 3-column 'Summ') and no mi_file row is written   [('REFUSED', ['archive/SALE_BILLWISE/2030-01/SALE_BILLWISE_SUMMARY1__2030-01-01__20300103-090100__6f293e5f.xls'])]
   NOTED (outside this kit's edit, mended by it at THIS door): the door as it is leaves that refused short statement AT REST in the
   archive (archive/SALE_BILLWISE/2030-01/SALE_BILLWISE_SUMMARY1__2030-0) -- a sale file. With S480's marg_take it is deleted.
  ok   the converted stock register: VERIFIED STOCK_ITEM_LEDGER/TEXT, a PHI type -- deleted at the door, kept nowhere (kept 0, not at rest)   [('VERIFIED', 'STOCK_ITEM_LEDGER', 'TEXT', 0, [])]
  ok   negative control, the OLD signatures: the register is not known (REFUSED )
  ok   B.5 on a scratch archive where sale sheets are kept (as manojz's): the router files the made-up closing stock and the EMPTY day; the kit's push_expected.sales_after lists 2030-01-02 with no lines; compute gives as_on = 2030-01-02   [({'20300101__stoc': 'VERIFIED STOCK_CLOSING/TOTALS', '20300103__repo': 'VERIFIED SALE_BILL ...
  ok   negative control, OLD files: the EMPTY sheet is refused at the router, sales_after lists no day, compute has nothing to compute   [({'20300101__stoc': 'VERIFIED STOCK_CLOSING/TOTALS', '20300103__repo': 'REFUSED SALE_BILLWISE/DETAIL'}, {'lines': 0, 'days': [], 'skipped': 0}, 'no sale report dated after the baseline (24-09- ...
-- 8  the staff-eye walk (D648): shavez, darpan, amir and the owner, on the scratch copy, a walk-only login store
  ok   both staff-eye probes ran to the end
  ok   shavez signs in; the home is byte-equal before and after (19 tiles); every door page too (4 pages)   [[]]
  ok      shavez: 5 duties in the map, 2 due now -- each due one is visible (its tile on the home, its marker on its door); the same on both sides   [[]]
  ok   darpan signs in; the home is byte-equal before and after (8 tiles); every door page too (5 pages)   [[]]
  ok      darpan: 8 duties in the map, 3 due now -- each due one is visible (its tile on the home, its marker on its door); the same on both sides   [[]]
  ok   amir signs in; the home is byte-equal before and after (3 tiles); every door page too (6 pages)   [[]]
  ok      amir: 9 duties in the map, 2 due now -- each due one is visible (its tile on the home, its marker on its door); the same on both sides   [[]]
  ok   manoj signs in; the home is byte-equal before and after (54 tiles); every door page too (10 pages)   [[]]
  ok      manoj: 9 duties in the map, 7 due now -- each due one is visible (its tile on the home, its marker on its door); the same on both sides   [[]]
  ok   the walk's far day holds nothing before its rows go in: the sale row is 'due' on both sides   [({'state': 'due', 'reason_hi': '', 'reason': ''}, {'state': 'due', 'reason_hi': '', 'reason': ''})]
  ok   a VERIFIED SUMMARY1 sale sheet does NOT tick the tile's sale row: the staff see the tile's own words -- 'Item detail nahi hai -- 'With Item Details = Yes' karke dobara banaiye.'   [{'state': 'refused', 'reason_hi': "Item detail nahi hai -- 'With Item Details = Yes' karke dobara banaiye.", 'reason': 'no item detail -- the  ...
  ok   negative control, reports_tile as it is (9d2244a6): the same row DOES count as the day's sale report (state arrived)   [{'state': 'arrived', 'reason_hi': '', 'reason': ''}]
  ok   the DETAIL report for the same day, arriving after it, is what the row then shows -- on both sides   [({'state': 'arrived', 'reason_hi': '', 'reason': ''}, {'state': 'arrived', 'reason_hi': '', 'reason': ''})]
  ok   the salts reader on the server's own newest list (235e9643): NEW files 0 of its 380 items under the firm's name; OLD (40cb2615) files 12   [({'before': 78, 'n': 380, 'firm': 0, 'advert': 0, 'md5': '235e9643', 'after': 82}, {'before': 78, 'n': 380, 'firm': 12, 'advert': 0, 'md5': '235e9643', 'after': 78})]
  ok   the owner's salts page on the scratch copy: 'Marg confirms 78' as it is; with the corrected list 82 (the brief expects 78 -> 82); with the list as the OLD reader reads it, 78   [(78, 82, 78)]
WALK_S480 server GREEN -- 31 checks
```

The installer's own steps of that run:

```
[1/14] kit gates green (SUMS, KIT_ID, the venv's flask, the duty map -- read, not edited --, the databases, the router at its pin)
[2/14] the ten live files at their FROM pins (the brief's section 10)
[3/14] live bytes + anchored edits give the ten pinned files; signatures.json, both marg_ingest marg_report.py and lib/push_expected.py are the kit's own files, byte for byte (what manojz holds)
[4/14] compiles on /usr/bin/python3 and the venv python (a scratch copy); the built signatures.json is JSON; marg_txt S480 --selftest: SELFTEST OK
[5/14] on scratch copies of the built files: salts_refresh.py --once --dry-run exits 0 (it reads the live archive; sends and writes nothing); the collector, the door, the shadow and the rescan import as the crontab runs them
[6/14] the router's own selftest with the built signatures: SELFTEST OK; reports_tile.py's own selftest on the built file: reports_tile selftest: 40 checks, 0 failures (the same line as the box as it is)
[7/14] walk_s480 sections 4 and 8 green on scratch copies; every negative control red on the box as it is (above)
[8/14] finance.db.bak_S480_20261005_072506 made (backup API); a .bak_S480_<from8> beside each of the ten files, read back; the lock is held by S480_MARG_TEXT_READERS
[9/14] placed (each by a rename); md5 read back = the ten TO pins
health : finance healthz 200
         /finance/reports/aaj 302 (302/401 = the login gate, expected)
         /finance/clinic/marg/upload 302 (302/401 = the login gate, expected)
         /finance/purchase/page/salts 302 (302/401 = the login gate, expected)
         /finance/api/marg-file 401 (401 = the machine door asks for its key, expected; no key is read here)
[10/14] clinic-finance active (restarted 2026-10-05 07:25:15); healthz 200; the gated pages answer the gate; nothing else moved; the crontab is as it was
   finance ok=True empty=True day=['2030-01-02'] | marg_ingest ok=True empty=True day=['2030-01-02'] | lib ok=True empty=True day=['2030-01-02']
   LIVE_READ GREEN
[11/14] the three placed marg_report.py read the walk's EMPTY sheet ok / empty (read-only; the sheet is the walk's made-up one)
[12/14] the five-minute collector run once as the crontab spells it: exit 1, nothing raised in the placed code (a quiet run prints nothing; a busy lock or a busy database is the next run's)
   salts_refresh 05-10-2026 07:25 file=SALT_WISE_ITEM_LIST_DEFAULT__2026-10-04__20261004-175549__235e9643.xls as_on=2026-10-04 rows=380 salts=242 -> server 200: ok marg_items=380 stored=0 kept=None
   before: 379 items in the Marg salt list the page holds, 12 of them filed under the firm name
   after : 379 items in the Marg salt list the page holds, 0 of them filed under the firm name
[13/14] the corrected salt list posted once through the app's own door (above); the page's list no longer files an item under the firm's name
[14/14] done · healthz 200 · backups: /root/finance/finance.db.bak_S480_20261005_072506 and a .bak_S480_<from8> beside each file
S480_MARG_TEXT_READERS: DONE
```

After it, read separately at 07:25:44: healthz 200; `clinic-finance` active since 07:25:15; 0 error lines in its journal since the
restart; the five-minute collector's own next run finished at 07:25:43 with `listed 288, new 0, failed 0` (the installer's hand-run at
07:25 met the lock of that same run, hence its "exit 1" in step 12 — nothing was raised). No scratch folder is left in `/tmp`.

### 5 · Every section's negative control (the OLD file goes red)

| section | NEW | OLD |
|---|---|---|
| 1 byte equality | 21 of 21 texts the same bytes; 21 of 21 equal to the kept conversions in `_spool` | one figure changed → other bytes |
| 2 cutter vs Marg's Excel | 72 + 564 + 3,505 = 4,141 cells, none different | one figure changed → exactly one cell differs (each pair) |
| 3 landing | 15 of 15 samples VERIFIED and typed | OLD signatures: category UNKNOWN, valuation REFUSED, register REFUSED; `marg_txt` ed17bb76 takes none of the 15 |
| 4a / 4 the empty day | EMPTY sheet → every `read_report` ok/empty → door VERIFIED, lines 0, `EMPTY — no sale on <date>` → `sales_after` lists the day → `compute` as_on = that day; exported on its own day → the staff's words | `to_rows`: "no GRAND TOTAL line"; `read_report`: TRUNCATED (all copies); the door: REFUSED; `sales_after`: no day |
| 5 the marker | 57 of 57 sale sheets carry `Total No. of`; all still verify | a sheet cut before its footer → REFUSED (TRUNCATED) |
| 6 the watcher | a salt list saved as `user_1.txt` kept and logged, kind SALT; twin not kept twice; 12 kind words | 297cc3d9 drops it: "not a Marg report", nothing kept, no log line; only 3 kind words |
| 7 the salts | 0 under the firm's name, 380 items; the four named items on their salts | 40cb2615: 12 under the firm's name |
| 8 staff-eye | four homes and their door pages byte-equal; a SUMMARY1 sheet does not tick the sale row — "Item detail nahi hai…" | `reports_tile` 9d2244a6 counts it as the day's sale report (state `arrived`) |

### 6 · What the brief asked to be stated

- **B.3 count:** 57 `SALE_BILLWISE` sheets in manojz's `MargArchive` (56 when the brief was written), all variant
  DETAIL, **every one carries `Total No. of` within its last 40 rows**, and all 57 verify under the new marker exactly as under the old.
- **The orthotic proof:** **not yet.** The EMPTY day of 04-10 has not landed, because the medical PC still runs ed17bb76 and the 09:43:21
  text of 04-10 stays refused by B.1's own rule (walked on the real text, §3 4a). The one export that lands it: a DETAIL sale report of
  04-10-2026 made on any later day, **after** the medical PC's two files are delivered.
- **Samples with no real EMPTY shape yet — recognised, kept, not verified:** purchase (all four), sale return (both), expiry, the lists,
  the valuation, the register and the short sale statement are refused as `EMPTY` (`EmptyReport`, "kept; not taken until a real empty
  sample of this report has been verified") and kept in `refused` with a note. The order sheet's empty shape is not touched
  (`order_rows` is one of the three live readers). The only verified empty is the DETAIL sale day.
- **The salts page:** on the scratch copy, as the owner, "Marg confirms 78" → **82** with the corrected list (the OLD reader: 78).
  Live: the list was posted once at 07:25:24 (`server 200: ok marg_items=380`); 12 → 0 items under the firm's name. The live page itself
  was not opened (it is behind the login).
- **Section 8, D648:** shavez (19 tiles, 5 duties, 2 due), darpan (8 tiles, 8 duties, 3 due), amir (3 tiles, 9 duties, 2 due), the owner
  (54 tiles, 9 duties, 7 due): every home and every door page byte-equal before and after, every due duty visible. No duty is added,
  moved or removed, so `DUTY_MAP.md` / `DUTY_MAP.json` are not edited.

### 7 · Calls I made (the brief or the rulebook implied each; none was put to the owner)

1. **A number with a leading zero stays text.** A.1 says "a cell that is wholly a number is a number". Marg's own Excel keeps an
   all-digit cell with a leading zero as text — 32 such bill numbers across 172 archived sheets, none as a number — and the purchase
   loader matches bills by that text; cut as a number, the text road would have given a different bill number from the Excel road for
   the same bill. The 4,141 cells still match.
2. **Two-line heads.** A head on the second line under a head of the first is the same column; one standing clear adds a column. For
   the list of items that is exactly the union the brief describes; for the register it keeps `Bill No. /` in column 0 — with a plain
   union the title would have been read from the wrong column and the sheet would be UNKNOWN.
3. **The valuation signature has seven head cells, not "eight":** `S.No. Description` is one head, as in every other signature.
4. **`STOCK_VALUATION/BATCHWISE` carries `end_row: ["TOTAL"]`, `STOCK_ITEM_LEDGER/TEXT` carries `end_marker: "Issued :"`** — both read
   off the real text samples, so a cut sheet is refused at the router too.
5. **Under the OLD signatures the register is REFUSED, not UNKNOWN** as §9.3 expected: its title is known there and its heads are not.
6. **`reports_tile.py`: three anchored edits, not two.** The SELECT and the DETAIL filter alone leave the row "due"; the third makes a
   day that has only the short statement show the tile's existing *Item detail nahi hai — 'With Item Details = Yes' karke dobara
   banaiye*, as A.2 says the staff must see. A row with no variant at all counts as DETAIL (the tile's own selftest writes such rows;
   live, all 57 VERIFIED sale rows are DETAIL).
7. **`marg_take.py` reads no item line from a SUMMARY1 sheet.** As it was, the door raised on a short statement, wrote no `mi_file`
   row and **left the file at rest in the archive** (shown by the walk's negative control). Now it lands: VERIFIED, lines 0, deleted (S186).
8. **A "today" refusal is not remembered by its bytes.** The same empty report exported a day later is byte-identical; remembered as
   seen, the one export B.6 asks for would have been skipped without a line. (Walked in the watcher's selftest.)
9. **The note may carry two fixed phrases of the reader** — the "today" words and "an empty report" — never a line of the file. With
   them the tile's existing Hindi line about the date shows for a blank report of today.
10. **The corrected salt list was posted once by the installer** (`salts_refresh.py --once --force`). The brief expected "the next
    10-minute run posts the corrected list", but the cron posts only a list it has not applied, and this one was applied by the old
    reader at 18:00 yesterday. This is the kit's **one data write**: `purchase_salt_marg` replaced whole through the app's own door, as
    at every new list. To take it back: the database backup above — or nothing; the next list replaces it again.
11. **TRUNCATED fires only where a bill row exists** (B.2); a sheet with no bill row that is not the zero-bill day is refused with its
    own sentence, so a file cut right after its heads still refuses.
12. **Placed by rename** on the server, so the five-minute collector can never read half a file.

One command of mine was refused by the permission list (a PowerShell line whose text quoted the installer's own clean-up lines). I did
not re-spell it: the same edits to my scratch file were made with the editor instead. Nothing destructive was run.

### 8 · Noticed outside the brief (not touched)

**(1) The spine's reader does not know the empty day — settle this before the medical PC's line is given.**
`/root/finance/spine/marg_read.py` (7ec9b325, not in this kit) reads the EMPTY sale sheet as SALE_BILLWISE with two failed checks:
*GRAND TOTAL = sum of bill GROSS* and *footer bill count = bills read* (run on manojz, with the repository's copy of that reader — the
same bytes — on the walk's made-up EMPTY sheet). By its code, `spine_evidence.py` reads every sheet in Drive's MargArchive
every ten minutes, and the reports tile certifies the sale row from that reading. So for a **weekday** with no sale, some minutes after
the empty report lands and verifies, Shavez's sale row would turn to *"jaanch me fail"* — on a correct report. Sunday 04-10 is not
asked for by the tile, so the one export of §13 does not show it; the first closed weekday would. The mend is in `marg_read.py`
(read_sale_detail), which this brief does not name.

(2) **The five-minute Drive collector has the same two gaps the door had** (`marg_ingest.py`, "not touched"; read in its code, not
walked): `run()` calls `sale_lines` for every VERIFIED `SALE_BILLWISE`, so a SUMMARY1 sheet arriving by Drive before the push would
fail every run and stay at rest in the archive; and an EMPTY day arriving that way gets `lines 0` but no `EMPTY — …` reason. The push normally arrives first
(within a minute) and then the collector skips the md5. S481 reads these rows — worth the same two lines there.

(3) `marg_shadow.py` serves `sales_after` from `mi_sale_line`, so an empty day (no line) is not a day for the nightly shadow; B.5's edit
in `lib/push_expected.py` is in place but the shadow does not go through it.

(4) **The whole-shop category list is not read cleanly by the spine's reader**: its heading `OTHERS … 0.00 D98` carries a code, which
`read_grouped_list` calls UNCLASSIFIED (text and Marg's own Excel alike — same cells). The orthotics-only list of 18-Sep reads clean.

(5) An EMPTY sale sheet made by Marg's **Excel** export on the day itself (if Office returns to the medical PC), or sent by hand
through the upload page, would verify at the server: the "is the day over" rule lives in the medical PC's text reader only.

(6) `finance_app.py`'s own Marg upload route answers "no item detail" for an empty-day sheet (0 item lines) and writes nothing.

(7) The collector's log ends on a `database is locked` traceback of 26-Sep; its runs since are clean (heartbeat 07:25:43).

(8) `marg_watch.py` line 843 (`_captured_txt\held`, unchanged since S389) prints a SyntaxWarning on Python 3.12+; harmless.

### 9 · Not done, and why

- **`deliver_S480.ps1` was not run** (the instruction, and F-715): the medical PC's two files are packed only.
- **The EMPTY day of 04-10 was not put through the door by hand** — B.1 keeps that text refused; the brief gives the export to the
  owner or Shavez.
- **Not in this kit, as the brief says:** the bill chain and its gap lines (S481) · audit #24 · the proof's pairing rule and Amir's
  card wording (S482) · the chain replacing `weekday()==6` (S483) · the dd-mm-yyyy text compares (S484) · F-726 a, F-717, the
  learnt-name strike, `shelf_figure` onto `spine_read` · the register's strips:loose arithmetic · K2.
- The analysis paper's "the purchase loader takes the same bills twice without counting them twice" is shown only as far as §9.2 goes
  (the converted purchase sheets are Marg's Excel cell for cell); the loader itself was not run on a text/Excel pair.

### 10 · Publish

`PUBLISH_ALL.bat` ran at 07:29:01 and answered `PUBLISHED AND VERIFIED - origin HEAD = ab58e39fcf` (commit of 07:29:02 +0530): the kit's
18 files, the brief, this report, and **one line in `.gitignore`**. The repository hides every `.json` by default and the publish gate
refuses a kit file that would be dropped; `deploy_kits/S480_MARG_TEXT_READERS/sig_blocks_s480.json` (report titles and column heads, no
number, no secret) is allowed by its exact path, as S454's `sig_entry_s454.json` was. The F-185 gate over every added file:
`NO_PHONE_NUMBERS: clean -- 21 staged file(s) checked`. No `__pycache__` in the kit folder.

On the server at 07:29:23: `git pull --ff-only` → HEAD `ab58e39fcf`; in the repository's kit `md5sum -c SUMS.md5` 17 of 17 OK, and all
18 files are identical (`cmp`) to the copy that ran from `/tmp/S480kit`. The brief's own line then answers
`-- ALREADY INSTALLED: the ten files are at the kit's pins; clinic-finance active; healthz 200`.

This section was added after that, and the report published again with it (a second run of `PUBLISH_ALL.bat`).

### 11 · Undo

Server: put back the nine `.bak_S480_<from8>` files (ten paths), restart `clinic-finance`, healthz 200, read the md5s back. The
database backup is needed only to take back the salt list of call 10 — say so before using it.
manojz: `python -B deploy_kits\S480_MARG_TEXT_READERS\install_manojz_S480.py --undo`.

### 12 · The owner's lines

The server: nothing to run — it is installed. (The brief's line, if run, answers `ALREADY INSTALLED`.)

The medical PC: done — the owner's line was run at 07:59 (§0).

Left: **one DETAIL sale export of 04-10-2026 from Marg** (the owner or Shavez), and the proof runs by itself.
