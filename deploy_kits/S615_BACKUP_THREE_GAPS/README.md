# S615_BACKUP_THREE_GAPS — three server files that were in no backup (S336, 22-Oct-2026)

**The gap (AF-19, S608, F-972).** Every inclusion list was read first: the encrypted nightly's `SRC_FILES`,
`SRC_DIRS`, `SRC_TREES`; the code bundle (root/wa `*.py` and `*.sh` only, `att_config.py` named out); the sheets,
asset, petty, GAS and finance backups (their own stores). None held:
- `/root/wa/wa_logs/` — every incoming WhatsApp push, one `YYYY-MM-DD.jsonl` a day (the inbox reads it forward);
- `/root/wa/wa_inbox/send_log.jsonl` — every WhatsApp send and MyOperator's answer (S608, live 21-Oct);
- `/root/att_config.py` — the attendance settings, secrets included (so the encrypted bundle, never the code one).

**The change.** Two exact edits (`edits_s615.py`) to `/root/state_backup/clinic_state_backup.py` be57fe75: the two
files join `SRC_FILES`, `wa_logs` joins `SRC_TREES`. Same encryption, read-back and refusal stances as every other
store there. No service to restart; tonight's 01:50 run is the first that carries them.

**The one line (VPS):**

    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S615_BACKUP_THREE_GAPS/install_S615_BACKUP_THREE_GAPS.sh

**Proven by:** `walk_s615.py` (10 checks on made-up files: the three taken, a secret-shaped and a temp file skipped,
the vanished-source guard; on the box the three real paths and wa_logs' size); the S476 file goes RED. After
placing, the backup's own `preflight` must pass, or the old file goes back.

**Undo:** `--undo` puts the S476 file back (`/root/s615_backup/`).
