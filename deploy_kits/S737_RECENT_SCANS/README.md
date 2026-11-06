# S737_RECENT_SCANS — recent scans by scan date (D845 item 2)

*Built in the Scan App chat, session 395, 06-Nov-2026, on your **final** (20:24 IST) of the mock-up
https://claude.ai/artifact/KfzGHJFyPdnMsgqEmC8EdD. You did not edit it, so the mock-up as drawn is the specification. Kit number
from the board (`_numbers` v998 → v999).*

## What it adds — installed SWITCHED OFF
Nothing on any page changes until you switch it on at **Admin → Recent scans by scan date → Switch ON**.

When ON:
- **The scan app's home page** (yours and Shavez's) shows three counts first: *On the desk*, *Scanned today*, and
  *Read failed — scan again*. Below them is the **Recent scans** card:
  - papers are listed newest scan first, grouped by the day each was scanned, whatever date is printed on the paper;
  - you can show **7 / 14 / 30 days** (14 to start);
  - you can filter to **All · Needs someone · Clinic · NK · Dr MK · Pharmacy**;
  - each row shows the time, stamp, supplier, kind, lane and **where it sits now**, plus *Open*, which goes to the paper's own door.
- **All papers** lists the newest scan first, with a **Scanned** column (IST) and a **Where it sits** column. The **Bill date**
  button gives today's order back.
- **Shavez never sees a Personal paper.** This is the same rule All papers already follows.

*Where it sits*, in order:
- *Second scan* / *Set aside*
- *Read failed — scan again*
- *Filed (pharmacy)* / *Pharmacy — not filed yet*
- *On the desk — waiting* (the desk's own list)
- *Stationery page* (a listed supplier)
- the section it was sorted to (*Procedure room*, *Stationery & packaging*, *Implant stock*, …)
- *Accepted* / *Filed* / *Not accepted yet*

The scan time is the moment the paper was saved, in IST. This uses the same rule *The month* already uses.

## Files
| file | from | to |
|---|---|---|
| `/root/assetapp/asset_register.py` | 5f44f65e (S731) | see `PIN_TO_asset_register.txt` |

There are 15 counted edits (`edits_s737.py`), rebuilt on the box by `make_s737.py` and checked against the kit's whole file. There is
no table, no column and no data step; it only reads, apart from the switch itself. Only `assetapp` is restarted. Read-only pins:
`stationery.py` (S735), `sorting_desk.py` (S732), `clinic_papers.py`, `asset_machine.py`, `procroom.py`, `batteries.py`,
`xray_costs.py`, `claude_reader.py`, `claude_reread.py`.

## Proof
- **App walk on the real app** (`walk_s737_app.py`, made-up papers *Z-2031-7…* at made-up times, an owner login and a manager
  login): 14 of 14 green.
  - switched off, both pages are as before, including All papers' order;
  - the switch card works;
  - the home card's day groups follow IST, so a paper scanned at 01:30 IST counts as that day's;
  - the order is newest first and the three counts are right;
  - the row words are right for the desk, pharmacy, set aside, read failed, Procedure room and Dr MK;
  - 30 days, *Needs someone* and *Pharmacy* each show the right papers;
  - Shavez's login never shows a Personal paper;
  - All papers lists newest scan first, with the IST time;
  - a confirmed second scan that the desk lists reads *On the desk — waiting*;
  - a listed supplier's challan reads *Stationery page*;
  - Shavez's All papers, with the switch on, never shows a Personal paper;
  - *Bill date* gives back today's order;
  - the desk, the Stationery page and the intake still open.
- **Its control on the live file:** 11 of 11 S737 checks red, and 3 of 3 keep-checks green.
- **Switched off, both pages are byte-for-byte today's:** the home page and All papers rendered by the old and new files are
  identical (same md5).
- **An independent cold review** found it SAFE TO INSTALL, with no blockers. Its should-fix points are built in: the desk's own
  list is read first and built once per page, the supplier list is read once per page, the Bill date order is kept through a
  search, and a Document paper's kind shows correctly.
- **Rehearsal on a made-up root** (`rehearse_s737.sh`): 7 of 7.

## Install (the VPS, as root)
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S737_RECENT_SCANS/install_s737.sh
```

## Undo
```
\cp -p /root/assetapp/asset_register.py.bak_S737_5f44f65e /root/assetapp/asset_register.py && systemctl restart assetapp
```
(Or simply switch it OFF on Admin; the pages are then exactly as before.)
