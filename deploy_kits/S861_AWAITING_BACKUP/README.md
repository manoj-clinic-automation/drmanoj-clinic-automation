# S861_AWAITING_BACKUP — the WhatsApp awaiting-reply store joins the encrypted nightly backup (the parent, S478, 17-Nov-2026) — F-1365, D964

**The gap.** `/root/portal/wa_awaiting.db` (S818 — which patient chats wait for a reply or a call-back, and since when) is in no
backup at all.

**The change.** One source line at the end of `SRC_FILES` in `/root/state_backup/clinic_state_backup.py` (5282b72c → see
KIT_ID / the installer's TO). A database, so it goes through the sqlite online backup and the integrity check like the other
stores. No service is restarted; nothing on any page changes; the nightly runs at 01:50 as before. **S806's kit, one store.**

**The installer (S719's / S806's pattern)** proves the store present and sound first (a missing source would refuse the whole
night — FATAL 41), walks the kit's file against the live one on made-up stores (17/17 — two WAL stores and a store in the
default journal mode with a write in progress; the control — the live file in the kit's place — red), places the file, then
runs the backup's own `preflight` (every source, the encryption round trip, Drive — nothing shipped). If the preflight fails,
skips the store, or does not show it taken and sound, the old file goes back (and the going-back is itself read back).

**Install** (after the publish): the S478 combined line, or alone:
`cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s861kit && cp -rp /root/deploy/repo/deploy_kits/S861_AWAITING_BACKUP /tmp/s861kit && bash /tmp/s861kit/install_S861_AWAITING_BACKUP.sh`
Undo: `bash /tmp/s861kit/install_S861_AWAITING_BACKUP.sh --undo`.
