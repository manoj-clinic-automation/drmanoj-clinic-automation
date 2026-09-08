# S232_F368_QUARANTINE — six stale copies of the secrets file, out of the live folder

**PREPARED. Two one-line commands on the VPS, and the first one changes nothing.**

## What is wrong

`/root/wa/` holds **six old copies of the secrets file**, each carrying `MYOP_AUTH_TOKEN` and
`MYOP_LOGS_TOKEN` — **and every other secret in that file, including ones that have never been
rotated.** Plus three stale code copies. **These are the files a future sweep finds and believes.**

## Why before the rotation, not after

The record said *"not to be touched mid-rotation"*. **The rotation has not started.** Doing it now
means six fewer files holding the old token on the day it is replaced. *Mid*-rotation is the one
moment this must not happen — and that moment has not arrived.

## The limits, which are the design

- **It moves. It never deletes.** One dated folder, mode 700, files 600.
- **An explicit list of nine filenames. No globs.** A sweep that matches `*.bak` by shape is how a
  live file gets moved by accident.
- **It refuses to run if `/root/wa/.env` is missing**, and it never touches it — checked again after
  the move.
- **It never touches the `_backup_S231_*` copies**, which the S231 close recorded as current.
- **It prints no file content, ever.** These are secrets; the point is to handle them without
  reading them.

## Run it

```
cd /root/deploy/repo && git pull
```

```
/root/wa/venv/bin/python3 /root/deploy/repo/deploy_kits/S232_F368_QUARANTINE/quarantine_f368.py --check
```

```
/root/wa/venv/bin/python3 /root/deploy/repo/deploy_kits/S232_F368_QUARANTINE/quarantine_f368.py --apply
```

`--check` lists what it would move and moves nothing. `--apply` prints the undo line when it
finishes. **After the WABA rotation, delete the quarantine folder** — that is when the old token in
those files is finally worthless.
