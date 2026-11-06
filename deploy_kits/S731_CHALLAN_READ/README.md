# S731_CHALLAN_READ — a challan is read on any lane (F-1136)

*Built in the Scan App chat, session 392, 06-Nov-2026. Kit number from the board (`_numbers` v976 → v977).*

## Why
B-0250, a Variety Stationers challan scanned 05-Nov 15:10 IST, said **read failed** and nothing explained it. The box's own record
(read 16:5x IST 06-Nov): the reader was on and worked that day (20 reads), but B-0250 has no reading and no retry. It was scanned with
the **Challan** button on the **Other document** lane ("bill nahi"), and that lane is never put to Claude; Sarvam is off, so the paper
was marked failed at once. The desk moved it to the clinic lane at 08:51 on 06-Nov, but the move did not read it. It was read only
when *Read it again* (S715) was pressed at 11:11. B-0234 (27-Oct) has the same record.

## What changes (nothing on any screen)
1. A **challan** is read by Claude whichever lane reception pressed, Other document included. Letters, forms, resumes, the Personal
   section and patients' papers on that lane stay unread, as before.
2. After the desk's **Save** or the **lane button**, a paper that was **never put to Claude** and says *read failed* is read once,
   by itself, in the background. Only empty fields are filled. A paper Claude has already tried (for example a photo too large) is
   not tried again this way; *Read it again* stays for that.

## Files
| file | from | to |
|---|---|---|
| `/root/assetapp/asset_register.py` | 63a8b15b | see `PIN_TO_asset_register.txt` |
| `/root/assetapp/sorting_desk.py` | 4990350b | see `PIN_TO_sorting_desk.txt` |

There are 3 counted edits (`edits_s731.py`), rebuilt on the box by `make_s731.py` and checked against the kit's whole files. There is
no data step and no new table. Only `assetapp` is restarted. Read-only pins: `clinic_papers.py`, `asset_machine.py`, `procroom.py`,
`batteries.py`, `xray_costs.py`, `claude_reader.py`, `claude_reread.py`, `stationery.py`.

## Proof
- **Walk on the real app** (`walk_s731_app.py`, made-up rows, Claude replaced by a stand-in): 13 of 13 green.
- **Control on the live files:** all 6 S731 checks red (V2 reproduces B-0250 exactly: *failed*, never put to Claude); all 7 guards
  green.
- **Rehearsal on a made-up root** (`rehearse_s731.sh`): 7 of 7 — dry run, install, already installed, a moved file refused, the
  lock, health red restores both files, a moved read-only file refused.

## Install (the VPS, as root)
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S731_CHALLAN_READ/install_s731.sh
```

## Undo
```
\cp /root/assetapp/asset_register.py.bak_S731_63a8b15b /root/assetapp/asset_register.py && \cp /root/assetapp/sorting_desk.py.bak_S731_4990350b /root/assetapp/sorting_desk.py && systemctl restart assetapp
```
