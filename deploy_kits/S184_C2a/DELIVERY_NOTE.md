# Kit S184_C2a — regenerate the medical exceptions after the C1a correction

**Session 184 · follow-up to S184_C1a · reversible · no code, no service restart**

C1a corrected the money but left the `recon_exception` snapshot stale — the dashboard
still showed the obsolete "13 Aug −₹30,056" negative-cash shout and 36 carry-forward
breaks whose adjustments C1a removed. There is no live detector that recreates those
two kinds (only the one-shot importer did), so this kit regenerates them:

1. **carry_forward_break** — all resolved. After C1a the opening is computed and the
   sheet's Old-Balance drift no longer exists, so these breaks are gone.
2. **negative_cash** — the stale ones resolved, then recomputed straight from
   `v_cash_ledger` (the live corrected ledger). The days that are genuinely negative
   now are the **cash-parking windows** (June–early Aug), kept as honest exceptions per
   your choice, each labelled as cash parked with Dr Bhawna ahead of a bank trip.
3. **line_sum_vs_day_total** (F-104 Marg attribution) and **missing_day** — untouched.

Gated: refuses unless C1a is applied and C2a has not run. Whole-db backup first;
one transaction; idempotent; reversible (rollback block in the .sql + the backup).
Rehearsed offline on the C1a-corrected seed: 35 breaks → 0, negative_cash recomputed
to the 29 parking days, line_sum/missing untouched, rollback byte-restores.

## To run
PC: `deploy/push_kit.bat`. VPS: `bash /root/deploy/vps_deploy.sh S184_C2a`
