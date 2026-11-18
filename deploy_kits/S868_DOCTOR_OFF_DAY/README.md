# S868_DOCTOR_OFF_DAY — the parent, S480, 18-Nov-2026

**His word (12:08–12:11 IST 18-Nov):** what to do about the consultation and clinical data reports on days he does not sit (16, 17 and 18-Nov); "proceed" on the plan — plus the Clinic PCs page's second point (the reception PC's "No report") and the lab PC's "Needs a look".

**Found:** on 16 and 17-Nov reception exported the consultation report (empty — no consultations) and the follow-up log. The pickup set the empty report aside ("no date in the file"), so his money page, his console and the 08:15 / 21:45 alert called the day's export missing.

**What changes:**
- **NEW `/root/finance/off_days.py`** — his page `https://followup.dr-manoj.in/finance/console/off-days`: "I am not sitting today", a day ahead (leave), take back. A marked day writes ONE consultation row of the day (0 rows, nothing stored, drive_id `offday:<who>`), so every page and alert that asks for that day's report is satisfied unchanged; reception's evening job then waits for the follow-up log alone.
- **`docterz_pickup.py`** a26c1467 → TO — an empty consultation report belongs to the day it was exported; with no OPD slip that day (or the day marked) it is that day's report (0 rows, not kept) and the day is marked by the server; with OPD slips it is set aside and said. A report with patients clears a mark (he sat). The old empty "no date" ones are no longer shouted.
- **`owner_console.py`** bbe47872 → TO — mounts the page; "No consultations on <day> — you were not sitting"; one link line.
- **`pc_kits.py`** 9353d510 → TO — the reception PC heard within 20 minutes reads **Working** (was "No report"); that word is now "Off or not heard"; the lab PC's item named in fixed words (never the PC's own text — S865 review 3).
- The installer marks **16, 17 and 18-Nov-2026** (his word).
- Already so, no change: the Patients page counts only days with visits ("per open day").

**Proof:** `walk_s868.py` 34/34 on a made-up root (the pickup's empty-report cases, the marks, the page for every role, the two PC words); control red (the live files + the new page: 23/32). Console built on a copy of the live database, old against new: every section read, only "work" changed. Rehearsal: dry, install, again, undo, undo again, red rollback, tamper, live moved, file present, lock held.

**Install:** his publish, then one server line (the installer's head). **Undo:** `bash /tmp/s868kit/install_S868_DOCTOR_OFF_DAY.sh --undo` (the marks stay — they only say "no consultations" for those days).

**Next (S869):** patients whose follow-up fell on a not-sitting day — "Doctor was away — offer a new date" on the call list, and no "missed" WhatsApp to them.

**Cold review (S480):** SAFE TO INSTALL. Built in: LOW 5 (an empty report exported after the day's real one is recorded 'superseded', never shouted). SHOULD 2 (a marked day must not count as a sign of work for the 21:45 / 08:15 push) is built into **S870** (`docterz_missing_alert.py`), installed in the same line. Known limits, recorded: SHOULD 1 — an empty report through the reception PC's direct door is taken once (the door skips bytes it has seen; every empty report has the same bytes); the Drive road takes every one. LOW 3 — "Take back" after an empty report arrived leaves that report as the day's (true: it had no consultations). LOW 4 — an empty report on a day he sat, before any OPD slip is entered, marks the day until the real report comes (his console then says "not sitting"). LOW 7 — a reception PC heard lately whose only note is an old Windows reads Working (the note still shows).
