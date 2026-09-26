# S405_BANK_SMS_DOOR — the phone's bank-SMS door: never silent, ICICI tolerant, Yes Bank read, NEFT provisional

**Sanjeevni project · session 283 · 26-Sep-2026 · decision D621 · fault F-634. First of the five-brief paste (S405 → S406 → S407 → S409 → S408).**

## What the owner asked for
"Are you sure MacroDroid SMS export from my mobile is working properly?" — it is: the phone posted the ICICIPOS SMS nine mornings
(17–25 Sep, HTTP 200 each), yet the Bank SMS page read "Last SMS received: none yet". He has cloned the macro for Yes Bank
(*Bank SMS 2 (Yes Bank) to Clinic Server*, same HTTP action). The bulk supplier NEFT from Yes Bank is one debit whose SMS amount
equals the NEFT portion of the month's pay sheet.

## The finding
`bank_sms.py` (S290) kept NOTHING of a post its strict regex did not read — by design, "not even a count by sender". So nine
posts vanished without a trace and nobody could say why. The strict regex was written against the sample in its own docstring
(`ICICI Bank Account XX000 credited:Rs. 1,234.00 on 17-Sep-26. Info EZY*ICICIPOS_SET_10XX123456_. Available Balance is Rs. …`);
the walk proves that sample still parses STRICT and is then ignored as *unknown merchant* (its merchant id is an illustration) —
from today that ignore is a visible row with that reason, not silence. What the real phone text looked like nobody can say
(it was never kept); tomorrow morning's post will land either in the table (grade strict or tolerant) or in the Ignored card
with its masked text and a reason.

## What was built (three live files, patched from their live bytes by `make_s405.py`)
**`bank_sms.py`** (S290 → S405, APP_VERSION `S405-BANK-SMS-2.0`)
1. **Nothing is silent.** New table `bank_sms_ignored` (received_at, phone_sender, bank_guess ICICI | YESBANK | UNKNOWN, reason,
   masked_text). Every post the door does not store lands there with a MASKED copy: every digit run of 4+ → `#`s, an account tail
   written the bank's way (`XX1234`) kept, amounts `Rs ####`; never the raw text. The owner's page gains the collapsed card
   **Ignored (N, last 30 days)** with reason and masked text. The phone still hears `200 {ok, stored:false, ignored:true}`.
2. **ICICI tolerant.** `parse()` is a ladder: the strict S290 regex, then `TOL_RE` (case-free; `Rs` / `Rs.` / `INR`; `credited` or
   `credited with`; `dd-Mon-yy`, `dd/mm/yy`, `dd-mm-yyyy` and more; the Info text and the balance optional; whitespace/newlines
   free). `bank_sms_settlement` gains `parse_grade` (strict | tolerant), added on first request.
3. **Yes Bank read.** New table `bank_sms_yes` (kind neft_debit | cash_credit | other_debit | other_credit, sms_date, amount_p,
   acct_tail, ref/UTR, balance_p, masked_text, phone_sender, received_at, seen; UNIQUE kind+date+amount+ref). `parse_yes()` is
   tolerant the same way: the first amount, the first debit/credit word, the first date; NEFT / RTGS / IMPS debit = neft_debit,
   a cash-deposit credit = cash_credit (the statement's own narration is `CASH DEP-SELF-…`). A Yes Bank text that matches nothing →
   the ignored table with `bank_guess='YESBANK'`; never a 4xx to the phone.
4. **The NEFT provisional (zero taps).** New table **`purchase_neft_event`** — the table S407 also writes:
   | column | meaning |
   |---|---|
   | id | |
   | month | the pay month `YYYY-MM` |
   | kind | `provisional` · `rejected` |
   | source | `sms` (this kit) · `owner` (S407's tap) |
   | amount_p | the debit, paise |
   | sms_date | the date in the SMS (S407: the date the owner types) |
   | utr | the UTR / reference when the text carries one |
   | yes_id | the `bank_sms_yes` row that made it (sms only) |
   | bank_line_id | S407: the `bank_statement_line` that confirms it (NULL here) |
   | created_at · created_by | `sms` here; the login in S407 |
   | confirmed_by · confirmed_at | the owner's **OK** (NULL = awaiting him) |
   | note | free text; "Not this" writes who/when here and sets kind `rejected` |
   When a fresh `neft_debit` arrives, every FINALISED pay month (`purchase_month.status='final'`) with no live event (kind ≠ rejected)
   is read through **purchase_app's own sheet** (`_pay_rows`, in process, never copied): the NEFT portion = the sum of the NEFT lines'
   payable. Equal within `neft.sms_tolerance_p` (setting, default 0 — seeded) → ONE row, `provisional` / `sms`. A repeated SMS (same
   kind, date, amount, ref) bumps `seen` and never re-triggers. A rejected event does not block a genuine later SMS for that month.
5. **The owner's page** `/finance/bank-sms`: "Last SMS received" as before, now also "Last Yes Bank SMS"; a Yes Bank table (last 30
   days) with the events under it; the Ignored card; the MacroDroid card names macro 2 (trigger `YES BANK` / `YESBNK`, same door).

**`sanjeevni_approvals.py`** (v1.5 → v1.6): Needs you gains `NEFT of ₹X seen on <date> — matched to <Month>. OK?` (read from
`bank_sms.needs_you_lines`, fail-soft) and the two routes `POST /finance/sanjeevni/api/neft-event/ok` (sets confirmed_by/at) and
`POST …/neft-event/reject` (kind → rejected). Checker only, as every route here.
**`finance_ui/finance_approvals.html`** (clinic — declared): a Needs-you line that carries `neft_event` renders **OK** and **Not this**.

Not here (S407's): the amber "Sent, awaiting statement" lines on the pay page, the statement confirmation, the supplier messages.
`purchase_app.py` is READ only. No `finance_app.py`, portal or grants change (`/finance/api/bank-sms` is already on the public list).

## Pins (FROM read on the box 26-Sep-2026 07:50 IST → TO; built by `make_s405.py` from the live bytes)
| file | FROM | TO |
|---|---|---|
| /root/finance/bank_sms.py | 3a8f0a8863942cde3fce2d0294a86769 | a70d6d96e700380d08b8e379ea0720e5 |
| /root/finance/sanjeevni_approvals.py (S403's TO) | 675aab4a46ab8792f05b17cab15d17ee | 126f90fc9912092378e817f101a8f74e |
| /root/finance/finance_ui/finance_approvals.html (S403's TO; clinic — declared) | c319bb56d30ac960d49d4a67083a55b2 | 928a25ef503267ce8e518f126306c236 |

Restarts `clinic-finance` only. `finance.db` is backed up first; the seed adds one setting (`neft.sms_tolerance_p` = 0, INSERT OR
IGNORE). The three tables and the `parse_grade` column are made by `bank_sms.py` on its first request (F-303).

## Proof
`walk_s405.py` — the REAL finance_app over a SCRATCH copy of finance.db, the door opened with the walk's OWN key file (never the live
key), every SMS text crafted in the walk and never printed (the merchant id it needs is read from the scratch copy and not printed):
a wrong key 401 and nothing written · the strict text stores as before (grade strict) · three wording variants store via the
tolerant rung (one posted as JSON) · a random OTP text → ignored, MASKED (no 5+ digit run, `Rs ####`, the OTP gone), 200 · the
docstring's sample → strict, then *unknown merchant* in the ignored table · a Yes Bank NEFT debit → neft_debit with amount, date,
UTR, tail, balance; a cash deposit → cash_credit; a UPI debit → other_debit; an OTP → ignored YESBANK · three crafted pay months
(2099-08 final with a cheque vendor beside the NEFT one, 2099-07 final, 2099-09 open) read through purchase_app's own sheet · the
equal debit → exactly ONE event; the same SMS again → seen 2, no second row; off by ₹10 at tolerance 0 → no row; at tolerance
₹10 → a row; the open month → no row · the real August 2026 NEFT portion is read and held against the Yes Bank statement's NEFT
debits (said in the walk's line) · Needs you carries the two lines for the owner and not for bhati/darpan/amir · darpan cannot
tap; bad id 400; unknown 404 · OK sets confirmed_by (again = already); Not this sets rejected; both lines leave · a later genuine
SMS still matches the rejected month · the owner's page (the cards, the events, no 10-digit number; bhati/darpan refused) · the
approvals page carries the renderer. **Negative controls** on the box as it is: the old door stores the strict text but ignores
all three variants; keeps nothing of the random text or the Yes Bank NEFT (no tables); the old page and Needs you have none of it.
Then **S404's, S403's, S400's and S402's own walks re-run** on the patched files (their negative controls rebuilt from the
`.bak_S404` / `.bak_S403` / `.bak_S400` / `.bak_S402` files; S400's re-run with `NEEDS_YOU_WITHOUT_S403=1` exactly as S403's
installer ran it).

## Run
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S405_BANK_SMS_DOOR/install_S405_BANK_SMS_DOOR.sh
```
Undo: put back the three `.bak_S405_<from8>` files, `systemctl restart clinic-finance`, healthz 200. The three tables and the
setting are data and harmless; the database backup is used only if the owner says so.
