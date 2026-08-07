# START HERE — SESSION 157 (regenerated at S156 close)

Paste the evergreen START_HERE_PROMPT_v5 opener, or just type **start** — then Phase 0 runs (D247):
verify **every** row of `CANONICAL_MANIFEST.md` by md5 (all tiers); read into context ONLY Tier 0
(this file · KB_Register v2.9 · HANDOFF_RUNBOOK v94 · any open incident — none open).

**State in one breath:** the **full backend salary system is LIVE** (D259). `staff_ledger.py` **v3.1**
(`8bcf1b2d296786717437db672fb29b05`, selftest 184, at `attendance.dr-manoj.in/ledger`) computes salary
end-to-end: its `/salary` page reads `att_month_report.py`'s output files as the interface, pulls the
informed-flag / EARLY_BIG / OT / outstation rulings on-screen, folds in the ledger's closed adjustments +
each base salary, and produces the NET table (nearest rupee). **APPROVE & LOCK** appends one `SALARY_PAID`
row per staff + writes `salary_final_<month>.csv` + freezes the full report `salary_final_<month>.html`
(which is the owner's vetted attendance grid HTML + a spliced salary layer). A locked month is never
recomputed; corrections are next-month adjustment entries. The **F-51** UI-safety batch is live (contra
2-step confirm, skip confirm, void-pair greying, statement month headers). `clinic_watchdog.py` now guards
`staff-ledger.service` (11 services; also guards owner's `gutlog.service` from a separate Health project).

**TOP JOB (owner carry): finish the July reconciliation** — on `/salary/report?m=2026-07`, compare each
NET vs actually-paid. A clean verdict officially demotes the salary workbook to read-only. **July never
gets an APPROVE press** (it was paid via the workbook). Then the **first REAL approval is August**
(~Sep 01–09): enter all August events → close 2026-08 → preview → APPROVE & LOCK.

**Owed:** GitHub commit (ledger v3.1 `8bcf1b2d…` + watchdog `01ca6591…` + canonical-docs mirror,
now two session-sets behind). Tiny: `rm /root/watchdog_live_copy.py`.

**Backlog:** HANDOFF_RUNBOOK v94 §2. **Next free: D260 · F-54.** Notion catch-up spans S151–S156.
