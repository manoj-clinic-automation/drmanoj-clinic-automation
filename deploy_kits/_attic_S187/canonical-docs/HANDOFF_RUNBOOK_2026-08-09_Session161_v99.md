# HANDOFF RUNBOOK — 2026-08-09 · Session 161 · v99 (Tier 0)

**Dr. Manoj Agarwal Clinic · Bareilly.** Supersedes v98. §0 = what just happened · §1 = mental models · §2 = the live backlog.

---

## §0 — WHAT HAPPENED THIS SESSION (S161)

Phase 0 verified all canonical rows by md5 — **zero mismatches**. A build session, two streams, both shipped live and browser-verified: (1) finished the **Staff Register onboarding features**; (2) built **`salary_engine.py`** — a standalone, read-only salary-reconciliation engine (Stage A) that reproduces the July FINAL-SALARY output and extends it with a new leave model. **Eleven decisions minted (D272–D282); one finding (F-64). All work is on synthetic/empty-register data; the July run is a MECHANICS TEST, never paid.** Owner delegated all tech decisions and confirmed the work is planning-stage (real records entered later via maker-checker).

- **`staff_register.py` (live) → `406a793f96b743bccce53c5c783c1ce3`** (`/root/staff_register/`, `staff-register.service`, Flask 127.0.0.1:8044, proxied `attendance.dr-manoj.in/register`; each install via `--init`). Added: **degree → many council registrations** (each its own certificate; table `degree_registration`; degree flagged "NOT registered" until one added; cascade delete); **job-roles tick-list** + custom; **current/permanent address**; **family-relation dropdown**; **issued-assets register** (`asset_issue`: mobile_phone/bicycle/motorcycle/other, issue → mark-returned-with-date → delete[manoj]; custodian-gated Shavez+override).
- **`salary_engine.py` (live) → `a639f2b4be50b0e0d3e31fa3604ba175`** (`/root/staff_register/`, std-lib, **READ-ONLY** — writes nothing any live service reads; imported by the register app under a guard). Pure `reconcile()` core; loaders reuse att's `salary_inputs_<ym>.csv` + the ledger's `compute_salary` **read-only** — no money-math re-implementation (D281). Web `/register/salary?ym=YYYY-MM` gated `require("check")` (checker Shavez + doctors override; makers excluded); CLI writes `register_salary_<ym>.html`, **no rupees printed** (F-31).
- **Intended output confirmed:** the July attendance report (att Month Summary grid + **FINAL SALARY — TOTAL PAYOUT ₹107,447**, PREVIEW) is the target the engine now reproduces. July dry-run: 12 staff matched, incentive→pot 373.34, C-model base/30 deductions applied. Partial-August preview generated then **owner-deleted** at close.
- **F-64:** the ledger's **code** is `/root/staff_ledger.py` but its **data** dir is the separate `/root/staff_ledger/`; reusing `compute_salary` needed `/root` + `/root/portal` on `sys.path` (guarded).
- **Dossier:** `Staff_Daily_Register_Dossier` marked **non-DRAFT v1.1** — its §5 encashment design is noted superseded by the C-model (D279/D280).

**Decisions D272–D282 · Finding F-64 minted. Next free: D283 · F-65 · Session 162.**

---

## §1 — MENTAL MODELS (carry these)

- **Phase 0 first, every session** — hash-verify every manifest row before any work (D172/D188/D201). A filename/label is not provenance (F-62: audit the code, not the doc's category tag).
- **Build from the md5-verified live file**, full-file replacements only (D202), `py_compile` on the **VPS Python path** (F-53); for any **live Flask** change, a **test-client route hit** (200 + expected content) is part of the gate (F-63). String replacement with count assertions, never sed.
- **Reuse, don't re-implement, money math (D281).** The salary engine reads att's `salary_inputs_<ym>.csv` and the ledger's `compute_salary` **read-only** — the marks/fine/early/ledger math has exactly one home each; the engine only adds a delta. This is how drift is prevented.
- **The C-model is the salary law now (D279/D280).** C = discretionary leaves + genuine absences; a 2-day/month buffer; every day beyond it (+ over-quota festival) cut at **base÷30**; encashment paid **only if zero deductible extra days**; ₹50/₹100 fines stack unchanged; incentive → the annual pot. It **supersedes** the dossier's §5 encashment design.
- **Register = the single staff-master (D273);** absence classification stays the **biometric/attendance system's job (D275)** — the register captures the leave decision + exceptions only. Per-staff scoping matters (D276): Arjun = leave-only; extra-duty = Shivani; outstation = Darpan.
- **Stage A vs Stage B (D281).** Stage A (this session) = a read-only preview. **Stage B** = the official locked/approvable maker-checker run — built once the register holds real data. Shavez is both maker and checker but **cannot self-approve his own dates** (D272).
- **One writer per store; append-only ledger; maker-checker for money.** F-31: salary/finance data never in public repos or shared drives; the engine prints no rupees.
- **Off-Drive VPS-native is the phase-3 direction (D270/D274):** local PHI apps migrate to VPS **disk** (not Drive), keeping the leaked service-account key (F-56) out of the loop.
- **Secrets:** a secrets file entering the transcript = rotate (S128). `portal_config.py` did this at S160 → rotate `CLINIC_SSO_SECRET` when convenient.

---

## §2 — LIVE BACKLOG (the authoritative open list)

### ⭐ NEXT-SESSION TOP TASKS (owner-directed, do these first)
1. **Portal starting point** — decide/confirm where a staffer (and the doctor) **starts in the portal** for the daily register + salary flow; wire the entry tiles so the maker-checker job has a clear front door.
2. **Drive the July-style FINAL SALARY through the new system** — reproduce the att **FINAL SALARY — TOTAL PAYOUT ₹107,447** format end-to-end via `salary_engine.py` (Sundays half-day automatic, D282), as the acceptance test that the new pipeline matches the intended output.
3. **Build/wire the Manager + Alisha portals (Stage B).** The **Manager portal (Shavez = checker)** and the **Alisha portal (maker)** for their daily maker-checker jobs = making the Stage-A preview the **official locked/approvable run** (D281 Stage B), once the register is filled with real data. Enforce D272 (Shavez cannot self-approve his own dates → override approves).

### Main build track
4. **Staff Daily Register — fill + operate.** Dossier now **v1.1 (non-DRAFT)**; the register app is live with onboarding features. Remaining: seed real staff data via the maker-checker screens → yearly-balances store → engine reads real entries (dress/i-card/leave/extra-duty/outstation/encashment per the C-model) → **July + partial-August dry-run against real entries** before the first real APPROVE.
5. **Phase-3 local-apps strategy — hard-bake** (gates item 6). One doc: off-Drive VPS-native migration (Case Pack → Vitals[D34 waiver] → CC→Tally full-VPS); a shared doc-ingestion + Sarvam service; a VPS patient index; Marg/Labmate revenue plumbing (wired-LAN PCs); backup floor = app-level nightly self-backup; off-Drive to keep F-56 parked.
6. **Case Pack → VPS (D270)** — build after item 5 is signed off. Off-Drive; VPS-disk archive + PC-push patient CSVs; systemd + portal SSO (doctor-only); optional Sarvam extraction stored for search.

### Repo / commits
7. **GitHub commits.** Commit **`staff_register.py` `406a793f…`** + **`salary_engine.py` `a639f2b4…`** → `staff_register/`. Older owed: `portal.py` `81c2baef…` → `launcher/`; the register dossier → `canonical-docs/`; staff_ledger/watchdog mirror; canonical-docs mirror. External md5 re-check of the S158 six files still needs the **repo-owner path** (GitHub connector was OFF).

### Salary / attendance
8. **July salary reconciliation** — rupee-by-rupee vs actually-paid (owner carry).
9. **August salary run** (~Sep 01–09) — first real **APPROVE & LOCK**; ideally after the register build lands (Stage B).

### Standing items
10. **WABA — operationalise** (NOT blocked; owner-corrected). Confirm the live send path fires, then migrate `wa_approve` nohup→systemd.
11. **Callback Tracker — remaining polish** (refs: Core Dossier + AppsScript Audit).
12. **Cold-kit collection — organise** (with Cowork).
13. **Parked / small:** SSO passthrough for the 3 health apps · **rotate `CLINIC_SSO_SECRET`** (S160 transcript exposure) + re-run `portal_setup.py` · Notion catch-up (S151–S160) · verify `staff_master.sunday_group` populated · tidy the stale `:8090` comment in `portal.py`.
14. 🔴 **PARKED by owner (do not raise until asked):** rotate the Google **service-account key** (F-56) + CALLHOOK Steps 3–4 (Lokesh).

*Backlog pointer for next session: this §2 (TOP TASKS block first). Next free D283 · F-65 · Session 162.*
