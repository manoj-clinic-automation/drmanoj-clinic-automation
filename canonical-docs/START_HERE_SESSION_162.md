# START HERE — SESSION 162 (session-specific entry point, regenerated at S161 close)

Hi Claude. Continuing the clinic-automation project — **Session 162**. I'm Dr. Manoj Agarwal, orthopaedic surgeon, Bareilly. Solo practice, older Hindi-first semi-urban patients.

**Do Phase 0 FIRST (D247), before anything else:**
1. Open **`CANONICAL_MANIFEST.md`** (Tier 0 linchpin) and **md5-verify every row**. A mismatch halts work until reconciled (D172/D188). The S161 set: Register **v3.4** (`5066584cb695b63da311b7cae12bb179`), History Archive **v1.13** (`4ea7dfdf28f79baa34f0099d84918a7e`), Runbook **v99** (`HANDOFF_RUNBOOK_2026-08-09_Session161_v99.md`), Fault Register **v2.7** (`a2b1cf6f4224b2df6bb05560207b5dfd`), this START_HERE, and the Tier-1 dossier `Staff_Daily_Register_Dossier` **v1.1** (non-DRAFT).
2. Read into context only **Tier 0** (manifest, this file, KB Register v3.4, Runbook v99). Open Tier 1 only if the task touches it. Tier 2 is hash-verified, never read in the loop.
3. Confirm, then ask which **HANDOFF_RUNBOOK §2** backlog item to start.

**Where S161 left it (Runbook §0 has the detail):**
- **`staff_register.py` `406a793f…`** live (onboarding features: degree→council registrations, job-roles, addresses, family relation, issued-assets register).
- **`salary_engine.py` `a639f2b4…`** live — a **read-only Stage-A** reconciliation engine that reproduces the July **FINAL SALARY (TOTAL PAYOUT ₹107,447)** format and extends it with the **C-model** (D279/D280). Reuses att `salary_inputs` + ledger `compute_salary` read-only (no re-implementation, D281). **Stage B (official locked/approvable run) is DEFERRED** until the register holds real maker/checker data.
- Both files **repo-commit-owed** → `staff_register/`.

**⭐ TOP TASKS this session (owner-directed — Runbook §2 head):**
1. **Portal starting point** — where a staffer/doctor starts in the portal for the daily-register + salary flow.
2. **Drive the July-style FINAL SALARY (₹107,447 format) through the new system** as the acceptance test.
3. **Build/wire the Manager (Shavez = checker) + Alisha (maker) portals** for the daily maker-checker job = **Stage B** (make the Stage-A preview the official locked/approvable run). Enforce D272: Shavez cannot self-approve his own dates → override approves.

**Working protocol (strict):** plain language; ONE step at a time, wait for explicit OK; full-file replacements only; mask patient numbers (last-4) and all secrets; nothing live rebuilt without OK; build offline → `py_compile` on `/root/wa/venv/bin/python3` → **for live Flask, a test-client route hit (F-63)** → owner installs → md5 verify. Money math is never re-implemented — reuse att's `salary_inputs` + ledger `compute_salary` (D281). ALL-CAPS from me = urgent.

**Parked (do not raise unless I ask):** F-56 service-account key rotation + CALLHOOK Steps 3–4 (Lokesh); SSO passthrough for the 3 health apps; rotate `CLINIC_SSO_SECRET` at convenience (S160 transcript exposure).

**Next free: D283 · F-65 · Session 162.**
