# S495_LIST_PAGE_FLOORS — the lists' floor, on the pages the lists open

Session 298 · 07-Oct-2026 · the parent's kit · second half of the lists ruling

## Why
The owner, 06-Oct: the staff's lists start from 1 October, and staff must not see September "on the list or on the page a
line opens". `S493_LISTS_2` laid the floor under the lists. Four of the parent's pages that a line opens still listed
September: the counter sheet's day list, Check karein, Report baaki, and the physiotherapy tick card of the petty book.

## What it places
| file | what |
|---|---|
| `/root/finance/aaj_floor.py` | new. `floor_for(con, require)` — the day, or `None`. Reads two setting rows. |
| `/root/finance/clinic_register.py` | `eaaea278` → edited: the list of days (2 places, 1 helper) |
| `/root/finance/records.py` | `6492135c` → edited: Check karein's open items (1 place, 1 helper) |
| `/root/finance/slip_log.py` | `caef39f6` → edited: Report baaki's four lists (1 place, 1 helper) |
| `/root/finance/petty_book.py` | `698c988e` → edited: the physiotherapy card's 14 days (1 place) |

The edits are made on the box by `apply_s495.py` from exact anchors on the real bytes; each result must be the md5 the
kit was built to (`apply_s495.py --pins`).

## The rule
`floor_for` gives a page a day only when **all** of these hold: the login is not a doctor and not the owner (checker of
unit `packs`), the lists are started (`aaj.staff_on`), and the day can be read (`aaj.from`, default 2026-10-01). Otherwise it gives
`None` and the page is byte for byte what it is today. So:

- until the owner presses Start, nothing changes on any page;
- the doctors' view of every page is whole, always;
- a page never fails, and never hides work, because its floor could not be worked out.

Not touched: any money figure, the doctors' own line and counts (`check_line`, `pending_counts`), any write path, a day
or an item opened by its own address.

## The walk — `walk_s495.py`
Each page is asked twice through Flask's test client — of the file as it is live (loaded under another name) and of the
edited file — on one database, as the same login, and the answers compared. 68 checks on a made-up clinic; with `--db`,
16 more on a copy of `finance.db` with the lists marked started on the copy (counts only are printed).

## Install (one line; S493 first)

    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S493_LISTS_2/install_S493_LISTS_2.sh && bash /root/deploy/repo/deploy_kits/S495_LIST_PAGE_FLOORS/install_S495_LIST_PAGE_FLOORS.sh

## Not in this kit
The Vaapsi Desk and the bill-gap card on Aaj ki reports are the Sanjeevni chat's pages; the ask is on the board
(`aaj_floor.floor_for` is there for them to call).
