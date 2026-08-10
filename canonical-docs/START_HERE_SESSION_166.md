# START HERE — SESSION 166 (regenerated at S165 close)

Paste-to-resume entry point. The evergreen procedure is `START_HERE_PROMPT_v5.md`; **this** file is the session-specific state snapshot. Do **Phase 0** first: verify `CANONICAL_MANIFEST.md` by md5 (all tiers), read only Tier 0.

## Where we are
- Last session **S165**; this file opens **S166**. Next free: **D297 · F-71**.
- No open incident.
- **D223 gist tile is LIVE** end-to-end: `portal_gist.py` (builder, cron `*/30 9-20 IST`, sole writer of `/root/wa/portal_gist.json`) → `portal.py` doctor-only **📊 Clinic Gist** tile + `/portal/gist` page + `/portal/gist-data`. Metrics 1–4 live (pipeline health, call volume, unfiled callbacks, 3rd-strikes); **metric 5 (verdict) deferred** pending the AI-verdict store.
- **Live code:** `portal.py f0655abd…`, `portal_gist.py 55e111d7…` (both commit-owed, F-31). Unchanged: `salary_engine.py 5514918…`, `staff_register.py cef76859…`, `staff_ledger.py 92665b64`, `att_month_report.py v2.5 e64cad19…`.
- Salary parity holds July **₹1,07,447**; August still uncovered (no register entries yet).

## ⭐ Top of the backlog (Runbook §2)
1. **D297 — the Call-Log & Staff-Performance console** (owner's big ask): **signed contract first** (columns → live tabs; staff-summary; join map; layout), then build. Diagnosis IS live (F-70). Locate the **AI-verdict store** — it binds the console's verdict/recording/transcript columns **and** gist metric 5 (one hunt).
2. **Git commit owed** (code-only, F-31): `portal.py`, `portal_gist.py` + canonical-docs mirror (S162–S165).
3. **August reconciliation** at/after month-end (approve + lock the register run; confirm Darpan outstation not double-counted, D295).

## Fresh findings to action
- **F-69** — `Call_Feed` dead since 28 Apr (writer stopped; Follow-Up Tracker reconciliation degraded). **F-70** — Callback Tracker Core Dossier lags the live Sheet (diagnosis column present; no "Escalations" tab).

## Housekeeping owed
- Delete superseded stragglers from project knowledge: `START_HERE_SESSION_162.md`, `Staff_Daily_Register_Dossier_v1_0.md`.
- Notion catch-up S151–S165. Overdue key rotations (`CLINIC_SSO_SECRET`, GCP key). `wa_approve` nohup → systemd. Optionally `rm portal.py.bak-S165gist`.

**Confirm Phase 0 clean, then ask which backlog item to start.**
