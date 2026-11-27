# S968_REGISTER_PUSH — the day check told to Shavez and reception

**The parent, S531, 27-Nov-2026 · his "PROCEED" 10:40 IST.**

## What happened (26-Nov)

A dressing was charged in the evening: Rs 100, cash. It had no parchi and no Docterz entry.

**Evening:** the evening check (S960) only looks for parchis missing from Docterz. It found none and sent "sab parchi Docterz mein". The Docterz export at 20:34 held 5 X-rays and no procedure.

**Morning:** Shavez saved the register, cash 7,700 against Docterz's 7,600. The day check carded it ("Rs 100 — Docterz entry missing, patient not found · procedure · cash"), but nobody was told. The heading above still read "all agree", because it compared UPI alone.

## What this kit does

1. **The push.** `NEW /root/finance/register_push.py` sends a push to `REGPUSH_TO` (shavez, reception) through the call-back clock's own route. It runs the moment a register is saved (the Save starts it in its own process and never waits), and every 5 minutes from 08:00 to 21:55 (cron `# S968_REGISTER_PUSH`). The messages:
   - **New line on a day:** "26-Nov: 1 galti — din ki jaanch", with the day check's own words for the lines.
   - **Clean at first look:** "26-Nov: register, Docterz aur parchi sab mile".
   - **Lines fixed after a push:** "26-Nov: sab galtiyan theek".
   - **The same lines, or fewer:** nothing. Each line is told once.
   - **Only the staff's lines:** the Docterz and parchi corrections not yet ticked. Your back-date rows and the "check by hand" lines stay on your page. A partly fixed line (its amount changed) is not a new one. A day whose Docterz export comes days late is still told.

   The push opens the staff's own day check:
   - **Whole lines:** a day whose Docterz export and register are not both in is not judged.
   - **No old news:** a day older than yesterday that the sweep meets for the first time is recorded quietly, so the install brings no push about old days. A Save always judges its own day.
   - **Switches:** `REGPUSH_ON=0` turns the pushes off, and `REGPUSH_SPAWN=0` turns off the Save's start.
2. **The heading.** "all agree" was read off UPI alone. Now:
   - If cash or card differ between the register and Docterz, the heading says "cash differs" (or "card differs") and names both figures.
   - When the bank is not in yet, or the bank differs, the line also names a cash or card difference.
3. **The card.** "Patient not found" now asks for the parchi too ("mareez dhoondein: Docterz mein entry kijiye, parchi na ho to parchi bhi banaiye"). Shavez (and you) get a "Parchi banayein" button on it.

## Files

| live file | FROM | TO |
|---|---|---|
| /root/finance/clinic_register.py | 321f659a | TO_PINS.md5 |
| /root/finance/day_check.py | 6f17979a (S962) | TO_PINS.md5 |
| /root/finance/register_push.py | NEW | TO_PINS.md5 |
| crontab | — | + `# S968_REGISTER_PUSH` |

`register_push` keeps one table of its own, `register_push`: the day, the open lines' keys (no names), the outcome and what was sent.

## Proof

- **walk:** 35/35 on the TO; the control on the FROM is red.
- **cold review:** SAFE, no MUST. Its three SHOULDs are built in: staff lines only, late days still told, amounts not part of a line's name. Its note that Bhati gets no button is reflected above.
- **live shape:** a copy of the database, no push, counts only. Every recent day is judged with no error.
- **The 26-Nov case** on the 27-Nov copy, with the morning's register put back as written:
  - The Save sends ONE push: "26-Nov: 1 galti".
  - A second Save and the sweep stay silent, and the old days are seeded quietly.
  - With Docterz carrying the dressing, the card turns into "X-ray/Proc parchi nahi", and the push says so.
- **Rehearsal:** the installer is run on a made-up root and gives REHEARSAL n/n.

## Install

```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s968kit && cp -rp /root/deploy/repo/deploy_kits/S968_REGISTER_PUSH /tmp/s968kit && bash /tmp/s968kit/install_S968_REGISTER_PUSH.sh
```
