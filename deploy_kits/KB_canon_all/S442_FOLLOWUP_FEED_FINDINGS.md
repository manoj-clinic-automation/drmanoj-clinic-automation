# S442 — THE FOLLOW-UP FEED — the owner's findings and what was measured (13-Nov-2026, the parent)
*Noted at the owner's word (05:09 IST 13-Nov): "note these here and then in the next session do your working on this, analyze these, review these things, and tell me your final plan there. Do not start to build anything on your own there." Nothing here is built. Counts only; no patient name or number.*

## 1 · What the owner said (his findings, in his order)
1. **The follow-up tracker is set up the old way and the new way at once.** The tracker is on his PC: there the Docterz reports are processed and the follow-up lists, the grace period and the patients who did not turn up are made; the system matches that with the callback tracker; both meet on his call console, where the WhatsApp integration is also largely set up. **The need: set the follow-up tracker up properly now, so that the callback tracker, the call console and the WhatsApp system get a proper feed in time.**
2. **The call console's "called" counts are wrong for the grace-period and older lines.** The folded line says "so many called", but those patients were called on the day of their appointment. They are in the grace period because they did NOT come when they were due — a call made on or before that day is not a call about the miss.
3. **The WhatsApp part of the call console shows as "awaiting" chats that should not be there:** ones he has already replied to (a reply he sent the night of 12-Nov was still shown), a vendor sending pictures of instruments and implants, greetings. Later they read as missed call-backs and confuse.
4. **Now that WhatsApp sending is set up, accurate lists must be generated, filled and matched everywhere** — the follow-up tracker, the callback tracker, the call console, the WhatsApp system.
5. **The tiles:** there are three WhatsApp tiles in the *Call & WhatsApp* group, and the new *WhatsApp messages* tile sits in *Patients*. Retire or update the older tiles and move this one to *Call & WhatsApp*. (Its small line still says "Show only · who would get which message".)
6. **How the next session works:** analysis, review and a final plan put to him. No build without his word.

## 2 · What was measured tonight (for the plan — facts, not proposals)
**Two roads carry the clinic's visits to the server, and they do not arrive together.**
| what | road | reaches the server | who reads it |
|---|---|---|---|
| `patient_visit` — who came, by day | the tracker on the owner's PC makes `Visit_Ledger_Join.xlsx` and pushes it to `/root/wa/followup-inbox/`; `finance_patient_sync.py` folds it in at :20 past each hour, 08:00–21:00 only | when the PC's tracker has been run on the day's log and has pushed | the WhatsApp lists (`wa_ladder.plan`: "seen today", "has come since") |
| `dx_visit` — diagnosis and the follow-up date | Docterz's clinical data report → Drive → `docterz_pickup.py` (every 15 min) → `dx_feed.py` | when that report is exported and reaches Drive | the WhatsApp lists (the follow-up dates) |
| `docterz_export` / `clinic_day_line` — the consultation report, a line per consultation with the clinic ID | the reception PC's export → Drive → `docterz_pickup.py` | the same evening | the owner's command console (money, the day) — **not** the WhatsApp lists |
- **13-Nov, 01:40 IST (the database copy) and 04:57 IST (live):** the consultation report of 12-Nov was taken at 21:15 IST (36 rows; 48 lines, 34 patients in `clinic_day_line`) — while `patient_visit` and `dx_visit` both stopped at 11-Nov. The owner's clinical report, exported about 04:25 IST, had not reached the server by 05:00.
- **Earlier days (the copy of 11-Nov):** 11-Nov's consultation report taken 20:30, clinical 21:30; 10-Nov's 20:45; the clinical rows of 2–7 Nov arrived only on 10-Nov at 19:45.
- **What it does to the WhatsApp lists:** "has come since" is a day or more behind. On 13-Nov the "date passed yesterday" list showed 19 names while the visits of 12-Nov were not in — some of those patients very likely came. Kit S808 holds a dated list until the visit records reach the last clinic day (it waits 90 minutes, then skips the day and says why) — so nothing wrong is sent, **and nothing dated would be sent at all until this feed is right.**
- **The assistant's error of this session (F-1321):** it told the owner that reception's export had not arrived. It had; the page's "visits on record" line is the PC tracker's ledger, not the consultation report.

## 3 · What the next session must lay out before any plan (the assistant's work)
- Every reader of "who came" and "what is the follow-up date" — the PC tracker, the callback tracker (Apps Script), the call console, the Patients page, the staff's lists, the WhatsApp lists — with its source, its road and the hour it is fresh. One table.
- What "called" means on the call console for a missed follow-up: only a call AFTER the due date; what the folded lines count today, read from the page's own code first.
- What "awaiting WhatsApp" means: a chat he has answered; a sender who is not a patient (vendors, greetings); how the console decides today.
- The tiles: the three WhatsApp tiles in *Call & WhatsApp*, what each opens, which are superseded; the move of *WhatsApp messages*.
- Earlier papers to read first: `S431_FABLE_BRIEF_PATIENTS_CALLS.md`, `S433_PATIENTS_STUDY.md`, `S435_FRONT_DESK_FINDINGS.md`, `S437_WHATSAPP_FINDINGS.md`, `S421_RETURN_PATTERN_ANALYSIS.md`; the owner's direction on the two trackers (the memory file on the follow-up tracker); F-1274, F-1276, D919.
- Then ONE plan, in plain words, on what he can see — the lists, the counts, the tiles — for his yes.
