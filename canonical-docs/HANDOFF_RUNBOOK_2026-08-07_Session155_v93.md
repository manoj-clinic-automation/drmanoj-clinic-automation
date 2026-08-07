# HANDOFF RUNBOOK — 2026-08-07 — Session 155 — v93

## §0 — WHAT HAPPENED (S155, FULL EOS — Staff Ledger v2.4; D258 minted + EXECUTED; Darpan loan live in-app; repo trim pushed)

1. **F-49 CLOSED by ruling:** the blanket `*.csv` gitignore IS the enforcement (verified: `staff_master.csv` 404 on live GitHub); no explicit line. S154's three-file commit hash-verified byte-exact. NTFY wiring + dress/I-card import DROPPED by owner.
2. **Digest recipe REDISCOVERED + documented** — `md5sum <folder>/* | sort | md5sum` from repo root; proven by exact reproduction of the S147 pin on the git-history-reconstructed freeze folder. New pins: `attendance/` (11 files) `c4c9c83f44fbbbb39609047671e77d60` · `clinic_writer/` (7 files, v28 already in repo) `1b4f0f2299cd6c9e72b6d04f45847556`. S149 Fault-Register push carry found already DONE.
3. **Phase-2 trim ruled + EXECUTED + pushed** (keep 6 staff-facing docs · archive 4 · rm 2 byte-identical dupes) via `Repo_Trim_Phase2_Ruling_S155.ps1`; HEAD-verified. Lessons: PS-5.1 needs pure-ASCII deliverables; a commit isn't pushed until "Push origin" is clicked. `canonical-docs/` mirror = one session-set stale + ~15 root strays (rides the next doc push).
4. **THE DAY'S CENTRE — D258 minted AND executed.** Owner ruled ALL Darpan money — the structured loan included — into the Staff Ledger; workbook Darpan sheets RETIRED. Reading the live workbook (scoped F-31 waiver) caught a real engine error pre-migration: the instalment IS the whole monthly deduction (interest comes OUT of it, cross-tranche waterfall, interest stops at tranche clear, skip = pause + ₹1,000 capitalise, 2/FY). Record corrected: skips this FY = 1 (2026-04); perks ₹19,000 after a test row was deleted from the workbook (1,496 formulas 0 errors, new md5 `a0e3b038…`).
5. **`staff_ledger.py` v1.2 → v2.4 `74dac84eb15f5172478a97066f56c99d`** (five verified installs; selftest 42→123; ~15 mutation probes): statement view (checker=all, maker=own via staff_link) · workbook-exact loan engine (replayed the REAL history to the rupee) · PERK (doctor-only, narrated, salary-excluded) · atomic idempotent `migrate-loan` (validate-before-append; one instalment; perks brought forward; case-insensitive names) · entry-form position strip (checker-only, privacy two-gate-proven) · ₹0-advance refused. **F-50 raised by the owner live + fixed** (checker powers were derived-everything → explicit allow-lists rule).
6. **Migration EXECUTED:** verification exact (183,000 / 180,000 / 1 skip / 19,000) → `close 2026-07` → Darpan **−5,000** July line, loan **179,000**; phone-verified. Audit found one pre-migration **Shivani test ad-hoc fine → contra owed (owner, phone)**; ignore her line when entering July salary.
7. **Workbook's new canonical home: VPS `/root/clinic_salary/Salary_System_2026.xlsx`** (chmod 600, md5 verified); PC copy replaced. Monthly download→enter→upload loop is TEMPORARY (see backlog 1).

Fault codes: **F-50** minted (fixed). Decision: **D258**. Notion absent a FIFTH session. No incident.

## §1 — MENTAL MODELS (delta only)

- **One home per rupee.** A rupee lives in exactly one system; systems meet only through one net line at monthly close. The workbook keeps salary computation; every event and every loan rupee is the ledger's.
- **Repayment is never typed; a skip is never a ₹0.** The close computes; the Skip button pauses. Any urge to type a loan number by hand means you're on the wrong page.
- **A role's powers are an explicit allow-list** (F-50) — never "everything in a growable dict" — and every power-set carries a negative selftest.
- **In an append-only ledger, validation completes before the first append** — a half-migration can't be rolled back, so it must be impossible.
- **A green first run proves nothing until mutations fail it** — and a mutation must break the *actual* protective gate; surviving a probe against one gate of a two-gate defence indicts the probe, not the code.

## §2 — LIVE BACKLOG (ordered)

1. **S156 TOP (owner mandate): full backend salary automation** — no manual Excel entry, no monthly workbook upload; VPS computes salaries end-to-end (att_month_report inputs × ledger close CSV × staff_master bases); workbook demotes to read-only reference or retires. Design first: output format, approval gate, payslip artefact.
2. **Owner (phone, 2 min):** contra the Shivani test fine (Full ledger → row id → contra form, narration "test entry - reversed").
3. **Watchdog coverage:** add `staff-ledger.service` to `clinic_watchdog.py` (carried from v92 — untouched this session; bundle with 1).
4. **Repo commit owed:** `staff_ledger/staff_ledger.py` v2.4 `74dac84e…` + canonical-docs mirror refresh (S155 set + archive the ~15 root strays). Git kit ships both.
5. **August attendance run ~01-09** (first billing): v2.5 flow per v92 §2.3.
6. **August ledger close ~01-09** with the salary run: `close 2026-08` (contains Darpan's next 5,000 + all August events + the Shivani contra netting).
7. First-real-entries onboarding: Shavez & Alisha briefing + passwords (carried).
8. `wa_approve` systemd — verify `systemctl status` first (record conflict) — carried.
9. Overdue key rotations — carried. 10. WABA sends blocked on Lokesh — carried.
11. **Notion catch-up S151–S155** (five sessions). 12. clinic_writer Hindi spellings — carried.
13. Parked: D255 appraisal, Insight Harvest D241, D223 gist tile, Docterz (D243), Sunday-roster code drop items already live via v2.5.

## §3 — REPO

Commits owed (one GitHub Desktop session): `staff_ledger/staff_ledger.py` v2.4 `74dac84eb15f5172478a97066f56c99d` · `canonical-docs/` refresh (Register v2.8, Archive v1.7, Runbook v93, START_HERE_156, manifest; superseded root strays → `archive/`). Ledger DATA, workbook, salary CSVs: NEVER (F-31).

*Runbook v93 supersedes v92. Next session: 156. Next free: D259 · F-51.*
