# S792_PUNCH_CLOCK — the attendance machine's wrong clock: today's punches corrected, and corrected by themselves from now on

**The owner, 11-Nov-2026 11:21 IST:** Shavez's punch shows 6:55 a.m.; he came around 10. — **12:10 IST:** *"Ok and correct today's
punches also"* (his word waives the attendance freeze D247 for this change).

**What was wrong.** Not a time zone: the server, his console and the Call Console are on India time. A punch's time is the
machine's own clock, and on 11-Nov it ran **1 h 39 min to 2 h 57 min behind** (it advanced 29 minutes while 1 h 46 min passed —
a clock that stops whenever the power goes, i.e. a weak backup battery), and still 13 min behind at 10:22. The server received
each punch at the true time (`received_at`). History (2,369 punches since 21-Jun): 90 % arrive within a minute; the late ones
are mostly backlogs sent in a burst after the machine was offline — their machine time is the right one.

**What changes**
| file | from | to |
|---|---|---|
| `/root/attlistener_v2.py` | 52b26645 (S535) | 588ea08e |
| `/root/finance/owner_console.py` | 2c77db31 (S791) | ba977832 |
| `/root/punches.csv` | 11-Nov's rows that arrived alone and were >5 min off | `datetime` = the server's time; the machine's kept in the new last column `machine_time` |

- **The listener:** when the machine has been *steadily online* for the last 5 minutes (it calls about every 12 s; no silence over a
  minute) and a punch's machine time is more than 5 minutes off, the server's time is stored and the machine's kept in
  `machine_time`; a `CLOCK` line goes to its log. A punch sent after an outage keeps the machine's time. De-duplication stays on the
  machine's time, so a re-sent punch never doubles. Every reader of the file (the register, salary, console, dashboard) takes
  `datetime` and needs no change.
- **Today:** `fix_punch_clock.py` (run once by the installer, listener stopped) gives 11-Nov's punches that arrived ALONE (no other
  punch received within a minute) and were >5 min off the server's time: Ranjeet 08:08, Shivani 09:00, Shavez 09:31, Darpan 09:54,
  Amir 10:22. A burst is left alone. Backup of punches.csv kept beside it.
- **His console (Attendance):** an amber line on any day with corrected punches — how far off the clock was, how many punches
  carry the server's time, and that the machine's clock and battery need BL Computers.

**Proof.** Walk 15/15 (a listener on a spare port: not-yet-online keeps the machine's time, steadily-online 3 h off stores the
server's, a re-send adds nothing, a right clock is untouched, after an outage the machine's time stands, a restart keeps the
de-dup; the one-off on a file shaped like 11-Nov — exactly the five, the burst and other days byte-identical, a second run
changes nothing; the console line); the CONTROL red on the live files; make_s792 byte-exact; rehearsal install / ALREADY / undo.

## Install (after the publish), one line on the server
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s792kit && cp -rp /root/deploy/repo/deploy_kits/S792_PUNCH_CLOCK /tmp/s792kit && bash /tmp/s792kit/install_S792_PUNCH_CLOCK.sh
```
Undo: `bash /tmp/s792kit/install_S792_PUNCH_CLOCK.sh --undo` (the two files back; the corrected times stay — they are the true ones).
