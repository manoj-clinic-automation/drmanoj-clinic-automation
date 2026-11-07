# S745_STAFF_CARDS_FIX — the staff cards follow the phone roster · the parent · session 397 · 07-Nov-2026

**For the owner, in two lines.** Missed calls and WhatsApps are now counted against the phone staff on duty (Shivani, Alisha); anyone else — Shavez — is counted only while he is covering, i.e. when no phone staff is on duty. Your own calls are never a card, and a call returned after more than an hour shows as "(+N later)".

## Why
The live read of S744 (07:3x IST 07-Nov): Shavez carried 29 missed calls in 7 days though, by the owner's roster (02-Nov), he answers the line only to cover an absence; the owner's own agent showed as a card; a call returned after the hour was in neither count.

## File
| live file | FROM | TO | what |
|---|---|---|---|
| `/root/portal/calls_console.py` | df484ee5 (S744) | see the installer | `staff_cards()`: the phone staff (setting `PORTAL_PHONE_STAFF`, default `shivani,alisha`); anyone else charged only while no phone staff is on duty; a phone staff member not in the staff list means nobody is counted as covering (said on the card); the owner's agent (first name Manoj) never a card; `cb_later`. |

## Proven (S397, made-up data only)
`walk_s745.py` **71 of 71** (S744's 63 + R1–R8); control on the live page: 6 of 7 new checks red · Chromium green · the installer's read-only proof on the live stores: calls, follow-ups and Call ke baad identical · rehearsed (DRY, install, ALREADY, STOP paths, red restores).

## Install (after the publish; window 04:00–23:30 IST)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s745kit && cp -rp /root/deploy/repo/deploy_kits/S745_STAFF_CARDS_FIX /tmp/s745kit && bash /tmp/s745kit/install_S745_STAFF_CARDS_FIX.sh
```
## Undo
```
\cp -p /root/portal/calls_console.py.bak_S745 /root/portal/calls_console.py && systemctl restart clinic-portal
```
