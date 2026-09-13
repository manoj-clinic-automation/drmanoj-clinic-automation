# S243_WATCHDOG_FINANCE

**What:** full-file replacement of `/root/wa/clinic_watchdog.py` on the VPS, adding three
units to its `SERVICES` list so the 5-minute watchdog (clinic-watchdog.timer) alerts if they stop:

| unit | app | port |
|---|---|---|
| clinic-finance.service | finance app | 127.0.0.1:8106 |
| staff-register.service | staff register | 127.0.0.1:8044 |
| assetapp.service | asset register | 127.0.0.1:8030 |

**Why:** the live watchdog (md5 `389afcfe318c1618ad87349aa9695e22`, the S231/F-358 ntfy-from-.env build; the live_pins_S242close row `01ca6591` is STALE - F-454 candidate) guards 11 units; these three
went live after it was written and were unguarded.

**How the file expresses units:** a single `SERVICES` list of `(unit, label, fix-command)`
tuples checked with `systemctl is-active`. The file has **no HTTP-probe framework**, so no
probes were added (the healthz/health URLs are noted here for a future probe step only).
Diff versus base = 4 added lines (one comment + three tuples), 0 removed.

**Pins:** from `389afcfe318c1618ad87349aa9695e22` -> to `35e406261f27b2b0845911ee6382bb3d`

## Install (one line, on the VPS)

```
bash /root/deploy/repo/deploy_kits/S243_WATCHDOG_FINANCE/install_S243_WATCHDOG_FINANCE.sh
```

The installer refuses unless the live md5 equals the from-pin, backs up to
`/root/wa/clinic_watchdog.py.bak_S243_389afcfe`, installs, py_compiles with
`/root/wa/venv/bin/python3` (fallback `/usr/bin/python3`), runs an import-only smoke
(reads SERVICES, asserts 14 units; no systemctl, no network - the watchdog has no dry mode),
restores byte-identically on any failure, and ends by printing `md5sum` of the installed file.
A second run prints `ALREADY INSTALLED` and exits 0.

**No service restart needed** - clinic-watchdog.timer starts the script fresh every 5 minutes.
Proof of install: the next `/root/wa/watchdog.log` heartbeat reads `CHECK all 14 services healthy`.

## Rollback (one line)

```
cp -p /root/wa/clinic_watchdog.py.bak_S243_389afcfe /root/wa/clinic_watchdog.py
```

## Files
- `patch_watchdog_s243.py` - builds `clinic_watchdog.py` from the live copy (`followup-vps/clinic_watchdog.py`) with count==1 guards
- `clinic_watchdog.py` - the complete new file (md5 `35e406261f27b2b0845911ee6382bb3d`)
- `selftest_watchdog_s243.py` - AST check: 11 originals + 3 new, each exactly once
- `install_S243_WATCHDOG_FINANCE.sh` - installer (honours `ROOT=` for mock testing)
- `EVIDENCE_S243.txt`, `KIT_ID.txt`, `SUMS.md5`
