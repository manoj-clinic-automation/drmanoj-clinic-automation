# START HERE — SESSION 464 — the Scan App chat (papers & bills)

*Written at the S461 close (14-Nov-2026, 18:4x IST, full EOS) by the Scan App chat. Session **464 is RESERVED for this project** on the board (`board/_numbers`): take it there as the FIRST act (NUMBERS_PROTOCOL_v1) with a SHORT line (under 400 characters). The project's custom instructions govern every reply.*

## A · The open (OPEN_ROUTINE_v1)

1. **Connections:** `D:\Downloads` · `D:\dr-manoj-git` · `F:\ClinicBackup`. The device shell; never `git` in it. `/sessions` is full (F-1326): scratch in `/tmp`, and run Python with `TMPDIR=/tmp` (a walk's `tempfile` otherwise lands on the full disk). The shell refused at the S461 close ("bridge sockets") — the file tools still work; retry the shell once.
2. **The number:** 464 by a pinned write; the clock from the clock tool. Read the counters from the newest close's END line; read `_numbers` whole only to write it (F-1405). A kit number: read `kit_next`, not the last line (another chat's line may sit above).
3. **The board:** unread messages to `scanapp`; the packs reminder (D713).
4. **The day's checks:** `D:\Downloads\_kbtools\DAY_OPEN_LATEST.txt` — run `day_open.py` only when it is not today's or a publish / bundle came since.
5. **The pins:** this project's DECLARED-PENDING 6 — `procroom.py` 38c5bbaa (S831) · `claude_reader.py` a7df99bb · `clinic_papers.py` b8f551c4 · NEW `reader_watch.py` 5ba95fce (S833) · `scan_checks_s441.py` 5c934bdb · `asset_register.py` 63eba920 (S826) — CONFIRMED by a bundle newer than 14-Nov 18:25 IST. The cron line `# S833_READER_WATCH` is in the bundle's `crontab.txt`; `reader_watch.log` shows ticks.

## B · The work — in this order

1. **CREDIT NOTES ON THE SORTING DESK (D986, F-1174; his "Final" 18:39 IST 14-Nov).** The mock-up IS the specification: artifact "Credit notes on the sorting desk (mock-up)" v2, `https://claude.ai/artifact/D8jjGw4t8TjhvZSJWWwRnv`; the written spec `S461_CREDITNOTE_SPEC.md` (canon; read it first). Take a kit number before the scratch folder.
   - **Read `sorting_desk.py` (baa7c6aa) WHOLE first — drift 5.** Its kinds: `KINDS` (bill, estimate, challan, receipt, statement — S560), `CLAUDE_KIND`, the receipt prompt's pattern (`data-s560k`, "Make it a Receipt"), `_s560_pre`, `NOT_SPEND`.
   - **The reader:** `claude_reader.py` (a7df99bb) — its bill prompt's `doc_kind` list gains a credit note (its no., the invoice no. it names, the amount back, the lines); `clean()` keeps it.
   - **"Against which bill?":** the dealer's bills of 90 days, the reader's pick pre-chosen; each opens its scan and, for a pharmacy bill, **Marg's purchase entry lines** — read-only from `finance.db`; find the table Sanjeevni's scan register pairs a scan with its Marg bill (`scan_register.py`, the Sanjeevni chat's — read only) — and the credit note's lines and whether Marg's purchase return is entered.
   - **After Save:** pharmacy — handed to Sanjeevni marked credit note (if any Sanjeevni file must move: a PLANNED line on `_numbers` first and the chat told; nothing on Amir's screens); clinic — filed with the bill, its group's month lowered in the month the credit note is dated (`clinic_papers.MONTH_OF`, The month page, Stationery / Procedure room totals: check each place that sums a group); on the dealer's account — lowers nothing. Never spend, never approved.
   - **His screen:** the same view on the credit note's page and the bill's page (still owed); The month's "Credit notes" line.
   - A mock-up walk of the desk (`--browser` in the chat if a browser is at hand), a walk on the real app with a made-up database + a control, a cold review; installed switched on only after he sees it (a staff screen change).
2. **His Procedure room page (S831, live):** nothing owed; read `reader_watch.log` and the page's Step 1 live if he asks about stock.

## C · What this project is now (S461)

- **S831 live (17:59):** `/scanapp/procroom` — tiles; Start here; the FY's expenses and revenue (a month: bought; procedures one row per patient slip with fee and items; one Save → `save_morning` day by day, only the slips he changed); Stock now (count + reorder in one Save; gloves typed in whole pairs, kept in boxes of `proc.gloves_box` = 50); the rest folded; Top. Revenue = `price_p − discount_p` (a rejected discount not taken off; 'nahi hua' and an approved cancellation out), from the morning screen's floor (1-Oct).
- **S833 live (18:25):** `reader_watch.py` (cron every 5 min, the venv python) pushes "Scan app · paper reader STOPPED" + the reason once per stop and "reading again" once; switches: the estate's `ALL_OFF`, `reader_watch.on = off`; to: `reader_watch.to` (manoj). An expired key is named on the admin card. `auto_home` never moves a summary.

## D · Lessons of S461 (into §2C's NEVER list)

- A page Save that sends every row re-writes rows nobody touched when the rules under them moved — send a row only when a field in it changes (F-1414).
- A walk run from the kit folder can import the kit's own NEW module; the control then proves nothing (F-1415).
- The board's kit counter can move by another chat's line above the last one you read: take `kit_next`, not the last line's "Next".
