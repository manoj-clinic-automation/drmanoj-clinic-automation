# S487_AAJ_KA_KAAM — the staff's own daily list ("Aaj ka kaam")

**Session 294 (parent) · 05-Oct-2026 · D679 · the owner's word:** "Start staff lists build now, dont populate old stale data,
use from current month only, and the leftovers of September." (04-Oct: "Currently there is no flow for these daily tasks in
their apps, which should be prominent.")

## What it is

- **One screen per person, in Roman Hinglish** — `/finance/aaj`, opened from a new dark-blue tile at the top of the staff's
  home page ("Aaj ka kaam · N kaam baaki · M late"). Sections: *Sabse pehle* (yesterday's Docterz exports), *Aaj ka kaam*,
  *Raat ko*, *Is hafte*, *Is mahine*, and at the bottom what has nothing pending. Each line has **Kholiye** (opens the page
  where the job is done) or **Ho gaya** (a tap, for jobs the system cannot see: who tapped and when is kept).
- **The lines** are the duty map's own (`claude_code_briefs/DUTY_MAP.json`, D648 — its `due_sql`, its Hinglish, its door;
  the map is **not edited**) plus the parent's lines in `aaj_duties.json`: yesterday's two Docterz exports, the night
  reminders, the staff register's counts, Shavez's slip check and month-end checklist, Bhati's two petty-book taps, and the
  weekly / monthly taps (float, film stock, pathology register, cheque register, purchase orders, slip audit, new register).
- **The owner's console reads the same lines.** "Today's work" now shows one block per list (Alisha / Shivani share one),
  each opening that list as its people see it; the owner's own "Needs you" lines are cut from the same engine.

## Nothing stale (the owner's rule)

- **Nothing before 01-Sep-2026 is shown or counted** (`aaj_duties.json` `from`; the setting `duties.from` overrides it). The
  floor is laid **under** the map's SQL: the engine's own read-only connection carries TEMP views that shadow the dated
  tables (`clinic_day_revenue`, `clinic_money_flag`, `day_entry`), so the SQL runs unedited and sees only rows from the floor
  on. A duty that began later starts on its own first day (the counter sheet: 12-Sep).
- A line whose oldest item is older than the floor through a table the floor is not laid under is listed **without a count,
  a day or a "late"**; the owner's line says older items are in it.
- What the floor keeps off is **said** on the console ("N older items …"), never silent.
- **Weekly and monthly taps begin with the first week / month that starts on or after the day the lists are first turned on**
  — nobody is shown a week or a month that was already running.

## It installs switched OFF for staff

No tile, no list for any staff login until the owner taps **Turn on** on the console's "Staff lists" line. Until then he
opens each person's list from the console (**List** beside the name) and sees it as they will, with taps off. Turning off and
on again does not restart the week's and month's lines.

## A list that is not whole says so

A line that cannot be read, a duty map or a duties file that cannot be read: the page shows a banner, and neither it nor the
home tile ever says "Sab ho gaya". Without the duties file there is no floor, and then no line of the map is shown at all.

## How it reads and writes

Reading is plain SELECTs through a `mode=ro` connection to `finance.db`; each SQL must be one SELECT. A staff login asking
while the lists are off costs one read of one setting. Two writes exist, both through the service's own connection and both
JSON-only POSTs (a form posted from another site is refused): a tap → one row in `duty_tick` (made on the first tap; one row
per line and period; the first tap stands), and the owner's switch → `aaj.staff_on` (and once, `aaj.staff_first_on`).
**Nothing is written at install**: no table, no setting, no unit row, no timer job.

Access: the five doors are in `finance_app.IDENTITY_ONLY_PATHS` (exact paths; a signed-in login only) and `aaj_kaam.py`
decides by login name — your own list, your own tap lines; `?as=` and the switch for the owner only (the console's own gate).

## Files

| File | Pin |
|---|---|
| `/root/finance/aaj_kaam.py` — NEW | `d65e0bf4360f2ac2a6d4b3f6dd851dde` |
| `/root/finance/aaj_kaam.html` — NEW | `03ccc58e6a55c445570046558f485feb` |
| `/root/finance/aaj_duties.json` — NEW | `7aa29bef179bcbb4526c72c26fb58f17` |
| `/root/finance/owner_console.py` — 1.0 → 1.1 | `be5558160aebd4f58a159d50740c11c5` → `4819eceb527e2a62b9d17984d90b71c5` |
| `/root/finance/owner_console.html` | `75b5d01735c555a57d5be6ad75fffc07` → `e6d35d88b87890911124b9778a43c5d2` |
| `/root/finance/finance_app.py` — 4 edits (the five doors signed-in-only; one guarded mount; the health row's part list; 28 → 29) | `ef1382d2ce26d13d3c8388fdeb85e867` → `bff362c38ec61526ea0047fd136df826` |
| `/root/portal/portal.py` — 2 edits (the staff's tile; its script) | `10a675e750086b4bffc6b1b1e41ea8de` → `63df9d49672e19e878245b30c0455bef` |

Not touched: `DUTY_MAP.json`, every other page and door, `TILES`, `tile_grants.json`, the crontab, any table.

## Install — the server, one line

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S487_AAJ_KA_KAAM/install_S487_AAJ_KA_KAAM.sh
```

It walks first on copies of the box (its own code, its own database, made-up rows, the whole edited finance app), then reads
the real box read-only — the console as today and as the 15th, and every person's list as counts — and only then places the
seven files and restarts `clinic-finance` and `clinic-portal` (about 20 seconds). After placing it loads the placed app the
way the console's builder does and asks the app itself whether the list's doors are among its routes (the login gate answers
before routing, so a door behind it proves nothing). Red after placing puts everything back. `DRY=1` in front places nothing.

## Undo — the server, one line

```
\cp -p /root/finance/finance_app.py.bak_S487_ef1382d2 /root/finance/finance_app.py && \cp -p /root/portal/portal.py.bak_S487_10a675e7 /root/portal/portal.py && \cp -p /root/finance/owner_console.py.bak_S487_be555816 /root/finance/owner_console.py && \cp -p /root/finance/owner_console.html.bak_S487_75b5d017 /root/finance/owner_console.html && rm -f /root/finance/aaj_kaam.py /root/finance/aaj_kaam.html /root/finance/aaj_duties.json /root/finance/console_reading.dat /root/finance/console_reading.dat.lock /root/finance/console_reading.dat.err && systemctl restart clinic-finance clinic-portal
```

The settings `aaj.staff_on` / `aaj.staff_first_on` and the table `duty_tick` (if a tap was ever made) are left; nothing reads them once the files are gone.

## Proof

- `walk_s487.py`: 143 checks on the scratch box (05-Oct 01:35 code and database + S481's four files). S481's checks of the
  console stand (every figure against its owning module, made-up rows, no patient in a reading), moved onto the floor. New:
  **the floor proven the other way** — every duty counted under the module's views equals the same SQL run on a copy with the
  old rows DELETED; a made-up row dated on the floor's own day counts and one of 2019 does not; who sees which queue; off / on
  / the switch; a tap (own line, once, the first stands, a form post refused); the weekly and monthly start rule on fixed days;
  off-and-on keeps the first-on day; a line that cannot be read, a line behind the floor, a missing map, a missing duties file;
  'late' on the map's own rule; the console's staff lines are the lists' lines; the installer's mount proof says yes for the
  edited app and no for the app as it is.
- Negative controls, each red on its own check: see `MUTANTS.txt` in the evidence folder (29 mutants).
- Every person's list, the staff tile and the console were read on screenshots by sub-agents (two passes); an independent code
  review found access control sound and its two high findings (a line that cannot be read was silence; a missing duties file
  served the map unfloored) and the rest are taken in.

## Not in this kit

- The loud notification on punch, stand-ins / "away", the Docterz-export lock; the attendance month-end sheet flow; approving
  inside the console. The parent's extra lines are offered to `DUTY_MAP.json` at the session's close.
- 'Late' is the duty map's own rule (late on the day its allowed days are used up) — one rule on the staff's list and on the
  owner's console.
