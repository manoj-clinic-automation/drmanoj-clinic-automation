# Claude Code brief — S405_BANK_SMS_DOOR (the phone's bank-SMS door: never silent, ICICI tolerant, Yes Bank read, NEFT provisional)

Written 26-Sep-2026 by the Sanjeevni chat (S283). Read `CLAUDE.md` first — every rule binds. **Kit S405 · decision D621 · fault F-634**
(claimed on the System Board). The owner has approved this WHAT. Build → test on a copy → install → verify → publish → report, in one run.
**This is the FIRST of five briefs in one paste (S405 → S406 → S407 → S409 → S408); finish, verify and publish each before the next.**
S404 and S403 moved `finance_app.py`, `portal.py`, `tile_grants.json`, `asset_register.py`, `purchase_app.py`, `sanjeevni_approvals.py`,
`finance_approvals.html` and others (REPORT_S404 / REPORT_S403): **read every FROM pin live**; this brief's pins are from the 26-Sep bundle.

## 1 · The owner's words (25/26-Sep)
- "Are you sure MacroDroid SMS export from my mobile is working properly?" — it is: the phone posts the ICICIPOS SMS every morning ~07:00
  (nine posts 17–25 Sep, HTTP 200 each, from the MacroDroid log he uploaded), yet the Bank SMS page reads "Last SMS received: none yet".
- He has since **cloned** the macro on his phone: *Bank SMS 2 (Yes Bank) to Clinic Server* — same HTTP action, triggers on SMS containing
  `YES BANK` / `YESBNK`. Both macros post to the same door.
- The bulk supplier NEFT from Yes Bank is one debit; its SMS amount equals the **NEFT portion** of the month's pay sheet (sheet minus cheques).

## 2 · What exists (all `/root/finance/`)
- `bank_sms.py` (3a8f0a88): `POST /finance/api/bank-sms` (key in header `X-Bank-Sms-Key` or `key`; rate limit); reads `text`/`sender`
  from form, query or JSON; `parse()` = one strict `SMS_RE` for "ICICI Bank Account XXnnnn credited: Rs … on dd-Mon-yy. Info ICICIPOS SET
  10XXnnnnnn. Available Balance is Rs …" and `MID_RE` for the merchant tail → `unit_for_mid()` via `business_unit.merchant_id`; a parse
  miss answers `{ok:true, stored:false, ignored:true}` **and keeps nothing** (the doc-string says so by design — that is F-634).
  Table `bank_sms_settlement` (unit, credit_date, business_date = credit_date − 1, amount_p, balance_p, acct_tail, ref, sms_text,
  phone_sender, received_at, seen). Page `/finance/bank-sms` (owner) with the "Last SMS received" line.
- The pay sheet: `purchase_app.py` (7896eae4 after S403; read live) — `/finance/purchase/page/pay/<month>`; route per vendor NEFT / CHEQUE
  (`route == "NEFT"` only when the account is confirmed); `neft_p` = the sum of the NEFT lines (~line 2259); cheque register
  `purchase_cheque`; the month is FINALISED (`purchase_pay_check` ok rows / the lock the page shows). August 2026 is finalised.
- Yes Bank statement reader `finance_yesbank.py` (825016c0) → `bank_statement_line` / `bank_statement_period` (account_ref).

## 3 · The build (D621)
1. **Nothing is ever silent.** New table `bank_sms_ignored` (received_at, phone_sender, bank_guess, reason, masked_text). Every post the door
   does not store lands here with a **masked** copy of the text: every digit run of 4+ replaced by `#…#` except a trailing 4 kept where it
   is clearly an account tail; amounts kept as `Rs ####`; never the raw text. `/finance/bank-sms` gains a collapsed card **"Ignored (N,
   last 30 days)"** with reason + masked text, so the next silence is visible the same morning. Keep the 200/ignored answer to the phone.
2. **ICICI tolerant.** `parse()` becomes a small ladder: the strict regex first; then a tolerant read (case-insensitive, `Rs`/`INR`/`Rs.`,
   `credited`/`credited with`, date in `dd-Mon-yy`, `dd/mm/yy` or `dd-mm-yyyy`, "Info" text optional, balance optional, whitespace/newlines
   free). Same row shape; `parse_grade` column (strict/tolerant) added to `bank_sms_settlement`. **The nine ignored posts are gone (never
   kept); the next morning's post decides — the report must say what the door would do with the sample ICICIPOS text the strict regex was written against (in bank_sms.py itself).**
3. **Yes Bank read.** Two new shapes, stored in a new table `bank_sms_yes` (kind ∈ `neft_debit` | `cash_credit` | `other_debit` |
   `other_credit`, sms_date, amount_p, acct_tail, ref/UTR, balance_p, masked_text, received_at, seen): the NEFT/IMPS/UPI **debit** (amount,
   date, UTR/ref if present) and the **cash deposit credit**. Read the real Yes Bank SMS wording from the statement narrations you can
   see in `bank_statement_line` and from Yes Bank's public formats; be tolerant the same way. A Yes Bank text that matches nothing goes to
   the ignored table with `bank_guess='YESBANK'` — never a 4xx to the phone.
4. **The NEFT provisional (the zero-tap part).** When a `neft_debit` arrives whose amount equals `neft_p` of a **finalised** pay month with
   no NEFT confirmation yet (tolerance: exact, or within the bank's charges as a setting `neft.sms_tolerance_p`, default 0): write ONE row in
   a new table `purchase_neft_event` (month, kind='provisional', source='sms', amount_p, sms_date, utr, created_at, confirmed_by NULL,
   confirmed_at NULL) — the same table S407 will write from the owner's tap (S407 reads it; define it here, document its columns in the
   README). `Needs you` on `/finance/approvals` gains the line `NEFT of ₹X seen on <date> — matched to <Month>. OK?` with one tap **OK**
   (sets confirmed_by/at) and **Not this** (kind='rejected'). Nothing else changes yet: the amber "sent, awaiting statement" lines on the
   pay page are S407's; here only the event and the Needs-you line.
5. **Owner page text** on `/finance/bank-sms`: "Last SMS received", now also "Last Yes Bank SMS", and the ignored card.

## 4 · FROM pins (read live first; mismatch = stop that file and report)
| file | FROM |
|---|---|
| /root/finance/bank_sms.py | 3a8f0a8863942cde3fce2d0294a86769 |
| /root/finance/sanjeevni_approvals.py | 675aab4a46ab8792f05b17cab15d17ee (S403 TO; the Needs-you line + two POST routes only) |
| /root/finance/finance_ui/finance_approvals.html | c319bb56d30ac960d49d4a67083a55b2 (S403 TO; clinic — declared; the one Needs-you line + two buttons) |
`purchase_app.py` is READ only (to compute `neft_p` for a month — import or copy its route logic into a small helper; do not patch it here).
No `finance_app.py`, no portal, no grants. Restart `clinic-finance` only. The door's key and the phone's address are never printed.

## 5 · The walk (scratch copy; own rows; never a real post to the live door)
The strict ICICI text stores as before (negative control: the old file on the same text) · three wording variants store via the tolerant
rung with `parse_grade='tolerant'` · a random text → ignored table, masked (assert no 5+ digit run survives, amount masked), 200 answered ·
a wrong key still 401, nothing written · a Yes Bank NEFT debit text → `bank_sms_yes` kind neft_debit with amount/date/UTR; a cash deposit →
cash_credit; an unknown Yes Bank text → ignored with bank_guess YESBANK · the provisional: a crafted finalised month whose `neft_p` equals a
crafted debit → exactly one `purchase_neft_event` row; a repeat SMS (same amount/date/UTR) → no second row; an amount off by more than the
tolerance → no row; an unfinalised month → no row · the Needs-you line renders for the owner and not for bhati/darpan (302/403 pattern) ·
OK sets confirmed_by; Not this sets rejected and the line disappears · S400/S402/S403/S404 walks re-run green.

## 6 · Done means
Kit `deploy_kits\S405_BANK_SMS_DOOR\` · installed, md5s read back · healthz 200 · published · `claude_code_briefs\REPORT_S405.md`
(owner lines first: what he will see on the Bank SMS page tomorrow morning and what the Needs-you line says; ending with
`https://followup.dr-manoj.in/finance/bank-sms` and `https://followup.dr-manoj.in/finance/approvals`). Then go on to S406.
