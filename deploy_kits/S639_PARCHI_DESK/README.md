# S639_PARCHI_DESK — the parchi desk (kit S639, session S347, 24-Oct-2026 · D775)

**Why.** The owner, 23/24-Oct-2026 (D775): *"all the entries need to be on one page only"* · *"Parchi - a warning helps in
duplicate entries cases, remaining ones go to shavez, and i also get have this desk available to me, if any need is there
due to staff absence"* · *"Flow should be quick and easy as much as possible, with minimum typing, by taps"*.

**What changes.**
1. NEW `/root/finance/parchi_desk.py` `99b7e43b` — one page, `https://followup.dr-manoj.in/finance/slips/desk`: OPD, X-ray/Proc
   and Blood test side by side, the day's list below, no reload. OPD: the next number filled, the ID typed, the name shown,
   Enter saves. X-ray/Proc: the patient tapped from the day's OPD chips (a new OPD parchi appears as a chip at once, and
   other screens see it within 8 s), items tapped from tiles (most-used first, a search box), side R/L/B tapped, the rate
   filled, Chhoot / Free with a reason only on a tap; the same item twice warns at once — *Dono rakhein* / *Yeh wali hatao*.
   Blood test: the patient tapped, Save. *Wapas* (Undo) takes back your own last entry of today. A day picker for a late
   parchi (the LATE_DAYS window). Hinglish for staff, English for the owner (a checker). Every save goes through
   `slip_log.log_slip` / `items_from_form` — the book, gaps (*Haan, yahi number*), a far-ahead ID (*ID sahi hai*), the
   late day, the chhoot to approval: unchanged. No table of its own.
2. `/root/finance/slip_log.py` `2419c536` → `93103944`, 7 counted edits (`make_s639.py`): mounts the desk (guarded); the
   room's Paid / Done ticks are no longer asked for (the night report's "room did not tick", the menu's "Paid/Done baaki",
   the room badge — Paid comes from Docterz at night, billed is done); *Parchi desk* first in the menu and linked from the
   report; and a fault this kit's walk found: a parchi line with a chhoot on the day's list raised a TypeError that took the
   whole slips menu down (three `%s`, two values). It never fired live — no line has carried a chhoot yet.
The old pages and the phone menu stay as they are, as the fallback.

**Proven.** `walk_s639.py` 27/27 on a made-up database (`--old` on the live file: 21 S639 red, 0 older red;
`--no-desk`: the new slip_log stands); a real browser walk 19/19 (type → Enter → the chip → tiles → the duplicate warning →
side → chhoot → save → blood → undo → the gap prompt; no script error; no sideways scroll at 375 px); the page and its state
on the 24-Oct database on manojz (19 OPD, 10 X-ray/Proc, 1 blood on 22-Oct; 61 tiles, most-used first).

**No data step.** One restart of `clinic-finance`.

## Install (on the server)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s639kit && cp -rp /root/deploy/repo/deploy_kits/S639_PARCHI_DESK /tmp/s639kit && bash /tmp/s639kit/install_S639_PARCHI_DESK.sh
```
## Undo
```
\cp -p /root/finance/slip_log.py.bak_S639_2419c536 /root/finance/slip_log.py && mv /root/finance/parchi_desk.py /root/finance/parchi_desk.py.off_S639 && systemctl restart clinic-finance
```
