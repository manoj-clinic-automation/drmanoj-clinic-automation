# S509_FOLLOWUP_DEFAULT_EXPORT — the follow-up log exported as Docterz shows it

Session 304 (parent), 10-Oct-2026. The owner, 22:38: *"we simply open the follow-up logs in Docterz and it shows the default from
date as the current date until one month and we export it as such … no date fields need to be altered."*

## What changes
- **The server** dated a follow-up log by its earliest due date minus one day — which is why reception had to move the start date
  to tomorrow by hand. Now a log's day is **the day it was exported** (India time); an export made **before 1 pm** counts for the
  previous working day (the morning catch-up of a missed evening). Docterz's default export (today → one month) is therefore
  tonight's log, reaches the next call day by itself, and turns reception's evening line green (S508).
- **The tracker on the owner's PC** needs no change: it already anchors a follow-up log to the consultation day (03-Oct: a log
  from 03-Oct → 02-Nov loaded Monday 05-Oct, Sunday skipped).
- **The hint reception reads** under the two lines: *"Follow-up log: Docterz jo date apne aap dikhata hai (aaj se ek mahina) wahi
  rehne dijiye aur export kijiye — date badalne ki zaroorat nahin."*

## Install (his one line on the VPS, after PUBLISH_ALL)
    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S509_FOLLOWUP_DEFAULT_EXPORT/install_S509_FOLLOWUP_DEFAULT_EXPORT.sh

## Undo
    cd /root/finance && \cp -p docterz_pickup.py.bak_S509_b54ce6af docterz_pickup.py && \cp -p aaj_seed.py.bak_S509_bb6bf911 aaj_seed.py && systemctl restart clinic-finance
