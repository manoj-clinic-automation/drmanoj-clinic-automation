# S627_LATE_FOLLOWS_MONTH — the 'late' mark follows the bill's-own-month rule; the desk states the rule

*Kit S627 claimed on the board `_numbers` v602 → v603 at the owner's "do all these" (15:49 IST 22-Oct-2026), the items S625 left.
Built, walked and rehearsed in the Scan App chat at session 337 — in the chat, not by the API-credit runner. **After S624 and S625.***

## What changes, as he will see it

- A paper scanned since S625 whose bill is dated in an earlier month (so it counts in that month) now carries the amber **late**
  mark for that month — on All papers, on its own page (*"late — belongs to 2026-07"*), and in the late number on the purchases
  page — the same mark a late bill has always had.
- The desk's *The month* page states the rule: *"… from 22-Oct-2026 a bill dated in an earlier month than its scan counts in its own
  month (a person's earlier month still wins) …"*.

## How

- `asset_register._set_late` — already run after every reading, every desk Save and every date or month change — also asks the one
  shared rule (`clinic_papers.MONTH_OF`, through S625's `_s625_counts`) and marks the paper late when the rule puts it in an earlier
  month than its scan, comparing with the scan month in IST (as the rule counts it).
- **The data step** (`heal_s627.py`, after the health checks, the database backed up first): papers scanned since S625's switch-on
  that were read before S627 get their mark now — it only fills an empty mark, never changes or clears one; with the rule off it does
  nothing; a re-run repeats it harmlessly (the ALREADY INSTALLED path runs it too).
- `sorting_desk.py` — one sentence of its *The month* page. `sorting_desk.py` stood at drift 8; it was read whole by the independent
  review before this publish (F-836).

## Files

| file | FROM | TO | edits |
|---|---|---|---|
| `/root/assetapp/asset_register.py` | f21ae7ca (S625's TO) | 2bb28600 | 1 |
| `/root/assetapp/sorting_desk.py` | 110335ea | 377adbca | 1 |

Read only, pinned: `clinic_papers.py` 89a3cd0a (S625's TO), S624's `batteries.py` b2cbb41e, `asset_machine.py` 7dbd5e0c,
`stationery.py` b6ce217a, and `xray_costs.py` 22e59f5a. **No database change.** Restarts `assetapp` only.

## Install — the owner's one server line (after his publish)

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S627_LATE_FOLLOWS_MONTH/install_s627.sh
```

Order: gates → lock → pins (both TO = ALREADY INSTALLED) → rebuild (`make_s627.py`, 2 counted edits) → TO pins → compile → the walk on
the REAL app with the TO files on a COPY of the live database, its control on the FROM files, and S624's and S625's real-app walks on
the new app → backups `<file>.bak_S627_<from8>` → place → read back → restart → `/healthz` 200, five pages 302, no part "NOT mounted"
→ the data step → `S627_LATE_FOLLOWS_MONTH: DONE`. Any failure after placing puts both files back, checks them against the FROM pins, and restarts.

## Undo

```
\cp /root/assetapp/asset_register.py.bak_S627_f21ae7ca /root/assetapp/asset_register.py
```
```
\cp /root/assetapp/sorting_desk.py.bak_S627_110335ea /root/assetapp/sorting_desk.py
```
```
systemctl restart assetapp
```

## Proven before the publish (in the chat, 22-Oct)

- `walk_s627_app.py` — the REAL scan app, all six parts mounted, made-up rows dated 2031: **12 green, 0 red** (with the rule off, the
  IST edge of the 1st, the 12-month limit, and the data step and its second run); its control on the FROM files: **the 4 must-red
  checks red**;
- an independent cold review K1 with the whole read of `sorting_desk.py` (F-836): SAFE TO INSTALL, 0 blockers, 2 corrections —
  made in place (the data step for papers read before S627; the IST scan month). Named, not changed: a month a person sets equal to the
  scan month cannot hold a back-dated bill there (S625's rule, his ruling); monthly suppliers' challans dated in an earlier month turn
  amber sooner on the desk and pre-tick only same-month bills (S625's rule at work);
- `rehearse_s627.sh` on a made-up root: **6 green, 0 red** (dry run, install, ALREADY INSTALLED, other bytes refused, S625 not first
  refused, health red after placing → both files back); S624's and S625's real-app walks green on the new app.

## Not built — the third item of "do all these"

Assets 7 and 12 (the two duplicate records retired 18-Oct) keep the 01 day their edit gave them: their true purchase days are in no
paper or record within reach (the live twin, asset 6, also reads 01-03-2026; no purchase bill of either is in the scan app). The
owner is asked for the two days; with them, they are typed on the machine's Edit page (S625 keeps a typed day from then on).
