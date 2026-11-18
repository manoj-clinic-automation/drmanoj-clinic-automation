# S484 — Sheet 7 as a voucher document: the analysis and the fix (18-Nov-2026, 17:49 his word; the share done 18:15)

**His word (17:49):** item 7 is still not up to the mark — (a) October's rows say the card statements are not up to date while the latest card statements cover the whole of October; (b) "Attachment in Drive: yes" says nothing about *where*; (c) as it stands it cannot go to the accountants — if it goes, it must be a proper document supported by the actual receipts.

## 1 · What is true today (read live as checker, 17:5x IST, counts only)

| fact | state |
|---|---|
| Card statements covering October | **ICICI Amazon Pay** dated 12-Nov (13-Oct → 12-Nov) and **ICICI Coral** dated 02-Nov (03-Oct → 02-Nov) are **read and proved** on the shelf. **HDFC Regalia's November statement has not come** (the shelf's own note: "the statement dated November 2026 has not come yet"); its October one covers only to 15-Oct. |
| October's sheet 7 live | 3 papers moved to the card sheet (the "Paid by card" sheet lists them: Amazon 2, Coral 1) · 6 left on the papers sheet: 2 "amount on the receipt", 2 after 15-Oct "not every card's statement of this date is read yet" (true only of HDFC), 2 "receipt only" · NK Pathology's sheet 2. |
| So (a) | the wording is the fault, not the shelf: two of the three cards *are* read for every October date; the line should say exactly which statement is missing ("HDFC Regalia's statement dated ~15-Nov, covering 16-Oct to 15-Nov — not come yet"), not "not every card's". |
| So (b) | the Payment Register (the Janitor's sheet, S233/S234) carries only a Yes/No "Attachment in Drive" and a Gmail link — no file name, no Drive link. The receipt itself is saved by the Janitor in **his PERSONAL Drive**: `My Drive / Payment Records / <vendor> / <mail date yyyy-MM-dd>_<attachment name>` (read from `saveThreadAttachments_` in the S233 export). The box has **no credential to the personal plane** (PERSONAL_GOOGLE_PLANE_v1_S233); it reads the clinic Drive's *Clinic Data Archive* and *Credit Card Statements* with a read-only service account. |
| So (c) | a proper document is possible with one one-time step by him (§3 — **done 18:15**): share the personal **Payment Records** folder, read-only, with the box's Drive reader. Then the receipts can be fetched nightly as the statements are, and sheet 7 becomes a bundle PDF (index + every receipt), exactly as section 8's bundles are built today (`build_bundle`: index page → `convert` → `pdfunite`). |

## 2 · The fix — kit S881_SHEET7_VOUCHERS_DOC (the parent's; packs.py + NEW payment_records.py + one cron line; taken at `_numbers` v1772)

1. **Receipts on the box.** `payment_records.py fetch` (nightly, after the 02:05 register ingest): lists the shared *Payment Records* folder (Drive search `sharedWithMe`, name = Payment Records), downloads new files into `/root/finance/payment_records/<vendor>/<name>` and records them in a table `payment_record_file` (drive_id, vendor folder, mail date, name, size, sha256, local path). Read-only on Drive, idempotent, never deletes. Each register row is paired to its files by **the same mail**: folder = the Janitor's vendor name of the sender, date = the mail date (both are what the register row carries); a row with "Attachment in Drive: Yes" and no file found is said so on the sheet ("receipt not reached the box yet"). **First act of the build: a read-only listing of the shared folder (counts only) proves the share is seen.**
2. **Amounts read from the receipt** where the register has none (today 4 of October's 14): the receipt PDF's text (`pdf_text`, already in packs.py) is searched for one labelled total (Total / Amount paid / Grand total / ₹ … ); one clear figure → the row gets it, marked "amount read from the receipt"; otherwise it stays "see the receipt" — never a guess.
3. **Sheet 7 = one document per month: "Payments not on a card — October 2026.pdf"**: page 1 the index (date · vendor · description · amount · where the debit is · receipt on page n), then every receipt in that order (PDFs as they are; images and HTML mails rendered to PDF). The xlsx stays beside it for Tally entry, its "Attachment in Drive" column replaced by **"Receipt" = the file name and its page in the bundle**. The NK Pathology rows get their own bundle (the lab's books). The "Paid by card" sheet's rows get the same receipt names (their bundle rides with the card sheet, item 5).
4. **"Where the debit is" says exactly what is missing**: for a paper on no bank line and no card line — "ICICI Amazon Pay and ICICI Coral statements covering this date are read, no such line; **HDFC Regalia's statement dated ~15-Nov (16-Oct to 15-Nov) has not come yet**" — computed from `card_stmt` (each card's last `period_to` and its cycle) and the shelf's bank line tables (each account's last line date). When every statement covering the date is read: "receipt only — on no statement read for this date (cash, or an account not on the shelf)".
5. **The card sheet (4.4) gets its receipts too**: "Card receipts — November 2026.pdf" (the receipts of the lines on that month's card sheet), and the *Every line* "Receipt" column names the file and its page. Same mechanism, second output.
6. **The page**: row 7 shows the bundle and the xlsx as two downloads (S877's in-place download), the count of receipts found / missing, and the one line about the missing statement. While there: the Send-to-accountants `confirm()` → the Hub's two-tap (F-1484).

**Not changed:** the Janitor and his personal plane (read, never act); the register ingest (S234); no figure of any other sheet.

## 3 · The one step only he could do (once) — DONE 18:15 IST 18-Nov

He shared the Drive folder **Payment Records** (his personal account, My Drive) as Viewer with the box's Drive reader (the service account's address, printed on the VPS by one line — the address only, never the key). The kit finds the folder by name under *Shared with me*.

## 4 · Order of work (the next parent session, 486)
- Prove the share (a listing, counts only). If not seen: one line to him, stop.
- Then §2 items 1 → 4 → 3 → 2 → 5 → 6 in one kit (S881), walked on a made-up shared folder (a stub as `STMT_DRIVE_STUB`), the live file as the control; a picture of the index page on made-up data for him before the install.
