# Kit S184_F1a — D322 missing-day classifier (finance_app.py)

**Session 184 · live-code change · gated + reversible · restarts clinic-finance**

## What changes
`refresh_missing_days` in `finance_app.py` is revised per **D322** (which overrides the
S179 "never silence a missing day" rule, on your ruling):

- **Sundays** and **attendance-sourced clinic holidays** (from the staff-register
  `clinic_holiday` table + `festival_day` rows with `clinic_closed=1`) become
  **optional** — recorded for clarity as a new exception kind `clinic_holiday`
  (low severity, NOT counted as owed, NOT in "days not filed"). Fileable if a
  sporadic sale happened; filing resolves the note.
- **Genuine weekday gaps** stay **owed** (`missing_day`, high) and keep shouting.
- Darpan's absence still leaves the day owed — who files it changes, not whether.

New helper `clinic_holidays()` reads the attendance DB **read-only** and is
**fail-soft**: if the attendance DB is absent/locked, it degrades to Sunday-only
and never crashes the finance app (D283). Path overridable via
`FINANCE_ATTENDANCE_DB` (default `/root/staff_register/staff_register.db`).

## Effect on the dashboard
On the next load after install, the ~12 Sunday shouts + any clinic holidays
reclassify from owed `missing_day` to optional `clinic_holiday`. 16 Aug (Sunday)
stops being owed. The two genuine weekday gaps (27 May, 4 May) stay owed.

## Safety
- **F-97 currency gate**: refuses unless live `finance_app.py` = `86382f62…` (the
  build this was made against). Wrong/stale live file → nothing touched.
- Proven S182 swap pattern: stop → backup (`finance_app.py` + `finance.db`) → swap
  → py_compile → **`--selftest` on a copy of the REAL store** → restart on green →
  healthz → honest red that restores both backups and restarts the old code.
- No DB migration (recon_exception.kind is free text). Reclassification self-heals.

## Rehearsed offline
py_compile clean; classifier proven on seeded stores (clinic_holiday-table date,
festival clinic_closed=1, festival clinic_closed=0 weekday, plain weekday gap,
Sunday — each classified correctly); reclassify-stale + filed-Sunday-resolves +
fail-soft all pass; app boots (healthz 200); **differential vs the live 86382f62 —
identical behaviour** (both stop at the same seed-limited point, so no regression).
The full `--selftest` runs at install against the real store, gated with rollback.

## To run
PC: `deploy/push_kit.bat`. VPS: `bash /root/deploy/vps_deploy.sh S184_F1a`
