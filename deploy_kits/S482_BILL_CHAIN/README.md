# S482_BILL_CHAIN — the chain of Marg's bill numbers says what is missing

Brief: `claude_code_briefs/S482_BILL_CHAIN.md` (Sanjeevni chat, session 295, 05-Oct-2026). Decisions **D675 b**, **D676**; faults
**F-731, F-732, F-733**. Report: `claude_code_briefs/REPORT_S482.md`. It runs on the live bytes after S480.

## What, and why

- **The chain, not the calendar (Part A — `marg_take.py`, `reports_tile.py`).** Marg's sale bills carry `A` + digits, credit notes
  `CN` + digits; each series runs unbroken across every day, open or closed. `marg_take.rebuild_chain` writes one row per series per
  day into the new table `mi_bill_chain` (from every distinct bill of `mi_sale_line`, from 17-Aug-2026 — the day the daily feed
  began — and one `empty` row per series for every EMPTY day of `mi_file`). A number is *missing* only when no day of the series
  carries it; it is written on the first day that carries a higher number (`gap_before`: between the numbered day before and that
  day; `gap_inside`: skipped within the day). An EMPTY day carries no number and is transparent; a gap across it names all three
  dates. `chain_state` is a pure read. The chain is rewritten whenever a sale report or an EMPTY day lands — at the door
  (`take()`) and by the Drive collector (`marg_ingest.run`) — never by the tile.
- **One line per open gap, only while a gap exists.** `reports_tile.status()` carries `bill_chain` (the state and its lines) and
  appends the English line to the owner's `line`; `render()` shows a red card after the scan card, in Hindi, for Shavez:
  *"Bill A… aur CN… nahi mile (08-Sep se 09-Sep ke beech) — 08-Sep aur 09-Sep ki bikri report dobara banaiye."* The line leaves by
  itself when a re-export closes the gap. No calendar word anywhere. The MISSED banner and `_due_day` are not changed.
- **The rename list carries the right names (Part B, D676 — `finance.db` `marg_item_rename`, `renames_s482.py`).** Seven rows
  (ids 5–9, 21, 22) get the spellings of S295_ORTHOTIC_RENAMES_CHECKED — the words staff type to search stay. Keyed by `id` AND
  `old_name`; a row already ticked is stopped and reported; the other rows are unchanged cell for cell.
- **The spine's reader knows the empty day (Part C, F-732 — `spine/marg_read.py`).** `Total No. of | Bills: 0 | DAY TOTAL :` on one
  row is the EMPTY footer, recognised before the `DAY TOTAL` branch: no failed check, `empty: True`, the day from the title. The
  reading the old reader wrote for the 04-10 sheet is removed with a `.bak_S482` copy beside it and written again.
- **The Drive collector takes SUMMARY1 and EMPTY like the door (Part D, F-733 — `marg_ingest.py`)** and keeps the chain current.
- **The outbox does not re-send an empty day (Part E, F-731 — manojz `MargPull\marg_gate.py`).** A VERIFIED sale sheet of at most
  three rows is recorded `empty_day` and skipped; the picture stops listing it; a stale `_NEEDS_ATTENTION.txt` goes.

## Pins — FROM → TO

| where | file | FROM | TO |
|---|---|---|---|
| server | `/root/marg_ingest/marg_take.py` | `3ac9bbe0` | `a86a0f26` |
| server | `/root/marg_ingest/marg_ingest.py` | `7f6b4dc2` | `828c4dad` |
| server | `/root/finance/reports_tile.py` | `406e452b` | `ea15aacb` |
| server | `/root/finance/spine/marg_read.py` | `7ec9b325` | `099d6213` |
| manojz | `D:\Downloads\margsync\MargPull\marg_gate.py` | `52f502d1` | `f5de9b4e` |
| server data | `finance.db` `marg_item_rename`, seven rows | S268's spellings | D676's (`renames_s482.py`) |
| server data | `finance.db` `mi_bill_chain` | — | created and filled |
| server | `/root/finance/spine/readings/15495622….json` | two failed checks | removed (`.bak_S482` beside it), written again by the new reader |

Full md5s: `PINS.sh`, `make_s482.py` (FROM), `install_manojz_S482.py`. Read only, md5 unchanged: `stock_app.py` `7e159de7`,
`amir_day.py` `709f20c1`, `item_alias.py` `5168c3c0`, `marg_router.py` `318086e3`, `spine/spine_evidence.py` `0fcf6c64`.

## The files here

| file | what it is |
|---|---|
| `make_s482.py` | the anchored patcher: every changed file built from the LIVE bytes, each anchor exactly once (`--server`, `--manojz DIR`) |
| `chain_block_s482.py`, `tile_block_s482.py` | the two blocks `make_s482.py` adds whole (the chain into `marg_take.py`; the lines into `reports_tile.py`) |
| `renames_s482.py` | Part B: the seven rows, the keyed update and its checks (`python3 -B renames_s482.py DB [--dry]`) |
| `install_S482_BILL_CHAIN.sh`, `PINS.sh` | the server installer: gates → pins → build → compile on both pythons → walk on scratch copies → database backup → the renames → file backups → place → md5 read-back → restart `clinic-finance` → healthz → the chain built once → the 04-10 reading written again → restore on red |
| `install_manojz_S482.py` | the one manojz file (`--undo` puts it back; `--check` reads only) |
| `walk_s482.py` | the walk: `server` (sections 1, 2, 3, the collector and fixture halves of 4, the staff-eye walk) and `manojz` (the reader on the real sheets, the outbox dry). Every section has a negative control on the OLD file |
| `DUTY_MAP.json` | the duty map (v6) the walk and the installer ran with: `shavez.bill_chain_gap` added |

## Run / undo

- Server: `bash /root/deploy/repo/deploy_kits/S482_BILL_CHAIN/install_S482_BILL_CHAIN.sh` (holding the build lock; `DRY=1` places
  nothing). Undo: put back each `<file>.bak_S482_<from8>`, restart `clinic-finance`, healthz 200, read the md5s back. The table
  `mi_bill_chain` may stay (the old files do not read it). The seven renames are taken back only from
  `finance.db.bak_S482_<stamp>` — row by row, said first — and only if Amir has ticked none of them.
- manojz: `python -B install_manojz_S482.py` from this folder; undo `--undo`. The `empty_day` entries in `_outbox_state.json` may
  stay: the old file ignores them and simply tries the empty sheet again.

## Calls made while building (each is in the report, with its reason)

1. **A missing number is one no day carries, and it is named once** — on the first day that carries a higher number. With Marg's
   numbers running in day order (as measured: no bill on two days, no day out of order) this is the brief's rule exactly; it also
   stays right if a bill is ever back-dated.
2. **A run of three or more missing numbers is one word, `A003481..A003499`**, in the column and on the screen (*"A003481 se
   A003499 tak"*); `n` counts every number. One or two are written singly, as the brief words them. A lost week would otherwise be a
   line of 150 numbers.
3. **A gap inside a day has its own words** (the brief words only the two between-days cases): *"Bill A… nahi mila (17-Sep ke
   andar) — 17-Sep ki bikri report dobara banaiye."* / *"Bill chain: A… missing inside 17-Sep — re-export that day."*
4. **`chain_state` adds `built`.** A chain never built (no table) is not known complete: `built False, complete False`, no gap.
5. **The empty reader gains one witness of its own:** *an empty day is named by its title (AS ON)* — an EMPTY sheet whose title
   names no day cannot be filed under a day, so it fails that one check.
6. **The outbox rule needs a KNOWN row count: 1–3.** The brief writes `int(row["rows"] or 0) <= 3`; a blank count would then read
   as an empty day and a real sheet would never be sent. It also holds under `--resend-all` (the route cannot take the sheet).
7. **`do_send` clears a stale `_NEEDS_ATTENTION.txt` when nothing is left to send** (not in a dry run). The old code removed it
   only after a send that had something to send, so after this kit it would have stayed for ever.
8. **The duty map gains `shavez.bill_chain_gap`** (CLAUDE.md, "every duty has a door"): the door is the tile's red line; the owner's
   line is the tile's own English line (`coded`), so nothing new is raised on Needs-you.
9. **The installer runs `spine_evidence.py` once** (evidence only, under the cron's own lock) after setting the old 04-10 reading
   aside, so the clean certificate is read back in the same run instead of ten minutes later.
10. **The five read-only files are gated at the brief's pins** before anything is built: the walk reads them.

## Not in this kit

The proof's pairing rule and Amir's card wording, F-726 a, F-717, the learnt-name strike, `shelf_figure` onto `spine_read`,
`item_alias.THE_22` (S483) · the chain replacing `weekday()==6` in the tile's banner, `spine_build`, `export_watch`, `darpan_kal`,
the freshness legs (S484) · the dd-mm-yyyy text compares (S485) · audit #24 · PHI kinds kept off Drive's `refused_text` · **the
parent's line:** the clinic's upload route (`finance_app.py` / `finance_returns.py`, the `no_item_detail` answer) should take an
EMPTY day as a day with no bills, so the *Sale bills from Marg* freshness leg stops ageing over a no-sale day. `stock_app.py`,
`amir_day.py`, `purchase_app.py`, `item_alias.py`, `finance_app.py`, `portal.py`, `tile_grants.json`, the crontab and every
medical-PC file are not edited.
