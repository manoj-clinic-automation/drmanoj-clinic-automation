# START HERE — SESSION 165 (paste to begin)

Hi Claude. Continuing the clinic-automation project — **Session 165**. I'm Dr. Manoj Agarwal, orthopaedic surgeon, Bareilly. Follow the evergreen protocol (`START_HERE_PROMPT_v5`): Phase-0 md5 verification first, ONE step at a time with explicit confirmation, full-file replacements only, mask secrets/patient numbers, build → sandbox py_compile → VPS-venv py_compile → I install → md5 verify. VPS python `/root/wa/venv/bin/python3`.

**Phase 0 — verify before work.** Open `CANONICAL_MANIFEST.md` and hash-verify every row (all tiers). Read into context only Tier 0: the manifest, this file, **KB_Register (S164)**, **HANDOFF_RUNBOOK v102**, and any open incident (none). Then confirm and ask which backlog item to start (Runbook §2 = live backlog).

**Where we are.** The salary + attendance machine is consolidated into a **single sole-reference dossier** — `Salary_Attendance_Master_Dossier_v1_S164.md` (supersedes the three old docs). **F-67 is fixed and CLOSED** (D291): salary coverage now keys off `day_review` **approved** capture, not exception rows — a register-captured month with genuine absences but no logged exceptions correctly applies the base÷30 C-model cut (CASE E regression proves it). **July parity re-verified to the rupee: ₹1,07,447, still uncovered.** Also shipped this session: the **pending-review board** `/register/review` + role-aware portal counts tile (D292, with same-origin proxy F-68), **Shivani activated** as a maker (D293), and **Manoj-only portal user management** `/portal/users` (D294).

**Live now** (md5-verified, services active): `salary_engine.py 5514918067243e3f39e7074144ee7db4`, `staff_register.py cef768594bee5360a388e66028456495`, `portal.py 4b75ee7b50b5530eaca7c347e4a432d0`. Unchanged: `staff_ledger.py 92665b64`, `att_month_report.py v2.5 e64cad19…`.

**⭐ TOP TASK S165:** the **owed git commit** — three S164 files (`salary_engine.py`, `staff_register.py` → `staff_register/`; `portal.py` → `portal/`) plus the carried `staff_ledger.py`, and the canonical-docs mirror + cold-kit refresh (S162–S164 sets). Then, at/after August month-end, the **first real August reconciliation** on `/register/salary?ym=2026-08` (clear the pending board → APPROVE & LOCK, Manoj-only) — the first month intended to be paid off a locked register run rather than the workbook.

**Install discipline (F-66):** upload `.new` → md5 in place → `mv`; always back up first; `--init` before restart for any new/altered table.

Next free: **D295 · F-69 · Session 165.**
