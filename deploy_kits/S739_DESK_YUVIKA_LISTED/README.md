# S739_DESK_YUVIKA_LISTED — Yuvika's slips and Variety's challans on the sorting desk (F-1159, D845 item 3)

*Built in the Scan App chat, session 398, 07-Nov-2026. Kit number from the board (`_numbers` v1012 → v1013). Your FINAL at 05:50 IST
on the mock-up https://claude.ai/artifact/RAA6esA8dF8Bi5ojdazUzo.*

## Why
- **F-1159:** on 06-Nov, Variety's challan B-0235 (all NK lines) was saved on the desk to NK Pathology. The paper moved to the NK lane
  and its line was lost. Variety's challans belong on the Stationery page, which sorts each line to the clinic or NK.
- **D845 (3):** Yuvika supplies the pharmacy on printed bills and the procedure room on handwritten slips (your word, 05:27 IST).
  The desk named her only as "a person always chooses".

## What the desk shows
- **A Variety challan** opened on the desk (by its number) shows a card: *sorted on the Stationery page*, with a button that opens it
  there. Its destinations and Save are off, and the server refuses a Save that would move it. If a second-scan question is open, its
  answer can still be saved; the paper then goes back to the Stationery page's To sort.
- **A challan whose supplier was misread**, and which you or Shavez pick as Variety on the desk: *Save — send it to the Stationery
  page*. It is filed under Stationery & packaging with no lines, and the Stationery page's To sort offers it.
- **Yuvika's papers** (only while the switch is ON):
  - her handwritten slip (no bill number) opens with **Procedure room** chosen and its lines ready;
  - her printed bill (it has a bill number) opens with **Pharmacy (Sanjeevni)** chosen;
  - with no number and no line read, two buttons: *Handwritten slip → Procedure room* or *Printed bill → Pharmacy*.
  These are only suggestions. Nothing moves until a Save. A place a person already gave the paper stays.
- **The switch** is *Yuvika slips on the desk*, on the Switches card of the scan app's home page. It is **installed OFF**; while it
  is OFF, Yuvika's papers open exactly as before.
- A Variety challan from before the Stationery page's start day (26-Oct) is sorted on the desk as before.

## Files
| file | from | to |
|---|---|---|
| `/root/assetapp/sorting_desk.py` | 52e959da (S732) | see `PIN_TO_sorting_desk.txt` |

There are 13 counted edits (`edits_s739.py`), rebuilt on the box by `make_s739.py` and checked against the kit's whole file. There is
no new table and no data step. Only `assetapp` is restarted. The read-only pins are `asset_register.py` (S737's TO), `stationery.py`
(S735's TO), `procroom.py`, `clinic_papers.py`, `asset_machine.py`, `batteries.py`, `xray_costs.py`, `claude_reader.py` and
`claude_reread.py`.

## Proof
- **App walk on the real app** (`walk_s739_app.py`, made-up rows): 20 of 20 green. Its control on the live file: 13 of 13 S739
  checks red (it reproduces F-1159: a Variety challan moved to the NK lane), with 7 of 7 guards green.
- **Page walk in Chromium on the real app** (`walk_s739_page.py`, at 1366 and 390 px): 17 of 17 green. Its control: 11 of 11 red, with
  4 of 4 guards green.
- **Rehearsal on a made-up root** (`rehearse_s739.sh`): 7 of 7.
- **Independent cold review:** round 1 SAFE TO INSTALL with 4 should-fix points (a kind pre-chosen from the reading could get past the
  refusal; a restore could move a paper someone had sorted to NK; papers you left on the Stationery page stranded; a second spelling of
  the supplier). All four are built and walked (V11, V12, K8). Round 2: SAFE TO INSTALL.
- **The installer** runs the app walk again on a copy of the live database, and its control on the live file, before anything is
  placed.

## Install (the VPS, as root)
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S739_DESK_YUVIKA_LISTED/install_s739.sh
```

## Undo
```
\cp /root/assetapp/sorting_desk.py.bak_S739_52e959da /root/assetapp/sorting_desk.py && systemctl restart assetapp
```
To undo only the Yuvika part, use the switch OFF.
