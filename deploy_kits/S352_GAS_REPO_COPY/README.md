# S352_GAS_REPO_COPY — F-591

`gas_export.py` (Sunday 02:20 IST) compares the live Apps Script projects against **the repository copy people
read**, named by `GAS_REPO_COPY=` in `/root/state_backup/clinic_state_backup.conf` and defaulting to
`deploy_kits/S230_GAS_EXPORT/` — the 07-Sep-2026 photograph, frozen (F-512) and behind on two projects since
S330/S348. Its report goes only to `/root/state_backup/gas_export.log`.

This kit sets **one conf line** — `GAS_REPO_COPY=/root/deploy/repo/deploy_kits/GAS_CURRENT` — pointing at the new
**living** folder `deploy_kits/GAS_CURRENT/` (its `READ_ME.md` says where every file came from and the rule that
keeps it current: every Apps Script change the assistant places in the owner's browser updates it in the same
breath). Backup of the conf beside it (mode 600), exactly one line, the conf is never printed. Then
`gas_export.py diff` — read-only, no Google call — prints what is still behind against the new folder.

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S352_GAS_REPO_COPY/install_S352_GAS_REPO_COPY.sh
```

No code moves: `gas_export.py` stays at its S234 pin `072a9411…` (checked). No restart. Touches the conf only.
Rehearsed on a fake root: add · replace an older line · rerun ALREADY · GAS_CURRENT missing refused · its sums broken refused.
