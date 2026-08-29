# S208_LEDGER3 — the ledgers, diagnosed; one predicate for pendCard

**Staged, not installed. Requires S208_DARPAN.**

## The finding

Reserve (Dr Bhawna), Dr Manoj's cash and the drawer all read through
`v_cash_custody_balance` — a view created by the **S186 migration**, not by
the schema file. Absent, all three ledgers freeze at once while the drawer
still falls (the transfer-out row is real) — exactly the 27-Aug complaint.

## The tools (owner-only, audited)

`GET /finance/darpan/api/ledger-check?date=…` returns the raw rows — the
movements, the custody events, whether the view exists — and **names the
fault** before anything is touched. `POST …/ledger-repair-view` creates the
view if absent (the migration's own SQL, additive). `POST …/transfer` records
a dated, noted custody event — perform or repair; it never moves money.

## The predicate

pendCard called an approved day "not filed" because it demanded an *applied*
ingest batch; a pushed report still in staging covers the day just as truly.
One additive clause. **Soft**: if the live query text drifted, it skips with
a warning and the ledger tools install anyway.

## Proven

50/50 — the Sprint-2 walk plus: transfer-out present + view missing → the
check names it → repair creates it → the owner records the 27-Aug transfer →
Bhawna's balance shows it. Pend patch round-trips byte-exact and its SQL is
proven on fixtures both ways.

## Install

```
bash /root/deploy/vps_deploy.sh S208_LEDGER3
```

At GREEN it prints the two browser-console lines: diagnose, then repair.

*S208_LEDGER3 · staged 30-Aug-2026.*
