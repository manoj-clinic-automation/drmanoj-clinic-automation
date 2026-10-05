# S483_SPINE_READS_TEXT — the spine's reader takes the two text-made sheets that froze its build

Brief: `claude_code_briefs/S483_SPINE_READS_TEXT.md` (Sanjeevni chat, session 295, 05-Oct-2026). Faults **F-734, F-735**; no
D-number. Report: `claude_code_briefs/REPORT_S483.md`. It runs on the live bytes after S482.

> **STATUS, 05-Oct-2026: BUILT AND WALKED — NOT INSTALLED.** The kit is the brief, exactly; its own walk is **red at section 3**
> on the server, so its installer placed nothing (it cannot place anything while that section is red). With both readings
> rewritten by the mended reader the category-list line passes and the purchase sheet's lines are dated 208 of 208 — but the gate
> line *every purchase line … belongs to exactly one bill* still fails, on **5 lines: bill number 160 of 01-Sep, which two
> suppliers share**. That is a rule of `spine_build.py` (read only in this brief), not of the reader. `/root/finance/spine/marg_read.py`
> is still `099d6213…`; the two readings, `spine.db` and every service are as they were. See the report.

## What, and why

`spine_build.py` ended every ten-minute build of 05-Oct from about 08:10 with `GATE FAILED -- nothing swapped`: two sheets made by
S480's text readers at 07:59 failed the spine's own witness.

- **E.1 — `read_purchase_lines`, the DATE row (F-734).** The BILL/ITEM WISE text prints each day's date alone on a line; the
  cutter puts it into column 1 (the date is wider than the `BILL` head), Marg's own Excel has it in column 0. The reader took a
  DATE row only in column 0, so the text-made sheet read 208 lines with no date (its 27 date rows as supplier headings) and none
  tied to a bill. Now: **a row whose non-empty cells are exactly one, and that cell is a date, is a DATE row — wherever it sits.**
- **E.2 — `read_grouped_list`, the HEADING row (F-735).** Marg prints a category's own code in a cell of its heading row
  (`OTHERS | 0.0 | D98`). The reader took a heading only when every other cell was empty or zero, so the row was unclassified and
  the next serial "broke". Now: **a heading's other cells are each empty, zero, or ONE short code** — letters and digits with a
  letter among them, no spaces, at most 6 characters, at most one such cell. The code is kept as `data["code"] = {group: code}`,
  present only when a heading carried one (nothing reads it yet). A row with a rate or a packing beside its name is still not a
  heading.

Nothing else in the file. The cutter's own column rule (a one-token line at column 0 belongs to column 0) is the root of F-734 and
belongs to the next medical-PC kit.

## Pins — FROM → TO

| where | file | FROM | TO |
|---|---|---|---|
| server | `/root/finance/spine/marg_read.py` | `099d621315f3bf9297a9b4626a5caee5` | `96f565a8d138d9ce75c0ed228b471495` |
| server | `spine/readings/de92f5d5185646d4de563e30d5464f6e.json` | ok True, 0 of 208 lines dated | removed (`.bak_S483` beside it), written again: 208 of 208 dated |
| server | `spine/readings/f62cc9e3d93c692f1795229be9e7cfe1.json` | ok False (3 failures) | removed (`.bak_S483` beside it), written again: ok True |

Read only, md5 unchanged: `spine_build.py`, `spine_evidence.py` `0fcf6c64`, `spine_read.py` `712a1e4e`, `selftest_spine.py`,
`spine_rules.json`, `reports_tile.py`. `spine.db` is never written by this kit: the build swaps it in by itself when its gate
passes.

## The files here

| file | what it is |
|---|---|
| `make_s483.py` | the anchored patcher: `marg_read.py` built from the LIVE bytes, three anchors, each exactly once |
| `walk_s483.py` | the walk: `manojz` (sections 1, 2 — the two sheets, and every purchase-lines sheet and grouped list in MargArchive) and `server` (section 3 the gate on scratch copies, section 4 every kept reading re-read, the tile's own certificate) |
| `install_S483_SPINE_READS_TEXT.sh`, `PINS.sh` | gates → pin → build → compile on both pythons → `selftest_spine.py` on the built file → walk on scratch copies → backups → place by rename → md5 read-back → the two readings removed → restart `clinic-finance` once → healthz → the spine's own job once, as the crontab spells it → the gate's line read back → restore on red |

## Run / undo

- `bash /root/deploy/repo/deploy_kits/S483_SPINE_READS_TEXT/install_S483_SPINE_READS_TEXT.sh` (holding the build lock; `DRY=1`
  places nothing).
- Undo: put back `marg_read.py.bak_S483_099d6213`, copy the two `….json.bak_S483` over the two readings, restart
  `clinic-finance`, healthz 200, read the md5s back. The spine's gate then fails again on the same two lines, as on the morning of
  05-Oct (its last good `spine.db` stays in place, as the build always leaves it).

## Calls made while building (each is in the report, with its reason)

1. **The code lives in `data["code"]`, a `{group: code}` map, only when a heading carried one.** The reader has no group object
   (an item carries its group's name); a key on every item or on every reading would have changed the data of every list already
   in the store, and the brief asks that nothing else move.
2. **A code must hold a letter.** "Letters and digits" alone would take a bare number — a rate, as an `.xlsx` cell prints a whole
   one — for a code, and the brief says a row with a rate is still not a heading.
3. **Section 4 re-reads every reading whose sheet the server keeps** (purchases, stock, lists — 114 of them), and counts the
   rest instead of fetching them: the sale sheets are never at rest on the server (S186) and the walk does not pull them from
   Drive to prove a negative — the sale reader, the file door and `identify()` are shown to be the same text, statement by
   statement. The two category lists the server does not keep are read on manojz by the same walk.
4. **The installer runs the spine's job once itself** (`spine_evidence.py && spine_build.py`, as the crontab spells them, under
   `/tmp/spine.lock`, into `spine.log`) — the brief allows either this or waiting for the next ten-minute run — so the gate's
   line is read back in the same run. It waits for the lock (the cron line does not).
5. **`finance.db` is backed up although the kit writes no row** (the rulebook's standing rule 6).
6. **No staff-eye walk section:** no page, tile, duty or door changes; the one page module that imports the reader
   (`reports_tile.py`) is exercised by the walk through its own `certify`, old reader against new.
7. **Nothing was installed in part.** The two edits are right in themselves and move nothing else (section 4), but with them
   alone the spine would stay refused today and could later be let through by any newer purchase export while five purchase
   lines of 01-Sep are still tied to no bill. Whether the spine may build in that state is the chat's ruling, not this kit's.
