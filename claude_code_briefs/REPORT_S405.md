# REPORT_S405 — S405_BANK_SMS_DOOR (the phone's bank-SMS door: never silent, ICICI tolerant, Yes Bank read, NEFT provisional)

Installed on srv1746119 on **26-Sep-2026**, installer stamp 08:17:01 IST, done 08:21:45 IST, verified 08:22:13 IST (times read from
the log and the probe). Every pin re-read live first (07:50 IST). Published with PUBLISH_ALL.bat.

## For Dr Manoj (plain English)
- **Your phone's macro was working all along; the server was throwing the message away without a word.** The door only kept a
  message that matched one exact sentence and forgot everything else, by design. From now on nothing is forgotten: anything the
  door does not understand is listed on the Bank SMS page under **"Ignored (N, last 30 days)"** with the reason and a masked copy
  of the text (digits hidden). Tomorrow morning you will see either the settlement figure in the table, or that ignored line
  telling us exactly what the phone sent.
- **The ICICI reading is now tolerant** (capital letters, Rs or INR, "credited with", three date shapes, with or without the
  balance line). What the phone sent these nine mornings cannot be recovered — it was never kept — so tomorrow decides.
- **Your second macro (Yes Bank) posts to the same door** and is read: NEFT / IMPS / RTGS debits, cash deposits, other credits
  and debits, all in a **Yes Bank SMS** table on the same page with "Last Yes Bank SMS".
- **The NEFT provisional, zero taps:** when a Yes Bank NEFT debit arrives whose amount equals the NEFT portion of a finalised
  pay month, the server records it and your approvals page asks, in Needs you: **"NEFT of ₹X seen on <date> — matched to
  <Month>. OK?"** with two buttons, **OK** and **Not this**. Nothing else changes yet; the amber "sent, awaiting statement"
  lines are the next brief's (S407).
- Everything was proved on a copy of the live database with crafted messages; nothing was posted to the live door and your
  phone's key was never used or printed.
- **https://followup.dr-manoj.in/finance/bank-sms** · **https://followup.dr-manoj.in/finance/approvals**

## For the chat
### The finding, and what the door would do with the docstring's sample
`bank_sms.py` (S290) answered `200 {ok, stored:false, ignored:true}` and kept nothing whenever `SMS_RE` missed — "not even a count by
sender", by design. The nine posts (17–25 Sep) are gone; nothing can say what shape they had. The sample the strict regex was written
against (in the module's own docstring, `…XX000 credited:Rs. 1,234.00 on 17-Sep-26. Info EZY*ICICIPOS_SET_10XX123456_. Available
Balance…`) still parses **strict** on the new door and is then ignored as **"unknown merchant (id ending 3456)"** — its merchant id is
an illustration — and the ignored table now says exactly that (walk, section 1). So if the real text matched the sample, the fault was
the merchant id, not the sentence; if it did not, the tolerant rung or the masked copy shows it tomorrow.

### Live files FROM → TO (md5 read back after placing; re-read 08:22 IST identical)
| file | FROM | TO |
|---|---|---|
| /root/finance/bank_sms.py | 3a8f0a8863942cde3fce2d0294a86769 | a70d6d96e700380d08b8e379ea0720e5 |
| /root/finance/sanjeevni_approvals.py (S403's TO; v1.5 → v1.6) | 675aab4a46ab8792f05b17cab15d17ee | 126f90fc9912092378e817f101a8f74e |
| /root/finance/finance_ui/finance_approvals.html (S403's TO; clinic — declared) | c319bb56d30ac960d49d4a67083a55b2 | 928a25ef503267ce8e518f126306c236 |

Built on the box by `make_s405.py` from the live bytes (anchored edits, each anchor exactly once); TO pins matched the kit.
`purchase_app.py` read only (its `_pay_rows` is called in process for the NEFT portion). No finance_app / portal / grants change.

### Backups · services · health
`/root/finance/finance.db.bak_S405_20260926_081701` (backup API) · `bank_sms.py.bak_S405_3a8f0a88` · `sanjeevni_approvals.py.bak_S405_675aab4a` ·
`finance_ui/finance_approvals.html.bak_S405_c319bb56`. Restarted `clinic-finance` only (active; portal and assetapp untouched, active).
`/finance/healthz` 200; `/finance/bank-sms` and `/finance/approvals` 302 to a plain curl (login gates, expected); a keyless POST to
`/finance/api/bank-sms` 401 (the key gate, expected). Journal: nothing "NOT mounted", no traceback.

### Data
Seed: `setting` `neft.sms_tolerance_p` = 0 (INSERT OR IGNORE). The three tables (`bank_sms_ignored`, `bank_sms_yes`,
`purchase_neft_event`) and the `parse_grade` column are created on the door's or the page's first request (F-303) — at 08:22 IST they
did not exist yet, `bank_sms_settlement` 0 rows, no W405 / 2099 rows: the walk's writes stayed on the scratch copy.
**`purchase_neft_event` columns (S407 reads them):** id · month · kind (provisional | rejected) · source (sms | owner) · amount_p ·
sms_date · utr · yes_id · bank_line_id (S407) · created_at · created_by · confirmed_by · confirmed_at (the owner's OK) · note.

### The walk (walk_s405.py — the real finance app over a scratch copy; the walk's own door key; texts crafted, never printed)
`WALK_S405 GREEN -- 29/29`: a wrong key 401, nothing written · the strict text stores (grade strict) · three variants store tolerant
(one as JSON) · a random OTP text → ignored UNKNOWN, masked (`Your OTP is ###### for a payment of Rs ####…`) · the docstring's sample →
strict, then unknown merchant · Yes Bank NEFT debit → neft_debit (amount, date, UTR, tail, balance); its masked copy keeps `XX4405`,
hides the amount; cash deposit → cash_credit; UPI → other_debit; OTP → ignored YESBANK · crafted months 2099-08 (final, NEFT ₹4,05,000
beside a cheque vendor), 2099-07 (final, ₹3,03,000), 2099-09 (open) read through purchase_app's sheet · the equal debit → ONE event;
repeat → seen 2, no second; ₹10 off at tolerance 0 → none; tolerance ₹10 → a row; the open month → none · Needs you: the two lines
(`NEFT of ₹4,05,000 seen on 24-Sep-2026 — matched to August 2099. OK?`), bhati/darpan/amir 302/403 · darpan cannot tap; bad id 400;
unknown 404 · OK → confirmed_by manoj (again = already); Not this → rejected, both lines leave; a later genuine SMS still matches the
rejected month · the page (cards, events, no 10-digit number; bhati 302, darpan 403) · the approvals renderer.
**Negative controls (the old files):** the old door stores the strict text but ignores all three variants; keeps nothing of the
random or the Yes Bank text (no tables); the old page and Needs you carry none of it; APP_VERSION S290 vs S405.
**Re-runs on the patched files:** `WALK_S404 GREEN 65/65` · `WALK_S403 GREEN 52/52` · `WALK_S400 GREEN 63/63` · `WALK_S402 GREEN 16/16`
(controls rebuilt from the `.bak_S404` / `.bak_S403` / `.bak_S400` / `.bak_S402` files; S400's re-run with `NEEDS_YOU_WITHOUT_S403=1` as
S403's installer ran it). One installer run before this went red only because S404's re-run was handed the live v28 portal instead of
the v27 one S404 built — the installer now hands it the pre-S403 copy; nothing was placed by that run.

### Outside the brief, noticed (not changed)
- **The real August 2026 sheet's NEFT portion does not equal any NEFT debit on the loaded Yes Bank statement (nearest differs by
  ₹1,19,072)** — the walk reads it (section 3). So when the September NEFT SMS comes, the match will be exact only if the sheet and
  the transfer agree; for August the provisional would not have fired. Worth the chat's eye before S407 turns lines green.
- The Yes Bank SMS wording is unknown until the first real one lands; the parser is tolerant and the ignored card catches the rest.

### Kit
`deploy_kits\S405_BANK_SMS_DOOR\` — make_s405.py, seed_s405.py, walk_s405.py, install_S405_BANK_SMS_DOOR.sh, README.md, KIT_ID.txt,
SUMS.md5. Ran from `/tmp/s405kit/S405_BANK_SMS_DOOR` (md5sum -c OK before the run; sibling kits linked from the repository clone); the
repository copy is byte-identical (SUMS verified on the box after `git pull`). No `__pycache__`. NO_PHONE_NUMBERS gate: clean.
Build lock held from 08:11 IST to the publish, then removed.

### Undo
Put back the three `.bak_S405_<from8>` files, `systemctl restart clinic-finance`, healthz 200, md5s read back. The tables and the
setting are data and harmless; `finance.db.bak_S405_20260926_081701` only if the owner asks.
