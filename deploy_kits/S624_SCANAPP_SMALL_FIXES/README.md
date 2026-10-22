# S624_SCANAPP_SMALL_FIXES — three of the S323 close's open faults (F-977, F-978, F-979)

*Kit S624 claimed on the board `_numbers` v595 → v596 at the owner's "do it" (14:50 IST 22-Oct-2026) on the next scan-app round.
Built, walked and rehearsed in the Scan App chat at session 337 — in the chat, not by the API-credit runner (his word, 14:07 IST).*

## What changes, as he will see it

| fault | where he sees it | before | after |
|---|---|---|---|
| **F-977** | Batteries — https://followup.dr-manoj.in/scanapp/batteries | a battery whose warranty has passed (and is not yet at its usual life) said **OK** | it says **Out of warranty since dd-mm-yyyy** in grey; *Due for replacement*, the 30-day warranty amber and *Bill awaited* are unchanged |
| **F-978** | a machine's page, folds *Cover history* and *Parts* | a cover or part saved without its paper could never be given one | a row with no paper has a small **B-____ link** box, as *Spends* already had; a voided cover and a removed part get none (and refuse one); a pharmacy paper, a patient's paper, a copy or a page is refused as before |
| **F-979** | the sorting desk's Save words; his Stationery page | 100 typed against *Token, plain (packet of 100)* went in as 100 packets with no word | the Save says *"Check: Token, plain: 100 saved, and the list counts it in 'packet of 100' — if the paper means 100 single pieces, type 1 instead and Save again."*; his Stationery page marks the item **check the quantity (B-____)** for this month's such lines. Only a line in pieces (or with no unit) whose quantity is a whole number of packets is questioned; a true purchase of that many packets can stand — the mark goes at the month's end |

The stock arithmetic does not change (F-979 warns; it never alters what was typed). The desk's own screen code (`sorting_desk.py`,
drift 8) is not touched, so the warning is in the Save's words rather than beside the line while typing.

## Files

| file | FROM (22-Oct bundle) | TO | edits |
|---|---|---|---|
| `/root/assetapp/batteries.py` | 775471e6 | b2cbb41e | 1 |
| `/root/assetapp/asset_machine.py` | 7d4fdffc | 7dbd5e0c | 6 (two new routes: `/assets/<id>/covers/<cid>/paper`, `/assets/<id>/parts/<pid>/paper`) |
| `/root/assetapp/stationery.py` | 18268ff0 | b6ce217a | 4 |

Read only, pinned (the installer stops if one moved): `sorting_desk.py` 110335ea, `asset_register.py` 70e35b10 (S618's TO),
`xray_costs.py` 22e59f5a, `clinic_papers.py` 6db07c12. **No database change.** Restarts `assetapp` only.

## Install — the owner's one server line (after his publish)

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S624_SCANAPP_SMALL_FIXES/install_s624.sh
```

Order: gates → the build lock → pins (all three at TO = ALREADY INSTALLED) → rebuild from the live bytes by `make_s624.py` (11
counted edits) → TO pins → compile → the walk on the TO files and the control on the live FROM files → the walk on the REAL app
(every part it mounts, from a scratch folder) on a COPY of the live database, and its control → backups
`<file>.bak_S624_<from8>` → place → read back → restart assetapp → `/healthz` 200, then `/stationery`, `/batteries`, `/assets/1`
302, the new cover-paper route 302 (proves the machine part mounted) and no "NOT mounted" in the scan app's log since the restart →
`S624_SCANAPP_SMALL_FIXES: DONE`. Any failure after placing puts all three files back, checks them against the FROM pins, and restarts.
`DRY=1` stops before the backups.

## Undo

```
\cp /root/assetapp/batteries.py.bak_S624_775471e6 /root/assetapp/batteries.py
```
```
\cp /root/assetapp/asset_machine.py.bak_S624_7d4fdffc /root/assetapp/asset_machine.py
```
```
\cp /root/assetapp/stationery.py.bak_S624_18268ff0 /root/assetapp/stationery.py
```
```
systemctl restart assetapp
```

A paper linked through the new boxes stays linked after an undo (the columns are S557's own); it is shown as before.

## Proven before the publish (in the chat, 22-Oct)

- `walk_s624.py` (the three files in a stand-in app, made-up rows only): **23 green, 0 red** on the TO files; the control on the
  FROM files: **all 11 must-red checks red**, the rest green;
- `walk_s624_app.py` (the REAL scan app, all six parts mounted, made-up rows): **8 green, 0 red**; its control on the FROM files
  **4 must-red red** (on the box it runs on a copy of the live database);
- an independent cold review K1 (in the chat): 1 BLOCKER (the `/assets/1` check could not prove the machine part mounted) and 4
  CORRECTIONS — all fixed in place: the route probe and the log check; the walk on the real app; a removed part refuses a paper;
  the packet check only questions lines in pieces, with plain wording, this month only, each paper once; the restore checks its bytes;
- `rehearse_s624.sh` on a made-up root: **6 green, 0 red** (dry run, install, ALREADY INSTALLED, other bytes refused, another
  build's lock refused and left, health red after placing → restored byte-identically);
- after S624, S623's installer would stop at its `stationery.py` pin rather than say ALREADY INSTALLED — expected (S623 is done).
