# S636_DAY_CHECK — the day's corrections page (kit S636, session S347, 24-Oct-2026 · D776 stage 1 · F-1017, F-1018)

**Why.** The owner, 23/24-Oct-2026 (D776): *"It should analyse properly, give the missing money details, and Docterz and
parchi required corrections … for shivani alisha, shavez and myself, becomes available as soon as the morning entry is
done, and the Docterz differs becomes a clickable button"* · *"1300 not billed - means Docterz entry is missing"* ·
*"is clarity here better ?"* · *"Here we also write which ones ?"*

**What changes.**
1. NEW `/root/finance/day_check.py` `f223cbf6` — one day, patient by patient: the parchi (done) × Docterz (billed) × the
   register (collected — the referee, counted from the handwritten book) × the bank (UPI). Every correction is one line
   ending in the buttons of the person who makes it: Docterz (Shivani, Alisha, Shavez) *Added / Not paid / Free*,
   *Changed / Not right*, *Found it*; Parchi (Shavez, Bhati) *Fix*, *Remove duplicate*, *Make it ID …*. *Free* and *Not
   paid* are the existing chhoot / radd entries (his Approve / Reject). A tick is kept, never taken as proof: a line
   clears only when the next Docterz export or the parchi shows it. Worked out each time it is read — nothing waits for a
   job. Its one table `day_check_tick` is made on first request.
   Page: `https://followup.dr-manoj.in/finance/clinic/check/<day>` (Hindi for staff, English for him).
2. `/root/finance/clinic_register.py` `38d0cb4f` → `321f659a`, 5 counted edits (`make_s636.py`): mounts day_check
   (guarded — without it the register is as before); the day list's chip opens the day and names the kinds; the Save says
   the day's check at once; the cards under the three records; a chip that is a link looks like one.
3. `/root/finance/owner_console.py` `2b985708` → `32780bcb`, 1 counted edit: his Money section gains the day's line —
   counts only, no patient (e.g. *"22-Oct: Rs 1,300 Docterz entry missing · 2 payment modes wrong · 1 parchi to fix"*),
   and below it each of the six days before that still has lines.

**Proven offline on the 24-Oct bundle's database** (on manojz; patient data never left it, and no patient is named in
this kit): 22-Oct reads exactly as the S343 analysis — Rs 600 (one patient's X-ray) + Rs 700 (UPI, patient not found)
Docterz entry missing, two payment modes wrong (a consultation card -> UPI, an X-ray cash -> UPI), one OPD parchi (an ID
written twice, the billed patient with no parchi); 07-Oct reads Rs 3,000 (one patient's X-ray and slab); 09-Oct reads
*all correct*. 45 days checked in 0.6 s.

**No data step.** One restart of `clinic-finance`.

## Install (on the server)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s636kit && cp -rp /root/deploy/repo/deploy_kits/S636_DAY_CHECK /tmp/s636kit && bash /tmp/s636kit/install_S636_DAY_CHECK.sh
```
`DRY=1` before `bash` runs every gate and the walk, and writes nothing.

## The walk (`walk_s636.py`, 27 checks)
The real Flask shape on a made-up database with made-up patients: the 22-Oct and 07-Oct shapes, a duplicate line, the
day list, the day page in Hindi and English, the Save, every button (tick, re-export clears, Not right, Found it, Free and
Not paid to approval, fix the ID, remove duplicate, permissions, undo, a login with no role), and his console line.
`--old` on the live files turns exactly the 24 S636 checks red and none of the 3 older ones; `--no-day-check` proves the
new register stands without day_check.py.

## Undo
```
\cp -p /root/finance/clinic_register.py.bak_S636_38d0cb4f /root/finance/clinic_register.py && \cp -p /root/finance/owner_console.py.bak_S636_2b985708 /root/finance/owner_console.py && mv /root/finance/day_check.py /root/finance/day_check.py.off_S636 && systemctl restart clinic-finance
```
