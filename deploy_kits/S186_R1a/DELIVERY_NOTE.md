# Kit S186_R1a — the data layer for all three upgrades

**Session 186 · additive only · the running app is bit-for-bit unchanged by this**

Nothing the app imports changes here. New tables, one view, one module that nothing calls yet.
The surfaces arrive in **S186_R2a**. Splitting it this way means the risky step is one step, not three.

## 1. Yes Bank cash-deposit reconciliation — the F-103 gap, and it is not theoretical

`finance_upi.py` reconciles what the app was told against what ICICI settled. **Nothing did that for
cash.** That absence is precisely how **F-112** happened: a ₹75,000 deposit that never occurred sat in
the live books until a statement was pulled by hand.

`finance_yesbank.py` closes it in **both** directions, and refuses to be silent about what it cannot see:

| Verdict | Meaning |
|---|---|
| `deposit_not_in_bank` | we booked a deposit the bank never received — **exactly F-112** |
| `bank_deposit_not_booked` | the bank received cash we never recorded — **exactly the S183 problem**, 16 deposits missing |
| `deposit_unevidenced` | booked on a date **no loaded statement covers** — not a failure, and **never a pass** |

That third verdict is the whole of F-112 in one rule. S183 wrote *"falls after the statement cutoff,
check when booking"* in prose, and prose does not stop a migration. This does.

### It found F-112 unaided

Given the real Yes Bank statement you supplied today and the **uncorrected** store:

```
matched                 : 5  (Rs 590,000.00)
deposit_not_in_bank     : 2026-08-13   Rs 75,000.00
```

One phantom caught, five real deposits matched, **zero false positives**. Run again after `S186_C1a`
and it reports `matched 5, nothing missing, 0 open exceptions`.

Account numbers are stored **last-4 only** — the full number never enters the database or a log.

## 2 & 3. The custody layer (D323(d))

`counter_person`, seeded with what you established today:

| | Hindi | Role | Cash goes to |
|---|---|---|---|
| Darpan | दर्पण | drawer | bank — **makes every deposit** |
| Vinay Saxena | विनय सक्सेना | counter | Dr Bhawna — **bypasses the drawer** |
| Dr Bhawna | डॉ भावना | custodian | drawer — **never banks** |

`cash_custody_event` records who handed what to whom, and carries the field whose absence hid a float
for five months: **`month_end_kind` — 'taken' or 'carried'.** `v_cash_custody_balance` derives who
holds what rather than storing a second source of truth.

**Why a new table and not a wider `cash_movement`:** its `party` is a CHECK constraint, and widening a
CHECK in SQLite means rebuilding the table. Rebuilding a live financial table to add an enum value is a
poor trade. This sits alongside it and references it.

## Hindi labels — your approval needed before R2a builds the UI

| English | Hindi |
|---|---|
| Cash handed to | नकद किसे दिया |
| Counter person | काउंटर पर कौन था |
| Kept with Dr Bhawna | डॉ भावना के पास रखा |
| Returned to drawer | गल्ले में वापस |
| Deposited in bank | बैंक में जमा |
| Month-end balance — taken | महीने का बचा हुआ — ले लिया |
| Month-end balance — carried forward | महीने का बचा हुआ — अगले महीने में |
| Cash counted today | आज गिना हुआ नकद |
| Not yet deposited | अभी जमा नहीं हुआ |

Change any of them and I will use your wording — they are strings, and they cost nothing to alter now.

## Safety

- **Additive only.** No existing table, view, row or index is read, written, altered or dropped.
- The module **selftest runs before anything is placed** — 23/23, including an explicit test that the
  13 Aug ₹75,000 case is caught and that an unevidenced deposit is never reported as a pass.
- Database backed up anyway; a red verify restores it.
- **Nothing imports `finance_yesbank.py` yet**, so this cannot change what anyone sees today.

## Install

```
bash /root/deploy/vps_deploy.sh S186_R1a
```
