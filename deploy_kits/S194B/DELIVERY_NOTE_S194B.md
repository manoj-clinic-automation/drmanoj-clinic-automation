# S194B — ⭐4 live doctor hand-overs (reserve / drawer / unbanked)

**One file: `finance_app.py`.** Installs on top of the live S194 build.

## What changes
`/finance/api/cash-position` now folds live `cash_movement`s to Dr Bhawna /
Dr Manoj on top of the 17-Aug counted baseline:
- **reserve** = counted(dr_bhawna) + net dr_bhawna hand-overs
- **with Manoj** = counted(dr_manoj) + net dr_manoj hand-overs
- **drawer** = closing − counted-baseline
- **unbanked** = drawer + reserve + manoj — a **hand-over leaves unbanked
  unchanged** (cash is still in the unit, just in a doctor's hands); only a
  **bank deposit** reduces it.
The endpoint also now returns numeric `*_p` fields (drawer_p, reserve_p,
with_manoj_p, unbanked_p, parked_p, baseline_p), and the reserve/Manoj detail
lists now show the live hand-overs (kind="handover") alongside the counted
events. The Hub Cash-position card and Darpan's Daily-page drawer track this
automatically — no HTML change.

## Install (one run, on the VPS)
```
cd /root/deploy/repo && git pull
cd deploy_kits/S194B && bash install_s194b.sh
```
Currency-gates finance_app (`87cf4568…`, the live S194 build), backs up, swaps,
ALL-GREEN smoke that must GROW (the ⭐4 checks run), restart, rollback on red.

## Pin after GREEN
- `finance_app.py` → `43d2b84515790b93279a91bd1a65a104`

## Verified offline
9/9 delta checks: a dr_bhawna hand-over raises reserve +₹X and lowers drawer −₹X;
a return reverses it; a dr_manoj hand-over does the same to with-Manoj; a bank
deposit lowers unbanked without touching reserve; the invariant
drawer+reserve+manoj==unbanked holds throughout. Box smoke is the authoritative
gate (569 → 571).
