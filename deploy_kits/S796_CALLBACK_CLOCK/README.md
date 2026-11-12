# S796_CALLBACK_CLOCK — a clock on the call-back (the parent, S435, 12-Nov-2026)

The owner, 12-Nov 07:47 / 07:52 IST: "a clock on the callback, this is fine. And the backup phone should be Shavez." — "Both".

NEW `/root/portal/callback_clock.py` + one cron line (every 5 minutes, 08:00–21:55 IST) + its own small store `/root/portal/callback_clock.db`. No live file is changed; no restart.

It reads `/root/wa/console.db` read-only (the Call Console's own store). A caller with a missed incoming call since yesterday's closing time who has not spoken to the clinic since (no answered call after it, either way) is notified again:
- after 30 duty minutes → one notification to shivani, alisha and the reception mobile (Hindi), with the count and who;
- after 60 duty minutes → one to Shavez, the backup;
- at closing time (Mon–Sat 20:30, Sunday 14:30) → the count still open, to the owner (English), only when above zero.
Duty minutes: Mon–Sat 09:00–20:30, Sunday 09:00–14:30. Judged as of the store's own build time; a store older than 25 minutes is not judged. A number the owner marked Spam is left out. Each caller's missed call is notified once per stage.

Install (after the owner's publish), on the server:
`cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s796kit && cp -rp /root/deploy/repo/deploy_kits/S796_CALLBACK_CLOCK /tmp/s796kit && bash /tmp/s796kit/install_S796_CALLBACK_CLOCK.sh`
Undo: `bash /tmp/s796kit/install_S796_CALLBACK_CLOCK.sh --undo`

Walk: `walk_s796.py <kit dir>` — 30 checks on a made-up console.db (made-up numbers); `--control` on a folder without the file goes red.
Not in this kit (the next one): the open duty on Aaj ka kaam that closes only by a call; the Needs-you line on the owner's console.
