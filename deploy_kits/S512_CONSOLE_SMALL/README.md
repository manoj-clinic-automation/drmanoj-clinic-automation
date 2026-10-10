# S512_CONSOLE_SMALL — the console's small kit (Club F, 2)

Session 304 (parent), 10-Oct-2026. The owner's list, item 8.

## What changes on his console — https://followup.dr-manoj.in/finance/console
- **Today's work follows his panel** (F-779): each person's list exactly as they see it — only the lines he switched on, his own
  lines, the green *done* rows (S508) — in his English; what waits to be tapped and what was tapped, by whom, when; **each
  person's tasks with their answers** (done / could not be done, the note, a link to close it); a list he switched off says so.
- **The System line carries its age** (F-774): *"34 of 34 feeds fresh (as of 10-Oct 03:10, 9 hours ago)"*; a reading older than a
  day says *"The freshness check last ran … — too old to call anything fresh"*, in amber.
- **Flags in words** (F-795): *pos_diff* → "the POS machine's UPI total differs from the bank's"; the two MPR flags too.

## Install (his one line on the VPS, after PUBLISH_ALL)
    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S512_CONSOLE_SMALL/install_S512_CONSOLE_SMALL.sh

## Undo
    cd /root/finance && \cp -p owner_console.py.bak_S512_4819eceb owner_console.py && systemctl restart clinic-finance
