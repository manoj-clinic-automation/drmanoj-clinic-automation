# S195_ENTRY — LIVE (21 Aug 2026)

/ finance/entry redirect deployed GREEN on the VPS.

- **`finance_app.py` new live pin: `85df28fea117f8fc977b319cdfe70631`**
  (was S194E `d2863c30ed0d3cc23126c7da13d9fe9b`).
- Change: `/finance/entry` now redirects by role — maker → `/finance/daily`
  (Daily Sale v2), checker → `/finance/review`. Old single-page entry kept ONLY
  at `/finance/entry?legacy=1`. The 4 `--selftest` fetches that assert the old
  page's body were repointed to `?legacy=1`; the 2 redirect-behaviour selftests
  unchanged. **SMOKE 573/573** before and after.
- Path: `/root/finance/finance_app.py` (NOT /root/deploy). Service `clinic-finance`
  (gunicorn 127.0.0.1:8106). Backup: `/root/finance/_backup_S195_ENTRY_20260821_092433`.
- Why: reception (Darpan) hit the old `/finance/entry` URL directly in incognito
  and saw the outdated screen; the portal tile + default route already resolved
  to `/finance/daily`, so the fix hardens the stale-URL path.
- Kit: `deploy_kits/S195_ENTRY/`. Installer is currency-gated + auto-rollback.
