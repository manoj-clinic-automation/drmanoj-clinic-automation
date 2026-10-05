# Claude Code brief — S482_BILL_CHAIN (the chain of Marg's bill numbers says what is missing; the empty day settles everywhere it touches; the rename list carries the right names)

Written 05-Oct-2026 by the Sanjeevni chat (session 295), after S480 went live on all three machines (07:59 IST) and the owner's empty day of 04-10 landed (08:49) and ran the orthotic proof (26 of 28 · 2 to correct). From `claude/S295_CALENDAR_GLITCH_AUDIT.md` (§1 rule b, §4), `claude/S295_ORTHOTIC_RENAMES_CHECKED.md`, `claude_code_briefs/REPORT_S480.md` §8 (1), (2), and the owner's rulings of 05-Oct. Read `CLAUDE.md` first. S480's brief is the shape to keep.

**Kit S482 · decision D676 · faults F-731, F-732, F-733** (numbers given here; mint none). D676 = the renames rule: a Marg item is renamed only where the system cannot tell it apart (its first 20 letters), and the words staff type to search never change. F-731 = manojz's outbox re-sends a VERIFIED EMPTY sale sheet to the clinic's upload route, which answers 422 `no_item_detail`, so every pull reports NOT ok. F-732 = the spine's `marg_read.read_sale_detail` fails an EMPTY sheet on two checks, so on a closed weekday Shavez's sale row would read *jaanch me fail* for a correct report. F-733 = the Drive collector calls `sale_lines` on a SUMMARY1 sheet (it raises; the file stays at rest) and writes no EMPTY reason.

**The owner's rule this kit builds, verbatim in intent (D675 b, 05-Oct):** *the continuity of Marg's bill numbers decides what export is missing — never the calendar. ANY gap, even one or two numbers, is flagged cleanly with the date and the exact bill numbers missing and must be re-exported by someone; it is NEVER presumed to be a cancelled bill — "otherwise every data will be spoiled, the inventory, the sale and everything."*

**What this kit is NOT.** No staff screen changes layout; one line is added to Shavez's reports tile and the owner's English line only when a gap exists. Nothing in `stock_app.py` / `amir_day.py` / `purchase_app.py` (the proof's pairing rule and Amir's card wording are S483). No parent file. No medical-PC file. No crontab.

**Runs on the live bytes after S480** (pins §8; read each live before its first edit).

**Touches — all Sanjeevni's, PLANNED on the board (`_numbers` v275):**

- Server `/root/marg_ingest/marg_take.py` 3ac9bbe0 (the chain, Part A) · `/root/marg_ingest/marg_ingest.py` 7f6b4dc2 (F-733, Part D).
- Server `/root/finance/reports_tile.py` 406e452b (the gap line, Part A) · `/root/finance/spine/marg_read.py` 7ec9b325 (F-732, Part C).
- Server `finance.db`: table `marg_item_rename`, rows 5–9 and 21–22 (D676, Part B — the kit's one data write, backed up).
- manojz `D:\Downloads\margsync\MargPull\marg_gate.py` 52f502d1 (F-731, Part E). Claude Code runs on manojz and places it itself, `.bak_S482_52f502d1` beside it.
- Server `/root/finance/spine/readings/15495622….json` — the certificate already written for the 04-10 EMPTY sheet with two failures: **removed with a copy beside it** (`.bak_S482`) so `spine_evidence.py` writes it again with the new reader (it reads a file once; without this the 04-10 reading stays red for ever).
- **Read only:** `stock_app.py` 7e159de7 (`_s444_renames`, `api_pad_rename_tick`; the renames gate is `_proof_state(con, _pad_report_data(con, cid))["state"] == "done"` behind `_S444_RENAMES_CACHE`, 600 s) · `amir_day.py` 709f20c1 · `/root/finance/item_alias.py` 5168c3c0 (the table's reader — `rows()`, `resolve_map`, `forms_of` key on `new_name`; its hard-coded `THE_22` keeps S268's spellings and is **left as it is on purpose**: `seed()` keeps existing rows by `old_name`, so the UPDATE stands; the list is corrected in S483) · `/root/marg_ingest/marg_router.py` 318086e3 · `/root/finance/spine/spine_evidence.py` 0fcf6c64 (it calls `marg_read`; reads a file once; not edited).

**READ ONLY data:** `mi_sale_line`, `mi_file` (the chain reads them); `spine/readings/*.json` (the certificates; the walk reads one).

---

## 0 · The rules this build stands on

1. **The chain, not the calendar.** Marg's sale bills carry `A` + digits (`A003983`, as `mi_sale_line.bill_no` stores them), credit notes `CN` + digits. Each series runs in one unbroken sequence across every day the shop was open or closed (measured 01-Sep → 03-Oct: A3321 → A4000; 20-Sep, a Sunday, had one bill). **A gap is a gap: shown, never explained away, never averaged, never used.**
2. **An EMPTY day is transparent to the chain** — a `mi_file` row (`SALE_BILLWISE`, VERIFIED, `lines = 0`, `reason` starting `EMPTY`) is a day with no numbers; the chain runs from the numbered day before it to the numbered day after it. If those two do not meet, the gap is flagged **between the two numbered days, naming all three dates** (the empty day may have been a false empty), action: re-export all three.
3. **Nothing computed over a gap, nothing blocked silently.** This kit shows; S483/S484 teach the figure-makers to wait on it. Every gap line names the dates, the numbers and the one action, in Hindi for the staff, in English for the owner.
4. **Nothing live rebuilt; anchored edits; a negative control on the OLD file for every walk section; no number of any kind in the repository (F-185); the bill numbers in the walk's fixtures are invented.**

## 1 · PART A — the chain (`marg_take.py`, `reports_tile.py`)

- **A.1 `mi_bill_chain`** (new table, created lazily in `marg_take._connect`'s path or beside it): `series` (`A` | `CN`) · `day` (ISO) · `first_no` · `last_no` (integers) · `n_bills` · `gap_before` (TEXT: the numbers missing between the previous numbered day's `last_no` and this `first_no`, written as Marg prints them — `A003478` — comma-separated; empty when none) · `gap_inside` (TEXT, the same format, for numbers skipped within the day) · `empty` (1 for an EMPTY day row, which carries no numbers) · `source_md5` · `computed_at`. Primary key `(series, day)`.
- **A.2 `rebuild_chain(con, from_day=None)`** — from `mi_sale_line` (every distinct `(bill_date, bill_no)`; `is_return` rows are the `CN` series by their letters, not by the flag) and from `mi_file`'s EMPTY rows (A row per series with `empty = 1`). Gaps are computed between consecutive **numbered** days of a series and written on the later day's row as `gap_before`; a number skipped inside a day is written on that day's row as `gap_inside` (a second TEXT column, same format). **The chain starts on 2026-08-17** (`from_day` default; a setting-free constant with its reason in a comment): `mi_sale_line` holds one test day in June and then nothing until 17-Aug, when the system began — a whole-table rebuild would show a 1,430-number June→August gap for ever. Called at the end of `take()` whenever a `SALE_BILLWISE` is VERIFIED or EMPTY, **and from `marg_ingest.run()` for the same case (Part D)** — a sheet that arrives by Drive alone must not leave the chain stale. Never called from the tile. One row per day per series; re-exported days (`distinct (bill_date, bill_no)`) count once. EMPTY rows come from `mi_file` rows with `type = SALE_BILLWISE`, `verdict = VERIFIED`, `lines = 0`, `reason` starting `EMPTY`, dated by `date_from` (ISO).
- **A.3 `chain_state(con)`** → `{complete: bool, gaps: [{series, between: [day_before, day_after], via_empty: [days], missing: ["A003478", …], n}], last: {A: [day, no], CN: [day, no]}}`. Pure read.
- **A.4 The lines.** `reports_tile.py`: `status()` (built on every request, ~l.637–688 of the pre-S480 file) gains a `bill_chain` key from `chain_state` (a pure read — `rebuild_chain` is never called here) and appends the English line to `line` after the banner clause (~l.673); `render()` (~l.786) gains a Hindi card after the `s454_scan` card (~l.806–810), in the shape of `_s454_scan_line`. **One line per open gap, only when a gap exists**: Hindi for Shavez — *"Bill A003478 aur CN00203 nahi mile (08-Sep se 09-Sep ke beech) — 08-Sep aur 09-Sep ki bikri report dobara banaiye."*; with an empty day between — *"… (08-Sep se 10-Sep ke beech, 09-Sep khali tha) — teen dinon ki bikri report dobara banaiye."*; English for the owner — *"Bill chain: A003478 and CN00203 missing between 08-Sep and 09-Sep — re-export both days."* The line leaves by itself when a re-export closes the gap. No "Sunday", no "holiday" anywhere. The MISSED banner and `_due_day` are not changed (S484).
- **A.5 Today's first case, after install:** `chain_state` on the live table must report exactly the one gap the chat measured — `A003478` and `CN00203` between 08-Sep and 09-Sep — and nothing else for 01-Sep → the newest day; the tile shows that one line. The report quotes the line as shown.

## 2 · PART B — the rename list carries the right names (D676): `finance.db` `marg_item_rename`

The seven rows below hold S268's spellings; the owner's rule of 05-Oct keeps the words staff type unchanged. **Before anything else in the install** (Amir's list may open any hour now — the proof shows 2 items left): `finance.db.bak_S482_<stamp>` by the backup API, then one `UPDATE` per row, keyed by `id` AND `old_name` (both must match, else stop), setting `new_name`, `new20 = item_alias.clip(new_name, 20)`, `new27 = item_alias.clip(new_name, 27)` (the table's own convention — a right-stripped cut), `note = note || ' · S482/D676: spelling per S295_ORTHOTIC_RENAMES_CHECKED (the search words kept)'`. Rows `done_by`, `done_at`, `verified_*` are NULL on all seven today — if any is not NULL at install time, **stop that row and report** (Amir already did it under the old name).

| id | old_name | new_name (replace with) |
|---|---|---|
| 5 | L S BELT CONT GRAY UNISON L | L S BELT L CONT GRAY UNISON |
| 6 | L S BELT CONT GRAY UNISON M | L S BELT M CONT GRAY UNISON |
| 7 | L S BELT CONT GRAY UNISON XL | L S BELT XL CONT GRAY UNISON |
| 8 | L S BELT CONT GRAY UNISON XXL | L S BELT XXL CONT GRAY UNISON |
| 9 | L S BELT CONT GRAY UNISON XXX | L S BELT 3XL CONT GRAY UNISON |
| 21 | BLING PELVIC TRACTION BELT L | BLING PELVIC L TRACTION BELT |
| 22 | BLING PELVIC TRACTION BELT XL | BLING PELVIC XL TRACTION BELT |

After the update: no two of the 23 rows share `new20`; no `new_name` exceeds 29 characters; the other 16 rows are byte-unchanged (compare the whole table before/after, those seven rows aside). `stock_app._s444_renames` and `api_pad_rename_tick` read `new_name` live — nothing to edit there; the walk opens Amir's rename list on the scratch copy (with the proof forced green there) and shows the seven new spellings.

## 3 · PART C — the spine's reader knows the empty day (F-732): `spine/marg_read.py`, one reading file

`read_sale_detail(rows)`, read on the real EMPTY sheet of 04-10 (title · heads · `Total No. of | Bills: 0 | DAY TOTAL : | 0.0 …`): the footer row is caught by the `DAY TOTAL` branch (`c[2]`) **before** the `Total No. of` branch (`c[0]`), so `grand` and `nfoot` stay `None` and exactly two checks fail — *GRAND TOTAL = sum of bill GROSS* (`None vs 0.00`) and *footer bill count = bills read* (`None vs 0`); the other four pass. The mend: a row whose `c[0]` is `Total No. of` with `Bills: 0` and `DAY TOTAL` on the same row is the **empty footer** — recognised first, `nfoot = 0`, `grand = 0.0`, `data["empty"] = True`, `bills = []`, and the day taken from the title's `AS ON dd-mm-yyyy` (today `date_from` is empty for this sheet: no DATE row). A DETAIL sheet's footer (`Total No. of | Bills: N | GRAND TOTAL :`, a separate `DAY TOTAL` row) is untouched. A sheet with no BILL row whose footer is **not** `Bills: 0` keeps failing as today. Nothing else in the file.

**The reading already written:** `spine_evidence.py` reads a file once (`f["md5"] not in have`), so `/root/finance/spine/readings/15495622….json` (the 04-10 sheet, two failures) is removed with a `.bak_S482` copy beside it, and the next 10-minute run writes it again with the new reader; the walk shows the new certificate clean. The tile's `certify` then shows the tick, not *jaanch me fail*.

## 4 · PART D — the Drive collector (F-733): `marg_ingest.py`

Three anchored edits in `run()` (~l.368–396), mirroring what S480 put into `marg_take.take` (`_s480_empty_day`): a `SALE_BILLWISE` VERIFIED with variant `SUMMARY1` → no `sale_lines` call, `lines = 0`; a `SALE_BILLWISE` VERIFIED whose `read_report` is `empty` → `lines = 0`, `reason = "EMPTY — no sale on <ISO date>"` and `date_from = date_to =` that day (the door's exact words and shape, so A.2 reads both); and `rebuild_chain` called after a `SALE_BILLWISE` is written, as `take()` does. `_readers()` already imports the S480 `marg_report`. Nothing else.

## 5 · PART E — the outbox does not re-send an empty day (F-731): manojz `MargPull\marg_gate.py`

A failure is **never** written to `sent` (only accepted / duplicate / superseded are; failures go to `failures` → `_NEEDS_ATTENTION.txt`), so the test is on the index row: in `do_send`'s first `todo` loop (~l.603–612), before the superseded logic, a candidate whose `read_index` row has `int(row["rows"] or 0) <= 3` (the EMPTY sheet is title, heads, one footer row; `rows` is a string in `index.csv`) is written `sent[md5] = {"result": "empty_day", "http": None, "business_date": row["date_to"], "when": now_str(), "export_stamp": …, "note": "an empty day — nothing for the sale-bill route (F-731); the door already has it"}` and skipped. `"empty_day"` is added to the skip tuples at ~l.605 (`do_send`) **and** ~l.313 (`build_picture.sent_here`, so `status` stops listing the day as NOT SENT and `refresh_upload_folder` stops copying the file into `_UPLOAD_NOW` every cycle) — **not** to ~l.451 (`delivered_stamps`: a later real DETAIL sheet of that date must still be sent). `pipeline_status.py` counts any md5 keyed in `sent` as not pending, so the pull's status line reads ok again. The already-queued 04-10 file (`15495622…`, `rows = 3`) is resolved by the same rule at the first run after placing; `_NEEDS_ATTENTION.txt` is rewritten clean. A DETAIL sheet (bill rows) is never touched by this rule. **One line for the parent, not done here:** the clinic's upload route (`finance_app.py` / `finance_returns.py` — the `no_item_detail` answer) should take an EMPTY day as a day with no bills, so the *Sale bills from Marg* freshness leg stops ageing over a no-sale day.

## 6 · Walk (`walk_s482.py`) — sections 1, 2, 3 and the collector half of 4 on the server against a scratch `finance.db` (backup API, rows keyed W482*); the reader half of 4 and section 5 on manojz (the real EMPTY sheet exists only in manojz's `MargArchive` — the server deletes every sale sheet, S186 — and never enters the repository, F-185)

1. **The chain on the live copy:** `rebuild_chain` → `chain_state` reports exactly `A003478` and `CN00203` between 08-Sep and 09-Sep, nothing else, `complete = False`; `last` = the newest numbered day. Negative control (OLD file): no table, no state.
2. **Invented fixtures (W482):** (a) remove one more number → it is named; (b) an EMPTY row for a Sunday between two days whose numbers meet → `complete`, the gap list unchanged; (c) an EMPTY row between two days whose numbers do **not** meet → one gap naming all three dates; (d) a gap inside a day → that day's `gap_inside`; (e) the tile renders each case's Hindi and English line exactly as A.4 words them, and renders **nothing** when `complete`.
3. **The renames:** the seven rows updated; the keyed update refuses a row whose `old_name` does not match (negative control: one invented row); `new20` unique over 23 rows; nothing else in the table changed; Amir's rename list on the scratch copy shows the seven new spellings — the gate is `stock_app._proof_state(con, _pad_report_data(con, cid))["state"] == "done"` behind `_S444_RENAMES_CACHE` (600 s): on the scratch copy the walk makes the proof `done` with W482 feed rows (or clears the cache and stubs `_proof_state`), never on the live database; staff-eye (D648): shavez, darpan, amir and the owner — every home and door page byte-equal before and after except the tile's gap line (shown because the live chain has one).
4. **The spine's reader (manojz, the repository's `marg_read.py` copy against `MargArchive\SALE_BILLWISE\2026-10\SALE_BILLWISE_DETAIL__2026-10-04__*.XLS`, and an invented 3-row fixture for the server's selftest):** OLD two failed checks, NEW none, `empty: True`, the day from the title; on a DETAIL sheet from the archive — the same checks, the same result; **the collector (server):** `marg_ingest.run` on a scratch archive with a SUMMARY1 and an EMPTY sheet — OLD raises / no reason; NEW `lines 0` and the EMPTY reason.
5. **The outbox (manojz, dry):** `marg_gate.py send --dry-run` on a scratch copy of `_outbox_state.json` and `index.csv`: the 04-10 EMPTY file goes to `empty_day` and is skipped; a DETAIL file is still in the send list; `status` no longer lists the day; OLD: the EMPTY file is in the send list. Then the real `send` once (`.bak_S482_52f502d1` beside the file first), `_NEEDS_ATTENTION.txt` gone or clean, and the pull's next status line reads ok (read from `_logs\pull_0000-00.log` — a clock read, not estimated).

## 7 · Done means

- The chain lives in `mi_bill_chain`; today's one gap is on Shavez's tile and the owner's line, worded as A.4; a re-export of 08-Sep and 09-Sep would clear it by itself.
- An empty day is transparent to the chain; an empty day with a gap across it names all three dates.
- Amir's rename list, when it opens, shows the D676 spellings; no other row moved.
- The spine certifies an EMPTY sheet clean, and the 04-10 reading is written again clean; the collector takes SUMMARY1 and EMPTY like the door and keeps the chain current.
- The pull reports ok again; the EMPTY file is `empty_day` in the outbox; the parent's line is named in the report.
- Every walk section green on NEW, its negative control red on OLD; healthz 200; the lock taken and released; the publish gate clean.

## 8 · Pins — the live bytes after S480; read each live before its first edit; STOP that file if different

| file | FROM |
|---|---|
| `/root/marg_ingest/marg_take.py` | `3ac9bbe03abf5c01c4ebc1bfffd30da2` |
| `/root/marg_ingest/marg_ingest.py` | `7f6b4dc25d1c247c8b45f05108e600ca` |
| `/root/finance/reports_tile.py` | `406e452b2e3cf5991e89100ee867e1d6` |
| `/root/finance/spine/marg_read.py` | `7ec9b325687de465ea6942affb25dec1` |
| manojz `D:\Downloads\margsync\MargPull\marg_gate.py` | `52f502d1ee1a59e37086fb3e514f7874` |
| `/root/finance/spine/readings/15495622….json` (removed, `.bak_S482` beside it) | read live |
| read only — `stock_app.py` `7e159de737c0ec03cea890053f1bcd58` · `amir_day.py` `709f20c1…` · `item_alias.py` `5168c3c0…` · `/root/marg_ingest/marg_router.py` `318086e3…` · `spine/spine_evidence.py` `0fcf6c64…` (md5 before and after) | |

Backups beside every file replaced (`<file>.bak_S482_<from8>`); `finance.db.bak_S482_<stamp>` by the backup API **before Part B's update** (the one data write besides the new table). Restart `clinic-finance` once; `/finance/healthz` 200. The lock taken and released.

## 9 · Report — `claude_code_briefs\REPORT_S482.md`

For the owner (3–6 lines): the bill chain is watched and today shows one gap (which bills, which days, what to do); Amir's list carries the agreed names; the empty day is accepted everywhere now; the pull's false "not ok" is gone. **No line of a sale sheet in the report.**

For the chat: every pin FROM → TO read back; the chain's state as measured live; the seven rows before/after; the walk's output and negative controls; the parent's line.

**Not in this kit, said plainly:** the proof's pairing rule and Amir's card wording, F-726 a, F-717, the learnt-name strike, `shelf_figure` onto `spine_read` (S483); the chain replacing `weekday()==6` in the tile's banner, `spine_build`, `export_watch`, `darpan_kal`, the freshness legs (S484); the dd-mm-yyyy text compares (S485); audit #24; PHI kinds kept off Drive's `refused_text` (a medical-PC kit); the clinic upload route taking an EMPTY day (the parent).

## 10 · The owner's line, after the publish

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S482_BILL_CHAIN/install_S482_BILL_CHAIN.sh
```

manojz: nothing — Claude Code places `marg_gate.py` itself and runs the outbox once.
