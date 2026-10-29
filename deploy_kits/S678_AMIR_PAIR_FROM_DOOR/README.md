# S678_AMIR_PAIR_FROM_DOOR — Amir's step 4 trusts the server's own door

*Sanjeevni session 367 · 29-Oct-2026 · on the owner's "yes" of 09:46 IST.*

## For the owner
Amir's report screen no longer tells him a report "never came" (and to close Excel and export again) when the server already has it.
If his file has reached the server but the clinic PC (manojz) has not yet passed its lines on, the screen says
*"Report server par aa gayi hai — padhi ja rahi hai … Aapko dobara nahi nikaalni"* and turns green by itself when the lines arrive.
A report that is really wrong or missing still says so, as before.

## What happened (29-Oct)
Amir exported the pair as text at 09:07 and 09:08 (the bill-wise again as Excel at 09:25). The server's door took all of them
VERIFIED within seconds (`mi_file`). Step 4 reads only `purchase_export`, which manojz's ten-minute pull fills — and manojz did not
pull from 00:22 to 09:43 IST (asleep). After six minutes step 4 said *"nahi aayi — Dobara banaiye … file band kijiye"*. False.

## What changes — one file
`/root/finance/amir_day.py` **3b7dae35 → a0907b74** (six anchored edits in four places, `make_s678.py`):
1. `KIT` names this kit.
2. `_door_receipt(cx, kind, day, first)` — the newest VERIFIED `mi_file` of type `PURCHASE_<kind>` that Marg stamped on the day,
   with non-empty dates whose printed period covers the 1st..day, received by the server no earlier than his newest step-2 tap
   (a bill entered after it leaves the re-export band in charge).
3. `_export_state` — **today only**: no `purchase_export` row (or only an OLDER non-covering one) while the door holds such a file →
   `wait` with `door = hh:mm`; never `bad`. Not a tick: the tick and the bill list still need `purchase_export`'s rows.
   A past day keeps its own reading.
4. `_step4` — the door wait's line (*"Server par hh:mm baje aa gayi — padhi ja rahi hai"*); when every wait is a door wait and
   nothing is bad or not yet taken, the head *"Report server par aa gayi hai"* with no minutes. **A bad or not-taken report beside a
   door wait keeps the old red / not-yet head and the "Dobara banaiye" buttons.**

Untouched: the re-export band, the owner's 48-hour line, the tick, the bills, every other page.

## The proof
`walk_s678.py`: 21 checks on the walk's OWN rows (day 2099-01-15 / 2000-01-15, md5 `walk678…`, user WALK678; removed after) + the
old = new proof on every real day since 1-Sep. Offline on the 29-Oct database copy: **22 of 22 green**; old = new on 24 days, 48
report-days identical, 0 differences; the control on the live file **6 S678 check(s) red · 0 older red · 15 green**.
An independent cold review found one blocker (a door wait hid a bad report's head) and three should-fix items (a stale door file
over a newer wrong-period export; a door file older than a later bill tap; an empty start date) — all four mended and walked (U, V,
T, R, S). The installer was rehearsed on a made-up root: dry, install, again (ALREADY INSTALLED), forced red at [8/8] (restored to
3b7dae35), a moved pin (STOP), a corrupt kit (refused); the lock released every time.

## Install (the server)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s678kit && cp -rp /root/deploy/repo/deploy_kits/S678_AMIR_PAIR_FROM_DOOR /tmp/s678kit && bash /tmp/s678kit/install_S678_AMIR_PAIR_FROM_DOOR.sh
```
Gates → pin 3b7dae35 → rebuild from the box's bytes → compile on both pythons → walk + old = new on a copy → backup
`amir_day.py.bak_S678_3b7dae35` → place → md5 read-back → restart clinic-finance → healthz 200 → `/finance/amir/day` 302 → journal
clean → walk on the placed file → lock released. Red after placing: the file back, finance restarted.

**Undo:** `\cp -p /root/finance/amir_day.py.bak_S678_3b7dae35 /root/finance/amir_day.py && systemctl restart clinic-finance`

## Named, not done
- The lasting cure — the server loading the purchase lines from its own door file, so manojz is not needed at all — is the board
  plan's step 5 (*the second parser + the manojz senders*), not this kit.
- A door wait has no time limit on Amir's screen: if manojz stays down all day, he sees "padhi ja rahi hai" until midnight; the
  owner's day table says "its rows wait for the manojz leg".
