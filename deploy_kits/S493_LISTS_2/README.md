# S493_LISTS_2 — the staff's "Aaj ka kaam" lists, rebuilt

Session 298 · 07-Oct-2026 · the parent's kit · **installed OFF**

## Why
The owner read the S487 lists and found them "confusing and complicated for the staff". His rulings of 06-Oct and the
mock-up he then edited with his own hand on 07-Oct:

1. A switch for each person and for each line.
2. The lists start from 1 October — nothing older.
3. One line = one job. No counts, no "late". The button opens the job itself.
4. His wording, his order, his groups.
5. A task section: work given from time to time, answered on the same page.
6. September, for him only.

## What it places
| file | what |
|---|---|
| `/root/finance/aaj_kaam.py` | replaced whole (S487 `d65e0bf4`). The engine. |
| `/root/finance/aaj_kaam.html` | replaced whole (S487 `03ccc58e`). The staff's page. |
| `/root/finance/aaj_seed.py` | new. His mock-up exactly as he left it, and each line's working. |
| `/root/finance/aaj_panel.html` | new. His panel. |

Not touched: `finance_app.py`, `owner_console.py`, `portal.py`, `aaj_duties.json`, `DUTY_MAP.json`. The five doors are the
five S487 already has. The installer writes no table and no setting.

## How it works
- **The floor.** `aaj_kaam.py` reads through its own read-only connection. On it, 22 dated tables are shadowed by TEMP
  views that hold only rows on or after the floor (`aaj_seed.FLOOR`; setting `aaj.from`, default 2026-10-01), so the duty
  map's SQL runs unedited. A view that cannot be laid makes every line that reads its table unread — never shown unfloored.
  Two tables are deliberately NOT shadowed (`purchase_order`, `purchase_bill`): another duty asks "is it already done?" of
  them, and a view would hide a 30-Sep answer to a 2-Oct question. The two duties that list them carry the floor in their
  own SQL (`aaj_seed.REWRITE`); if the duty map moves under that piece of SQL, the duty is unread.
- **The floor never makes work.** Where the floored books show something and the whole books show nothing, nothing is due.
- **The second guard.** A line whose oldest piece of work is dated before the floor is held back from staff, and his
  panel says so (`aaj_seed.NO_HOLD` names the four lines whose job is yesterday's, today's or this month's by nature).
- **The panel.** `https://followup.dr-manoj.in/finance/aaj`, the owner only. One document per person in the table
  `aaj_cfg` (made by his first change): on/off, each line's on/off, wording, group, order. A page can send a line's id,
  words, group and switch and nothing else; what decides a line is due, and the page it opens, come from `aaj_seed.py`.
  If the saved panels cannot be read, every list is off — what he switched off never comes back on by a fault.
- **The switch above them all** is S487's (`aaj.staff_on`). Off = no staff login sees anything. His panel's Start button
  and the console's own button both set it.
- **Tasks.** Tables `aaj_task`, `aaj_task_note` (made by the first task). The owner, or a login he names, gives; the
  person answers done / could not (with a reason) / a note; the giver closes, replies, or sends back with a word.
- **The owner's own lines** (person `manoj` in the duty map) keep S487's floor (01-Sep), except the clinic money flags and
  the physiotherapy days, which he ruled off for himself too. His console reads `build_all()` as before.

## The walk — `walk_s493.py`
Hermetic, through Flask's test client: a made-up clinic with the real tables (cut from the code's own CREATE TABLE
statements), then — with `--db` — a copy of `finance.db`, read only. On the build machine: 205 checks without `--db`,
217 with a stand-in database; green in Asia/Kolkata and UTC. Read three times by an independent agent; the page's
behaviour was walked in a real browser (not part of the kit). Negative controls: 1.0 itself is asked
the floor questions and must fail them.

    python3 walk_s493.py --kit . --finance /root/finance --dutymap /root/deploy/repo/claude_code_briefs/DUTY_MAP.json --code /root/finance --code /root/marg_ingest --old /root/finance/aaj_kaam.py --console /root/finance/owner_console.py --db /root/finance/finance.db

## Install (one line; the installer walks first and places nothing on red)

    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S493_LISTS_2/install_S493_LISTS_2.sh

`DRY=1` before `bash` walks and places nothing. Red after placing puts both files back and removes the two new ones.

## Known limits (said, not hidden)
- A weekly tap line begins with the first week that starts on or after the day the lists start; a monthly one with the
  first month. Started on a Wednesday, the weekly lines first show the next Monday.
- The two lines that ask the staff register's own door (`/portal/review-counts`) cannot be floored from here: that count
  belongs to the register.
- The console (not edited) still watches every duty of the map, whatever the panel's switches say, and does not show the
  lines the owner adds or the tasks. Its staff lines now count from 1 October.
- Darpan's two Vaapsi Desk lines are seeded OFF, with the reason on the panel: that page (the Sanjeevni chat's) still
  shows September. The ask is on the board.
- The pages a line opens are floored by the next kit, `S495_LIST_PAGE_FLOORS`.
