# S870_AWAY_DAY_CALLS — the parent, S480, 18-Nov-2026

**His word ("proceed", 12:11 IST 18-Nov):** patients whose follow-up fell on a day he is not sitting appear on the call list as "Doctor was away — offer a new date". S868's second half; it reads S868's `clinic_off_day` (no table = nothing changes).

**What changes (all `/root/portal/`, the parent's):**
- `calls_console.py` efd51956 → TO — the Call Console's follow-up row says **"Dr Manoj was away that day — offer a new date"**; nothing else on the list moves.
- `portal_followups.py` ed1121ec → TO — the follow-up WhatsApp batch never offers a message for such a row, and says why.
- `wa_ladder.py` c5e6a74c → TO — the WhatsApp ladder holds its "tomorrow", "date passed" and "long overdue" messages for a follow-up due on such a day (it would invite the patient to, or blame him for, a day the doctor was not there) — "Dr Manoj was away that day — offer a new date by a call".
- `docterz_missing_alert.py` 9cc227e1 → TO — S868's review SHOULD 2: a not-sitting mark is no sign the clinic worked, so a marked day with the clinic shut sends no 21:45 / 08:15 push.

**Proof:** `walk_s870.py` 17/17 on made-up data (the ladder, the batch page, the Call Console on S817's own made-up stores, the push), control on the live files red; S817's walk on the new page as on the live one (48/48, mutations 10/10); S811's walk on the new push 67/67; on the box `proof_s870.py` reads the live stores read-only (counts only): the list's bands old = new, the rows marked away = the rows due on a not-sitting day. Rehearsal: dry, install, again, undo, undo again, red rollback, tamper, live moved, lock held.

**Install:** after S868, in the same server line. **Undo:** `bash /tmp/s870kit/install_S870_AWAY_DAY_CALLS.sh --undo`.

**Cold review (S480):** SAFE TO INSTALL. Built in: SHOULD 1 (the Call Sheet's "28-Dec" on a January list is last December's — the year nearest today's list; a year written in the cell wins); LOW (the mark is no sign of work only when no real report of the day is there; an online-booking reminder for a not-sitting day is held too). Known, left: a Call Sheet date cell or an unreadable finance.db reads "not away" (fails open, as before); `/root/wa/wa_approve.py` (stopped and disabled since S860) and the manual WhatsApp page are not changed.
