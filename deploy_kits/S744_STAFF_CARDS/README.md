# S744_STAFF_CARDS — the Call Console's staff performance cards · the parent · session 397 · 07-Nov-2026

**For the owner, in two lines.** Under the follow-ups on the Call Console, one folded line per staff member who handled calls, with their figures on that line: answered of rung, missed on duty, calls made, called back within the hour, WhatsApps answered, not logged, staff ≠ AI, agreed. The line is rose when a missed call on their duty is not called back or a call is not logged, amber when only a staff ≠ AI call waits for you, green when clear; open it to see the calls behind each figure.

## Why
The owner's "Yes" (07:19 IST 07-Nov) to the staff cards — Build B of the Call Console (D819, D820), the Staff section of mock-up R3 (https://claude.ai/artifact/AwBDzfttkYPygGVcrQbTfD). This is part 1: the owner's own view. Part 2 (the next kit): his review buttons (Ask to log · Mark reviewed · Staff right · AI right · Note to staff) and each person's own card on *Aaj ka kaam*, in Hindi, with the dispute tap.

## File
| live file | FROM | TO | what |
|---|---|---|---|
| `/root/portal/calls_console.py` | 72f9769b (S742) | see `install_S744_STAFF_CARDS.sh` | the kit's copy, whole: + `load_duty`, `duty_window`, `staff_cards` and the Staff section. Nothing else on the page changes. Reads only. |

How the cards count:
- **A card** for each MyOperator agent with calls in the window; your own calls are not a card.
- **Duty**: `/root/staff_master.csv` — only user_id, name, the four time columns and active are read, never a pay column; a staff member is matched to an agent by first name, and only when that first name is unique. The first punch of the day from `/root/punches.csv`. Duty runs from the later of the shift start and the punch to the shift end; a Sunday follows the Sunday columns (blank = off).
- **Missed on duty**: an incoming missed call while the person was on duty. **Called back**: a connected call to that number afterwards; within the hour is counted. **Not logged**: an answered call with no outcome filed. **Staff ≠ AI**: the filed outcome and the recording disagree and you have not reviewed it. **WhatsApps**: received while on duty, answered by D820's rule.
- An unreadable staff list or punch log is said on the card; the page never fails for it.

## Proven (S397, cloud workspace, made-up data only — numbers built at run time)
- `walk_s744.py` **60 of 60** (S742's 46 + 14 staff checks); control on the live page: 13 of 14 staff checks red.
- `browser_s744.js` in Chromium at 1366, 1920 and 390 px: green (no sideways scroll, folded, expand / fold all, no script error).
- `proof_s744.py` (on the box in the installer, read-only, counts only): calls, the follow-up list and Call ke baad identical through the live and the new page for today, yesterday and 7 days; each read under 20 s; the page renders with the section.
- Rehearsed on a made-up server: DRY · install · ALREADY · changed live file / tampered kit / lock held STOP · red after placing restores byte-identically.

## Install (on the server, after the publish; window 04:00–23:30 IST)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s744kit && cp -rp /root/deploy/repo/deploy_kits/S744_STAFF_CARDS /tmp/s744kit && bash /tmp/s744kit/install_S744_STAFF_CARDS.sh
```
## Undo
```
\cp -p /root/portal/calls_console.py.bak_S744 /root/portal/calls_console.py && systemctl restart clinic-portal
```
