# S625_MONTH_AND_DAY — the machine form keeps its day (F-976); a bill counts in its own month (F-980)

*Kit S625 claimed on the board `_numbers` v596 → v597 at the owner's "do it" (14:50 IST 22-Oct-2026). Built, walked and rehearsed
in the Scan App chat at session 337 — in the chat, not by the API-credit runner (his word, 14:07 IST). **Install after S624.***

## The owner's ruling (F-980), asked in one line at 14:5x IST 22-Oct

*"A bill dated in an earlier month but scanned later: which month should it count in?"* — his pick: **"Bill's own month"** —
automatically, for papers scanned from now on; past months stay as they are.

## What changes, as he will see it

| fault | before | after |
|---|---|---|
| **F-976** — a machine's Edit form (Assets → the machine → Edit) | the purchase date (and cover start, EMI start) is shown as month and year; any Save wrote it back as the 1st (28-04-2026 → 01-04-2026; assets 7 and 12 on 18-Oct) | a Save that keeps the same month and year keeps the day the record had; a changed month, or a new machine, takes the dropdowns' value as before |
| **F-980** — The month, the desk's lists, X-ray costs, stationery's month | a paper counted in the month chosen on the scan screen (today's by default), so B-0203 (a July bill) stood in October until set by hand | a paper **scanned from this install on** whose bill is dated in an earlier month (not more than 12 months back, never a later month) counts in the bill's own month; its own page says *"Month: July 2026 (the bill's own date — scanned as October 2026)"*; a month a person chooses on the paper's page still wins if it is earlier; papers scanned before the install keep their months |

## How

- **F-980 in ONE place:** `clinic_papers.MONTH_OF`, the one shared rule every month view reads (The month, the sorting desk's
  lists and rates, X-ray costs, stationery). It is switched by one settings row, `papers.month_from_bill_date`, which the installer
  writes as the moment of the install (absent or `off` = the old rule). Nothing in the papers is rewritten.
- **F-976:** `asset_register.asset_edit` — a small helper keeps the record's own day when the month and year posted are its own.
- `asset_register.py` stood at drift 8 + S618: it was read whole by the independent review before this publish (F-836).

## Files

| file | FROM | TO | edits |
|---|---|---|---|
| `/root/assetapp/clinic_papers.py` | 6db07c12 | 89a3cd0a | 3 (the rule, and two lines on the papers pages that describe it) |
| `/root/assetapp/asset_register.py` | 70e35b10 (S618's TO) | f21ae7ca | 6 |

A paper's own page: *"Month: July 2026 (the bill's own date — scanned as October 2026; to count it elsewhere, choose an earlier month
below or correct its date)"*.

Read only, pinned: `sorting_desk.py` 110335ea, `xray_costs.py` 22e59f5a, and S624's TO `batteries.py`, `asset_machine.py`,
`stationery.py` (the installer refuses until S624 is in). Restarts `assetapp` only.

## Install — the owner's one server line (after his publish, and after S624)

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S625_MONTH_AND_DAY/install_s625.sh
```

Order: gates → the lock → pins (both TO + the row = ALREADY INSTALLED) → rebuild (`make_s625.py`, 7 counted edits) → TO pins →
compile (9 counted edits in all) → the walk on the REAL app with the TO files on a COPY of the live database (made-up rows dated 2031) and its control on the
FROM files → S624's real-app walk on the new app → backups `<file>.bak_S625_<from8>` → place → read back → restart → `/healthz` 200,
five pages 302, no part "NOT mounted" in the log → the database backup `assets.db.bak_S625_<stamp>` → the switch-on row →
`S625_MONTH_AND_DAY: DONE`. If the row's write fails, the code stays in place with the old rule, and the same line pasted again goes
straight to the data step. Any failure after placing puts
both files back, checks them against the FROM pins, and restarts. `DRY=1` stops before the backups.

## Undo

```
\cp /root/assetapp/clinic_papers.py.bak_S625_6db07c12 /root/assetapp/clinic_papers.py
```
```
\cp /root/assetapp/asset_register.py.bak_S625_70e35b10 /root/assetapp/asset_register.py
```
```
systemctl restart assetapp
```

The old code ignores the settings row, so the old rule stands at once. To keep the code but switch the month rule off, set
`papers.month_from_bill_date` to `off` in `settings`.

## Proven before the publish (in the chat, 22-Oct)

- `walk_s625_app.py` — the REAL scan app with all six parts mounted, made-up rows only: **18 green, 0 red** (on the box it also proves
  that every paper already in the live database keeps its month when the rule is switched on, F13); its control on the FROM
  files: **the 6 must-red checks red** (the July bill stayed in March's place; a 28-04 purchase was saved back as 01-04 —
  F-976 reproduced exactly), the rest green;
- `rehearse_s625.sh` on a made-up root: **7 green, 0 red** (dry run, install with the row, ALREADY INSTALLED, other bytes refused,
  S624 not first refused, health red after placing → both files back and no row, a failed row write finished by the re-run);
- an independent cold review K1 with the whole read of `asset_register.py` (F-836): SAFE TO INSTALL, 0 blockers, 5 corrections —
  made in place: the switch must look like a date (an empty value can never pull past papers); the re-run after a failed row write;
  the database backup before the data step; the papers pages' wording; the paper's page says how to count it elsewhere. Left for
  later, named: the desk's own wording line (`sorting_desk.py`, pinned), and the old "late" mark, which does not follow the rule;
- S624's real-app walk re-run on the new app: green.
