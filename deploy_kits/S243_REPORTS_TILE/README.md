# S243_REPORTS_TILE -- "Aaj ki reports": the Marg report generator's morning page

Built 13-Sep-2026 (S243) to the owner's ruling of the same day: **Shavez** (portal login `shavez`,
role manager) becomes the Marg **report generator** -- a morning job on the medical PC before any
sale starts, and on Amir's days too -- so that this job leaves the owner's desk. He generates the
reports in Marg; the server sees each one arrive through the one door within seconds; his page
confirms each and prompts him **only** for the refused and the still-due ones.

## What Shavez sees -- `/finance/reports/aaj` (Hinglish, phone-first, no JavaScript)

One line above the list: **"Marg me report banao, yahan khud tick ho jayegi."** Then today's rows:

| row | shown when | ✓ aa gayi (time) when | source |
|---|---|---|---|
| Bill-wise sale report, *kal ki* | always | a VERIFIED `mi_file` SALE_BILLWISE whose date range covers yesterday, or a `marg_push_staging` row (not rejected) naming yesterday | marg_take / marg_ingest; the pushed-report door |
| Stock closing report, *as on yesterday* | always | VERIFIED `mi_file` STOCK_CLOSING as on yesterday **or today** (a morning closing before sales is yesterday's close -- export_watch's rule), or `stock_feed` push_snapshot with that as_on | the one door; the stock snapshot |
| Purchase item-wise / Purchase bill-wise, *1 tareekh se aaj tak* | **Amir days only**: Amir punched today (export_watch's punch logic, staff-register machine id, 101 fallback) **or** an `amir_day` row for today | `purchase_export` (ITEMWISE/BILLITEMWISE; BILLWISE) received today covering the 1st..yesterday, or the VERIFIED `mi_file` PURCHASE_* equivalent | the purchase push; the one door |
| Salt-wise item list | **only when due**: a `purchase_salt_task` tick newer than the last VERIFIED SALT_WISE arrival (or one arrived today) | VERIFIED `mi_file` SALT_WISE_ITEM_LIST received today | the one door |

States: **✓ aa gayi** *HH:MM baje* · **✗ manzoor nahi** *HH:MM baje* + the reason in plain Hindi
(the router's English words beneath, small) · **○ baaki**. A verified copy always wins over an
earlier refusal. A file the router could not place at all today is said once at the bottom
("Ek file pehchan nahi aayi"). When everything is in: a green "Aaj ki sab reports aa gayi" card.
The page refreshes itself every 30 s (`meta refresh`); `/finance/reports/aaj/<date>` shows any
day without the refresh. **The page writes nothing and creates no table** (walk-proved).

**Owner (English):** one line on the hub's Marg card, under *Pushed reports*:
**"Today's reports: 2 of 3 arrived"** (+ ", 1 refused", the refused/due names, "(Amir day)",
"open"). From `/finance/reports/aaj/api/status`.

## Gate

Any role on the **medical** unit (maker / checker / viewer), exactly as Amir's page. `shavez`'s
portal role `manager` maps to nothing in the finance app (S179), so the installer runs
`seed_reports_role_s243.py`: **`unit_role (medical, shavez, viewer)` only if he holds no active
medical role** (S182 gave him medical maker; if that row is live, nothing changes). Idempotent.
Anonymous → the portal login (finance_app's own gate). A signed-in login with no medical role
(e.g. `alisha`) → the portal, nothing shown.

## Install (the owner's double-click publishes; then ONE line on the VPS)

```
bash /root/deploy/repo/deploy_kits/S243_REPORTS_TILE/install_S243_REPORTS_TILE.sh
```

Six files move, two services restart. **Pins the kit was built on (13-Sep capture):**

| file | from | to (predicted) |
|---|---|---|
| `/root/finance/finance_app.py` | `f002defb…` (S243_AUTOAPPLY) | `029aa24a…` alone · `9643e339…` after SCREEN_FIXES · `f9787ef7…` after DARPAN_KAL · **`dae5fd90…` after both** |
| `/root/finance/finance_ui/finance_approvals.html` | `cc349dd0…` | `3e01002e…` alone · **`b8578b8d…` after DARPAN_KAL** |
| `/root/portal/portal.py` | `d08721f6…` (S242_AMIR_TILE) | `4bb6bde0e2e07033ac0e0f5d7a7daaf6` |
| `/root/portal/tile_grants.json` | `7e7445a3…` v12 | `c9ee95c39bb805086b79d95327b2b626` v13 |
| `/root/finance/reports_tile.py` | new | the kit's bytes (SUMS.md5) |

The installer accepts `finance_app.py` at the pin **or carrying the S243_SCREEN_FIXES / S243_DARPAN_KAL
mark**, and the hub at its pin **or carrying the DARPAN_KAL mark** -- the patcher's count==1 anchors
are the real guard (the finance anchor is the `__main__` block at the very end; the hub anchors sit
inside the Marg card and `load()`; none of the sibling kits touch them, and the same bytes result in
either install order -- proven). The ACTUAL from-pin is recorded in every `.bak_S243_<pin8>` name and
the printout. `portal.py` and `tile_grants.json` must be exactly at their pins.

Gates: SUMS + KIT_ID → live pins → patcher selftest on the live bytes → every patch to `.new` / a
copy before anything is placed → `.bak_S243_<pin8>` of every changed file → place → py_compile →
import smoke of **both** apps (the `reports_tile` blueprint registered under the unit's environment;
the tile present, grants v13, shavez shown it) → seed → restart `clinic-finance` and `clinic-portal`
→ healthz within 20 s each. Any RED → every file restored, the new file removed, services
restarted, exit 1. Re-run → ALREADY INSTALLED. (The seeded viewer row survives a rollback --
harmless; `UPDATE unit_role SET active=0 WHERE unit='medical' AND username='shavez' AND role='viewer'` undoes it.)

Rollback by hand (pin8s are printed by the installer):
```
\cp -f /root/finance/finance_app.py.bak_S243_<pin8> /root/finance/finance_app.py && \cp -f /root/finance/finance_ui/finance_approvals.html.bak_S243_<pin8> /root/finance/finance_ui/finance_approvals.html && systemctl restart clinic-finance.service
```
```
\cp -f /root/portal/portal.py.bak_S243_d08721f6 /root/portal/portal.py && \cp -f /root/portal/tile_grants.json.bak_S243_7e7445a3 /root/portal/tile_grants.json && systemctl restart clinic-portal.service
```

**After install, prove on the box (builds its own db, touches nothing live):**
```
FIN_APP=/root/finance/finance_app.py FIN_MODS=/root/finance MI_DIR=/root/marg_ingest PORTAL_PY=/root/portal/portal.py /root/wa/venv/bin/python3 -B /root/deploy/repo/deploy_kits/S243_REPORTS_TILE/walk_reports_tile_s243.py
```

Nothing is left for the owner: Shavez opens the portal and taps **Aaj ki reports**.

## Files

| file | role |
|---|---|
| `reports_tile.py` | the module: the rows, the Hindi reasons, the page, `/api/status`; `python3 -B reports_tile.py` runs its 15-check selftest |
| `patch_finance_app_reports_s243.py` | on-box patcher for `finance_app.py` (mount, guarded) and the hub (line + loader + call), `--selftest` |
| `patch_portal_reports_tile_s243.py` | on-box patcher for `portal.py` (the tile + its group row), S242 style |
| `tile_grants.json` | v13 -- v12 plus `Aaj ki reports` in `shavez` and `amir` `extra`; nothing else moves |
| `seed_reports_role_s243.py` | `unit_role(medical, shavez, viewer)` if he has no active medical role (run by the installer) |
| `install_S243_REPORTS_TILE.sh` | the installer (gates, pins, backups, smokes, seed, two restarts, healthz, rollback) |
| `walk_reports_tile_s243.py` | live-shape walk, 60 checks (58 on a box without the sibling kits): the rendered page as shavez, every state, Amir-day by punch and by row, the salt rule, refusals in Hindi, anonymous/alisha, the hub line, the portal's `_visible_sections` |
| `mock_install_reports_tile_s243.sh` | the installer's six ROOT proofs (wrong finance pin, wrong portal pin, install, ALREADY, healthz rollback, sibling lineage + seed) |

## Not built / open

* `amir_day.py` step 4 (`_export_state`) compares `substr(export_stamp,1,10)` with an ISO day while
  `export_stamp` is `YYYYMMDD-HHMMSS` -- on the live bytes Amir's step 4 can never see a report.
  Not touched here (this page reads `purchase_export` by `substr(export_stamp,1,8)`, export_watch's
  way); flagged for its own fix.
* No push/notification when a report is refused -- the page is the prompt; the owner's hub line is
  the summary. A morning ntfy line can ride on `/api/status` later.
* The "as on today" stock closing is accepted at any hour (the PC comes up 8-10:30 and nothing is
  late by the clock); export_watch's 10:30 nuance is not repeated here.
