# S199_FLOW1 — THE MONTH-END FLOW (owner spec, S199)

## What goes live
1. **salary_policy.py (NEW)** — the settings-driven engine: progressive late
   pricing at each person's own salary minute-rate (90 free min/month over the
   10-min×8 grace; bands ×0.5/×1.0/×1.5), the **Improvement Hold** (25%
   collected, 75% held, released on 30% improvement — every number a setting),
   leaves at full day rate symmetric (credit for under-use), ₹50/₹100 fines,
   dress/I-card ₹15/day-without, incentive FULL≤5/HALF≤8. **PREVIEW is
   standard**: nothing is applied until a month is locked AND covered by the
   enforce-from date (default: unset = preview only).
2. **staff_register.py v0.6** — the flow pages behind the salary gate:
   - `/register/salary/flow` — the pack: Sheet 1 (attendance grid: P/L/A/*,
     punch times on hover, doors to the day pages; print version has the
     Staff-remark column) · Sheet 2 (advances this month, long-term loans with
     taken/instalment/this-month/balance, holds; doors to the ledger) ·
     **Approve Sheet 1 / Sheet 2** buttons · Sheets 3+4 preview (detail +
     signature, print-ready).
   - `/register/salary/policy-settings` — every fine and lever editable
     (doctor-only to save, audited). **Recalibration never touches code.**
   - **Lock gate**: salary lock refuses until both sheets are approved.
   - `/register/me/month` — each staff member's OWN grid, no money ("My month"
     link on their phone page).
   - Dress/I-card become **Yes/No dropdowns** ("Dress OK?"); only an explicit
     No stores a without-day.
3. **migrate_dress_S199.py** — one-shot: August's pre-dropdown ticks meant YES
   (owner ruling); flags zeroed with a DB backup, counts printed.

## Deliberate omissions (owner's edited sheet format)
- Early-departure money is NOT in the new model (visible in the grid; owner
  rules manually). EARLY_BIG stays a review item on the old report.
- The waiver is in the SYSTEM (holds waivable individual→all via the hold
  ledger; every hold row auditable) but NOT advertised in the staff notice.

## Pins
| File | Base (must match live) | New |
|---|---|---|
| staff_register.py | c1fede9f… (or 0b73ee54… if v1 installed) | see SUMS.md5 |
| salary_policy.py | (new file) | see SUMS.md5 |
Dependencies verified, not changed: att_scenario 4dcd19bc… · att_month_report 9ab98313… · salary_engine ca37c615…

## Install
    bash /root/deploy/repo/deploy_kits/S199_FLOW1/INSTALL.sh
Gates on the exact live bytes; backs up; compiles; runs BOTH selftests on the
box (restores on failure); runs the dress migration (with backup); restarts;
then writes July + August preview files as smoke.

## Proven offline
py_compile+pyflakes clean · policy math selftest (band arithmetic to the
rupee) · engine tested on a synthetic covered month (charges, holds, releases,
leave credits, advances/loans, nets to the paise) · register selftest PASS
with all new routes · full Flask walk: pack→doors→approve→lock-gate→settings
save→live recompute→me/month · dropdown save semantics (No→1, Yes→0).

## v2 additions (S199-B, owner rulings)
- Sheet 2 now lists ALL fines & deductions per staff (late/collect/hold, leave
  amt, Rs.50/Rs.100, dress, I-card, incentive) — the pack covers the whole
  money side before approval.
- Staff month view: remark form ("raise a remark for the doctor's review");
  remarks land on the owner's flow page with an open-day door and a 'handled'
  button; staff see 'waiting'/'seen by doctor'.
- Visibility windows AS SETTINGS: running month live (staff_view_current, on),
  completed month until N days after lock (staff_view_after_lock_days, 5),
  remarks on/off. The 'revised' sheet is automatic — the view always
  recomputes from the stores after the owner's corrections.
