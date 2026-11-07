# S741_STATIONERY_PRODUCT_PICK — the product box on the Stationery page (F-1160)

*Built in the Scan App chat, session 398, 07-Nov-2026, at your "yes" of 06:35 IST. Kit number from the board (`_numbers` v1016 →
v1017).*

## Why
On 06-Nov you found that the product box on the Stationery page does not open its list on your device; only typing worked. It was a
browser "datalist", which some phones and tablets never show.

## What the pages show
- **Each product box** on the sorting form works like the supplier box on the sorting desk. Tap it, or type a few letters, and the
  matching products drop down; one tap picks one.
  - If you type a name that is not on the list, the list says so: *"… is not on the list — it is added on Save"* (on Shavez's page,
    *"Naya saamaan … Save par list mein judega"*). It is added on Save, exactly as today.
- **The unit box** works the same way (ream, piece, pack, box…).
- These forms change: your Stationery page (To sort, and Change on a sorted paper) and Shavez's Stationery sort page. Nothing else on
  them changes, and the server's rules do not change.

## Files
| file | from | to |
|---|---|---|
| `/root/assetapp/stationery.py` | 2abbc10a (S735) | see `PIN_TO_stationery.txt` |

There are 2 counted edits (`edits_s741.py`), rebuilt on the box by `make_s741.py` and checked against the kit's whole file. There is
no data step and no table. Only `assetapp` is restarted. The read-only pins are `sorting_desk.py` (S739's TO), `asset_register.py`,
`procroom.py`, `clinic_papers.py`, `asset_machine.py`, `batteries.py`, `xray_costs.py`, `claude_reader.py` and `claude_reread.py`.

## Proof
- **App walk on the real app** (`walk_s741_app.py`, made-up rows): 6 of 6 green. Its control on the live file: 4 of 4 red, 2 of 2
  guards green.
- **Page walk in Chromium on the real app** (`walk_s741_page.py`, at 1366 and 390 px): 18 of 18 green. This includes typing two
  letters, the one-tap pick, a new name, the unit box, and a Save that records the picked product. Its control: 9 of 9 red, 9 of 9
  guards green.
- **Rehearsal on a made-up root** (`rehearse_s741.sh`): 7 of 7.
- **Independent cold review:** SAFE TO INSTALL. Its one should-fix is built: the list touches only the sorting form, and the unit
  boxes of the item list stay as they were (K5).

## Install (the VPS, as root)
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S741_STATIONERY_PRODUCT_PICK/install_s741.sh
```

## Undo
```
\cp /root/assetapp/stationery.py.bak_S741_2abbc10a /root/assetapp/stationery.py && systemctl restart assetapp
```
