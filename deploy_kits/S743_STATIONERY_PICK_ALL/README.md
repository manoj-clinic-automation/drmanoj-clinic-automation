# S743_STATIONERY_PICK_ALL — a box holding a name not on the list still lists every product (F-1160, its follow-up)

*Built in the Scan App chat, session 398, 07-Nov-2026. The live read of S741 at 07:0x IST found the gap; kit number from the board
(`_numbers` v1020 → v1021).*

## Why
Most lines arrive with the reader's name already in the product box. When that name is not on the list (B-0250's first line reads
"A4 Ream"; the product is "A4 paper (75 gsm)"), S741's list showed only *"… is not on the list"* and no product to pick.

## What the pages show
- Tap such a box: the note comes first, then **every product**, the nearest by shared words first (15 at a time). One tap picks
  the right one.
  - The note on your page: *"… is not on the list — it is added on Save — or pick one below"*.
  - On Shavez's page: *"… ya neeche se chunein"*.
- A box whose text matches products lists those products, as before. The unit box does the same: if nothing matches, it lists every
  unit.
- No server rule changes.

## Files
| file | from | to |
|---|---|---|
| `/root/assetapp/stationery.py` | S741's TO (`PIN_FROM_stationery.txt`) | `PIN_TO_stationery.txt` |

There are 2 counted edits (`edits_s743.py`), rebuilt on the box by `make_s743.py`. There is no data step. Only `assetapp` is
restarted. The read-only pins are the same as for S741.

## Proof
- **Page walk in Chromium on the real app** (`walk_s743_page.py`, at 1366 and 390 px): 20 of 20 green. Its control on S741's file:
  3 of 3 red (it reproduces the live finding), 9 of 9 guards green.
- **App walk** (`walk_s743_app.py`): 6 of 6 green.
- **Rehearsal** (`rehearse_s743.sh`): 7 of 7.
- **Independent cold review:** SAFE TO INSTALL.

## Install (the VPS, as root)
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S743_STATIONERY_PICK_ALL/install_s743.sh
```

## Undo
```
\cp /root/assetapp/stationery.py.bak_S743_8f85815d /root/assetapp/stationery.py && systemctl restart assetapp
```
