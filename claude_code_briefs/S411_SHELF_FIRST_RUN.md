# Claude Code brief — S411_SHELF_FIRST_RUN (the statement shelf's first real run: 8 refused, 14 unplaced — read, fix, place)

Written 26-Sep-2026 by the Sanjeevni chat (S283). Read `CLAUDE.md` first. **Kit S411 (follow-up to S408; PARENT-owned, same README rule).**
The owner has done his part: *Bank Statements* (the folder itself, not only its 2026 subfolder), *Credit Card Statements* and Shavez's
workbook are now shared with the service account. He wants NO further commands from the chat — **you diagnose on the box yourself.**

## 1 · What the first real run showed (owner's paste, 11:18 IST)
`fetch: 21 new, 99 seen` · `identify: placed 8, unplaced 14, read 0, refused 8, skipped 0`. Earlier runs: cards 39 originals + 38 decrypted
placed and `n/a`/`locked original` (fine); All_Transactions.xlsx skipped (fine); 1 unplaced from the card folders.
So: of 21 bank-statement PDFs, 8 were placed by holder name and **every one of the 8 was refused by a reader**; 14 could not be placed.

## 2 · Do, in this order, read-only first
1. **Read the refusals** (`stmt_file.read_status LIKE 'refused%'`, joined to `stmt_slot`): which bank, which reader, what message. Expect two
   different causes: the Yes Bank reader (`finance_yesbank.ingest_statement`, S360) is strict about its own period/opening/closing proof and may
   refuse a statement whose layout differs from the one it was proven on (savings vs current, or a different statement period format); the ICICI
   reader (`finance_icici.py`, S408) has **never seen a real ICICI PDF** — the report said "the first real one decides". Fix each reader on the
   real files (pdftotext -layout on the box; keep the proof — opening + rows = closing, every running balance — and refuse only when the proof
   fails). Do not loosen a proof to make a file pass; make the parser read the real layout.
2. **Read the unplaced 14**: for each, the identifier's `note`/`ident_how`, the holder text and tail it extracted. Expect: the holder-name match
   was too narrow (initials, "DR", "M/S", "HUF" spellings, the clinic's name variants, "SANJEEVNI" vs "SANJEEVANI"), or the tail is on a page
   the identifier did not read. Widen `identify_text`/`place` on the real text (words as data in `stmt_slot.ident_words`, editable on the page),
   re-run `process_inbox` on the unplaced rows. Whatever still cannot be placed stays for the owner's drop-down, with the holder text the PDF
   shows (masked tail) so his choice is easy. Never place by file name.
3. **Re-run the shelf** (`stmt_shelf.py run`) and read back the month grid for August and September 2026: which cells are arrived / read /
   matched, which are still empty. Put the grid in the report.
4. The cron is 05:40 IST; leave it. Restart `clinic-finance` only if a served module changed.

## 3 · Pins (read live; S408 TO pins: packs.py 734c7fc0, stmt_shelf.py e74c29c0, finance_icici.py a79dce4…; finance_yesbank.py 825016c0 —
touch the Yes Bank reader only with an anchored, proof-keeping change, declared; it is the Sanjeevni file the NEFT matching (S407) reads)

## 4 · Walk
The S408 walk re-run green · each fixed reader proves the real files it refused (say how many lines, opening/closing to the paisa) and still
refuses the tampered fixture · the widened identifier places the real 14 (or names the remainder with their masked holder text) and does not
mis-place a crafted look-alike · the grid read back.

## 5 · Done means
Kit `deploy_kits\S411_SHELF_FIRST_RUN\` · installed · published · `claude_code_briefs\REPORT_S411.md` — owner lines first: how many of the
21 are now read, how many still need his drop-down (and what each one shows him), what the September pack will hold tonight; ending with
`https://followup.dr-manoj.in/finance/packs`. **No account number, card number or amount from a personal statement in the report.**
