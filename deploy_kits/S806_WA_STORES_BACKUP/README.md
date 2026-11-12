# S806_WA_STORES_BACKUP — two small front-desk stores join the encrypted nightly backup (D939, the WhatsApp items, d)

**The gap.** `/root/portal/wa_ladder.db` (S798 — the WhatsApp STOP list, the numbers taken off it, the listener's place) and
`/root/portal/callback_clock.db` (S796 — which missed caller was notified when) are in no backup at all.

**The change.** Two source lines at the end of `SRC_FILES` in `/root/state_backup/clinic_state_backup.py`
(fd1647de → 5282b72c). Both are databases, so they go through the sqlite online backup and the integrity check like the other
stores. No service is restarted; nothing on any page changes; the nightly runs at 01:50 as before.

**The installer (S719's pattern)** proves both stores present and sound first (a missing source would refuse the whole night —
FATAL 41), walks the kit's file against the live one on made-up stores (17/17 — two WAL stores, and a store in the default journal mode with a write in progress; the control — the live file in the kit's
place — red), places the file, then runs the backup's own `preflight` (every source, the encryption round trip, Drive —
nothing shipped). If the preflight fails, skips either store, or does not show each store taken and sound, the old file goes
back (and the going-back is itself read back).

**Cold review (a second reader, S439): SAFE.** Its three should-fixes built: the walk's missing case (the real stores are not in
WAL), the positive check on the preflight, the put-back verified.

**Install** (after the publish), one line on the server:
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s806kit && cp -rp /root/deploy/repo/deploy_kits/S806_WA_STORES_BACKUP /tmp/s806kit && bash /tmp/s806kit/install_S806_WA_STORES_BACKUP.sh
```
Undo: `bash /tmp/s806kit/install_S806_WA_STORES_BACKUP.sh --undo`.
