# HANDOFF RUNBOOK — v103 (2026-08-10 · Session 165 close)

## §0 — WHAT HAPPENED LAST (S165)

1. **Phase 0 caught a stale linchpin + fixed it.** `CANONICAL_MANIFEST.md` was at **S161** while S162–S164 had advanced every other Tier-0/1 doc. Reconciled (three S164 Tier-0 docs cross-checked, agreed; 20 unchanged Tier-1/2 docs re-hashed live, **zero drift**) and **regenerated the manifest** (S161→S164→S165, S162–S165 delta blocks appended). Project-KB check: no canonical file missing; two superseded stragglers to delete (`START_HERE_SESSION_162`, `Staff_Daily_Register_Dossier_v1_0`).

2. **D223 GIST TILE DELIVERED end-to-end** (deferred ~40 sessions). **Unit 1 `portal_gist.py`** (`55e111d7…`, selftest 21/21) — read-only builder, sole writer of `/root/wa/portal_gist.json`, fail-loud, cron `*/30 9-20 IST`; live dry-run matched the probes exactly, first write + cron armed. **Unit 2 `portal.py`** (`4b75ee7b…` → `f0655abd…`) — doctor-only 📊 Clinic Gist tile + `/portal/gist` page + `/portal/gist-data`, all reading the JSON; F-63 test-client PASSED; restarted; owner confirmed the rendered page. Metrics v1 = pipeline health · call volume · unfiled callbacks · 3rd-strikes; metric 5 (verdict) deferred (store not on the Sheet). **The JSON is the contract** — future metrics add keys, portal unchanged.

3. **D295 — Darpan outstation +₹250/night IN salary** (closes S163-open). Already the register engine's behaviour; verify no cash double-count next salary touch.

4. **F-69** `Call_Feed` dead since 28 Apr (writer stopped; volume rebound to `Call_Durations`; Follow-Up Tracker reconciliation likely degraded). **F-70** Callback Tracker Core Dossier lags the live Sheet (diagnosis column IS present; no "Escalations" tab; strikes in `K_Strikes`).

**Live now** (md5-verified, service active): `portal.py f0655abd3221d64daf07441270488344`, **new** `portal_gist.py 55e111d71e95032c21234ae540a49431` (+ cron). Unchanged: `salary_engine.py 5514918…`, `staff_register.py cef76859…`, `staff_ledger.py 92665b64`, `att_month_report.py v2.5 e64cad19…`. Backup kept: `portal.py.bak-S165gist`.

## §2 — LIVE BACKLOG

⭐ **NEXT-SESSION TOP TASKS**
1. **D297 — the Call-Log & Staff-Performance console** the owner asked for: **its own signed contract first** (columns → live tabs; staff-summary definition; join map; layout), then build. Diagnosis column IS available (F-70). Locate the **AI-verdict store** to bind the verdict/recording/transcript columns AND gist metric 5 (one hunt).
2. **Git commit owed (code-only, F-31):** `portal.py f0655abd…` → `portal/`; `portal_gist.py 55e111d7…` → its `/root/wa` repo home; + canonical-docs mirror refresh (S162–S165). *(S164 salary/register commit reported done by owner at S165 open.)*
3. **August reconciliation** at/after month-end once the register is used for August: makers clear the pending board → `/register/salary?ym=2026-08` → reconcile the Delta line-by-line → **APPROVE & LOCK (Manoj-only)**. Confirm Darpan outstation not double-counted (D295).

**Then (staged retire-for-good, only after a real captured month is paid + matched):**
4. Redirect the ledger salary page → `/register/salary` (small `staff_ledger.py` change, like D286).
5. Delete dormant `compute_salary`; clean stale `/root/wa/staff_ledger.py 06bf03cb…`.

**Carried longer-horizon:**
- **F-69** find + restart the `Call_Feed` writer (Follow-Up Tracker reconciliation degraded since Apr). **F-70** update the Callback Tracker Core Dossier from the live Sheet.
- WABA sends blocked pending Lokesh; `wa_approve` nohup → wants a systemd service; key rotations overdue (`CLINIC_SSO_SECRET`, GCP service-account key from S156/S157).
- Case Pack → Vitals (needs D34 waiver) → CC-to-Tally migration (all VPS-hosted, off-Drive).
- Notion catch-up S151–S165.
- Delete the two superseded stragglers from project knowledge; optionally `rm portal.py.bak-S165gist` after a day.

## §3 — INSTALL DISCIPLINE (F-66)
Upload with a `.new` suffix → `md5sum` the file **in place** → only then `mv` into position. Always `cp file{,.bak-SNNN}` before install (instant rollback). A filename is not provenance — trust the hash. New/altered table → run the app's `--init` **before** `systemctl restart` (F-65). Any live Flask change must pass a test-client route hit (HTTP 200 + expected content) in `--selftest` before install (F-63). VPS python `/root/wa/venv/bin/python3` (F-53).
