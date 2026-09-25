# S401_SLIP_LATE_ENTRY — missed parchis, written afterwards, by whoever is at the desk

**The owner, 25-Sep-2026:** a parchi missed on the day has no easy way in afterwards — that day or the next few
days — and Bhati and reception must be able to do it as Shavez does; the X-ray room ticks (UPI, Cash, Done) by
Shavez or Bhati.

**Found first:** Bhati, Alisha and Shivani already hold the tile and the maker role on unit `slips` (S324) — the
room ticks and every form are open to them today; only Shavez has used it (164 of 164 slips). What was missing
is the late entry: a parchi written the next day was dated TODAY, so the night report and the room list saw it
on the wrong day, and a number left *chhoota* on a past day vanished from every screen.

**What changes (slip_log.py only):**
1. Every OPD and X-ray/Proc form has a **Din** choice — Aaj, Kal, … 7 days back. A late parchi is saved on its
   own day; the X-ray form's "pick from OPD" list follows that day. A late parchi never marks other numbers
   *chhoota* (those belong to today); a far-ahead late number still asks *Haan, yahi number* first.
2. A new menu screen **Chhooti parchi** lists every number left *chhoota* in the last 7 days, each with
   **Ab likhein** (opens the right form with the number and the day filled in) and Radd / Kharab; the tile's
   top line counts past days' ones.
3. The **Report** link shows for Bhati as for Shavez.
4. Taking off one's own wrong entry needs no reason on the day it was typed (it used the slip's day).

**Proof.** `walk_s401.py` 108/108 over a scratch copy of the live finance.db on the walk's own books
(90001–90600): Bhati and reception write, fill a chhoota number from yesterday on yesterday, write a
never-entered parchi 3 days back, the window's edges refused/taken, a duplicate late parchi keeps its day on
the way back, Bhati's late X-ray parchi waits in the room and he ticks UPI/Done/Cash, every screen for six
logins. Negative control: the live S398 file puts the same late parchi on today. pyflakes 0.
`slip_log.py` d208f57a → 36405348. Restarts clinic-finance only.
