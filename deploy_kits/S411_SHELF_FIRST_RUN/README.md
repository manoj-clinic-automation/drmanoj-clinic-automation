# S411_SHELF_FIRST_RUN — the statement shelf's first real run: read, fixed, placed

**Session 283 · 26-Sep-2026 · follow-up to S408 · OWNER: PARENT (clinic).** The owner shared the Drive folders; the first real run
(11:18 IST) fetched 21 bank files: 8 placed and every one refused, 14 unplaced. Diagnosed on the box, read-only first.

## What the box showed
- **All 21 bank files are ICICI** — six ICICI accounts, not three: Sanjeevni Medicos (current), Dr Manoj Agarwal Clinic (current),
  **NK Pathology (current)**, Dr Manoj Kumar Agarwal (savings), **Dr Bhawna Agarwal (savings)**, **Manoj Kumar Agarwal HUF (savings)**.
  12 are ICICI's "iCRM" monthly PDFs (July and August for each), 4 are ICICI's pipe-delimited `.txt` statements for odd periods
  (e.g. 15-Aug to 14-Sep), and **5 are Yes Bank PDFs that are password-locked** (`Incorrect password` to pdftotext) — 3 monthly savings
  statements and 2 "YFB monthly" current-account ones. Nothing Yes Bank ever reached the Yes Bank reader.
- **Why 8 were refused:** the S408 ICICI reader was written against a layout ICICI does not send. The real iCRM PDF prints the holder under
  "Your Details With Us:", the closing balance on a Summary row (`Savings XXXX1234 1,23,456.78 Cr`), the opening as a `B/F` row, the
  transaction dates with EN dashes (`03–08–2026`), amounts as withdrawals · deposits · [autosweep · reverse sweep] · balance `Cr|Dr`, and
  `Page Total:` rows across two or three pages. Six refusals said "no opening balance printed"; the other two were ICICI files that the
  identifier had labelled Yes Bank (a `UPI/…/YES BANK L` narration) and routed to the Yes Bank reader ("does not print 'Period:'").
- **Why 14 were unplaced:** 9 the identifier could not read at all — the 4 `.txt` (it only opened `.pdf`) and the 5 password-locked PDFs;
  4 iCRM PDFs had holders no slot named (NK Pathology at ICICI; Dr Manoj Kumar Agarwal at ICICI, whose slot words "MANOJ AGARWAL" did
  not match the printed "MANOJ KUMAR AGARWAL"); and 1 is All_Transactions.xlsx (fine). Of the 8 that WERE placed, two were placed wrong:
  the identifier read the WHOLE text, so "NK PATHOLOGY" inside a transfer narration put Dr Bhawna's statement on NK's slot.

## What was built
1. **`finance_icici.py` v1.1** (full-file revision of S408's file, backed up beside itself): reads the iCRM PDF (holder, Summary closing,
   B/F opening, EN-dash rows, Cr/Dr, page totals skipped), the pipe `.txt` (columns taken from its header row; no closing printed → the
   running balance stands and the record says so), and the S408 generic layout. **The proof is kept:** B/F + every row = every running
   balance = the printed closing; any row that does not carry the balance refuses the whole file, naming the row. A password-locked PDF
   raises "password-protected PDF". **The lines go to `icici_statement_period` / `icici_statement_line`**, ICICI's own tables — not to
   `bank_statement_*`, which `sanjeevni_approvals.yesbank_position` / `bank_view` / `_statement_covers` / `_seen_in_yesbank` and S407's
   `bank_check` read as "the Yes Bank statement" with no account filter (twelve ICICI statements there would have put an ICICI closing on
   the owner's Bank card and matched Yes Bank movements against ICICI lines).
2. **`packs.py`** (anchored): `identify_text` reads the **header** (the first 24 lines) — the bank, the holder line after "Your Details
   With Us:", the account tail, the period — never a narration; **holders match as word sets** (`M/S.`, `DR.` dropped; SANJEEVANI folded),
   **a phrase printed as such ranks above a word set, then the longest match wins** (MANOJ KUMAR AGARWAL HUF beats MANOJ KUMAR AGARWAL;
   DR MANOJ AGARWAL CLINIC beats MANOJ KUMAR AGARWAL; with S408's older words, "HUF" printed beats "MANOJ AGARWAL" assembled), a tie
   is unplaced; the twelve accounts' words as the banks print them; **three ICICI slots added** (`icici_nk`, `icici_bhawna`, `icici_huf`);
   **a by-words placement learns the account tail** (the `.txt`, which prints only the account number, then lands by tail — the
   identifier re-passes while a pass is still learning tails, so a `.txt` fetched before its account's PDF is not left behind); `.txt` / `.csv`
   are read; a locked PDF is named ("password-protected PDF — put a decrypted copy in *Bank Statements/Decrypted*") and the owner's tap files
   it as a locked original; a statement covering only part of a month is **`partial`** — never the month's statement, not in the pack, not
   Amir's; the electricity row reads ICICI's own table; **the owner edits a slot's words** (`POST /finance/packs/api/slot-words`, data never
   code) and the unplaced files are re-identified; the unplaced table shows the **holder text the PDF prints** with the masked tail.
3. **`packs.html`**: the holder column; the "words" tap on each cell.
4. **`seed_s411.py`**: the three slots; the words replaced only where they are still S408's seed values; every bank file's identification
   cleared and re-run with the new code; the month grid printed (states only).
5. `stmt_shelf.py` (e74c29c0) and `finance_yesbank.py` (825016c0) **not touched** — the fetch already takes `.txt`; no Yes Bank text was ever
   refused by the Yes Bank reader (all five Yes Bank files are locked).

## Pins (read live 26-Sep-2026 12:14 IST)
| file | FROM | TO |
|---|---|---|
| /root/finance/packs.py | 734c7fc0f4ff780a94448e2b834f72b1 | afd429bf8c0e7f685adda7d688045ab7 |
| /root/finance/packs.html | 03fb47f68ffd28b375b50c91567cfcaa | b46d817c7a77944c4280ac72f95a6808 |
| /root/finance/finance_icici.py (replaced, v1.0 → v1.1) | a79dce49bfd757a6db22aa68783d67a7 | the kit file's md5 (SUMS.md5) |

Restarts `clinic-finance` only. `finance.db` backed up first. After placing: the seed re-identifies the live files and the 05:40 fetcher runs
once by hand. **Declared:** S408's frozen walk has one check that asserted the ICICI fixture's lines in `bank_statement_period/_line`; S411
supersedes it (see 1). The installer accepts S408's walk at 26/27 only when the single red is that named check.

## Proof
`walk_s411.py` — the real finance app over scratch copies: (1) a fixture Drive in ICICI's real shapes (iCRM PDFs with EN dashes and Cr
suffixes for the six holders, a July one, a look-alike holder, a tampered copy, a pipe `.txt`, a PDF with an `/Encrypt` dictionary no
password opens, a Yes Bank head): the header decides (a Yes Bank narration and "SANJEEVNI" inside the HUF file do not move it), the longest
word set wins, the look-alike is unplaced with its holder text, the tails are learned and the `.txt` lands by tail; the reader reads every
good file and refuses the tampered one naming its row; the lines are in `icici_statement_*` and nothing in `bank_statement_*`; the locked
file is named and the owner's tap files it as a locked original; the owner edits words (darpan cannot); the grid — August six ICICI cells
read / matched, July NK "arrived" (its file is the tampered one), September Sanjeevni **partial**; the pack rows and Amir's pack follow.
(2) **The real 21 files** in a second scratch copy, exactly as the install does it: the reader over each (counts and the proof only — never
an amount), the seed, the grid, the tails, nothing in the Yes Bank tables. Negative controls: the S408 identifier and reader on the same
crafted files (bank flipped, Bhawna on NK, "no opening balance printed", `.txt` unreadable). Then S410's, S409's, S408's (26/27 + the
declared supersession), S407's, S406's, S405's, S404's, S403's, S400's and S402's own walks re-run.

## Run
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S411_SHELF_FIRST_RUN/install_S411_SHELF_FIRST_RUN.sh
```
Undo: the three `.bak_S411_<from8>` files back, `systemctl restart clinic-finance`, healthz 200. The re-identification is data (stmt_file
rows, learned tails, three slots, ICICI tables) and harmless; the database backup is used only if the owner says so.
