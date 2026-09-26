# S407_NEFT_MESSAGES — NEFT done in one tap; suppliers told by WhatsApp from the reception phone, automatically

**Sanjeevni project · session 283 · 26-Sep-2026 · decision D623. Third of the five-brief paste, after S406. Uses `purchase_neft_event` (S405).**
**Numbers rule, absolute:** supplier phone numbers, account numbers and IFSCs live only in the live database; they go into a message
body built on the server for the reception phone (the token door) or into a wa.me link answered ONLY to a sender's login — never
into a page, a log, the audit, the kit, the walk's output or the report.

## What the owner asked for (25/26-Sep)
"The bulk NEFT goes by cheque to Yes Bank 2–3 days after the papers; the SMS comes from Yes Bank. A provisional entry visible to Amir
and the staff; suppliers told by WhatsApp with the full account number and IFSC. All messages from the reception mobile. Per-supplier
taps are too taxing. I log the provisional once; then maximum automated."

## What was built
**NEW `/root/finance/supplier_msg.py`** (mounted from `purchase_app.init`, fail-soft; reads purchase_app's own sheet, phone book and
cheque register in process).
1. **NEFT done, one tap (owner).** On the pay page of a FINALISED month: **"NEFT done (bank SMS received)"** — date (default today), UTR
   optional → `POST /finance/purchase/api/neft-done` writes ONE `purchase_neft_event` (kind provisional, source owner, the sheet's NEFT
   portion) — or **confirms S405's pending SMS event** for that month (never two live events for one month). A repeat answers `already`.
   Every NEFT vendor on the sheet turns **amber "Sent <date> — awaiting bank statement"**; cheque vendors keep their cheque status.
   **Undo** within 24 h (`/api/neft-undo`, owner, audited): the event becomes `rejected` ("undone by …"), its unsent messages are
   cancelled; refused once the bank has confirmed.
2. **Confirmed by bank.** On every read of the pay page / Amir's board / Needs you: a `bank_statement_line` NEFT debit equal to the
   portion (setting `neft.stmt_tolerance_p`, default 0) within −3..+15 days of the date → `bank_line_id` set, **green "Confirmed by bank
   <date>"**. A statement that covers the date and holds a different NEFT debit → **red with the difference** on the page and in Needs
   you. (The statement loader `finance_yesbank.py` is not touched; the next page read after a load is the check.) The account is the
   letter's debit account tail when the statement carries it, else every line.
3. **The message queue (server).** On the provisional, one `supplier_msg` row per NEFT supplier: `to_number` = the phone book's first
   number (`_phone_for`, as S225's WhatsApp order uses it), `body` EXACTLY
   `Sanjeevni Medicos, Bareilly: ₹<amount> for <Month YYYY> purchases transferred by NEFT on <dd-Mon-yyyy> to your account <full account
   number>, IFSC <IFSC>. Thank you.` — amount from the sheet line, account and IFSC from `_advice_accounts_s265` (the advice file's own
   source). No number → `skipped` "number nahi" (a line on Shavez's page points at the phone book). **Cheque suppliers:** when
   `purchase_cheque.handed_at` is set, one row `… paid by cheque no <n> dated <date> for <Month YYYY> purchases. Thank you.`
   Columns: id, month, vendor_norm, vendor, kind neft|cheque, ref (event id / cheque id), channel, to_number, body, status
   queued|sent|failed|skipped, queued_at, sent_at, sent_by, attempts, last_error, last_try_at.
4. **The reception phone sends (MacroDroid).** `GET /finance/api/supplier-msg/next` → the oldest queued row `{id, to, text}` or `{}`;
   `POST /finance/api/supplier-msg/done` `{id, ok, error}`. Token in header `X-Phone-Token` (setting `supplier_msg.phone_token`, made at
   install, **shown ONCE** on `/finance/purchase/page/phone-setup` — Hindi, staff; the owner may open it again). A failure → `failed`,
   attempts+1, offered again after 30 minutes (five tries). The setup page prints the macro step by step (Regular Interval 5 min while
   unlocked → HTTP GET next → if id: open `wa.me/<to>?text=` → wait → UI Interaction tap Send → POST done; battery unrestricted;
   accessibility on) and says plainly that it drives a personal WhatsApp by automation. **The `.macro` export file is not offered** — its
   format could not be produced with confidence; the printed steps are the record.
5. **Backup, one tap.** A row queued (or failed) for 30+ minutes shows as `Pending — <vendor>` with **Bhejo** on the pay page for a sender
   (setting `supplier_msg.senders`, default `manoj,shavez`; the doctor always) → `POST /api/supplier-msg/send` answers the wa.me link to
   that login only and marks the row sent (who, when). Needs you gains `N supplier message(s) unsent`.
6. **Where it shows:** the pay page card **"NEFT — done, told, confirmed"** (owner, English) / **"NEFT — bank aur supplier"** (staff,
   Hindi) with the suppliers' statuses (told · waiting · not sent); the chip beside every NEFT vendor on the sheet; Amir's board card on
   every step **`NEFT <Month>: bheja <date> — bank se confirm baaki / ho gaya`** with the tick list `bata diya`; Needs you (unsent
   messages; a bank mismatch). Every save: a green card (S394), the page reloads on it.

Front gate: the two token doors join `PUBLIC_PATHS` in `finance_app.py` (anchored, declared) exactly as `/finance/api/bank-sms` does; the
module checks the token itself (`hmac.compare_digest`).

## Pins (FROM read on the box 26-Sep-2026 08:46 IST, after S406 → TO; built by `make_s407.py` from the live bytes)
| file | FROM | TO |
|---|---|---|
| /root/finance/purchase_app.py (S403's TO) | 7896eae4dff4427a2ebdb4f5023fd686 | fdec7ec01d2ceb449aaa0a62956a7a0f |
| /root/finance/amir_day.py | 00c443cbce0b07ba763bbe655a3e3c58 | 59a51d471cb30702dfd0cb8b6b6f3a44 |
| /root/finance/sanjeevni_approvals.py (S406's TO; v1.7 → v1.8) | 74fe5437afd646851d0c28200592177d | f6fc90d5d31badd3c5eec3691a78c4fb |
| /root/finance/finance_app.py (S403's TO; the two public paths only) | 8055b0deddcb65234f1b9d818d56fda9 | d19c2046b190a4ec00745dc4121152e8 |

Restarts `clinic-finance` only. `finance.db` is backed up first; the seed adds `supplier_msg.senders`, `neft.stmt_tolerance_p`
(INSERT OR IGNORE) and makes `supplier_msg.phone_token` once (random 48 hex; never printed). Tables on first use.
`finance_approvals.html` is not touched (the two lines ride the existing renderer).

## Proof
`walk_s407.py` — the REAL finance_app over a SCRATCH copy of finance.db, its own months 2099-05/07/08/09 with crafted vendors, numbers,
accounts and IFSCs built at run time and never printed: the mount and the public list · the state before · an open month 409, darpan 403,
bad month / future date 400 · the tap → ONE event, `already` on the repeat · the queue: A queued to the phone book's number with the exact
body, B skipped "number nahi" · the owner's, Shavez's (Hindi) and darpan's pages carry no number; bhati refused · the token door: 401
without/with a wrong token; next → the oldest row; done fail → failed/attempts/retry after 30 min; done ok → sent by reception-phone ·
the cheque row appears only once the cheque is marked handed, with the exact cheque body · Pending after 30 min on the state, the page
(Bhejo) and Needs you; Bhejo: bhati refused, darpan refused with no number in the answer, shavez gets the exact wa.me link, marked sent
by shavez, again = already · a statement debit equal to the portion → confirmed, green chip, undo refused; a differing debit → mismatch
−₹2,000, red, a Needs-you line · undo (darpan refused; the owner's undo rejects the event and cancels the queue); a fresh tap; 25 h later
too late · S405's pending SMS event is confirmed by the tap, not duplicated · Amir's card (ho gaya / bata diya / baaki), no number · the
setup page: the token once for Shavez, again for the owner, bhati refused · the audit rows carry no number · the Needs-you gate.
**Negative controls** on the box as it is with the same crafted months: no card, no route, no Amir card, no setup page, no table, no line.
Then **S406's, S405's, S404's, S403's, S400's and S402's own walks re-run** on the patched files (S400's with both env switches).

## Run
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S407_NEFT_MESSAGES/install_S407_NEFT_MESSAGES.sh
```
Undo: put back the four `.bak_S407_<from8>` files, remove `supplier_msg.py`, `systemctl restart clinic-finance`, healthz 200. The
tables, settings and the token are data and harmless; the database backup is used only if the owner says so.
