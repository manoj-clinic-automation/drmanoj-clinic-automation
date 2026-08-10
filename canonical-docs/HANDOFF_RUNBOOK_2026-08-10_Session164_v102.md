# HANDOFF RUNBOOK — v102 (2026-08-10 · Session 164 close)

## §0 — WHAT HAPPENED LAST (S164)

A five-part session, all installed and live.

1. **F-67 FIXED / CLOSED (D291).** In `salary_engine.load_register()`, `covered` now keys off **`day_review.status='approved'`** (checker capture), not `daily_register` exception-row count. The old rule let a genuinely captured month with real biometric absences but zero exception rows read as *uncovered* and silently skip the base÷30 C-model cut → overpayment (proven ₹2,100 on a test month). Used `'approved'` (not any row) so the live stray 2026-07 **draft** day_review row can't flip July to covered. Table-missing → covered=False. New selftest **CASE E** (captured month, zero exceptions → covered=True, base30_ded>0) fails on the old engine, passes on the new. **July re-verified: TOTAL ₹1,07,447, all rows "no grid" (uncovered).** Live `salary_engine.py 5514918067243e3f39e7074144ee7db4` (from `303c7059`).

2. **Pending-review board (D292).** New `/register/review` in `staff_register.py`: **maker-pending** (working dates with no day_review row, up to today) + **checker-pending** (draft dates, with maker stamp + D272-safe one-click Approve), month nav + progress, all keyed off the existing `approval_blockers()` so the board and the salary lock can never disagree. Added `GET /register/review/counts` (JSON, role-aware: makers never see an approve count). Portal Staff-Register tile now lands on the board and shows **✍️ N to enter · ✅ M to approve**.

3. **F-68 (new finding).** Cross-origin credentialed browser fetch through OpenLiteSpeed is fragile (Origin/CORS stripped) — the tile first showed no counts. Fix: a **same-origin portal proxy** `GET /portal/review-counts` that server-side calls the register over localhost (`REGISTER_COUNTS_URL`, default `127.0.0.1:8044`), forwards the SSO cookie, 2s timeout, empty `{}` on failure. Tile confirmed live for manoj: **"✍️ 10 to enter · ✅ 0 to approve"**.

4. **Shivani activated (D293).** Roles are `_cfg`-driven (env → `staff_register_config` → default; empty = unset). No override existed, so the code default `SR_INACTIVE_MAKERS` was changed `"shivani"` → `""`. Shivani is now an active maker identical to Alisha; alisha/shavez unchanged.

5. **Portal user management (D294).** New **Manoj-only** `/portal/users` admin over `clinic_users` (list / add / set-role / reset-password / activate-deactivate / delete). Tile via `USER_TILE_EXTRA["manoj"]`; route `abort(403)` for non-admins (`PORTAL_USER_ADMINS=manoj`). Guards block deactivating/deleting self or the last active doctor. Portal-active = the login master switch; per-app maker/checker powers stay per-app; deactivation blocks future sign-ins only (epoch is global).

**Live now** (md5-verified, services active): `salary_engine.py 5514918067243e3f39e7074144ee7db4`, `staff_register.py cef768594bee5360a388e66028456495`, `portal.py 4b75ee7b50b5530eaca7c347e4a432d0`. Unchanged: `staff_ledger.py 92665b64`, `att_month_report.py v2.5 e64cad19…`. Install chains this session: staff_register `f24664db → 7c6bae8b → cef76859`; portal `bd37157f → 5cf81346 → 4b75ee7b`; salary_engine `303c7059 → 5514918`. **New sole-reference dossier delivered:** `Salary_Attendance_Master_Dossier_v1_S164.md` (supersedes Attendance v1.2, Salary KB v1, Staff Daily Register v1.1).

## §2 — LIVE BACKLOG

⭐ **NEXT-SESSION TOP TASKS**
1. **Git commit owed (code-only, F-31):** `salary_engine.py 5514918…` + `staff_register.py cef76859…` → `staff_register/`; `portal.py 4b75ee7b…` → `portal/`. (Carried: `staff_ledger.py 92665b64` → `staff_ledger/`.) Cold-kit + canonical-docs mirror refresh (S162–S164 sets, incl. the new dossier).
2. **August reconciliation** at/after month-end, once the daily register is actually used for August: makers clear the pending board (target zero blockers) → view `/register/salary?ym=2026-08`, reconcile the Delta column line-by-line (grid fines, C-model, incentive→pot, OT removal, Darpan outstation) → **APPROVE & LOCK (Manoj-only)**. First month intended to be paid off a locked register run instead of the workbook.
3. Confirm Darpan outstation +₹250/night should be IN salary vs paid cash (still open from S163).

**Then (staged retire-for-good, only after a real captured month is paid + matched):**
4. Redirect the ledger salary page → `/register/salary` (small `staff_ledger.py` change, like D286).
5. Delete dormant `compute_salary`; clean up stale `/root/wa/staff_ledger.py 06bf03cb…`; do NOT install the superseded ledger accordion `e799c8f8…`.

**Carried longer-horizon:**
- WABA sends blocked pending Lokesh; `wa_approve` nohup → wants a systemd service; key rotations overdue (`CLINIC_SSO_SECRET`, GCP service-account key from S156/S157).
- Case Pack → Vitals (needs D34 waiver) → CC-to-Tally migration (all VPS-hosted, off-Drive).
- Notion catch-up S151–S163 (S164 page created this EOS).

## §3 — INSTALL DISCIPLINE (F-66)
Upload with a `.new` suffix → `md5sum` the file **in place** → only then `mv` into position. Always `cp file{,.bak-SNNN}` before install (instant rollback). A filename is not provenance — trust the hash. New/altered table → run the app's `--init` **before** `systemctl restart` (F-65). Any live Flask change must pass a test-client route hit (HTTP 200 + expected content) in `--selftest` before install (F-63). VPS python `/root/wa/venv/bin/python3` (F-53).
