# REPORT_S407 — S407_NEFT_MESSAGES (NEFT done in one tap; suppliers told by WhatsApp from the reception phone, automatically)

Installed on srv1746119 on **26-Sep-2026**, installer stamp 09:03:19 IST, done 09:08:23 IST, verified 09:08:58 IST (times read from
the log and the probe). Every pin re-read live first (08:46 IST, after S406). Published with PUBLISH_ALL.bat.

## For Dr Manoj (plain English)
- **Your one tap.** On the Vendor payments page of a finalised month there is now a card **"NEFT — done, told, confirmed"** with one
  button, **NEFT done (bank SMS received)** (the date is filled with today; the UTR is optional). The moment you tap it, every NEFT
  supplier on the sheet turns amber *"Sent <date> — awaiting bank statement"*, and one WhatsApp message per supplier is prepared on the
  server with the full account number and IFSC, word for word: *Sanjeevni Medicos, Bareilly: ₹X for August 2026 purchases transferred
  by NEFT on 24-Sep-2026 to your account …, IFSC …. Thank you.* When the Yes Bank statement arrives and carries the same debit, the
  lines turn green *"Confirmed by bank <date>"*; a different amount turns red with the difference and appears in Needs you. You can
  undo within 24 hours (not once the bank has confirmed). If the bank SMS already recorded the NEFT (S405), your tap confirms that
  entry instead of making a second one.
- **What Shavez must do once, on the reception phone:** open **https://followup.dr-manoj.in/finance/purchase/page/phone-setup** from
  his login. It prints the MacroDroid steps in Hindi and shows the phone's key **once**. After that the phone sends the prepared
  messages by itself every five minutes while unlocked, and reports back. If a message is still unsent after 30 minutes, a **Bhejo**
  button appears on Vendor payments (for Shavez or you) that opens WhatsApp with the message ready, and Needs you says so.
  A cheque supplier gets its message the moment Shavez marks the cheque handed over.
- **What Amir sees:** a card on every step of his board — *NEFT <Month>: bheja <date> — bank se confirm baaki / ho gaya* — with each
  supplier ticked *bata diya* once told.
- The supplier numbers, accounts and IFSCs never appear on any page, in any log or in this report; they travel only inside the message
  the phone sends. Everything was proved on a copy with crafted suppliers; nothing was sent to anyone, and August's sheet is untouched
  until you tap.
- **https://followup.dr-manoj.in/finance/purchase/page/pay** · **https://followup.dr-manoj.in/finance/purchase/page/phone-setup**

## For the chat
### Live files FROM → TO (md5 read back after placing; re-read 09:08 IST identical)
| file | FROM | TO |
|---|---|---|
| /root/finance/purchase_app.py (S403's TO) | 7896eae4dff4427a2ebdb4f5023fd686 | fdec7ec01d2ceb449aaa0a62956a7a0f |
| /root/finance/amir_day.py | 00c443cbce0b07ba763bbe655a3e3c58 | 59a51d471cb30702dfd0cb8b6b6f3a44 |
| /root/finance/sanjeevni_approvals.py (S406's TO; v1.7 → v1.8) | 74fe5437afd646851d0c28200592177d | f6fc90d5d31badd3c5eec3691a78c4fb |
| /root/finance/finance_app.py (S403's TO; the two public paths only, anchored, declared) | 8055b0deddcb65234f1b9d818d56fda9 | d19c2046b190a4ec00745dc4121152e8 |

New: `/root/finance/supplier_msg.py` 02b4a9edc4ff6bc42ed896e7f260be72. `finance_approvals.html` untouched (the two Needs-you lines ride
the existing renderer). `finance_yesbank.py` untouched (the confirmation runs on every page read; the read after a statement load is
the check). Mounted from `purchase_app.init`, fail-soft.

### What the kit does (decisions for the record)
- `purchase_neft_event`: the tap writes kind provisional / source owner (amount = the sheet's NEFT portion, `_pay_rows` in process),
  confirmed_by = the owner; a pending S405 SMS row for the month is confirmed instead. Undo = kind `rejected`, note "undone by …",
  queued messages cancelled; refused after 24 h or once `bank_line_id` is set. Repeat within 10 min = `already`.
- The bank check: `bank_statement_line` NEFT debits within −3..+15 days of the date, equal within `neft.stmt_tolerance_p` (seeded 0),
  on the letter's debit-account tail when the statement carries it; a covering statement with a different debit = mismatch (red, a
  Needs-you line); no covering statement = awaiting (amber).
- `supplier_msg` (month, vendor, kind neft|cheque, ref, to_number, body, status queued|sent|failed|skipped, attempts, last_error…):
  the NEFT body from `_advice_accounts_s265` (the advice file's own source) and the phone book's first number (`_phone_for`); a vendor
  without a number → skipped "number nahi" with a link to the phone book on the staff page. Cheque rows on `handed_at`, read on every
  page read (the cheque-mark route is not patched).
- The phone: `GET /finance/api/supplier-msg/next` / `POST …/done`, header `X-Phone-Token` (setting `supplier_msg.phone_token`, 48 hex,
  made once by the seed; shown once on the setup page — the owner may open it again); failed → retried after 30 min, five tries.
- Senders (the backup wa.me link): setting `supplier_msg.senders` = `manoj,shavez` (the doctor always). Darpan is NOT a sender here —
  the brief's number-leak gate names him with bhati and amir.
- **The `.macro` file is not offered.** MacroDroid's export format could not be produced with confidence; the printed steps on the setup
  page are the record, as the brief allows.
- **Numbers:** every page lists vendor, status and time only. One thing the gate had to allow: the pay page has carried the S265 bank
  advice annexure — every NEFT vendor's account and IFSC — since April, by the owner's own design; the walk's page gate is therefore on
  phone numbers, and on everything for every API answer, audit row, Amir's page and the setup page.

### Backups · services · health · data
`/root/finance/finance.db.bak_S407_20260926_090319` · `purchase_app.py.bak_S407_7896eae4` · `amir_day.py.bak_S407_00c443cb` ·
`sanjeevni_approvals.py.bak_S407_74fe5437` · `finance_app.py.bak_S407_8055b0de`. Restarted `clinic-finance` only (active; portal, assetapp
untouched). healthz 200; the pay page, the setup page and `/finance/amir` 302 to a plain curl; the phone's door 401 without a token.
Journal clean. Seed: `supplier_msg.senders` manoj,shavez · `neft.stmt_tolerance_p` 0 · `supplier_msg.phone_token` set (48 chars, never
printed). At 09:08 IST the tables did not exist yet (first read makes them); no W407 / 2099 rows on the live database — the walk's writes
stayed on the scratch copy. Nothing was recorded for August 2026; no message was queued or sent.

### The walk (walk_s407.py — the real finance app over a scratch copy; crafted months 2099-05/07/08/09, numbers built at run time)
`WALK_S407 GREEN -- 27/27` (full output in this session's log): the mount and the public list · the state before · an open month 409,
darpan 403, bad month / future date 400 · the tap → ONE event, `already` on the repeat · the queue: A queued to the phone book's number
with the exact body, B skipped "number nahi" · the owner's, Shavez's (Hindi) and darpan's pages carry no phone number; bhati refused ·
the token door: 401 without / wrong; next → the oldest row (id, number, exact text); done fail → failed, attempts 1, empty until 30 min;
then offered again; done ok → sent by reception-phone · the cheque row only once handed, the exact cheque body · Pending after 30 min on
the state, the page (Bhejo) and Needs you ("1 supplier message unsent (30 min or more)"); Bhejo: bhati 302, darpan 403 with no number,
shavez gets the exact wa.me link, the row sent by shavez, again = already, the line gone · a statement debit equal to the portion →
confirmed, "Confirmed by bank 25-Sep-2026", undo 409 · a differing debit → mismatch −₹2,000, red, the Needs-you line · undo (darpan 403;
the owner's rejects the event and cancels the queue); a fresh tap; 25 h later too late · S405's pending SMS event confirmed by the tap,
not duplicated · Amir's card (ho gaya / bata diya / baaki), no number · the setup page (once for Shavez, again for the owner, bhati
refused) · the audit rows carry no number · the Needs-you gate. **Negative controls** (the old files, the same crafted months): no card,
404 routes, no Amir card, no setup page, no table, no line. **Re-runs:** `WALK_S406 27/27` · `WALK_S405 29/29` · `WALK_S404 65/65` ·
`WALK_S403 52/52` · `WALK_S400 63/63` · `WALK_S402 16/16`. One earlier installer run went red on the walk's own gates (the annexure's
accounts; the setup page opened once by the shared probe) and on two real slips in the module (the queued count, the event's bank line
not re-read) — all four corrected; nothing was placed by that run.

### Outside the brief, noticed (not changed)
- The `assetapp` service unit carries the OCR key on an `Environment=` line; a `systemctl cat` prints it. My S409 look printed it into
  this session's terminal (not into any file, kit or report). Worth moving to an EnvironmentFile with 0600, as the finance key file is.
- 19 of the 39 phone-book vendors carry a WhatsApp number; the other NEFT suppliers will read "number nahi" until Shavez adds them.

### Kit
`deploy_kits\S407_NEFT_MESSAGES\` — supplier_msg.py, make_s407.py, seed_s407.py, walk_s407.py, install_S407_NEFT_MESSAGES.sh, README.md,
KIT_ID.txt, SUMS.md5. Ran from `/tmp/s407kit/S407_NEFT_MESSAGES` (md5sum -c OK; sibling kits linked from the clone); the repository copy
is byte-identical (verified after `git pull`). No `__pycache__`. NO_PHONE_NUMBERS gate: clean. Build lock held from 09:01 IST to the
publish, then removed.

### Undo
Put back the four `.bak_S407_<from8>` files, remove `supplier_msg.py`, `systemctl restart clinic-finance`, healthz 200, md5s read back.
The tables, settings and the token are data and harmless; `finance.db.bak_S407_20260926_090319` only if the owner asks.
