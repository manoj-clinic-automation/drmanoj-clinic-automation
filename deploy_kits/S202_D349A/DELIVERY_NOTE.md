# S202_D349A — D349 on the finance side: one rule, and the table

**Session 202 · `finance_app.py` `3f72e9ad…` → `7a1e9bad…` · `finance_approvals.html` `402fa7b2…` → `89e02711…`**

## What the owner asked for, in his words

> *"variance was dealt with for portal health page in last session — it should be the rule at one
> place and all data shd follow that"*
>
> *"a clear intuitive table format, with reconcilation there only as inbuilt flow, no page hopping"*

## The fault

S201 retired *variance* and *low confidence* on `/finance/health` for the owner's own words — **sale
bills without a clinic ID** (D348). The exceptions card on `/finance/approvals` kept saying
"variance", because **nobody realised the two surfaces were showing the same underlying rows.** One
rename, two screens, one of them missed.

**And the word was the smaller half.** That card mixed two populations:

| | |
|---|---|
| **5 days** | the only difference is bills not yet matched to a patient. Under **D313** the Marg import cannot touch money at all, so **nothing is wrong** |
| **4 days** | genuinely unexplained — including **12-Jun at −8,487**, negative, meaning the lines *exceed* the day's total, **open since S186** |

**Five harmless rows were hiding four real ones**, all under one alarming label.

## The rule

`difference_meaning()` — one definition, and **classified from DATA, never from the description
text.** Parsing the detail string would have been a *third* copy of the rule, drifting the moment
somebody reworded it, which is the exact fault this function exists to end.

```
diff < 0                                  -> look   (lines exceed the day; cannot be unmatched bills)
open review rows exist AND value == diff  -> parked (D348: bills with no clinic ID)
otherwise                                 -> look
```

**Validated against the live data before a line was written:** it classifies the nine open rows as
exactly 5 parked / 4 look, matching the session's independent analysis.

## The table

The card is now two tables, and **each row closes where it is shown** — through the *existing*
`/finance/api/exception/<id>/resolve`, so no second write path was invented and it still refuses
without a reason.

- **⚠ Needs you** — the four, with the negative row first.
- **Bank vs what was entered** — the eight UPI days, each saying **which way** it went, because the
  direction decides who is out of pocket: *"the drawer was expected to hold Rs 30 that was never in
  it"*. Net across all eight: **Rs 241 in the maker's favour** (4 short, 4 over). The owner worked
  that out himself; the page never said it.
- **ⓘ folded away** — the five, in a `<details>`, present but not shouting: *"the money is counted in
  FULL — only the patient name is missing. Nothing is wrong here."*

**No money path is added.** Closing an exception records a judgement with a reason; it books nothing.
Any cash correction stays a separate deliberate entry.

## Proven offline — on a harness rebuilt from live bytes only

**F-87 forbids shipping into a suite that cannot be run.** At S192 that stopped a build outright. Here
it was satisfiable, by the S189 method: **every live module recovered by md5** (`finance_ingest`
`6cb83302…`, `marg_report` `6411a57d…`, `finance_yesbank`, `finance_returns`, `finance_identity`,
`finance_upi`, `staff_ledger` `9e764f80…`, and five UI pages) — **by hash, never by filename (D188)**.

- **SMOKE 693 → 701, +8 exactly.** The projection was written down before measuring.
- **FAIL SET BYTE-IDENTICAL: 48 → 48, the same rows.** The offline gap is `finance_entry.html`, whose
  live bytes exist only on the box (F-169); the live server runs all-green, so expect **701/701**.
- Design Language v1 markers on the page counted before and after — none lost (F-130).

## Install

```
cd /root/deploy/repo && git pull && cd deploy_kits/S202_D349A && bash install_d349a.sh
```

The installer gates on **both** files' current md5, backs up both, and restores both and restarts the
service if the live suite does not report 701/701.

## Reverse

```
cp -f /root/finance/finance_app.py.bak_S202_D349A_<stamp> /root/finance/finance_app.py
cp -f /root/finance/finance_ui/finance_approvals.html.bak_S202_D349A_<stamp> /root/finance/finance_ui/finance_approvals.html
systemctl restart clinic-finance.service
```

## What this does NOT do

- It does not touch `finance_ingest.py`, so the exceptions themselves are still *created* the same way.
- It does not book the Rs 241, or any adjustment. It shows the position and lets a reasoned judgement
  close a row.
- The four unexplained days are now **visible**, not diagnosed. 12-Jun's −8,487 has been open since
  S186 and still needs a person.
