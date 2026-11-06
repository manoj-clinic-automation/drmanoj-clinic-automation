# S718_STAFF20_INACTIVE — staff 20 off the list, his pay put back · the parent · session 390 · 06-Nov-2026

**For the owner, in one line.** Staff 20 (Arjun, who left on 30 September, paid and all dues cleared) is taken off the staff list from November, and his base pay goes back to ₹3,200; September and October stay exactly as locked and paid.

## Why
- **F-1131** (S389): kit S712 moved staff 20's base pay 3,200 → 3,500 believing him to be the new cleaner. The cleaner is **Arjun Dev**, a different person (D835); staff 20 'Arjun' left on 30-Sep (D824, 02-Nov).
- **F-1132** (S389): staff 20 was still `active Y` on `/root/staff_master.csv` after D824.
- **The owner, 14:10 IST 06-Nov:** "2 ok, paid and all his dues cleared" — to the question *staff 20 inactive from October; October's ₹570 paid or recovered?*

## What it changes
| where | what |
|---|---|
| `/root/staff_master.csv` | number 20 *Arjun*: `base_salary` 3500 → 3200, `active` Y → N. One line; every other byte proved identical; backup `staff_master.csv.bak_S718_<time>`, atomic replace, read back. |
| `staff_register.db`, table `staff` | the active row named exactly *Arjun*, **if there is one**: `last_working` 2026-09-30, `active` 0, one `audit_log` row (as S298 did for Pravesh). S712's read found him only on the staff list, so this most likely does nothing. |

**Money guard.** An inactive row is dropped from every month the attendance report computes, so the tool **refuses** unless September and October are both LOCKED in the register (`locked_run`). Their pay is then frozen. November has not been computed. Joining Arjun Dev is separate (the Add staff form).

## Proven (session 390, the cloud workspace)
`walk_s718.py`: **32 of 32** on made-up lists (LF, CRLF, BOM) and registers — the two cells only, a second run ALREADY, the register row when present (Arjun Dev untouched), and every refusal writes nothing (October or September not locked, number 20 someone else, pay neither 3500 nor 3200, number 20 twice, a quoted line, two register rows, a half-changed row, no register). Control (an untouched list): red. Installer rehearsed: DRY, install, ALREADY.

## Install (on the server, after the publish)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s718kit && cp -rp /root/deploy/repo/deploy_kits/S718_STAFF20_INACTIVE /tmp/s718kit && bash /tmp/s718kit/install_S718_STAFF20_INACTIVE.sh
```
## Undo
Copy the newest `/root/staff_master.csv.bak_S718_*` back over `/root/staff_master.csv` If the tool also wrote the register (its output says *written: the register*), stop the staff register service, copy the newest `staff_register.db.bak_S718_*` back over the register database, and start the service again.
