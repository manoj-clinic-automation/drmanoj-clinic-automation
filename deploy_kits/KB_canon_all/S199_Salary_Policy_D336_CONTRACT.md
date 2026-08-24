# D336 — SALARY POLICY 2.0 (S199 · owner-ruled clause by clause · SIGNED via session rulings)

**Dr. Manoj Agarwal Clinic, Bareilly · 24 Aug 2026 · engine: `salary_policy.py` v1.3 (`7f86cc87…`)**
**Purpose (the owner's frame, verbatim intent): the system promotes and rewards punctuality and
minimum absence; deductions are deterrents, waivable; the month-end wraps in 5 minutes.**

## 1 · Late money — progressive at the person's own salary minute-rate
- Marks (notice-v6 bands, ≤10-min ×8-day grace) remain the TRACKING SCORE only; money never
  comes from the slab again.
- Minute-rate = base ÷ (30 × weekday shift minutes) — fair across pay grades (the flat ₹1/min
  had charged the lowest-paid ~3× their earned minute).
- First **90 minutes/month free** (over the daily grace) → band to 180 cum-min at **×0.5** →
  to 360 at **×1.0** → beyond at **×1.5**. Charges below **₹10** become 0.
## 2 · The Improvement Hold
- **25% of the late charge collected; 75% HELD** in the staff member's name.
- Released with next month's salary on **≥30% fewer chargeable minutes** (or no prior lateness).
- Written to `hold_ledger.jsonl` ONLY at a real lock (once per staff-month, re-lock-safe).
- **Waivable individual → all** at the owner's discretion (in the system; deliberately NOT
  advertised in the staff notice).
## 3 · Leaves — no ladder (owner ruling: "don't penalise")
- (leaves − allowed_offs) × base ÷ 30, **symmetric**: beyond allowance = no-work-no-pay;
  under-use credits back (the owner's July practice preserved). Per-staff allowed_offs
  (2; Arjun 4) from the staff master.
## 4 · Fines
- ₹50 per uninformed absence · ₹100/day beyond 3 genuine absences.
- **OPEN RULING (the Arjun case):** the ₹100 threshold is flat 3 while allowances are per-staff —
  Arjun (allowance 4) is fined for an absence his allowance permits. Proposed: fine begins only
  beyond allowed_offs. Owner to rule (Runbook §2).
## 5 · Dress & I-card
- ₹15/day-without each, recorded as explicit **Yes/No** ("Dress OK?") — only "No" stores a
  without-day (F-175). August 2026 pre-dropdown ticks ruled = Yes and migrated to 0 (backup kept).
## 6 · Incentive — the Diwali pot (S163 kept, ruled S199)
- ≤5 marks = one day's salary · ≤8 = half day — **accrues to the annual pot, paid at Diwali;
  never in the month's net.** Notice v3 wording matches.
## 7 · Everything is a setting
- `salary_policy_settings.json` (doctor-only save, audited via `salary_policy_settings_audit.jsonl`).
  **Recalibration never touches code** (the owner's standing plan; D332 pattern).
- Keys: free_late_min 90 · band1_end 180 · band2_end 360 · mult1/2/3 0.5/1.0/1.5 ·
  collect_now_pct 25 · improve_pct 30 · hold_enabled 1 · min_charge_rs 10 · dress_rs/icard_rs 15 ·
  fine_uninformed 50 · fine_excess 100 · excess_free_days 3 · incentive_full/half 5/8 ·
  day_divisor 30 · extra_duty_rs 200 · outstation_rs 250 · staff_view_current 1 ·
  staff_view_after_lock_days 5 · staff_remarks_enabled 1 · require_pack_approval 1 · enforce_from "".
## 8 · Enforcement
- `enforce_from` (YYYY-MM; empty = preview). Until it covers a month, EVERYTHING is preview and
  **the lock refuses** (D337). F-150 cannot recur structurally.
## 9 · Deliberate omissions
- Early-departure money is NOT in this policy (owner's edited sheet format; punch-outs visible in
  the grid for manual ruling; EARLY_BIG stays on the old report as a review item).
- Duty credits: night duty (ledger, ₹200/night default) + extra duty ₹200 + outstation ₹250
  credit into net.

*Validation: the engine's raw-late computation reproduces the owner's July manual sheet to the
minute for all ten staff; the July leave line reproduces at (leaves−2)×base÷30.5 — the ÷30.5 vs
÷30 difference is absorbed by the day_divisor setting going forward.*
