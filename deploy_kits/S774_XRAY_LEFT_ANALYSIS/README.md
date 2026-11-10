# S774_XRAY_LEFT_ANALYSIS — why the parked X-ray pictures still need a person (READ-ONLY)

**The owner, 10-Nov-2026 13:01 IST:** *"I do not want to leave any work for staff in Check karein as much as possible."*
After S772 (installed 12:57) the box proof left 41 of 70 parked pictures for a person. This kit, on a scratch copy of finance.db
(deleted after), plays three S772 filing runs, then sorts every picture still parked by why — using the dates and clinic IDs read
from the films (`xray_filmdate`) — and counts what each candidate extra rule would place. Counts only, by mail; nothing live written.

Run (after the publish), one line on the server:
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S774_XRAY_LEFT_ANALYSIS/run_S774.sh
```
