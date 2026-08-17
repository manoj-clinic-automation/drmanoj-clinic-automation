# Kit S184_C1a — correct the Sanjeevni (medical) historical cash books

**Session 184 · corrects finance.db · reversible · no code, no service restart**

## What it does
The S179 import loaded the Google Sheet verbatim, including its bugs: 31 deposit
movements (₹16,59,114, the sheet's own Deposit column) and 36 carry-forward
"adjustments" (net −₹84,533, the sheet papering over its own drift). Together they
reproduce the impossible **−₹30,056** closing. This kit replaces that with the truth:

1. **31 sheet deposits → 16 bank-verified Yes Bank credits** (₹16,45,600, real dates).
2. **36 legacy adjustments removed** — backed up first into `s184_removed_*` tables.
3. **₹40,000 Darpan salary advances** added as drawer expenses — **no staff link, so
   nothing posts to the Staff Ledger** (owner's choice; salary system reviewed later).
4. **₹337 procedure-medicine** (the 20 Apr + 19 Jun cells mis-keyed into Deposit) as
   noncash bills.

**Result: 13 Aug closing −30,056 → +27,654.** The sale money (`day_line`) is never
touched. No money moves in reality — this makes the record match the bank.

## Safety
- **State gate**: refuses unless the box is at exactly −30,056 with the correct cash
  total and the correction has not run before. Wrong state → nothing touched.
- **Backup**: whole `finance.db` copied to `finance.db.bak_S184C1_*` before applying.
- **One transaction**; **idempotent**; **reversible** (rollback block in the .sql, plus
  the `s184_removed_*` backups).
- Rehearsed offline against a database seeded to reproduce the live −30,056 exactly:
  apply → +27,654, sale money unchanged, idempotent; rollback → byte-for-byte back to
  −30,056; a tampered kit goes honest-red and restores.

## After it runs — the parking to verify from Dr Bhawna's copy (option 2, later)
Interim days around the big bank lumps show negative cash. That is the honest footprint
of cash **parked with Dr Bhawna ahead of a bank trip** — real money, timing not recorded.
To model it later, check her copy for these periods and amounts:

| Period to check | Driven by deposit | Approx cash parked |
|---|---|---|
| 4–5 Jun | 4 Jun ₹1,50,000 | ~₹20,450 |
| 12–13 Jun | 12 Jun ₹1,10,000 | ~₹24,393 |
| 17–19 Jun | 17 Jun ₹85,000 | ~₹27,712 |
| 7–10 Jul | 7 Jul ₹1,80,000 | ~₹70,924 |
| 14–20 Jul | 14 Jul ₹1,05,000 | ~₹71,358 |
| 22–28 Jul | 22 Jul ₹85,000 | ~₹63,388 |
| 30 Jul–4 Aug | 30 Jul ₹85,000 | ~₹58,679 |

April and May need no check — the first week's float covers them.

## To run
On the PC: double-click `deploy/push_kit.bat`. Then on the VPS:
```
bash /root/deploy/vps_deploy.sh S184_C1a
```
