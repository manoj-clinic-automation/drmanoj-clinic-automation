# S434_PACKS_FIXES — the August accountant pack, made fit to send

**Session 286 (parent) · 28-Sep-2026.** The assistant walked the live August pack in its own browser, attachment by attachment, on the owner's instruction. What it found, and what this kit does:

| fault | what it was | now |
|---|---|---|
| F-653 | S433 retired the clinic's Yes Bank current row, taking the …0460 account for it; the account exists and the branch simply did not send August — the checklist then read "all statements 11/11" | the row is back and reads *missing* until the branch sends it |
| F-654 | the payment digest carried every payment-register mail — OTPs, sign-in links, failed or paused payments, expiry / storage / trial notices, report mails, one mail twice, and **a Docterz appointment line with a patient's name** | only receipts, invoices, bills and renewals; an appointment line never; an exact repeat once; an amount the mail did not state reads *see the receipt*; a total row |
| F-655 | the pharmacy's cash/UPI corrections read keys finance_app does not return — every row Rs 0 | finance_app's own keys: the amount, what happened, the likely bills, Marg's and the bank's UPI |
| F-656 | electricity looked only in the ICICI statements and read *ready* on 1 of 2 bills | the card sheet (All_Transactions.xlsx) too — the owner: the second bill is auto-paid by the ICICI Amazon Pay card; *ready* only at `packs.electricity_expected` (2) |
| F-657 | the income summary left out the split takings (Rs 29,100 short of the total) | an *of which split* line; the summary adds up |
| F-658 | the bundles picked scanned bills by the OCR's date | the month the scanning person confirmed (S435) first; a late bill already sent in its own month's pack is not sent again |

**Also:** the NEFT letter goes as a PDF (it was a bare 1 KB .html); every attachment has a readable name (*NK Pathology - Yes Bank current statement - August 2026.pdf*); the owner's page shows the clinic's UPI check (the bank's UPI against the takings paid online and split); and **the page is folded**: one summary card on top (ready count, what is missing, Send), every section below opens on a tap, a section with something to do opens by itself, the choice is remembered on the browser — the owner: *"do not keep it so long to scroll"*.

**Files:** `/root/finance/packs.py` c3eb9db0 → 6a1cf6ce (25 anchored edits from the live S433 bytes) · `/root/finance/packs.html` 2e06943b → 4c46cd0e. **Data:** `packs.retired_slots` cleared; `packs.electricity_expected`, `packs.digest_drop_words` added (INSERT OR IGNORE). No Sanjeevni file.

**Proof:** on a copy of the 28-Sep database — the clinic row back and empty; the digest 25 payments kept, 20 mails set aside (18 not payments, 1 repeat, 1 appointment), total Rs 1,89,412.42; electricity 2 of 2 (Rs 10,542 ICICI savings …9197 + Rs 10,821 Amazon Pay card, both 17-Aug); the income summary adds up; readable names; the page renders folded, no script error, 828 px closed. The bundle rule tested on crafted bills (a 2016 misread confirmed as August lands in August; a late August bill leaves September's pack once August's was sent). The installer walks a copy of the live database first (`walk_s434.py`), including the NEFT letter as a PDF and the corrections' amounts.

**Install (one line, with S435):**
`cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S434_PACKS_FIXES/install_S434_PACKS_FIXES.sh && bash /root/deploy/repo/deploy_kits/S435_SCAN_BILL_MONTH/install_S435_SCAN_BILL_MONTH.sh`
