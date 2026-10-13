# S549_WA_ALERT_DIRECT — kit S549 (session 313, 13-Oct-2026) · URGENT

**The owner, 13-Oct:** *"ntfy whatsapp alert have stopped from 7th October, system ones are still coming"* (18:23) · *"why not move to server from Google sheets, if it's more reliable?"* (18:29) · *"It's urgent"* (18:47).

**The cause.** `notifier_wa.py` re-read the WA_Inbox sheet every 30 s and pushed what was new. At 14:37 IST on 7-Oct a Google read never returned; its service stayed *active*, so no watch noticed. The messages kept landing in the sheet (27 since 7-Oct); no alert went out. Its state file stopped at 14:37 7-Oct; restarted by hand 18:27 13-Oct.

**The fix — Google off the alert path.** `wa_receiver.py`, which MyOperator pushes every inbound WhatsApp to, now hands the message to `wa_alert.py` the moment it arrives, before it touches Google. The alert reads as before (*New WhatsApp — name*, the number and the text). A failed send is retried (5 s, 30 s, 2 min, 10 min); if all fail, one warning goes to the system topic (at most once in 30 minutes). Names come from Patient_Master, refreshed in the background — a slow Google costs a name, never an alert. The sheet is written exactly as before, so the tracker is unchanged. `wa-notifier.service` is retired (stopped, disabled; the watchman and the health report no longer list it).

| file | from → to |
|---|---|
| `/root/wa/wa_receiver.py` | 9f46279e → 793f0182 (3 counted edits) |
| `/root/wa/wa_alert.py` | NEW |
| `/root/wa/clinic_watchdog.py` | 35e40626 → d7844f8e (1) |
| `/root/wa/clinic_health_report.py` | beb33190 → 27cbc9e4 (2) |

**Proof (S313, offline):** 16 checks green — the alert's words, one alert per message id, retries then one warning, no topic configured; the receiver alerts with Google DOWN and stays quiet for status pings, repeats and our own replies; wa-notifier retired. The old files fail 5 of 7. Nothing is sent by the walk.

**Install — one line on the VPS:** `cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S549_WA_ALERT_DIRECT/install_S549_WA_ALERT_DIRECT.sh` — it ends by sending ONE test alert: *"WhatsApp alerts are working again"*.

**Undo:** `\cp -p /root/wa/wa_receiver.py.bak_S549_9f46279e /root/wa/wa_receiver.py && \cp -p /root/wa/clinic_watchdog.py.bak_S549_35e40626 /root/wa/clinic_watchdog.py && \cp -p /root/wa/clinic_health_report.py.bak_S549_beb33190 /root/wa/clinic_health_report.py && rm -f /root/wa/wa_alert.py && systemctl restart wa-receiver && systemctl enable --now wa-notifier`
