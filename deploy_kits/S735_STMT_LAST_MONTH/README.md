# S735_STMT_LAST_MONTH — make last month's statement first (D845 item 1)

*Built in the Scan App chat, session 395, 06-Nov-2026. Kit number from the board (`_numbers` v992 → v993).*

## Why
D845 asked for the Variety flow's first month to be checked end to end on the live page. Read-only, 06-Nov evening:

- B-0250 (05-Nov, three Clinic lines) and Variety's six earlier challans are sorted: 18 lines on 7 papers, all Clinic, all *unbilled*.
- Variety's phone is on the Vendors page, so *Send on WhatsApp* will work.
- **No statement has ever been made.** The page only offers **this** month's statement (November). That means October's could not be
  made on its own any more: November's would have taken every older line.

You confirmed (19:3x IST) that the six challans from 24-Aug to 14-Oct are all unpaid, so they belong on October's statement.

## What your Stationery page shows after this
In section 5 (*Monthly statement*):

- When last month has no statement (and this month has none either) and has lines waiting, the page shows
  **Make October 2026's statement**, with its line and paper count, and the note *"November 2026's comes after it."*
- Once that statement is made, the page is exactly as before. November's button comes back, carrying only November's lines.
- The statement is the same one S674 always made. It goes challan by challan in Variety's own numbers, marked *bill to: Clinic* or
  *bill to: NK Pathology*, and the August and September challans are marked *"earlier, not billed yet"*.

Nothing else changes: the table, the make door, the staff screen and the account are all as they were.

## Files
| file | from | to |
|---|---|---|
| `/root/assetapp/stationery.py` | 3a22c6bb (S674) | see `PIN_TO_stationery.txt` |

There are 6 counted edits (`edits_s735.py`), rebuilt on the box by `make_s735.py` and checked against the kit's whole file. There is no
table and no data step. Only `assetapp` is restarted. Read-only pins: `asset_register.py` (S731), `sorting_desk.py` (S732),
`clinic_papers.py`, `asset_machine.py`, `procroom.py`, `batteries.py`, `xray_costs.py`, `claude_reader.py`, `claude_reread.py`.

## Proof
- **App walk on the real app** (`walk_s735_app.py`, made-up suppliers *WALK735 …* and made-up dates): 10 of 10 green.
  - last month is offered first, and the page's own button makes it;
  - older lines are named earlier, and this month's line is left out;
  - once last month's statement stands, the page is as before;
  - nothing in last month means the page is as before;
  - if this month's statement already stands, no button returns;
  - the year's turn (December offered in January);
  - the make door is unchanged, and a second statement for the same month is still refused;
  - the staff screen still opens.
- **Its control on the live file:** 4 of 4 S735 checks red (the live page offers only the current month: the gap reproduced), and
  5 of 5 keep-checks green.
- **On the box** the installer runs the same walk on a copy of the live database. Its *LIVE SHAPE* line says, in counts only, what
  the page will offer today (expected: October 2026, 15 lines on 6 papers).
- **Rehearsal on a made-up root** (`rehearse_s735.sh`): 7 of 7.

## Install (the VPS, as root)
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S735_STMT_LAST_MONTH/install_s735.sh
```

## Undo
```
\cp -p /root/assetapp/stationery.py.bak_S735_3a22c6bb /root/assetapp/stationery.py && systemctl restart assetapp
```
