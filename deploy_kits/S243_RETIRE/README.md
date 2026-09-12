# S243_RETIRE — empty `/root` and `/root/finance` of superseded files (move only)

**Why.** `/root/finance` holds 500 files of which ~66 are live; the rest are `.bak` copies (≈60 of
`finance.db` alone), applied patchers, walk/selftest helpers and install residue. S230 diagnosed it;
nothing was ever moved. This kit moves — never deletes — and can put everything back with one line.

**Two steps, one line each, on the VPS. Step 2 refuses unless step 1 ran in the last 6 hours and the
box has not changed since.**

Step 1 — dry run, READ ONLY (paste the output back for review):
```
git -C /root/deploy/repo fetch --depth 1 origin main && git -C /root/deploy/repo reset --hard origin/main && bash /root/deploy/repo/deploy_kits/S243_RETIRE/retire_dryrun.sh
```

Step 2 — the move (only after the dry run is reviewed):
```
bash /root/deploy/repo/deploy_kits/S243_RETIRE/retire_move.sh --go
```

Undo (any time, prints itself at the end of step 2):
```
bash /root/_retired/S243_<stamp>/UNDO.sh
```

**What it will not touch.** `.acme.sh`, `crontab.bak_S237`, `_quarantine_S232_*` (rulings); `finance.db`,
every `*.log`, `*.json`, `*.env`, `clinic-finance.service`; every live module; every directory except
`_backup_S*`, `S180_U*`, `vhosts.BACKUP_S179`. Anything a live `.py/.sh/.html/.conf/.service/.timer`,
the crontab or `/etc/systemd` mentions by name is **HELD** and not moved.

**What it writes.** `/root/_retired/S243_<stamp>/` (mode 700 — the S231 backup folders contain
`env.bak` secrets) with `MANIFEST.md5` (hash of every file before it moved), `WHY_SAFE.txt`, `UNDO.sh`.
Nothing else. No service is restarted.

**Proof, offline (S243, 12-Sep-2026):** mock of the box from the survey listing → dry-run → move 43 /
held 1 → `md5sum -c MANIFEST.md5` inside the retired folder: 0 failures → `UNDO.sh` → `find` listing
byte-identical to before. Refusals proven: no `--go`; no dry-run list; list older than 6 h; box changed.
