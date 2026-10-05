# S481_COMMAND_CONSOLE — the owner's Today tile and command console

**Session 294 (parent) · 05-Oct-2026 · the owner's word:** "a small informative tile at top of my pwa, clickable and
expandable … who and when the exports and entries were done for the day, what all is pending where … the daily revenues …
anything I need to review, approve … all collapsible, expandable sections, down to granular details, across sanjeevni,
docterz, attendance, scanapp … this tile should lead to my command console type of page." Mock-up approved the same morning
("mock-up seems okay to build. Go ahead.").

## What it is

- **The Today tile** at the top of the Clinic app's home page, for the owner's login only: the clinic's last day and its
  word (matched / flags / not filled), Sanjeevni's last day, how many things wait for him, how many staff duties are late and
  how many are in today, the feeds' freshness, and "as of HH:MM". It is hidden until its own door answers, so for every other
  login, and with clinic-finance down, the home page is exactly as before.
- **The command console** at `/finance/console`: seven sections, each collapsed to a count and a word, each line opening
  the page that owns it — *Needs you · Money · Today's work · Attendance · Sanjeevni · Scans & papers · System*.

## What it reads — it computes nothing of its own

| Section | The owner of the figure |
|---|---|
| Needs you | the duty map's own `due_sql` for the owner (`claude_code_briefs/DUTY_MAP.json`, D648), each in the map's own owner's words; detail from `slip_adjust.pending`, `clinic_money.owner_queue`, `darpan_kal_day`, `day_entry` |
| Money | `clinic_money.match_day`, `clinic_register`, `bank_mpr_status.mpr_state`, `sanjeevni_cash.days`, `darpan_kal`, `packs.statement_road`, `packs.cells` |
| Today's work | `docterz_export`, `clinic_register_day`, `day_entry`, `darpan_kal_day`, `mi_file`, `petty_entry`; then the duty map again, person by person, with today's punch |
| Attendance | `/root/att_core.py` (`compute_day`) on the attendance system's own files; the usual first punch = the median of the last 30 days; the salary month's lock from the staff register (read-only) |
| Sanjeevni | `sanjeevni_approvals.needs_you` — the approvals page's own list, line for line |
| Scans & papers | the asset app's `bills` (read-only), `records.check_line`, `slip_log.pending_counts`, `slip_log.match_day` (counts only), the reception PC's heartbeat |
| System | `freshness.json`, the reception PC's heartbeat; the health line is filled by the page from the existing `/finance/api/tile-summary`, the staff register's count from `/portal/review-counts` |

## How it cannot write

Several of those readers write (they create tables, keep counters, refresh a cached figure), so **none is ever called on the
live connection**. The page asks for a reading; a **separate short process** (`owner_console.py --build`) copies `finance.db`
with SQLite's own backup through a read-only door into a private temp folder, points `FINANCE_DB` at the copy **before** any
module of the app is loaded, calls the owners on the copy, writes one file (`/root/finance/console_reading.dat`, mode 600)
and deletes the copy. The service only ever reads that file. Every reading says which database the app's modules saw
(`guard`). A reading older than five minutes is replaced in the background when the tile or the page asks — **no timer job**.
One builder at a time; a failed build says so on the page and is not retried for a minute; a killed one is taken over.

**No patient in the reading.** Where an owner's answer carries a patient's name, clinic ID, phone or a bank reference (the slip
match, the bank pairs, a flag's sentence), only its count, code and amount are taken. The file is not named `*.json` because the
nightly code bundle takes every `/root/finance/*.json` to Drive.

## Files

| File | Pin |
|---|---|
| `/root/finance/owner_console.py` — NEW | `be5558160aebd4f58a159d50740c11c5` |
| `/root/finance/owner_console.html` — NEW | `75b5d01735c555a57d5be6ad75fffc07` |
| `/root/finance/finance_app.py` — 3 edits (one guarded mount; the health row's part list; 27 → 28 parts) | `47a83382595c59f42b80d2f72831837d` → `ef1382d2ce26d13d3c8388fdeb85e867` |
| `/root/portal/portal.py` — 2 edits (the tile above the doctor-only strip; its script) | `d9b7685f75926164df34a10eca5dcb77` → `10a675e750086b4bffc6b1b1e41ea8de` |

Not touched: every other page and door, `TILES`, `tile_grants.json`, the crontab, any table.

## Install — the server, one line

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S481_COMMAND_CONSOLE/install_S481_COMMAND_CONSOLE.sh
```

It walks first on copies of the box (its own code, its own database, made-up rows), then makes one reading of the real box
read-only — once as today and once as the 15th of the month would read — and only then places the four files and restarts
`clinic-finance` and `clinic-portal` (about 15 seconds). Red after placing puts everything back. `DRY=1` in front places nothing.

## Undo — the server, one line

```
\cp -p /root/finance/finance_app.py.bak_S481_47a83382 /root/finance/finance_app.py && \cp -p /root/portal/portal.py.bak_S481_d9b7685f /root/portal/portal.py && rm -f /root/finance/owner_console.py /root/finance/owner_console.html /root/finance/console_reading.dat /root/finance/console_reading.dat.lock /root/finance/console_reading.dat.err /root/finance/console_build.log && systemctl restart clinic-finance clinic-portal
```

## Proof

- `walk_s481.py`: 94 checks on the scratch box (05-Oct 01:35 code and database): the edits; the builder leaves the database
  it read byte-identical; every figure against its owning module asked directly in a second process; made-up rows move the reading
  by exactly that; a made-up patient name put where the owners keep names is in no reading; none of the phone numbers and bank
  references the database holds is in a reading; the service's part (owner only, one builder at a time, a dead lock taken over,
  an old reading shown with its date, a failed build said and not looped).
- Negative controls, each red on its own check: the builder writing its source; `FINANCE_DB` not pointed at the copy; a flag's
  sentence or the owner queue's sentence let into a line; a bank pair let into a line; the owner's count off by one; the wrong
  sale field; the state door left open; the lock ignored; the copy left behind; the file written 644; an old reading labelled
  as today's; the tile not hidden / shown to every role; the fallback removed; the duty map read before the approvals tree
  (a stale cached returns count); no wait after a failure.
- The page and the tile were read on screenshots (phone light and dark, desktop) by two sub-agents; an independent code review
  found no high defect and its ten findings are taken in.

- **05-Oct 18:0x IST, the first server run: the walk went RED on one check (D8b) and nothing was placed.** The fault was the walk's:
  D8b and C11 asked only that each of the owner's counts appear in *some* line, and the line "Last month's purchases not finalised"
  carries no count — on the scratch box another line happened to hold a lone "1", on the server none did. Reproduced on a copy with one
  more unconfirmed petty entry, then corrected: each line is now compared with the duty map's own owner's line filled with the count
  and date the owner's SQL gives (C11, C13b for the staff's lines, D8b). Three more negative controls (a wrong count, a wrong date, a
  dropped staff line) are red. The four files this kit places or edits did not change.

## What this kit is not (the next two kits)

- The staff's own "Aaj ka kaam" lists, the punch-triggered notification, stand-ins, the Docterz-export lock, the attendance
  month-end sheet flow and Bhati's petty list — the duty ledger, built on this same duty map.
- Approving from inside the console (and Shavez-then-owner two-stage approval). Here every line opens the page that owns it.
