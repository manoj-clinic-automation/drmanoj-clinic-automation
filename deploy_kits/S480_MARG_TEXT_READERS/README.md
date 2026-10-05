# S480_MARG_TEXT_READERS — every Marg text report lands; an empty report is an answer

Brief: `claude_code_briefs/S480_MARG_TEXT_READERS.md` (Sanjeevni chat, session 295, 05-Oct-2026). Decision **D675**; faults **F-726 b,
F-728, F-729, F-730**. Report: `claude_code_briefs/REPORT_S480.md`. The bill chain (D675 b) is **not** here — it is S481.

## What, and why

- **One cutter, a spec per report (Part A — `marg_txt.py`, the medical PC).** Marg's Excel export is its text page cut into cells at the
  column heads. `page_to_sheet` does that cut (rule A: a word belongs to the column in which it *ends*; rule B: a line that is one run of
  words is one cell), and `TEXT_SPECS` holds one entry per report: title, heads, the note's kind word, how it ends, its integrity check,
  `empty_ok`. Thirteen specs: purchase bill-wise, supplier/item-wise, supplier-wise, bill/item-wise · salt-wise, category-wise, list of
  items · the short sale statement · sale return (short, detailed) · the batch-wise stock valuation · expiry · the stock register.
  The three live readers (`to_rows`, `stock_rows`, `order_rows`) are not rewritten; every text they took converts to the same bytes.
- **An empty sale day is an answer (Part B, F-729).** A sale text with its title, heads, no bill and the one row
  `Total No. of Bills: 0 … DAY TOTAL` is a no-sale day when its `AS ON` day is **before** the day it was exported; on its own day it is
  refused in the staff's words (*aaj ki report — kal ki tareekh chun kar dobara banaiye*). `marg_report.read_report` (every copy) reads
  the sheet `ok` / `empty` with one day taken from the title; `marg_take` writes `EMPTY — no sale on <date>` with `lines = 0`;
  `push_expected.sales_after` counts the day; `signatures.json`'s end marker for the sale statement becomes `Total No. of`.
- **No Marg text is dropped unlogged (Part D, F-728 — `marg_watch.py`, the medical PC).** A text the reader does not take is kept and
  logged when it carries the end mark, the firm's name or a report word — whatever the file is called. The note names its kind.
- **The signatures are the same bytes on the server and on manojz (Part E):** the server gains manojz's category block; both gain
  `STOCK_VALUATION / BATCHWISE` (taken as nothing) and `STOCK_ITEM_LEDGER / TEXT` (a PHI type: deleted at the server's door).
- **The salt reader stops naming the firm as a salt (Part F, F-730 / F-726 b — `salts_refresh.py`).**
- **The door's refusal kinds gain the new words (Part G — `marg_door.py`).**
- **The short sale statement lands and never ticks the day's sale row (A.2 — `reports_tile.py`, `marg_take.py`).**

## Pins — FROM → TO

| where | file | FROM | TO |
|---|---|---|---|
| server | `/root/marg_ingest/signatures.json` | `64943ac6` | `21604e0f` |
| server | `/root/marg_ingest/marg_report.py` and `lib/marg_report.py` | `eeab5605` | `2bf284ba` |
| server | `/root/marg_ingest/marg_take.py` | `b41195e4` | `3ac9bbe0` |
| server | `/root/marg_ingest/lib/push_expected.py` | `4b3b700c` | `1ba52985` |
| server | `/root/finance/marg_report.py` (the copy the door runs) | `f9370dde` | `d9c9a9b2` |
| server | `/root/finance/marg_door.py` | `6a236663` | `dc5c1e36` |
| server | `/root/finance/salts_refresh.py` | `40cb2615` | `f0021618` |
| server | `/root/finance/reports_tile.py` | `9d2244a6` | `406e452b` |
| manojz | `MargPull\signatures.json` | `7f72c572` | `21604e0f` (the server's bytes) |
| manojz | `MargPull\marg_report.py` | `28b47d44` | `2bf284ba` (the kit's file) |
| manojz | `PUSH_STOCK_DAILY.bat` (one line: `set KIT=` → this folder) | `5cbec862` | `fe8b7f54` |
| medical PC, **packed, not placed** | `D:\SendToClinic\marg_txt.py` | `ed17bb76` | `14b75012` |
| medical PC, **packed, not placed** | `D:\SendToClinic\marg_watch.py` | `297cc3d9` | `58b54f37` |
| Drive `ToMedical\_kit`, **packed, not placed** | `KIT_MANIFEST.txt` | `9e754e5c` (CRLF) | `ea2b437a` (this folder's `c9681701` with CRLF) |

Full md5s: `PINS.sh`, `SUMS.md5`, and the header of `deliver_S480.ps1`. Read only, md5 unchanged: `marg_router.py` `318086e3` (server and
manojz), the medical PC's `marg_push.py` `566e189e`, manojz `expected_on_capture.py` `bd8565d6`.

## The files here

| file | what it is |
|---|---|
| `make_s480.py` | the anchored patcher: every changed file built from the LIVE bytes, each anchor exactly once (`--medical`, `--server`, `--manojz`) |
| `txt_block_s480.py`, `txt_selftest_block_s480.py`, `sig_blocks_s480.json` | the blocks `make_s480.py` adds whole |
| `marg_txt.py`, `marg_watch.py`, `KIT_MANIFEST.txt`, `deliver_S480.ps1` | the medical PC's part — **packed; `deliver_S480.ps1` is not run by Claude Code** |
| `marg_report.py`, `push_expected.py`, `signatures.json` | the copies that are the same bytes everywhere; `PUSH_STOCK_DAILY.bat` runs the first two from this folder |
| `install_S480_MARG_TEXT_READERS.sh`, `PINS.sh` | the server installer (gates → pins → build → compile on both pythons → walk on scratch copies → backup → place → md5 read-back → restart `clinic-finance` → healthz → restore on red) |
| `install_manojz_S480.py` | the three manojz files (`--undo` puts them back; `--check` reads only) |
| `walk_s480.py` | the walk: `manojz` (sections 1, 2, 3, 4a, 5, 6, 7) and `server` (sections 4, 8). Every section has a negative control on the OLD file |

## Run / undo

- Server: `bash /root/deploy/repo/deploy_kits/S480_MARG_TEXT_READERS/install_S480_MARG_TEXT_READERS.sh` (holding the build lock;
  `DRY=1` places nothing). Undo: put back each `<file>.bak_S480_<from8>`, restart `clinic-finance`, healthz 200, read the md5s back.
  The database backup `finance.db.bak_S480_<stamp>` is needed only to take back the one data write (the salt list posted once).
- manojz: `python -B install_manojz_S480.py` from this folder; undo `--undo`.
- Medical PC: **not yet.** After the Sanjeevni chat has read `marg_txt.py` and `marg_watch.py`:
  `powershell -ExecutionPolicy Bypass -File deliver_S480.ps1`. Then one DETAIL sale export of 04-10-2026 lands the empty Sunday.

## Calls made while building (each is in the report, with its reason)

1. **A number with a leading zero stays text** (`0077`, not `77.0`). Rule A says "a cell that is wholly a number is a number"; Marg's own
   Excel keeps an all-digit cell with a leading zero as text (32 such bill numbers in MargArchive, none as a number), and the purchase
   loader matches bills by that text. The three same-moment pairs still come to 4,141 equal cells.
2. **Two-line heads:** a head on the second line that stands under a head of the first is the same column; one that stands clear adds a
   column. For the list of items this *is* the union of both lines' starts (as Marg's Excel has it); for the stock register it keeps
   `Bill No. /` in column 0, where the router looks for the title.
3. **The valuation's header has seven cells, not eight:** `S.No. Description` is one head (single space), as in every other signature.
4. **`reports_tile.py` takes three anchored edits, not two:** the SELECT, the `DETAIL`-only filter, and the line that shows a
   short statement as the tile's own *Item detail nahi hai* refusal. With the filter alone the row would read "due", not those words.
5. **`marg_take.py` reads no item line from a `SUMMARY1` sheet.** As it was, the door raised on a short statement, wrote no row, and left
   the file at rest in the archive; now it lands (VERIFIED, lines 0, deleted — S186).
6. **A refusal for "today" is not remembered by its bytes** — the same report exported the next day has the same bytes and must be taken.
7. **The corrected salt list is posted once by the installer** (`salts_refresh.py --once --force`): the cron posts only a list it has
   not applied, and the newest list was already applied by the old reader.
8. **`TRUNCATED` fires only where a bill row exists;** a sheet with no bill row that is not the zero-bill day is refused with its own words.

## Not in this kit

The bill chain and its gap lines (S481) · a byte-identical re-export dropped on the PC although the server lost the first push (audit #24)
· the proof's pairing rule and Amir's card wording (S482) · the chain replacing `weekday()==6` (S483) · the dd-mm-yyyy text compares (S484)
· F-726 a, F-717 · the register's strips:loose arithmetic · K2. `marg_router.py`, `marg_ingest.py`, `marg_push.py`, `medical_agent.py`,
`expected_on_capture.py`, the crontab, `finance_app.py`, `portal.py`, `tile_grants.json`, `stock_app.py`, `amir_day.py`,
`purchase_app.py` are not edited. No duty is added, moved or removed: the duty map is read, not changed.
