# S725_RETIRE_CODE20 — the old Arjun's machine number retired for good · the parent · session 390 · 06-Nov-2026

**For the owner, in one line.** The old Arjun's attendance number 20 is now retired on the exit register, so it can never be given to anyone else; his exit record shows two steps still yours — his finger off the machine, and his dress, I-card and keys.

## Why
Staff 20 'Arjun' left on 30-Sep (D824); the owner, 06-Nov 14:10: *"paid and all his dues cleared"*. At S390 his exit record **EXIT-2026-0002** was opened through the owner's own staff page (decided; portal login — he never had one, ticked from the logins list). The register's own *removed from the biometric device* step retires only the code already on the record, and the record's code was blank, so code 20 would never have been retired (a fault in that step's order; the register keeps working).

## What it changes (finance.db, data only)
EXIT-2026-0002: `emp_code` 20 (only if blank) · `emp_code` 20 (*Arjun*): `retired_on` 2026-09-30 (only if not retired) · one `joiner_event` row. Refused, nothing written: the record not Arjun's leaving, complete, or carrying another code; code 20 someone else's or on another record. Backup first through sqlite's backup API; one transaction; read back.

## Still on the exit record (the owner's, on the staff page)
*Removed from the biometric device* (MENU → 1 Register → 2 Delete, number 20) · *dress, I-card and keys returned*. The roster, dues and staff-master steps are already true (S718; his word) and are ticked after those, in the register's own order.

## Proven
`walk_s725.py` **13 of 13** on made-up databases (written, read back, Arjun Dev and code 17 untouched, ALREADY, five refusals writing nothing, DRY). Control: 12 red.

## Install
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s725kit && cp -rp /root/deploy/repo/deploy_kits/S725_RETIRE_CODE20 /tmp/s725kit && bash /tmp/s725kit/install_S725_RETIRE_CODE20.sh
```
## Undo
Copy the newest `finance.db.bak_S725_*` back while clinic-finance is stopped (only if this must be undone; it is two cells and one event row).
