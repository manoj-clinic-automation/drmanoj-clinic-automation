# S811_FEED_ON_ARRIVAL — visits fold in on arrival; a missing reception export is told to the owner (the parent, S443, 13-Nov-2026, build 2)

**The gap.** On 12-Nov the PC's two join workbooks (`Visit_Ledger_Join.xlsx`, `Patient_Master_Join.xlsx`) reached
`/root/wa/followup-inbox/` at 21:20:58 — after the day's last patient sync (cron `20 8-21 * * *`). The visits waited until 08:20
next morning and the WhatsApp lists, which read `patient_visit`, were a day behind. And when reception's Docterz export does not
come, the staff page says so but the owner hears nothing.

**The change.** Two NEW files and three cron lines. No live file is changed; no service is restarted.

**A. `/root/finance/patient_sync_on_arrival.sh`** (modelled on `/root/wa/fu_push_on_arrival.sh`, S376) — every 5 minutes:
- a workbook that is not the one the last GOOD run read (no stamp yet = new, once) and has been left alone for 60 seconds starts
  the SAME `/root/finance/finance_patient_sync.py` the hourly line runs: same interpreter, `-B`, no arguments, from root's home,
  into the same `patient_sync.log`. The stamp moves only when the sync exits 0. So visits reach the records within about
  5 minutes of the PC sending them, at any hour except 01:25–02:15 at night;
- `finance_patient_sync.py` is not changed and its hourly line stays (the backstop);
- never two at once: its own lock; a sync already running — the hourly one, or one started by hand under any path (a python
  process whose arguments name the file; an editor that has the file open does not count) — means the tick is skipped; the
  hourly run's own minute (HH:20, 08–21) is left to it; the sync is stopped after 240 seconds;
- nothing between 01:25 and 02:15 (the nightly backups); a failed sync is tried again, not before 15 minutes;
- one line per run or skip-with-a-reason in `/root/finance/patient_sync_on_arrival.log` (cut back before 200 KB); a quiet tick
  says nothing and only moves that log's time (the pulse `job_pulse.py` reads).
  Off: `/root/finance/_off/ALL_OFF` or `/root/finance/_off/PATIENT_SYNC_ON_ARRIVAL_OFF`.

**B. `/root/portal/docterz_missing_alert.py`** (beside `ring_common.py` and `callback_clock.py`, whose push it uses):
- 21:45 Monday–Saturday: if today's consultation report or follow-up log has not reached the server — by the staff page's own
  rule (`aaj_kaam._exports_confirmed`: `status='current'`, `business_date` = the day, and a follow-up log whose `due_to` reaches
  the next call day) — ONE notification to the owner, in English, naming which, and the day and date it is about;
- 08:15 Monday–Saturday: the same about the LAST WORKING DAY (Tuesday–Saturday: yesterday; Monday: Saturday); one more if it is
  still missing. Nothing is said on a Sunday;
- a day the clinic did not work says nothing: the sign of work is a slip logged that day (`slip`, `state='ok'`) or either export
  of that day; neither report and no slip = no notification;
- the words say only what is read or what holds "unless / until" the export comes — nothing a later export can make false;
- one notification per report-day per slot (`/root/portal/docterz_missing_alert_state.json` and its `.lock`, made on the box):
  two runs at the same instant cannot both send; a run stopped mid-way leaves the slot taken and the next run says "outcome not
  known" and sends nothing more;
- a push no device took is tried twice more, 60 seconds apart; after the third the private ntfy topic of the morning freshness
  alarm is used (`NTFY_URL` in `/root/finance/freshness.conf`, read on the box, never printed). Only a delivery counts as told;
- `ring_common` may tidy its own device list when it pushes (it drops a device the push service reports as gone) — its doing,
  as on every push;
- `--dry` says what it would send; `--date` always means `--dry`; `--probe` is the installer's read-only gate; any error = one
  log line, exit 0. The message carries no patient data.
  Off: `/root/finance/_off/ALL_OFF` or `/root/finance/_off/DOCTERZ_MISSING_ALERT_OFF`.

**The cron lines** (added from a good read of the crontab, each once, read back):
```
*/5 * * * * /bin/bash /root/finance/patient_sync_on_arrival.sh >> /root/finance/patient_sync_on_arrival.log 2>&1 # S811_PATIENT_SYNC_ON_ARRIVAL
45 21 * * 1-6 /root/wa/venv/bin/python3 -B /root/portal/docterz_missing_alert.py --slot evening >> /root/portal/docterz_missing_alert.log 2>&1 # S811_DOCTERZ_MISSING_ALERT
15 8 * * 1-6 /root/wa/venv/bin/python3 -B /root/portal/docterz_missing_alert.py --slot morning >> /root/portal/docterz_missing_alert.log 2>&1 # S811_DOCTERZ_MISSING_ALERT
```

**The installer** proves first that the box is what the kit was built on (`finance_patient_sync.py` there; its hourly line in
the crontab exactly as read; the inbox folder; `docterz_export` and the slip table answer the alert's own reads;
`ring_common.push_user` loads), counts the phones registered for the owner's login, runs the walk and its control on the box,
places the two files (read back against their pins), adds the three lines, reads the alert dry and runs the on-arrival script
once for real — it folds whatever is waiting, which is the wanted effect. The crontab is handled byte-wise (`LC_ALL=C grep -a`)
and is never written if a line that is not this kit's would be lost; this kit's lines are known by their tag at the END of
the line. If anything is red after placing, the files come out and the crontab goes back byte for byte. With no phone
registered the last line says so. `DRY=1` before `bash`: every gate, nothing written (not together with `--undo`).

**Install** (after the publish), one line on the server:
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s811kit && cp -rp /root/deploy/repo/deploy_kits/S811_FEED_ON_ARRIVAL /tmp/s811kit && bash /tmp/s811kit/install_S811_FEED_ON_ARRIVAL.sh
```
Undo: `bash /tmp/s811kit/install_S811_FEED_ON_ARRIVAL.sh --undo` (the three lines and the two files out; visits already folded stay).

**Walk:** `walk_s811.py <kit dir>` — 67 checks on a made-up root (a stand-in sync, a stand-in push, a made-up `docterz_export`,
a listener of its own on 127.0.0.1 for the ntfy fallback; no patient, no number). `--control`: the same walk on two broken
copies it makes itself (the stamp moving on a failed sync; the once-per-slot guard removed) must go red.
