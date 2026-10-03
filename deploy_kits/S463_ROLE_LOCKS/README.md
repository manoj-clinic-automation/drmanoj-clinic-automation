# S463_ROLE_LOCKS — the checker's figures answer only the checker (session 292, 03-Oct-2026)

At the owner's word of 03-Oct-2026 ("Do these"). F-707; source: S291 whole read, lead 2 — every one of the 38 handlers
without a role check was read with every page that calls it before anything was locked.

**One file changes:** `/root/finance/finance_app.py` `27a162e6` (S462) → `49f52391`. Needs S462 first.

| who may ask | routes |
|---|---|
| the checker only | `/finance/review` · `/finance/workbench` · `/finance/api/month/<ym>` · `/finance/api/days` · `/finance/api/parked` · `/finance/api/month/<ym>/close-check` · `/finance/api/sources` · `/finance/api/archive/queue` (or the worker's token) · `/finance/clinic/review` · `/finance/clinic/api/month/<ym>` · `/finance/clinic/api/days` · `/finance/clinic/api/parked` |
| maker or checker | `/finance/api/day/<date>/lines` (patient names) · `/finance/clinic/api/day/<date>` |
| left as they are | `/finance/clinic/api/tile` and `/finance/clinic/api/exceptions` (reception's entry page reads both; they need a field-by-field cut, its own kit) · both attachment routes · `/finance/api/shout` · `/finance/clinic/entry` · the five clinic "not in this slice" stubs |

A refused API answers the app's own 403 `not_permitted`; a refused page goes back to the portal, as the other checker pages do.
No page a maker uses calls a locked route (`finance_daily.html`, `finance_entry_clinic.html`, Darpan's pages were read).

**The selftest:** five lines inside `selftest()` are edited so its own role assumptions stay true (it asked for the
review page, the month twice and the day list as a maker). They could not be run here: `--selftest` needs the live
database and still writes its test bank statements into the live statement folders (found this session, not yet fixed),
so no installer runs it.

## Files
- `apply_s463.py` — 19 exact anchors, each found once, or nothing is written.
- `walk_s463.py` — 32 checks: six made-up logins ask every route touched and every route left, on the old file and the new.
- `install_S463_ROLE_LOCKS.sh` — gates → build lock → pin → apply on scratch → walk → backup `.bak_S463_27a162e6` → rename into place → restart → door and journal checks → restore on red. `DRY=1` places nothing.

## The owner's one line (runs S462, then this)
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S462_ADVANCE_POST_ONCE/install_S462_ADVANCE_POST_ONCE.sh && bash /root/deploy/repo/deploy_kits/S463_ROLE_LOCKS/install_S463_ROLE_LOCKS.sh
```
