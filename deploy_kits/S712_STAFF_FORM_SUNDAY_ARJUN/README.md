# S712_STAFF_FORM_SUNDAY_ARJUN — the Add staff form's Sunday choice, and Arjun's pay · the parent · session 389 · 06-Nov-2026

**For the owner, in two lines.** The Add staff form's Sunday choice now reads only **Works every Sunday** (with his hours) or **Sunday off**: the salary has only ever read those two. Arjun moves to ₹3,500 a month from November. His 4 offs, his uncounted late minutes and his every-day duty were already set, and they stay as they are.

## Why
- **F-1125** (minted at S385). The form offered *1st and 3rd* / *2nd and 4th Sunday*, with *1st and 3rd* already chosen, and said *"A 5th Sunday is a normal full day for everyone."* The Sunday rota (D253) was never adopted: `att_month_report.py` has `ROSTER_FROM = "2099-01"`, and nothing on the server sets `ATT_ROSTER_FROM` (crontab and service units read). Until the rota is adopted, any saved Sunday start makes Sunday a duty day, and an empty one makes it a day off. The form saved the weekday hours as the Sunday hours for A and B, so anyone added with *1st and 3rd* would have been on duty **every** Sunday, and each Sunday he stayed home would have counted as an absence. **Nobody was harmed:** no joining has been saved through the form since it went in (finance.db `joiner`: Amir 03-Sep and Arjun 18-Oct, both before S607). The A/B/C groups on the live list (A 3, B 5, C 3, ARJ 1; read 06-Nov 08:1x IST) were set by hand earlier and are dormant. This kit does not touch them.
- **D834** (the owner, 06-Nov 07:26–07:55 IST, *"This looks like a good plan"*; and 08:15 IST: *"cleaner is arjun dev, skip his hours, joining date 1st nov 2026"*). Arjun's terms are met by the existing rules, with no new rule. The live list, read 06-Nov 08:1x IST through `/finance/staff/api/staff_master`, shows him as number 20: Cleaner · offs 4 · minutes exempt Y · weekday 09:00–10:30 · Sunday 09:00–10:30 (every day a duty day) · group ARJ. The only thing missing was the pay: October's locked sheet shows base ₹3,200 (net ₹570). It becomes ₹3,500 from November. *Skip his hours:* his hours are stored only so that each day counts as a duty day. Late minutes are not counted for him, so the times never cost him anything. October stays exactly as approved and paid (locked 06-Nov 07:19). The lock desk may show a "today's recompute differs" line for him for October; that line is for information only (S303).

## Files
| live file | FROM | TO | what |
|---|---|---|---|
| `/root/finance/staff_easy.py` | c5344291 | da4aabd2 | `SUNDAY` = *Works every Sunday* (C) / *Sunday off* (OFF). The form value OFF is saved as group `""` with no Sunday hours. It is never saved as "OFF", because the attendance report refuses an unknown group. A and B are refused. The old line that copied the weekday hours into Sunday is removed. `KIT = "S712"`. |
| `/root/finance/staff_easy.html` | 05c1f7b8 | 45dd0a01 | The two chips, with *Works every Sunday* chosen by default. The Sunday hours default to the weekday hours and follow them until they are touched. The 5th-Sunday line is replaced by *"A Sunday he does not come counts as one of his offs."* The detail line says *Sunday: off* or *Sunday: every Sunday (hh:mm–hh:mm)*. |
| `/root/staff_master.csv` | Arjun 3200 | 3500 | One cell. `set_base_s712.py` stops on any other shape (a different name, pay, offs or hours, a duplicate number, quotes). It proves that every other byte is identical, keeps a backup first and replaces the file atomically. |

## Proven (session 389, the cloud workspace; the files from the 05-Nov bundle = the pins)
- `walk_s712.py` (the installer runs it on the server) — the form's server code on a made-up root, with the **real** `att_core` / `att_month_report` reading what it wrote: **12 of 12 green**. **Control** on the live files: **9 S712 check(s) red . 3 green**.
- `browser_walk_s712.js` — the page in Chromium at phone width, with a made-up API: **13 of 13 green**, no script error and no sideways scroll at 390 px. **Control:** the live page is red on its first four checks and then stops (its Sunday hours are hidden, because *1st and 3rd* is the default).
- `set_base_s712.py` on made-up lists (LF, CRLF, BOM): exactly 1 byte differs (`3200` → `3500`); a second run says ALREADY. With pay 3000, the name *Arjun Dev*, a quoted line, a duplicate number, offs 2 or no Sunday hours, it STOPS and writes nothing.
- The installer rehearsed on a made-up server (see the close report).

## Cold review (independent agent, S389)
**SAFE TO INSTALL**, no blocker. Its four should-fix points are all built: (1) `DRY=1` on an already-installed form now runs the pay step `--dry`; (2) that path now reports a stopped pay step instead of exiting green; (3) the live files are checked again after the lock is taken; (4) the offs line now shows only with *Works every Sunday*, and gate 2 also reads the service's environment files. Its three outside points, checked: the staff register's `staff.sunday_group` is a plain `TEXT` with no check (`staff_register.py` schema), so `""` is accepted. `build_staff_master.py` (which refuses a group outside A/B/C/ARJ and would rebuild the list from the old salary workbook) is not on the server: it is not in the 05-Nov bundle and not in the crontab. If it is ever brought back, it would also undo every joining made through the form, so it stays retired. Arjun is not on the staff register's `staff` table, so his pay is read only from `staff_master.csv`.

## Install (on the server, after the publish; window 04:00–23:30 IST)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s712kit && cp -rp /root/deploy/repo/deploy_kits/S712_STAFF_FORM_SUNDAY_ARJUN /tmp/s712kit && bash /tmp/s712kit/install_S712_STAFF_FORM_SUNDAY_ARJUN.sh
```
## Undo
```
\cp -p /root/finance/staff_easy.py.bak_S712 /root/finance/staff_easy.py && \cp -p /root/finance/staff_easy.html.bak_S712 /root/finance/staff_easy.html && systemctl restart clinic-finance
```
To undo the pay change, copy the newest `/root/staff_master.csv.bak_S712_*` back over `/root/staff_master.csv`.
