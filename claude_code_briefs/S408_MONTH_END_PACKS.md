# Claude Code brief — S408_MONTH_END_PACKS (statement shelf · ICICI reader · accountant pack · Amir's pack · Shavez's checklist)

Written 26-Sep-2026 by the Sanjeevni chat (S283). Read `CLAUDE.md` first. **Kit S408 · decision D624.** The owner approved this WHAT
(26-Sep, his formal list). **Runs LAST in the paste, after S409** (it reads S409's scan lanes). **Ownership: PARENT (clinic) — the kit's
README says so**; the three Sanjeevni pieces (Amir's pack, the NEFT details, the Sanjeevni statement matching) are marked as such.
Everything here is server-side; no phone, no mail-relay, no Apps Script change. The accountants receive nothing until the owner taps Send.

## 1 · The owner's words (26-Sep) — the formal list, final
**Accountant pack, automatic:** (1) doctor's monthly income sheet + the date-wise clinic ledger, physiotherapy excluded (the paper OPD
register stays their own add-on); (2) UPI totals + the cash/UPI correction report (the CA ruling); (3) **every bank statement received by
email, every month** — Yes Bank current: NK Pathology · Dr Manoj Agarwal Clinic · Sanjeevni Medicos; Yes Bank savings: Dr Manoj Agarwal ·
Dr Bhawna Agarwal · Manoj Kumar Agarwal HUF; ICICI: all accounts; (4) credit-card statements, password removed — HDFC Business Regalia,
ICICI Amazon Pay, ICICI Coral — plus `All_Transactions.xlsx`; (5) electricity: the two auto-paid bills (his and Dr Bhawna's) as one
reconciliation line each from the ICICI statements; (6) Sanjeevni NEFT details: advice Excel + letter copy; (7) the monthly payment digest;
(8) scanned bills: Dr Bhawna's lab-purchase bills and his expense-file bills (S409 lanes) as a numbered bundle with a one-line index.
**Physical only:** lab register accounts, lab receipt book. **Excluded:** salary sheet, attendance.
**Amir's pack — pushed in his app, no email:** paid NEFT sheet (each line marked paid, bank date once confirmed), Yes Bank Sanjeevni
statement, ICICI Sanjeevni statement — previous month. **Shavez's monthly checklist** becomes a page.

## 2 · What exists
- **Drive (clinic account drmka.ortho, service account on the box):** the mail relay in the owner's personal Gmail forwards every bank
  statement mail (content-based, tag [STMT]) to the clinic account; the clinic account's filer script (S195; masked copy in
  `deploy_kits\GAS_CURRENT\UPIReconciliation\Bank_Statement_Filer.gs`) files each PDF at **Clinic Data Archive / Bank Statements / <year> /**
  (folder id `1wGzaXnCoKcILw1VSv3UGYfQlVTl78UgT`) and mails a copy to both accountants (their two addresses are in that script — read them
  into `setting` `packs.accountant_to` at install; never into code). **The server never reads that folder today.**
- **Credit Card Statements** (owner's personal account, shared VIEW with the clinic account 26-Sep 07:13 IST): folder
  `1XpDt8YMovgMBivMC4_aBvK_gwTESCAA6` → `HDFC Business Regalia/`, `ICICI Amazon Pay/`, `ICICI Card 5007/` (password-locked originals),
  `Decrypted/` (`1LOSA173EQPF5IvWK3ISksS1Qjh9DUXiV`, same three subfolders, password removed — filled in batches, not at arrival), and
  `All_Transactions.xlsx` (`1-DGksJHegCC0Md6uDDRCP8Z9w3uxeqv0`). File names carry the date and a masked card number; the ICICI Amazon card
  number changed in Feb 2026 (two masked forms, one card). **Take only from Decrypted; flag a card whose newest original has no decrypted twin.**
- **Drive reads from the box:** `/root/finance/records_drive.py` (83a7171f) — the venv helper (`/root/wa/venv/bin/python3`, S335: `list <folderId>`
  and `media <fileId>`); the web app's python has no Google libraries — go through the helper, as records.py does.
- **Readers:** Yes Bank PDF `finance_yesbank.py` (825016c0; `ingest_statement`, `bank_statement_line`/`_period`, account_ref); **no ICICI
  statement reader exists** (S281/S283 confirmed; only `bank_anchor` seeded by hand from the August closing, S377). `pdftotext` is on the box (S360).
- **Clinic figures (parent, read-only here):** the day revenue page `finance_clinic_day.py` + `clinic_day_pdf.py` (`/finance/clinic/day/<date>`),
  the UPI report `clinic_upi_report.py`, the payment digest (find it: `payments_register.py` / the reports tile), the correction report
  ("cash/UPI correction report", find by that title). The Sanjeevni NEFT pack: `purchase_app.py` `/page/pay/<month>/advice.xlsx`, `/letter`, `/pack`.
- **Shavez's checklist:** Drive `SHAVEZ AND MKA MTHLY WORKS 2026.xlsx` (`1gFUSiuwZuVTd0LqExXy7b3o42_MXrHUP`), ~35 items in four groups
  (Sanjeevni · Lab · Clinic · "Accountant ka samaan"). The requirements doc `Accounts_Monthly_Requirements_v1_2026-08.docx`
  (`144bldDTpppC3LG7Frh-61mMCJBuSgv2V`) is superseded by §1 where they differ.
- Amir's board `amir_day.py` (as S407 left it — read live). Mail from the box: find the sender the health report uses (`/root/wa/clinic_health_report.py`).

## 3 · The build (D624)
1. **The shelf (nightly + on demand).** New tables `stmt_slot` (id, bank, holder_label, kind current/savings/card, ident_tail, ident_words,
   owner_set, sanjeevni 0/1) and `stmt_file` (drive_id, name, mtime, slot_id NULL, period_from, period_to, read_status, matched_status,
   sha256, fetched_at). A root cron line (declared) runs `/root/finance/stmt_shelf.py` at 05:40 IST: list Bank Statements/<year> and
   Credit Card Statements/Decrypted/*, fetch new files, **identify each by its content** (pdftotext: the account holder's name and the
   account/card tail printed inside; the statement period) against `stmt_slot`; never by file name, subject or sender. Seed the slots
   from §1's list with the holder labels only; the tails are learned: an unplaced file is listed on the owner's page with a drop-down
   "which account?" — his one tap sets `ident_tail` for that slot for ever. Every account's statement of a month is one slot-month cell:
   arrived / read / matched. **A month with any cell empty by the 10th** → a Needs-you line and a Shavez checklist line.
2. **ICICI reader** (`/root/finance/finance_icici.py`): the account statement PDF (pdftotext -layout) → the same `bank_statement_line`/
   `_period` shape as Yes Bank, proven against the statement's own opening/closing and each running balance (the S360 method); refuses
   with a message on any mismatch. Sanjeevni's ICICI statement then feeds the POS-settlement check and `bank_anchor` refresh; the
   Sanjeevni Yes Bank one feeds S407's NEFT confirmation. Personal and clinic accounts are read for the shelf and the electricity lines
   only — no other use, no other screen.
3. **The Month-end packs page** `/finance/packs` (owner, English; tile "Month-end packs", roles doctor — portal.py + grants, parent, declared)
   with a month picker. Three cards:
   - **Accountant pack**: every §1 item as a row: `ready ✓` / `missing — why` / `late (belongs to <month>)`; tap to preview each; the two
     paper items as ticks; one button **Send to accountants** → one email (or "part 2" when over 20 MB) to `packs.accountant_to` with the
     attachments, and a receipt row `pack_send` (month, when, by, what, message-id). A second send is a re-send, recorded as such.
     Electricity (item 5): the ICICI statement lines whose narration matches `packs.electricity_words` (setting, seeded from what the real
     statements show — read them; if nothing matches, say so on the row) → one line each `auto-paid ₹X on <date> from account …<tail>`.
     Scanned bundles (item 8): every S409 bill of lane `lab_purchase` and `owner_expense` with bill_date in the month (plus lane rows scanned
     in the month with an earlier bill_date, under "Late — belongs to <month>") → one PDF each bundle, stamp numbers as the index page.
   - **Amir's pack**: assembled when both Sanjeevni statements are on the shelf: the paid NEFT sheet (S407's marks) + the two statement PDFs;
     shown on Amir's board as **"Pichle mahine ka pack"** with tap-to-open each and a `dekh liya` tick (who, when). **No email to Amir.**
   - **Shavez's checklist** `/finance/packs/checklist` (staff, Hindi; tile "Mahine ka kaam" granted to shavez — portal/grants, parent,
     declared; new unit `packs` maker shavez, checker manoj, S400 pattern): the Excel's items as data rows (`packs_item` table seeded from
     the workbook, editable by the owner), each `system se ho gaya` where automatic (linked to the pack row) or a tick for the manual ones,
     with who/when; the Lab items ticks only. What is still open on the 10th → the owner's Needs you.
4. **Nothing manual changes** until the owner sees the first pack (September 2026, sent in October); the filer's own accountant mails continue.

## 4 · FROM pins (read live first; mismatch = stop that file and report)
| file | FROM |
|---|---|
| /root/finance/finance_yesbank.py | 825016c02364dc5d22027ff192d1d29d (only if the shelf needs a small hook; prefer calling it) |
| /root/finance/amir_day.py | as S407 left it — read live |
| /root/finance/purchase_app.py | as S407 left it — read live (read-only use of advice/letter/pack routes) |
| /root/finance/finance_app.py · /root/portal/portal.py · /root/portal/tile_grants.json | as S409 left them — read live (clinic — declared: unit `packs`, two tiles, grants) |
| /root/finance/sanjeevni_approvals.py · finance_ui/finance_approvals.html | as S407 left them — read live (Needs-you lines only) |
| /root/assetapp/asset_register.py | READ ONLY (S409's lanes; the bundle reads `bills` + files via the read-only connection S403 uses) |
New: `stmt_shelf.py`, `finance_icici.py`, `packs.py` + `packs.html` + `packs_checklist.html`. One root cron line (05:40 IST), declared.
Restart `clinic-finance` + `clinic-portal`. **Nothing here touches the clinic revenue or salary code — read-only imports/HTTP only.**

## 5 · The walk (scratch copies of finance.db and assets.db; own rows; Drive NOT called — a fixture folder of sample PDFs stands in;
never sends a real email — the sender is stubbed and its arguments asserted)
Identification by content places a Yes Bank current, a Yes Bank savings, an ICICI and a card PDF into the right slots; a file whose tail
is unknown is listed unplaced; the owner's one tap sets the tail and the file lands · a card whose original has no decrypted twin flags ·
the ICICI reader proves opening/closing/running balance on the fixture and refuses a tampered one · the month cells arrived/read/matched
compute; empty-by-the-10th → Needs-you + checklist line · every §1 row reads ready/missing with a reason on a crafted month; electricity
lines from crafted narrations; the S409 bundle from crafted lane rows with a late one under "Late" · Send builds one mail with the right
attachments and writes `pack_send`; > 20 MB splits · Amir's card appears only when both statements are on the shelf; the tick stores ·
Shavez's page lists the workbook's items; a tick stores once (10-min guard); the owner sees the open items · bhati/darpan/amir refused on
the owner page; shavez allowed on the checklist only · negative controls · S400–S409 walks re-run green.

## 6 · Done means
Kit `deploy_kits\S408_MONTH_END_PACKS\` (README: **owner = parent (clinic)**; Sanjeevni pieces named) · installed, md5s read back · healthz 200 ·
published · `claude_code_briefs\REPORT_S408.md` (owner lines first: what the September pack will hold, which slots are still unnamed and need
his one tap, what Shavez and Amir see; ending with `https://followup.dr-manoj.in/finance/packs`, `https://followup.dr-manoj.in/finance/packs/checklist`
and `https://followup.dr-manoj.in/finance/amir`). This is the last brief of the paste.
