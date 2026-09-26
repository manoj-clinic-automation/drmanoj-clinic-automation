# Claude Code brief — S407_NEFT_MESSAGES (NEFT done in one tap; suppliers told by WhatsApp from the reception phone, automatically)

Written 26-Sep-2026 by the Sanjeevni chat (S283). Read `CLAUDE.md` first. **Kit S407 · decision D623.** The owner approved this WHAT
(25/26-Sep). Runs THIRD, after S406. Uses `purchase_neft_event` defined by S405 (read its README). **Numbers rule, absolute:** supplier
phone numbers, account numbers and IFSCs live only in the live database (`purchase_vendor_contact`, `purchase_pay_config`, the phone book);
they go into a message body built on the server for the reception phone and nowhere else — never in a log, a report, the kit, the walk's
output or a response to a login that is not a sender.

## 1 · The owner's words (25/26-Sep)
- "The bulk NEFT goes by cheque to Yes Bank 2–3 days after the papers; the SMS comes from Yes Bank. A provisional entry visible to Amir and
  the staff; suppliers told by WhatsApp with **the full account number and IFSC**." "All messages from the reception mobile. Per-supplier
  taps are too taxing. I log the provisional once; then maximum automated." He liked the MacroDroid sender on the reception phone, the
  one-tap backup, and the cheque suppliers' messages when the cheque is marked handed.

## 2 · What exists (`/root/finance/`)
- `purchase_app.py` (7896eae4 after S403 — read live): the pay sheet `/finance/purchase/page/pay/<month>` (vendor route NEFT/CHEQUE,
  `neft_p`, finalise/lock, verify rows `purchase_pay_check`), the covering letter `purchase_pay_letter` (date_text, cheque_no), the advice
  `/page/pay/<month>/advice.xlsx`, the pack `/page/pay/<month>/pack` (S380), the cheque register `purchase_cheque` (handed_at/by, void),
  the phone book `/page/book` + `/api/book` (two numbers per vendor; bank fields owner-verified; `purchase_vendor_contact`), the WhatsApp
  link pattern `https://wa.me/<no>?text=` marked SENT (S225). August 2026: 19 suppliers, finalised, letter dated 24-Sep with its cheque no.
- Amir's board `amir_day.py` (00c443cb; `/finance/amir`, `/finance/amir/day`), Shavez's **Vendor payments** tile → `/finance/purchase/page/pay`.
- `purchase_neft_event` (S405): month, kind (provisional/rejected), source (sms/owner), amount_p, sms_date, utr, confirmed_by/at.
- Yes Bank statement lines `bank_statement_line` (finance_yesbank.py 825016c0); the pay month's NEFT portion = the sum of the NEFT lines.

## 3 · The build (D623)
1. **NEFT done, one tap (owner).** On the pay page of a finalised month: **"NEFT done (bank SMS received)"** — date (default today), UTR
   optional. Writes `purchase_neft_event` kind=provisional source=owner (or confirms an S405 SMS row if one is pending for that month —
   never two events for one month). Every NEFT line on the sheet turns **amber "Sent <date> — awaiting bank statement"**; cheque lines keep
   their cheque status. Amir's board and the Vendor payments page show the same amber. Undo within 24 h (audited).
2. **Confirmed by bank.** When a Yes Bank statement covering that date is loaded (existing reader) and holds a debit equal to the NEFT
   portion (tolerance setting `neft.stmt_tolerance_p`, default 0): the lines turn **green "Confirmed by bank <date>"** and the event gains
   `bank_line_id`. A differing amount: red with the difference, on the pay page and in Needs you. Runs on statement load and on page read.
3. **The message queue (server).** On the provisional event, one row per NEFT supplier in a new table `supplier_msg` (month, vendor_norm,
   channel='whatsapp', to_number (from the phone book, first number), body, status queued/sent/failed/skipped, queued_at, sent_at, sent_by
   ('reception-phone' or the login), attempts, last_error). Body, exactly: `Sanjeevni Medicos, Bareilly: ₹<amount> for <Month YYYY>
   purchases transferred by NEFT on <dd-Mon-yyyy> to your account <full account number>, IFSC <IFSC>. Thank you.` — amount from the
   sheet line, account and IFSC from `purchase_pay_config`/the phone book as the advice file uses them. A vendor with no number → status
   `skipped` "number nahi" and a line on Shavez's page to add it. **Cheque suppliers:** when `purchase_cheque.handed_at` is set, one row:
   `… paid by cheque no <n> dated <date> for <Month YYYY> purchases. Thank you.`
4. **The reception phone sends (MacroDroid).** Two token-gated routes (token in `setting` `supplier_msg.phone_token`, generated at
   install, printed ONCE on Shavez's setup page, never in the kit/report): `GET /finance/api/supplier-msg/next` → the oldest queued row
   as JSON {id, to, text} or {} ; `POST /finance/api/supplier-msg/done` {id, ok, error}. Write **`/finance/purchase/page/phone-setup`**
   (Hindi, staff): the printed steps to build the macro on the reception phone — trigger every 5 minutes while unlocked; HTTP GET next;
   if `id` present: open `https://wa.me/<to>?text=<urlencoded text>`, wait, UI-interaction tap Send (accessibility), wait, POST done;
   the exact MacroDroid action names; battery optimisation off. If MacroDroid's `.macro` export format can be produced with confidence,
   also offer it as a download on that page; the printed steps remain the record. State plainly on the page: a personal WhatsApp driven
   by an automation; if WhatsApp's screen changes the macro may need a small edit; the backup below always works.
5. **Backup, one tap.** A queued row older than 30 minutes shows on the Vendor payments page (Shavez) and the owner's pay page as
   `Pending — <vendor>` with a **Bhejo** button that opens the same wa.me link on whatever phone is tapping, then marks sent (who, when).
   Needs you gains `N supplier message(s) unsent` when any is > 30 min old.
6. **Where it shows:** pay page (owner, English), Vendor payments (Shavez, Hindi), Amir's board card `NEFT <Month>: bheja <date> — bank se
   confirm baaki / ho gaya` + per-supplier tick list `bata diya`. Every save: the S394 green card; repeat within 10 min refused.

## 4 · FROM pins (read live first; mismatch = stop that file and report)
| file | FROM |
|---|---|
| /root/finance/purchase_app.py | 7896eae4dff4427a2ebdb4f5023fd686 (S403 TO — read live) |
| /root/finance/amir_day.py | 00c443cbce0b07ba763bbe655a3e3c58 |
| /root/finance/sanjeevni_approvals.py · finance_ui/finance_approvals.html | as S406 left them — read live (Needs-you lines only; clinic — declared) |
| /root/finance/finance_app.py | as S403 left it (8055b0de) — ONLY if the two token routes need a gate exception like `/finance/api/bank-sms`; anchored, declared |
New module preferred (e.g. `/root/finance/supplier_msg.py` + `phone_setup.html`) mounted from `purchase_app.init`. Restart `clinic-finance` only.

## 5 · The walk (scratch copy; own month `2099-08` with crafted vendors and numbers; never opens wa.me; never posts to a real phone)
NEFT done writes one event, a second tap within 10 min refused, undo within 24 h works · lines amber; cheque lines untouched · a crafted
statement debit equal to neft_p turns them green with bank_line_id; a differing one red with the difference · the queue: one row per NEFT
vendor, body exactly the format with the FULL account number and IFSC from the crafted config; a vendor without a number → skipped; a
cheque handed → its row · `next` with a bad token 401; with the token returns the oldest queued then, after `done ok`, the next; `done`
with error → failed, attempts+1, retried after 30 min · **the number-leak gate:** every response body to bhati/darpan/amir/stranger, every
log line, the report and the kit contain no phone/account/IFSC (assert with the NO_PHONE_NUMBERS gate over the walk output too) · the
backup Bhejo marks sent with who/when · Needs-you line at > 30 min · S400–S406 walks re-run green.

## 6 · Done means
Kit `deploy_kits\S407_NEFT_MESSAGES\` · installed, md5s read back · healthz 200 · published · `claude_code_briefs\REPORT_S407.md`
(owner lines first: his one tap, what Shavez must do once on the reception phone (the setup page address), what Amir sees; ending with
`https://followup.dr-manoj.in/finance/purchase/page/pay` and `https://followup.dr-manoj.in/finance/purchase/page/phone-setup`). Then S409.
