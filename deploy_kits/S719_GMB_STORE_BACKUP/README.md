# S719_GMB_STORE_BACKUP — the GMB store into the encrypted nightly · the parent · session 390 · 06-Nov-2026

**For the owner, in one line.** From tonight the GMB Review Assist's saved drafts and readings are in the encrypted nightly backup on Drive, like the call console and the staff ledger; nothing on any page changes.

## Why — F-1129 (S389)
`/root/portal/gmb_store.db` (kit S713, live 06-Nov 09:34; S717's readings) was in no backup at all.

## What it changes
`/root/state_backup/clinic_state_backup.py` facfb897 → **37ed5524**: ONE line in `SRC_FILES` (plus its comment). A database, so it goes through the sqlite online backup and `PRAGMA integrity_check` like every other store there (it runs in WAL; the online backup carries the uncheckpointed rows). No service restarts. The night is FATAL if a named source is missing, so the installer proves the store is on the box and passes its own integrity check first.

## Proven
`walk_s719.py` **13 of 13**: the kit's file is the live file plus that one line and nothing else; on a made-up WAL store with 250 rows still in the `-wal` file, `gather()` takes it, the copy passes integrity_check and holds all 250 rows (a restore proof), its schema is dumped; a missing store is reported missing. Control (the live file): red. The installer then runs the backup's own `preflight` on the box (every source, the encryption round trip, Drive — nothing shipped) and puts the old file back if it fails. Rehearsed: DRY, a failing preflight (old file back), a missing store (stopped), ALREADY, undo.

## Install (on the server, after the publish)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s719kit && cp -rp /root/deploy/repo/deploy_kits/S719_GMB_STORE_BACKUP /tmp/s719kit && bash /tmp/s719kit/install_S719_GMB_STORE_BACKUP.sh
```
## Undo
```
bash /tmp/s719kit/install_S719_GMB_STORE_BACKUP.sh --undo
```
