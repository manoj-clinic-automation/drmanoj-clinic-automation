# S195_ENTRY — /finance/entry redirects to the live page

Fixes: a fresh/typed hit on the OLD `https://followup.dr-manoj.in/finance/entry`
showed the outdated single-page screen (reception hit it directly, not via the
portal tile — the tile + default route already send makers to /finance/daily v2).

Change (one route in finance_app.py, nothing else):
- `/finance/entry` now redirects by role — checker → `/finance/review`,
  maker → `/finance/daily` (the v2 Daily Sale). The old page is kept reachable
  ONLY via `/finance/entry?legacy=1` (nothing lost).

Safety: currency-gated to the exact live S194E file (md5 d2863c30…); backs up,
compiles, restarts clinic-finance, smoke-tests service+healthz+entry, and rolls
back automatically if the service doesn't return healthy.

Install:
```
cd /root/deploy/repo && git pull
cd deploy_kits/S195_ENTRY && bash install_s195_entry.sh
```
New finance_app.py md5 after patch: a161a70755cb89bf1763d8942722c6c4
Backup kept as /root/deploy/finance_app.py.bak_s195_entry .
