# S424_PHI_STORES_BACKUP — the Case Pack's records were in no backup · session 284 · 27-Sep-2026

**Found at S284, reading every inclusion list before moving Vitals & Plan beside the Case Pack:** `/root/wa/casepack` — the case ledger, the consent ledger, every saved case bundle and every issued consent — is in **no** backup. The nightly encrypted state backup names it in neither `SRC_FILES` nor `SRC_DIRS` (and walks `SRC_DIRS` only one level deep, so `case_archive/<year>/<patient>/…` would be missed even if it did); the code bundle takes only its `*.html` / `*.py`; nothing else on the box mentions it. The surgical records existed on one disk.

**v5 of `/root/state_backup/clinic_state_backup.py` (05397337 → ede26d98):** a new list `SRC_TREES` = `/root/wa/casepack`, `/root/wa/vitals` (S423). Each is walked to every depth; every file is taken except code, temp/backup names and anything the secret patterns match (matched first, as the existing walk does); SQLite files go through the same integrity check; everything lands in the same encrypted tarball under `data/casepack/…` and `data/vitals/…`. For the vanished-source guard (FATAL 41) each tree counts as **one** source — the apps version and supersede their own files, and one superseded file must never refuse the whole night; a store that vanishes still does.

No restart (cron 01:50). Backup `clinic_state_backup.py.bak_S424_05397337`.

**Proof:** `walk_s424.py`, 8 checks: every data file at every depth with PDFs and paths preserved; code, `__pycache__` and a temp file not taken; a secret-named file skipped and counted; SQLite integrity-checked; each tree one source; an absent tree reported, never fatal; a second apply changes nothing. The installer then gathers the **real** trees read-only into `/tmp`, prints the counts, and deletes them.

## Install — one line on the VPS (after the publish)
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S424_PHI_STORES_BACKUP/install_S424_PHI_STORES_BACKUP.sh
```
