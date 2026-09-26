# S408_MONTH_END_PACKS — statement shelf · ICICI reader · accountant pack · Amir's pack · Shavez's checklist

**Session 283 · 26-Sep-2026 · decision D624. OWNER OF THIS KIT: PARENT (clinic).** The three Sanjeevni pieces are marked (Sanjeevni):
Amir's pack, the NEFT details row, the Sanjeevni statement matching / the ICICI anchor refresh. Last of the five-brief paste, after S409
(it reads S409's lanes). Everything is server-side; the accountants receive nothing until the owner taps Send.

## What the owner asked for (26-Sep, the formal list)
Accountant pack, automatic: (1) the monthly income sheet + the date-wise clinic ledger (physiotherapy excluded); (2) UPI totals + the
cash/UPI correction report; (3) every bank statement received by email, every month (Yes Bank current ×3, Yes Bank savings ×3, ICICI);
(4) the card statements, password removed, + All_Transactions.xlsx; (5) electricity: the two auto-paid bills as one line each from the
ICICI statements; (6) Sanjeevni NEFT details: advice Excel + letter copy; (7) the monthly payment digest; (8) the scanned lab-purchase and
expense-file bills as numbered bundles with an index. Physical only: lab register accounts, lab receipt book. Amir's pack pushed in his
app. Shavez's monthly checklist as a page.

## What was built
**NEW `packs.py` + `packs.html` + `packs_checklist.html` + `stmt_shelf.py` + `finance_icici.py`** in `/root/finance`.
1. **The shelf.** `stmt_slot` — one row per account / card of the owner's list (12 seeded with the holder's words; **the tail is learned**
   by his one tap); `stmt_file` — every file fetched. `stmt_shelf.py` (venv python, **root cron 05:40 IST, declared**) lists
   *Bank Statements/<year>* and *Credit Card Statements* (the three locked-original folders, *Decrypted/<card>*, *All_Transactions.xlsx*)
   through the same service account `records_drive.py` uses, fetches what the shelf lacks into `/root/finance/statements/inbox`, then
   `packs.process_inbox()` identifies each file **by its content** (pdftotext: the bank's name, the holder's words, the account / card
   tail, the period) — never by file name, subject or sender. A file whose tail a slot already knows lands *by tail*; else by the words
   when exactly one slot fits; else it is **unplaced**, listed on the owner's page with a drop-down "which account?" — his tap sets
   `ident_tail` for that slot for ever and every later file of that tail lands by itself. Bank files are read into
   `bank_statement_period/_line` (Yes Bank by `finance_yesbank`, ICICI by the new reader); a card file is filed as arrived; a locked
   original as *locked original*; a card whose newest original has no decrypted twin is flagged. Every account's month is one cell:
   **arrived / read / matched** (matched = a Sanjeevni statement read into the bank tables). Any cell empty by the 10th → a Needs-you line
   and a checklist line.
   **Found on install (F, for the chat): the six Drive ids in the brief answer 404 to the box's service account** — the folders are not
   shared with it (it holds only the patient-records folder). Until the owner shares *Clinic Data Archive/Bank Statements*,
   *Credit Card Statements* (with *Decrypted* and *All_Transactions.xlsx*) and the two documents with that account, the nightly fetch
   finds nothing and says so in `stmt_shelf.log`; the walk proves the shelf on a fixture folder, as the brief asked.
2. **ICICI reader** `finance_icici.py`: `pdftotext -layout` → the same shape as Yes Bank (account_ref = the tail), **each row's amount
   placed by the running balance** (previous + amount = balance → deposit; − → withdrawal), the closing balance checked; any mismatch
   refuses the file naming the row. No ICICI statement had ever been on the box, so it is written against ICICI's printed layout
   (Date · Particulars · Deposits · Withdrawals · Balance) and proven on a fixture in that layout; the first real statement decides,
   and a refusal is visible on the shelf. (Sanjeevni) the ICICI Sanjeevni statement refreshes `bank_anchor` (unit medical, icici) to
   its closing balance when newer than the anchor's as-on; its lines feed the electricity row and are there for the POS-settlement
   check (S290's page reads `bank_statement_line`; no new screen).
3. **`/finance/packs`** (owner, English; tile *Month-end packs*, roles doctor; unit `packs`, the doctor checker) with a month picker:
   - **Accountant pack**: every item as a row `ready ✓` / `missing — why` / `late (belongs to <month>)`; previews; the two paper items as
     ticks; **Send to accountants** → ONE email (or parts over `packs.mail_limit_mb`, 20) to setting `packs.accountant_to` (read from
     `Bank_Statement_Filer.gs` in the repository clone at install, never into code) through the box's SMTP (`/root/wa/.env`, the
     health report's credentials, read at send time), receipt row `pack_send` (month, when, by, what, message id, parts, bytes); a
     second send is a re-send, recorded; a repeat within 10 minutes is not sent. Rows: (1) `Clinic_income_<m>.xlsx` — an Income sheet
     and the date-wise ledger from `clinic_day_revenue`; (2) `UPI_and_corrections_<m>.xlsx` — UPI totals per unit from `upi_txn` and
     `finance_app._correction_rows` filtered to the month; (3) one row per bank slot with the shelf's file; (4) one row per card slot +
     All_Transactions.xlsx; (5) the ICICI lines matching `packs.electricity_words` → `auto-paid ₹X on <date> from account …<tail>`, or
     the reason none matched; (6, Sanjeevni) `purchase_app`'s own advice Excel + the letter (as HTML) when the month is final; (7)
     `Payment_digest_<m>.xlsx` from `payment_register`; (8) `Bills_lab_purchase_<m>.pdf` / `Bills_owner_expense_<m>.pdf` — an index page
     (stamp numbers; late rows as *Late, belongs to <month>*) + every scan (ImageMagick → PDF, `pdfunite`), rejected duplicates excluded.
   - **Amir's pack** (Sanjeevni): ready when both Sanjeevni statements of the month are on the shelf: the paid NEFT sheet (S407's marks)
     + the two PDFs; on his board as **"Pichle mahine ka pack"** with tap-to-open and a **dekh liya** tick (routes under `/finance/amir/pack/…`
     so his medical viewer row opens them). No email to Amir.
   - **Shavez's checklist** `/finance/packs/checklist` (staff, Hindi; tile *Mahine ka kaam* granted to shavez; unit `packs`, shavez
     maker): `packs_item` rows in four groups; *system se ho gaya* where automatic (linked to a pack row or a system fact), a tick for the
     manual ones (who, when; a repeat within 10 minutes not written twice); the Lab items ticks only; what is still open on the 10th
     → the owner's Needs you. **The workbook could not be read** (Drive 404 to the service account), so the items are seeded from the
     brief's four groups — the owner edits them (add / rename / retire) on his page.
4. Nothing manual changes; the filer's own accountant mails continue.

## Pins (FROM read on the box 26-Sep-2026 09:45 IST, after S409 → TO; built by `make_s408.py` from the live bytes)
| file | FROM | TO |
|---|---|---|
| /root/finance/finance_app.py (S407's TO; the unit + the guarded mount) | d19c2046b190a4ec00745dc4121152e8 | 5d9f2703b0142950fa2a0ee56c5938bd |
| /root/portal/portal.py (S403's TO; two tiles) | 968ca6027ae30d67e7d18b83f35b395d | 912a1d8299c01b1b11f4ca81bef52482 |
| /root/portal/tile_grants.json (v28 → v29) | 0aadfc523f9ab9c59633dedcd618cee9 | df73b84a0bde3917b97c233647ffe0a5 |
| /root/finance/sanjeevni_approvals.py (S407's TO; v1.8 → v1.9, two lines; `NEEDS_YOU_WITHOUT_S408=1` for S400's frozen walk only) | f6fc90d5d31badd3c5eec3691a78c4fb | 3cde91fbfead8e698ca1e3981362a6d3 |
| /root/finance/amir_day.py (S407's TO; the card) | 59a51d471cb30702dfd0cb8b6b6f3a44 | 068a3988e296f6579e2e780b2e4f623b |

`finance_yesbank.py`, `purchase_app.py`, `asset_register.py`: read only. Restarts `clinic-finance` + `clinic-portal`. `finance.db` and the
crontab are backed up first; the seed adds the `packs` unit (shavez maker, manoj checker), three settings, the 12 slots, the checklist items.

## Proof
`walk_s408.py` — the REAL finance app over scratch copies of finance.db and assets.db; a **fixture Drive** (crafted text PDFs: a Yes Bank
current Sanjeevni, an ICICI Sanjeevni with a PVVNL line, a HUF savings, one with an unknown holder, an HDFC card locked + decrypted +
a newer locked one, All_Transactions.xlsx) stands in through `STMT_DRIVE_STUB`; the mail goes to `.eml` files (`PACKS_MAIL_STUB`); "today"
is set: the unit, the pages and the gates · the fetch and the identification of every fixture (by words; the card by its folder; the
unknown one unplaced with the reason) · the ICICI read (period, opening / closing, three lines by the running balance, the cash deposit
flagged) · **negative control: one running balance changed by ₹100 → refused, naming the row** · the Yes Bank fixture's read refused
by the real reader and said so · the anchor not moved backwards · the August cells · the owner's tap learns the tail and the September
file of that tail lands by itself · Needs you on the 12th, silent on the 5th · every pack row with its status and reason; the
electricity line; the NEFT row on the real (final) August; the lab bundle's index (B-9401, B-9402 late, not the rejected B-9404) and
page count; the card row's missing twin · the paper tick; Send → one mail to the two addresses with the attachments, `pack_send`; a
repeat within 10 minutes refused; a 0.05 MB limit → parts *i of N*, *resend*; bhati refused · Amir's pack ready, his card, the three
pieces, the tick · the checklist (four groups, a manual tick once, an automatic item refuses, the send auto-ticks, the owner's edits) ·
the portal tiles. **Negative controls** on the box as it is; then **S409's, S407's, S406's, S405's, S404's, S403's, S400's and S402's
own walks re-run** on the patched files.

## Run
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S408_MONTH_END_PACKS/install_S408_MONTH_END_PACKS.sh
```
Undo: put back the five `.bak_S408_<from8>` files, remove the five new files, remove the S408 cron line (`crontab.bak_S408_<stamp>` holds
the old crontab), `systemctl restart clinic-finance clinic-portal`, healthz 200. The tables, rows and settings are data and harmless; the
database backup is used only if the owner says so.
