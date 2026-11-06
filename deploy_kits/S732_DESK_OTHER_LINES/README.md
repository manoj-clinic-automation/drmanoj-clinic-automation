# S732_DESK_OTHER_LINES — Other lines on the sorting desk (D838, its second kit)

*Built in the Scan App chat, session 392, 06-Nov-2026. Kit number from the board (`_numbers` v979 → v980).*

## Why
At 17:19 IST on 06-Nov you asked for D838's deferred second kit: X-ray film lines and Others lines on the desk. At 17:25 you added:
*"check whether anything is really required for the X-ray part."* I checked it live:

- all 11 film bills since April (Jugnu Medicos: 10 boxes of 8×10, 1 of 11×14) were read with their size and box count;
- the film log shows none as *size unknown* and none held;
- the X-ray costs page shows none as *size not read*.

So there are **no X-ray film lines**; only the **Other lines** are built, on your approved mock-up
(https://claude.ai/artifact/XpbAyqQAyCimRnv3dz1ECm).

## What the desk shows
- A paper sorted to **Others** gets **Other lines**: what it is, quantity, unit and rate on each line, *+ Add a line*, × to remove,
  each line's amount, and the lines' total against the paper.
- The panel starts from what was read. A line with a quantity but no name says *what is it?*.
- Only when the panel is **changed** does the Save write these lines as the paper's own item lines. The first reading stays on
  record, and the change is audited (`desk_lines`).
- Nothing changes for X-ray film papers, Stationery, the Procedure room, pharmacy papers or a person's papers.

## Files
| file | from | to |
|---|---|---|
| `/root/assetapp/sorting_desk.py` | d2742ded (S731) | see `PIN_TO_sorting_desk.txt` |

There are 9 counted edits (`edits_s732.py`), rebuilt on the box by `make_s732.py` and checked against the kit's whole file. There
is no new table and no data step. Only `assetapp` is restarted. Read-only pins: `asset_register.py` (S731's TO), `clinic_papers.py`,
`asset_machine.py`, `procroom.py`, `batteries.py`, `xray_costs.py`, `claude_reader.py`, `claude_reread.py`, `stationery.py`.

## Proof
- **App walk on the real app** (`walk_s732_app.py`, made-up rows): 11 of 11 green.
- **Its control on the live file:** 7 of 7 S732 checks red, 4 of 4 guards green.
- **Page walk in Chromium** (`walk_s732_page.py`, a stand-in server with made-up data): 16 of 16 green.
- **Its control:** 10 of 10 red, 6 of 6 guards green.
- **Rehearsal on a made-up root** (`rehearse_s732.sh`): 7 of 7.

## Install (the VPS, as root)
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S732_DESK_OTHER_LINES/install_s732.sh
```

## Undo
```
\cp /root/assetapp/sorting_desk.py.bak_S732_d2742ded /root/assetapp/sorting_desk.py && systemctl restart assetapp
```
