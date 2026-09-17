# S286_ASSETAPP_BACKUP — the asset register's 02:30 backup gets a log and a verdict

**Session 263 · 17-Sep-2026 · VPS only · the "backup that names no log" (OWNER_TODO ⭐1 item 4; job pulse's NO TRACE line).**

## What was wrong

The asset register (assets.dr-manoj.in) is backed up by one bare crontab line:

```
30 2 * * * tar -czf /root/backups/assetapp_$(date +\%F).tar.gz -C /root assetapp/assets.db assetapp/uploads 2>/dev/null; find /root/backups -name "assetapp_*.tar.gz" -mtime +14 -delete
```

- it **names no log** — so the job pulse can only ever say **NO TRACE**;
- it **throws its errors away** (`2>/dev/null`) — a failed night is invisible;
- it **prunes whether or not tonight worked** — fourteen bad nights would leave no good copy;
- it **tars a live database file** — a write during the tar can give a copy that will not open.

## What replaces it

`/root/state_backup/assetapp_backup.py`, run by the same 02:30 line, appending to
`/root/backups/assetapp_backup.log`. **Same archive name, same folder, same members, same 14 days.** Plus:

1. `assets.db` copied through SQLite's own backup call and passed through `PRAGMA integrity_check` first.
2. The archive written as `.part`, reopened, **every member read back in full** (every gzip CRC), the
   uploads counted against the disk — only then given its real name.
3. Old archives pruned **only after a night that passed**, never today's; the age rule is `find -mtime +14` exactly.
4. A flawed archive **never replaces a good one already made today**; with nothing yet for today it is kept
   as the only copy and labelled.
5. One line per night — `OK` or `FAIL` with the reason, size, md5, table count, uploads count, pruned, kept.

## What it touches

| path | change |
|---|---|
| `/root/state_backup/assetapp_backup.py` | **new** (the nightly code bundle already carries this folder) |
| root's crontab | **one line swapped** — line 31, the tar; the other 67 untouched, read back whole |
| `/root/backups/assetapp_backup.log` | new, appended by the installer's first run and each night |
| `/root/finance/crontab.bak_S286` | the crontab as it was |
| the asset app, its service, its database | **nothing** — read-only; no restart |

## How it was proven

- Built against the **real crontab** in the 17-Sep bundle: the installer's old line matches it **byte for byte, once**.
- **Self-test 20 of 20** in a temporary folder: a good night passes · same name · members keep the old paths ·
  all uploads in · the archived database opens with its rows · `-mtime +14` (15 days pruned, 14 kept) · no
  `.part` or snapshot left · missing uploads is a FAIL that says why · a failed night prunes nothing · a flawed
  archive never replaces today's good one · a damaged database is refused before anything is written · with
  nothing for today a flawed archive is kept and labelled · no database says where it looked · one line each.
  **One of these was added after reading the code again:** the first draft would have let a photos-missing night
  overwrite that day's good archive; the self-test had not asked.
- **Installer rehearsed on a fake root with the real crontab:** installs (68 lines in, 68 out, only line 31
  differs) · the first run's line lands in the log · **job_pulse v1.2 reads the new line as
  `assetapp_backup.py` → `/root/backups/assetapp_backup.log`, no `tar` row left** · second run says *already
  installed* · a crontab that moved on is refused · a first run that fails **removes the script and never
  opens the crontab** · a crontab that reads back wrong is **restored identical** to the original.
- `py_compile` clean (compiled outside this folder); parses as Python 3.6; no ten-digit run.

## Worth knowing — not changed by this kit

The uploaded photos in `/root/assetapp/uploads` have **no copy off the server**: the encrypted state bundle
carries `assets.db` but excludes uploads by design, and the code bundle takes code only. These archives sit on
the same disk as the app. The first run prints the archive's size, which is what an off-box copy would cost.

## Pins

| file | before | after |
|---|---|---|
| `/root/state_backup/assetapp_backup.py` | *(absent)* | `9fdc66a3d7d0bfe94541b2eb228302e9` |
| root's crontab line 31 | the bare `tar` | `… assetapp_backup.py >> /root/backups/assetapp_backup.log 2>&1  # S286_ASSETAPP_BACKUP` |

## To install — one line on the VPS, after the publish

```
cd /root/deploy/repo && git pull --ff-only && /root/wa/venv/bin/python3 /root/deploy/repo/deploy_kits/S286_ASSETAPP_BACKUP/install_s286.py
```

The first real run happens during the install and can take a few minutes if the photos folder is large.

## To undo

```
crontab /root/finance/crontab.bak_S286
```

## Files

| file | what |
|---|---|
| `assetapp_backup.py` | the nightly backup, with `--selftest` |
| `install_s286.py` | gate, self-test on the box, first real run, one-line crontab swap, read-back, restore |
| `KIT_ID.txt` · `SUMS.md5` | identity and self-gate (verify from inside this folder) |
