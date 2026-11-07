# S748_MISSED_PEOPLE — net missed leads each staff card · the parent · session 400 · 07-Nov-2026

**For the owner, in two lines.** Each staff card on your Call Console now opens with **Net missed**: the patients who rang during that person's duty and were never reached afterwards, either by a call back or by getting through when they rang again. For example: "Net missed: 3 patients · 16 missed calls from 9 patients, 6 reached later · 39/55 answered …". The line is rose whenever net missed is above zero. Staff see the same at the top of their own card ("Jinse baat nahin hui: 3 log").

## Rules
- A missed call you marked reviewed still counts in net missed. It is a fact, not a verdict.
- A dispute you accepted takes the call out.
- Calls stay counted as calls everywhere else.

## Why
The owner asked at 10:01 IST on 07-Nov whether "39 of 55" counts raw calls or persons, and said "yes" at 10:02 to counting patients. At 10:06 he said "yes" to net missed as the lead figure, in patients.

## Files
| live file | FROM | TO |
|---|---|---|
| `/root/portal/calls_console.py` | df484c7d (S747) | f233b851 |
| `/root/finance/aaj_kaam.html` | dc684e46 (S747) | 791fbf8b |

`make_s748.py` builds both from the live bytes with counted edits.

## Proven (S400, made-up data only)
- `walk_s748.py`: 103 of 103 (S747's 98 plus M1–M5). The control on S747's live page turns all 5 M checks red and keeps the 98 earlier checks green.
- S747's walk on the new page: 98 of 98. S745's walk on the new page: 71 of 71.
- Chromium at 1366 and 390 px: 30 of 30.
- The installer runs the walks, the control and S747's read-only proof on the live stores (every figure identical) before writing anything.

## Install (after the publish; window 04:00–23:30 IST)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s748kit && cp -rp /root/deploy/repo/deploy_kits/S748_MISSED_PEOPLE /tmp/s748kit && bash /tmp/s748kit/install_S748_MISSED_PEOPLE.sh
```
## Undo
```
bash /tmp/s748kit/install_S748_MISSED_PEOPLE.sh --undo
```
