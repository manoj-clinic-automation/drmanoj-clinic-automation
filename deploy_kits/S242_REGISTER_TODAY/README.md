# S242_REGISTER_TODAY — the daily register opens on TODAY

**The owner, 12-Sep-2026:** *"its showing of 11 sept, shd be of today, to be used at end of day."*

## What was actually wrong — read from the screen's own code, not guessed

`register_index` in `clinic_register.py` builds its list of candidate days from one table:

```
SELECT business_date FROM clinic_day_revenue ORDER BY business_date DESC LIMIT 45
```

That table is **Docterz's** record of a day, and Docterz sends a day *after* it has happened. So at
the hour this screen is used — the end of the day — the newest day the code can see is **yesterday**,
and yesterday is the day it redirected to. Nothing was broken. The screen was reading a record that
does not know about today yet.

The register is the counter's own record. It does not wait for Docterz.

## The change

One helper, `_with_today(days)`, used at two call sites:

| route | before | after |
|---|---|---|
| `/finance/clinic/register` | opened the newest **Docterz** day that was unfilled | opens **today** when today is unfilled |
| `/finance/clinic/register/list` | "all days" could not show today | lists today too, so a filled today is visible |

**Nothing else moves.** Not the gate (`_require("maker","checker", unit="clinic")`), not a table, not
the day page, not the drawer count, not the three-record comparison. Once today has been filled,
*next unfilled day* walks back through the older unfilled days exactly as it did before.

The day page needed no change: it already accepts any valid ISO date (`_iso_ok`), and a day Docterz
has not sent reads as **not known** rather than as zero — `docterz_day` returns `known=False` and
`bank_upi` returns `(None, False)`. That is the existing design, and it is why today renders right.

## Pins

| | |
|---|---|
| from | `93a31e68234df066776b7b80ef65ffbd` (S223 drawer-count build, live since 04-Sep) |
| to | `c6b87682ccbfb03734a39ad33c26f2a3` |

The installer refuses unless the box is on the from-pin, and restores it if the service does not
come back.

## Proof

`EVIDENCE_walk_S242.txt` — a **live-shape walk**, not a simulation of the logic: the patched module
is mounted on a real Flask app exactly as `finance_app` mounts it, against a real sqlite database
shaped like the real one (Docterz knows yesterday and the day before, and does **not** know today).
Six checks, all green:

1. nothing filled → the index opens **today**, not yesterday
2. today's page renders, other two records read *not known* rather than zero, no traceback
3. today filled → the index falls back to the next unfilled day (yesterday)
4. *all days* lists today
5. a refused user still gets the denial, not a day — the gate is untouched
6. a day Docterz *does* know still renders — nothing regressed

The same walk is run **again on the box**, against the box's own python, before a single file is
copied. `patch_clinic_register_today_s242.py` is shipped for provenance — it is the exact,
anchored edit that turned the live bytes into this file, and it refuses on any anchor that does not
match exactly once. The installer does not use it; it lays down the full file.

## Install — one line on the VPS, after the publish

```
bash /root/deploy/vps_deploy.sh S242_REGISTER_TODAY
```
