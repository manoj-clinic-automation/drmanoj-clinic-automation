# S733_EXIT_CODE_GUARD — an exit never leaves a machine code live · the parent · session 394 · 06-Nov-2026

**For the owner, in one line.** When someone leaves, the exit now carries their attendance-machine number by itself, and ticking *removed from the biometric device* retires that number for good — it refuses if no number can be found, and never changes a date already recorded.

## Why (F-1147)
An exit opened from the Add staff page carried no machine number, so the *removed from the biometric device* tick retired nothing and the leaver's number stayed live (staff 20: S725 retired it by hand). And when an exit did carry a number already retired, the tick moved the retirement date to the day of the tick.

## What it changes — `/root/finance/joiner_app.py` 6305b05d → be2bf7e5 (make_s733.py: 7 counted edits on the live bytes)
- **Opening an exit:** the number is found from the person's exact name — only numbers still live on the code register count (the register's own rows of that name, and that name's joining records). Never a first name, never a login: *Arjun* (20, left) and *Arjun Dev* are two people. Two numbers for one name = none taken. A number typed at the open that the register gives to someone else is refused.
- **The tick:** the number is the typed one, else the exit's, else found then. None → refused, nothing ticked. A typed number different from the exit's, or ANY number the register gives to another person (typed, on the exit or found) → refused. A number from before the register is entered first. A number already retired keeps its date. `last_day` (yyyy-mm-dd, not in the future) is the retirement date, else today.
- The page shows, under the step, what the tick does. `/finance/staff/api/healthz` says `kit: S733`. Joining is untouched.

## Proven
- `walk_s733.py` **36 of 36** on a made-up register through the file's own routes. Control (the live file): **26 red** — including check 36, the live shape of EXIT-2026-0002, whose 30-Sep date the live file would move to the day of the tick.
- Independent cold review R1: NOT SAFE (2 blockers — a login match could retire a new joiner's live number for an old namesake; a retired number could let the tick pass while another stayed live) and 5 should-fix; all built (checks 29–35). R2: SAFE TO INSTALL; its three points built (a found number is used only when the register gives it to that same name; the live-shape read stops when an exit that carries a number would be refused; no compiled files in the kit).
- `live_shape_s733.py` on the 05-Nov database copy (in the PC's VM): every one of the 12 live codes found again from its own name; with the 06-Nov exits simulated, staff 20's tick keeps 30-Sep and a no-code exit retires only the number the register gives to that leaver. The installer runs it again on a read-only copy of today's register before placing anything.
- The installer rebuilds the file from the box's own bytes first.

## Changed on purpose
An exit opened on a bare login, or for a leaver whose only number is already retired, is now refused at the tick instead of ticking with nothing retired. The page sends no number on that tick, so Claude supplies it (the refusal says so).

## Install (after the publish)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s733kit && cp -rp /root/deploy/repo/deploy_kits/S733_EXIT_CODE_GUARD /tmp/s733kit && bash /tmp/s733kit/install_S733_EXIT_CODE_GUARD.sh
```
## Undo
```
bash /tmp/s733kit/install_S733_EXIT_CODE_GUARD.sh --undo
```
