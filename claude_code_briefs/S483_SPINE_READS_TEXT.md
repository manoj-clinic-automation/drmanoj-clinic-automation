# Claude Code brief — S483_SPINE_READS_TEXT (the spine's reader takes the two text-made sheets that froze its build this morning)

Written 05-Oct-2026 10:4x IST by the Sanjeevni chat (session 295), from `claude_code_briefs/REPORT_S482.md` §9 (1) and the chat's own reading of the two files on manojz. Read `CLAUDE.md` first. Small kit, one server file, one run.

**Kit S483 · faults F-734, F-735** (numbers given here; mint none). **No D-number.**

**Why now.** `spine_build.py` has ended every ten-minute build since about 08:10 today with `GATE FAILED — nothing swapped`; `spine.db` is the 08:00 build. Two sheets made by S480's text readers at 07:59 fail the spine's own witness:

- **F-734** — `PURCHASE_BILLITEMWISE_DEFAULT__2026-09-01_to_2026-10-03__20261005-075955__de92f5d5.XLS`: the BILL/ITEM WISE text prints each day's date on a line of its own at column 0; the cutter's rule A ("a word belongs to the column in which it *ends*") puts `01-09-2026` into **column 1**, because the date is wider than the `BILL` head. Marg's own Excel has it in column 0. `marg_read.read_purchase_lines` recognises a DATE row only as `RE_DATE.match(c[0]) and not any(c[1:])` (~l.419), so the sheet reads **208 lines with no date**, none ties to a bill, and the gate line *every purchase line of an export that is the authority for its whole period belongs to exactly one bill* fails (`spine_build.py` ~l.234). Measured on manojz with the repository's reader: `dates on lines: 208 False`; the Excel of 06-Sep: `43 True`. The purchase loader (`purchase_app.py` ~l.485) dates lines by their bills and is not hurt; `push_expected` dates by the bill-wise export and is not hurt. **The cutter's own rule is the root and belongs to the next medical-PC kit** (a one-token line at column 0 goes to column 0); this kit makes the spine's reader take the sheet as it is, which is also right in itself: a date-only row is a date wherever its one cell sits.
- **F-735** — `CATEGORY_WISE_ITEM_LIST_DEFAULT__2026-10-05__20261005-075955__f62cc9e3.XLS` (the owner's whole-shop category list): row 148 is `['OTHERS', 0.0, 'D98', '', '']` — Marg prints its category code in a cell. `marg_read.read_grouped_list` takes a heading only when every other cell is empty or zero (~l.207 `if c0 and all((not x) or num(x) == 0 for x in rest)`), so the row is UNCLASSIFIED, the next serial restarts at 1 "under" the previous group, and the check *serial restarts at 1 under every heading and never skips* fails. Marg's Excel of the same report prints the same cells (REPORT_S480 §8 (4)), so this is the reader's rule, not the cutter's.

**Touches — Sanjeevni's, PLANNED on the board (`_numbers` v276):**

- `/root/finance/spine/marg_read.py` — **post-S482 bytes `099d621315f3bf9297a9b4626a5caee5`** (S482 placed it at 09:5x; `.bak_S482_7ec9b325` beside it). Two anchored edits, nothing else.
- `/root/finance/spine/readings/de92f5d5185646d4de563e30d5464f6e.json` and `/root/finance/spine/readings/f62cc9e3d93c692f1795229be9e7cfe1.json` — the two certificates already written with the failures; **removed with `.bak_S483` copies beside them**, so `spine_evidence.py` (reads a file once; not edited) writes them again with the mended reader at its next ten-minute run.
- **Read only:** `spine_build.py` (the gate; md5 before and after), `spine_evidence.py` 0fcf6c64, `spine_read.py` 712a1e4e, `spine.db` (never written by this kit — the build swaps it in by itself when the gate passes). No parent file, no crontab, no medical-PC file, no manojz file.

## 1 · The two edits (`marg_read.py`)

- **E.1 `read_purchase_lines`, the DATE row:** a row whose non-empty cells are exactly one, and that cell matches `RE_DATE`, is a DATE row — wherever the cell sits. (Today: `c[0]` only.) Everything else in the function unchanged.
- **E.2 `read_grouped_list`, the HEADING row:** a row whose first cell is text that is not an item (no `RE_ITEM` match, not a bare number) and whose other cells are each empty, zero, **or one short code** — letters and digits, no spaces, at most 6 characters, at most one such cell in the row — is a HEADING; the code is kept on the group as `code` (information; nothing reads it yet). A row with a rate or a packing in `rest` is still not a heading. Everything else unchanged. The existing check *no heading is the shop name or a title* still applies.

## 2 · Walk (`walk_s483.py`) — on manojz against `MargArchive` (the two files lie there; the real DETAIL sale sheets are not read), with the kit's `marg_read.py`; the gate half on the server

1. `read_file` on `de92f5d5`: OLD `dates on lines: 0 of 208`; NEW `208 of 208`, every line dated inside 01-Sep … 03-Oct, `ok True`. On the Excel BILL/ITEM WISE of 06-Sep (`7aab826f`): OLD = NEW, byte-equal readings. On a SUPPLIER/ITEM WISE sheet (no date rows): OLD = NEW. Negative control: a date cell with two non-empty cells in the row is still not a DATE under NEW.
2. `read_file` on `f62cc9e3`: OLD `ok False` (UNCLASSIFIED + SERIAL at rows 148–149); NEW `ok True`, the group `OTHERS` with `code D98`, 341 items read, serials clean under every heading. On the orthotics-only list of 18-Sep (`f4a3406e`) and on the salt list `235e9643`: OLD = NEW. Negative control: a row `['OTHERS', 0.0, 'D98', 'X1', '']` (two codes) is still UNCLASSIFIED; a row with a rate in `rest` is still UNCLASSIFIED.
3. **The gate (server):** `spine_build.py` on a scratch copy of the readings store with the two readings rewritten by the NEW reader → the three gate lines that failed at 09:50 pass; the build swaps on the scratch copy; the live `spine.db` is not touched by the walk. Negative control: the OLD readings → GATE FAILED on the same two lines.
4. Every other reading in the store re-read by NEW on a scratch copy gives the same `ok` and the same `data` as the stored one for every family but the two mended rows' cases (count them; any other change = stop).

## 3 · Install, done means, report

`install_S483_SPINE_READS_TEXT.sh`: gates → pin (`099d6213…`) → compile both pythons → walk 3–4 on scratch copies → `.bak_S483_099d6213` beside the file, `.bak_S483` copies of the two readings → place by rename → md5 read back → the two readings removed → **restart `clinic-finance` once**: `reports_tile.py` imports `marg_read` inside `_reading_from_kept` (~l.268) to certify a kept file, so the running process must pick up the mended reader; healthz 200 after → wait for the next `*/10 8-23` spine run or run `spine_evidence.py` then `spine_build.py` once by hand as the crontab spells them, under the lock the crontab uses (`flock -n /tmp/spine.lock`) → `spine.log`'s new line read: **the gate passes and `spine.db` is swapped**, with its clock time quoted. Healthz 200 throughout. (`selftest_spine.py` imports `marg_read` too — run it on the built file: every check still passes.)

Done means: both sheets read clean by the spine; the spine builds again and `spine.db` is newer than 08:00; nothing else in any reading changed; every walk section green on NEW and red on OLD; the publish gate clean.

Report `claude_code_briefs\REPORT_S483.md`: for the owner, two lines — the spine is building again since HH:MM, and what froze it. For the chat: the pin FROM → TO, the two readings' before/after `ok`, the gate's line from `spine.log`, walk output, and the one line for the next medical-PC kit (the cutter's column rule, F-734 root).

## 4 · The owner's line, after the publish

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S483_SPINE_READS_TEXT/install_S483_SPINE_READS_TEXT.sh
```
