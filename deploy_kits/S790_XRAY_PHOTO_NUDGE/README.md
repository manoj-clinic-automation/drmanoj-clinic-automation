# S790_XRAY_PHOTO_NUDGE — the 3 p.m. and 6 p.m. X-ray photo notification

**The owner, 11-Nov-2026 09:49 / 09:51 IST:** a notification on the PWA when X-ray photos are not put in the Drive folder — *"The
notification should be at 3 p.m. and 6 p.m. and both notifications related work when completed should also be flagged everywhere, and if
it is not done then it also remains flagged so that it is visible to everyone."*

NEW `/root/finance/xray_photo_nudge.py` + two cron lines (15:00, 18:00 IST). It reads finance.db read-only: every X-ray slip from 23-Sep
through today with no X-ray photo filed (nor on its way, nor marked "X-ray not done") — reception's Aaj ka kaam rule, today included —
and sends ONE notification to the phones of reception, Shivani, Alisha, Shavez (Hindi; not Sukhveer — the owner 09:57: lab work only) and the owner (English):
*"X-ray photo baaki: N — aaj ki T, pehle ki O"* (tap → Report baaki's X-ray list, where each stays until its photo is in), or when none
is pending *"✅ X-ray photo: sab aa gayi"*. The pending ones also stay on Aaj ka kaam and Report baaki as before. Only phones that
allowed the portal's notifications get it.

**Walk** 9/9 on a copy of the 11-Nov database (read-only proven by md5); the control without the file red. No live file changed, no restart.

**Install** (after the publish), one line on the server:
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s790kit && cp -rp /root/deploy/repo/deploy_kits/S790_XRAY_PHOTO_NUDGE /tmp/s790kit && bash /tmp/s790kit/install_S790_XRAY_PHOTO_NUDGE.sh
```
Undo: `bash /tmp/s790kit/install_S790_XRAY_PHOTO_NUDGE.sh --undo`.
