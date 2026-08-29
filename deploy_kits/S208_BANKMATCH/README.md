# S208_BANKMATCH — the bank detail, kept and matched

**Staged, not installed.** Sprint 1 of the S208 plan.

## What it does

Every ICICI merchant statement already reaches this server daily (the GAS push,
09:30). Until now its transactions were **read and thrown away** — only the
daily total was kept, which is why the UPI difference could be seen but never
explained. This kit:

1. **keeps every transaction** (`upi_txn`: date, amount, RRN, mode, time) and
   **rebuilds the history** from the statement files already stored here;
2. **matches bank to bills** every morning — 09:45, retrying every 15 minutes
   until noon, requiring BOTH feeds, naming a missing one, closing the day
   honestly at 12:00 (`no_business` for a quiet Sunday, `FEEDS_INCOMPLETE`
   with a flag when something real is missing);
3. **reconciles like for like** — the bank column is everything that settled
   (UPI + card), so the entered side is now the day's whole non-cash. The old
   UPI-only comparison manufactured a permanent phantom difference the day a
   card was ever swiped;
4. **seeds the orthotics vocabulary** (only if empty) from Marg's own
   orthopaedic category — 31 keywords covering all 81 items — so the dead
   orthotics card has data to stand on.

## What each matched row means

| status | meaning | who acts |
|---|---|---|
| `agreed` | settled payment ↔ bill already entered non-cash | nobody |
| `cash` | settled payment ↔ bill **rung as cash** — the drawer is expected to hold money that was never in it | the feedback list; Sprint 2 puts it on the page |
| `bank_orphan` | settled, no bill — part payment, split, advance, other day | a question for Darpan (Sprint 2, two taps) |
| `bill_orphan` | entered non-cash, nothing settled | the reverse gap |

## Proven before staging

21/21 matcher checks **on the real 27-Aug shape** — 5 agreed, 3 rung-as-cash
(Sureshi Devi's ₹2,500 with its RRN), the ₹812/₹500 orphans, a credit note
ignored, idempotent re-run, the waiting/closing ladder, and a quiet day not
mistaken for a missing feed. The real 28-Aug MPR ingested: 10 transactions
kept with times; re-ingest does not duplicate.

## Install

```
bash /root/deploy/vps_deploy.sh S208_BANKMATCH
```

Gates: kit SUMS → live-file currency (md5 `3f5016f0…`) → backup → copy →
compile → 21/21 → finance_upi selftest → **the app's own smoke suite must not
lose a single check** → restart + import check → backfill → vocab seed →
first match → cron. Any red restores and restarts.

*S208_BANKMATCH · staged 29-Aug-2026 · the VPS was not touched.*
