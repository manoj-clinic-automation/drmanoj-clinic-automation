# S687_DARPAN_MONTH_JOBS — Darpan's monthly jobs

*The parent, session 372 · 31-Oct-2026 · on the owner's rulings and his mock-up "Darpan monthly jobs" (31-Oct).*

## For the owner
Darpan's *Aaj ka kaam* gets the month's jobs, each opening its own screen (Roman Hinglish, phone-first, big buttons):
**Home medicines — ginti** (from the last 7 days of the month: what is left at home; the page works out what to order), **Gaadi ki jaanch**
(month end: each vehicle's papers, stepney, jack aur paana — Hai / Nahi), **Expiry ki safai** (month end: each expired line
of Sanjeevni's newest expiry list — supplier ko wapas / nasht kiya / shelf par nahi mila) and **Kaagaz ki yaad** (a vehicle
paper inside its reminder time). Your English page is `https://followup.dr-manoj.in/finance/monthjobs/owner`: this month
(done, waiting, who and when), the home-medicine list, the vehicles and the paper-dates grid (due in amber), the lead times
and the first months, the expiry outcomes. Every save opens on the Saved card. No rupee amount anywhere.

## The rulings, as built
- **Home medicines.** The list starts empty; only you add, edit or retire (name, unit, needed per month). The count is for
  the month of *today + 7 days* — in the last 7 days of a month, the next month. MANGWANA = max(0, needed − left), worked out,
  never typed. Darpan or you may save; a later save for the month supersedes, the earlier is kept (`mj_home_count`, append-only).
  Line `darpan.home_meds`: due when today ≥ (1st of that month − 7 days), the month ≥ setting `home.floor` (November 2026),
  an active medicine exists, and no count is saved for it. 24-Oct not due · 25-Oct due for November · 1-Nov still due · 24-Nov December's.
- **Vehicles.** Seeded Scooty, Bike, Kia, Wagon R, Vento; stepney and jack aur paana only on Wagon R and Vento; you add,
  rename, retire, and say whether a vehicle has the spare items. One Save per month; a "Nahi" is on your page.
  Line `darpan.vehicle_check`: from the LAST day of month M until a check for M is saved (M ≥ `vehicle.floor`, October 2026).
- **Paper dates.** You enter each expiry date (pollution, insurance, RC); a new date replaces the old, the old is kept
  (`mj_paper`). Lead times are settings: pollution 7 days, insurance 1 month, RC 45 days. A lead in months is clamped: insurance
  ending 31-Mar is reminded from 28-Feb (never later than one calendar month before; plain SQLite would say 03-Mar). Line `darpan.paper_renewal`:
  n = papers whose reminder day has come, since = the earliest. Darpan sees "Kia — insurance 15-Dec-2026 ko khatm · Naya
  kaagaz banwa kar Dr Manoj ko dijiye"; he cannot enter a date.
- **Expiry ki safai.** READ ONLY from `stock_expiry_run` (newest `ok=1`, as `expiry_watch.newest()` reads) and
  `stock_expiry_line` (`section='expired'`; columns `k20, item, batch, expiry, units`). Outcomes in `mj_expiry_outcome`,
  keyed by item (`k20`), batch and expiry. Line `darpan.expiry_clear`: from the last day of M (M ≥ `expiry.floor`, October
  2026) while an expired line has no outcome. Only lines with units on the shelf (> 0, as the watch counts them) and an
  expiry month up to M are M's job: a batch the watch lists from the 1st of its expiry month is next month-end's. The form is
  keyed by item, batch and expiry, so a new expiry run landing before Save loses nothing; an answer for a line no longer on
  the list is said on the screen, not dropped silently. Amir's `amir.expiry_writeoff` is not touched.

## Who reaches what
`/finance/monthjobs/...` is unit **medical** by `_unit_for_path` (its default): **darpan** maker, **manoj** its only
checker. The medical *viewers* (shavez, bhawna, amir, alisha, shivani) pass the front gate and are refused **403** inside the module (no
viewer's job here); a login with no medical row is sent to the portal (302) by the gate. Owner-only: every `/owner/...` post.

## What changes — four files (`make_s687.py`, 4 counted edits, each anchor found exactly once)
| live file | from → to | what |
|---|---|---|
| `/root/finance/finance_app.py` | 1dd66af3 → 9ce1b67f | ONE inserted mount block (`month_jobs`), after S579's |
| `/root/finance/aaj_duties.json` | 1d085d58 → 0adf1a84 | four `extra` duties for darpan (kind sql, one read-only SELECT each) |
| `/root/finance/aaj_seed.py` | 2121947f → 73b8556a | `darpan.paper_renewal` in NO_HOLD; Darpan's four panel lines, on |
| `/root/finance/month_jobs.py` | NEW → 33fa557f | the pages and the nine `mj_*` tables (made on the first request) |

**Before anything is placed:** the three FROM pins and the duty map's md5 (78b5f07e, what the walk's counts were built
against; a `git pull` that changed it is refused at [2/9]), then a database backup `finance.db.bak_S687_<stamp>`, mode 600.

**Data step** (`cfg_s687.py`, idempotent): the `mj_*` tables (so the four lines read at once:
F-1024, unread = 0) and, only if you have SAVED a panel for darpan, his new lines appended to it switched on (a line you
took off stays off). Restarts `clinic-finance` only. Not touched: DUTY_MAP.json, /root/assetapp, Sanjeevni's files.

**Intended writes to two existing tables of the parent's own:** every save on these pages adds a row to `audit_log` (the app's
own audit trail), and the data step updates Darpan's row in `aaj_cfg` if one exists (his saved Aaj panel). Nothing else
existing is written; no table's shape changes.

**The mount, proven:** without a login the front gate answers 302 for ANY path, a missing one too, so the 302 proves the gate.
The live process's own word is the journal (a failed mount prints `month_jobs NOT mounted`); the installer goes red on any line
naming month_jobs, an import error or a part NOT mounted since the restart, and the walk on the placed files loads the real app
from them with `_MOUNT_FAILED` empty.

## Proof (device VM, a copy of the 31-Oct database — never the cloud workspace, D656)
- `walk_s687.py` on a copy, the REAL finance app (Flask test client, header sign-in for that process only): **75 of 75 green**.
  47 S687 checks through the app (routes and roles; the Saved card after every save; every line's `(n, since)` at fixed days --
  home 24-Oct / 25-Oct / 1-Nov / 23-Nov / 24-Nov, vehicle 30-Oct / 31-Oct / 15-Nov / 29-Nov / 30-Nov, expiry 30-Oct / 31-Oct /
  15-Nov and a November batch not due 2-Nov or 29-Nov but due 30-Nov, a zero-units line never; papers at their lead times and
  insurance ending 31-Mar reminded from 28-Feb; a new expiry run landing between load and Save; Darpan's list whole, unread 0)
  · 9 builder checks · 4 list checks (every other person's Aaj list unchanged) · 15 mutants, each caught.
- **Control** on the live files: `42 S687 check(s) red . 5 green`. The walk on the placed files: `47 of 47 green`.
- `rehearse_s687.sh` on a made-up root: DRY green, nothing written · a forced red at [8/9] put all four
  files back (three at FROM, month_jobs.py removed), the database backup mode 600 · a journal naming `month_jobs NOT mounted`
  red at [7/9], all four back · install DONE, the placed walk 47 of 47 · a second run ALREADY INSTALLED · a changed duty map
  refused at [2/9] · a changed live aaj_seed.py refused at [2/9]; nothing written by either.

## Install
`cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s687kit && cp -rp /root/deploy/repo/deploy_kits/S687_DARPAN_MONTH_JOBS /tmp/s687kit && bash /tmp/s687kit/install_S687_DARPAN_MONTH_JOBS.sh`
(`DRY=1` before `bash`: every gate, the rebuild, the walk and the control; nothing written.)

## Undo
`\cp -p /root/finance/finance_app.py.bak_S687_1dd66af3 /root/finance/finance_app.py && \cp -p /root/finance/aaj_duties.json.bak_S687_1d085d58 /root/finance/aaj_duties.json && \cp -p /root/finance/aaj_seed.py.bak_S687_2121947f /root/finance/aaj_seed.py && rm -f /root/finance/month_jobs.py && systemctl restart clinic-finance`
(The `mj_*` tables stay; nothing reads them after the undo.)
