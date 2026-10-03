# S467_WARRANTY_ON_HEALTH — D664: the owner's health page reminds him of a warranty

Session 292 (parent), 03-Oct-2026. Built on the owner's word "build." Companion to S466_EXPENSE_WARRANTY, and
independent of it: installed without S466, the health page is byte for byte what it was.

## What it does, in plain words

The owner's ruling: the inverter battery is a Dr MK expense, and the renewals list must remind him of the warranty
date. S466 keeps the warranty in the asset app. This kit makes the **Renewals row of `/finance/health`** say it while
the warranty is inside its own reminder window:

- more than 7 days left → the row is *info* (shown; does not colour the page or reach the portal tile);
- 7 days or fewer → the row is *warn* (reaches the portal tile line), reading e.g.
  `warranty: Inverter battery ends in 5 days (2026-10-08) · nothing inside 30 days · pushed …`;
- a renewal that is itself overdue or due soon keeps the row's state and its own words first; the warranty follows;
- a warranty that has ended, one set to "No reminder", and one whose paper left the Dr MK expense lane are never said.
  An ended warranty can never turn the row red.

## Files

| file | what |
|---|---|
| `apply_s467.py` | two insertions in `/root/finance/finance_app.py`: 49f52391 → 72d25382. Nothing removed. |
| `walk_s467.py` | old and new file through eleven situations, a made-up asset database, an empty finance database |
| `install_S467_WARRANTY_ON_HEALTH.sh` | gates → lock → pin → walk → the box's own asset database read once, read-only → backup → place → restart clinic-finance → checks → restore on red |

Writes nothing: no table, no file, no setting. `/root/assetapp/assets.db` is opened read-only (the way
`purchase_app.py` already opens it).

## Run

    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S467_WARRANTY_ON_HEALTH/install_S467_WARRANTY_ON_HEALTH.sh

## To take it back

    \cp -p /root/finance/finance_app.py.bak_S467_49f52391 /root/finance/finance_app.py && systemctl restart clinic-finance

## The three D664 kits on one line (S465, then S466; S467 whatever those two did)

    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S465_PAPERS_JOIN/install_S465_PAPERS_JOIN.sh && bash /root/deploy/repo/deploy_kits/S466_EXPENSE_WARRANTY/install_S466_EXPENSE_WARRANTY.sh ; bash /root/deploy/repo/deploy_kits/S467_WARRANTY_ON_HEALTH/install_S467_WARRANTY_ON_HEALTH.sh
