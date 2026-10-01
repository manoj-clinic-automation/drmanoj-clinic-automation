# S445_RING_OUTCOMES_BACKUP — session 287 · 01-Oct-2026 · F-677 / D654

**The gap.** `/root/portal/ring_outcomes.db` — the ring card's own store since S419 (27-Sep): every ring, who answered, the outcome tapped, the 10-minute reminder state and the queue of outcomes waiting to reach the tracker sheet — had **no second copy anywhere**. Every inclusion list was read before saying so (S258 rule):

| store | its lists | holds ring_outcomes.db? |
|---|---|---|
| encrypted nightly `clinic_state_backup.py` (01:50) | `SRC_FILES` · `SRC_DIRS` · `SRC_TREES` | no — `/root/portal` is in none of the three |
| code bundle `code_bundle.py` (01:35) | `root/portal` rows: `*.py *.html *.json`, `*.js` | no — code only, no `.db` |
| `sheets_pull.py` (01:45) | the tracker book, every tab | **partly** — only outcomes already mirrored into `Followup_Outcomes` / `Followup_Escalations`; not the rings, who answered, the reminders or the unmirrored queue |
| `finance_drive_backup.py`, `assetapp_backup.py`, `petty_backup.py`, `gas_export.py` | their own stores | no |

**The change (D654).** One line added to `SRC_FILES` in `/root/state_backup/clinic_state_backup.py` (`0e841f35` → `3bf7caea`), beside `console.db`. It goes through the same sqlite online backup, integrity check, encryption and read-back as every other database there. Nothing else in the file moves (the walk proves it byte for byte). No service restart; tonight's 01:50 run is the first that carries it.

**Proof.** `walk_s445.py` — 14 checks; negative controls (unpatched file; a misspelt path) go red. The installer runs it on a fake database and then on the **real** database, read-only, before placing anything.

## Install — one line on the VPS
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S445_RING_OUTCOMES_BACKUP/install_S445_RING_OUTCOMES_BACKUP.sh
```
Backup: `clinic_state_backup.py.bak_S445_0e841f35`. Already installed → it says so and stops.
