# START HERE — SESSION 447 — written at the S443 close (the parent), 13-Nov-2026 10:3x IST

**Project: Dr Manoj Clinic — Systems & Automation (the parent).** Open it in a fresh chat in this project, linked to manojz.
1. Follow `OPEN_ROUTINE_v1` (from the clone: `deploy_kits/KB_canon_all/OPEN_ROUTINE_v1.md`). **The first device call of the open is `cat` of the routine and NOTHING else — no `git`, not even read-only (F-1312, F-1295).**
2. **THE S443 CLOSE WAS HELD AT THE BUILD (the device shell was down, F-1336). FINISH IT FIRST:** `claude/S443_CLOSE_HELD_NOTE.md` in project knowledge has the steps; the parts are in `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S443\close_parts\`. If the canon already shows an S443 close, this step is done.
3. Read §2A items 1 and 2 of the Runbook, then **`S443_FOLLOWUP_FEED_PLAN.md` whole** (canon; also in project knowledge; §7 wins over §5).
4. **His words for this session:** 06:38 IST 13-Nov "Screens mockups are all ok" (D957); 10:12 IST — Step 2 is built in a fresh session (D958).

*FIRST ACT: take session 447 from `board/_numbers` (RESERVED for the parent at the S443 close).* Counters at this close: **D959 · F-1343 · A-D30 · kit S815 · session 448 next.** **A number is taken only by a write that moves the counter (F-1339); `_numbers` costs about 70,000 tokens to read.**

*Connected folders:* `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`. The PC tracker's program folder (`C:\followup_tracker_local_test_kit\local_test_kit\followup_tracker`) was a per-session grant (Y278): if this session needs it, ask again in ONE request.

Standing rules: as in `START_HERE_SESSION_443.md` and before, plus — **round one of a review builds the must-fixes only, the rest goes to a later kit; he is told the expected time when a build starts; the second look starts the moment the fixed bytes are final (F-1341)**; **a roster line is quoted from his latest word, not from an old D (F-1338)**; **an installer that edits a shared file proves by count and by hash that every line not its own came through (F-1340)**; **the clock is read before any time is written (F-1337)**.

## 0 · THE WORK — in order

**A · THE OPEN.**
- **The device shell and the VM's disk, first (F-1336):** does `echo ok` answer; how full is `/sessions`. If the shell is down, the file tools still work — say so on the board in one line and go on with what they allow.
- **The held S443 close** (step 2 above), then name the publish to him.
- **F-1330 — two kits carry the number S811** (the Sanjeevni chat's S811_MARG_WATCH_SMALL; ours S811_FEED_ON_ARRIVAL, live since 10:07 IST 13-Nov). Settle it before any new kit number is taken; nothing installed is renamed without his OK.
- The board; **remind him of the packs page (D713) and of BL Computers (F-1266, F-1268).**
- The day page (`TZ=Asia/Kolkata`) — the parent's DECLARED-PENDING 5: NEW `patient_sync_on_arrival.sh` 9b41c26f, NEW `docterz_missing_alert.py` 9cc227e1 and their three cron lines (`# S811_PATIENT_SYNC_ON_ARRIVAL`, `# S811_DOCTERZ_MISSING_ALERT`), `wa_ladder.py` c5e6a74c, `wa_ladder_send.py` d8f16f00, `portal_wa.py` 4b153e7d — the 14-Nov bundle should confirm all.
- **Whether the 9:45 pm alert's first run (13-Nov) and the on-arrival fold logged rightly** — `/root/portal/docterz_missing_alert.log` and `/root/finance/patient_sync_on_arrival.log` are on the server: read what the bundle or his console shows; **ask him for nothing.**
- Still unread: the server's state-backup report for `wa_ladder.db` / `callback_clock.db`. Owed: the first-session-of-the-day measure of project knowledge.

**B · THREE READS, read-only, counts only (in the browser as manoj — `https://followup.dr-manoj.in/finance/api/whoami` first):**
- **The sending** (`https://followup.dr-manoj.in/portal/messages/api/plan`). At 05:31 IST 13-Nov: 0 of 6 switches on, 0 tests confirmed (five tests sent by him at 05:29; "tomorrow" not yet), sent today 0; `fresh.last_visit` 2026-11-11, `fresh.last_dx` 2026-11-12; tomorrow 23 (22 go, 1 held) · date passed yesterday 11 · long overdue 12 for his tick.
- **The Inbox's send log** (`/portal/inbox/api/sendlog?days=3`, header `X-Inbox: 1`): 4 sent, 0 refused since the fix.
- **The Google Business Profile and `contact.dr-manoj.in` as a visitor:** the helpline? (13-Nov: the old number only; the website's 5 call links carry the helpline, its JSON-LD telephone the old number.)
Then three lines to him.

**C · STEP 2 OF THE FOLLOW-UP FEED — the three approved screens** (mock-up v1: `https://claude.ai/artifact/8J3R3QtW9awbajmLN4rmic`), **kit by kit, each cold-reviewed, must-fixes only in round one; tell him the expected time when each build starts:**
- **(a) The tiles (F-1324; `portal.py`:134–658):** *WhatsApp messages* → *Calls & WhatsApp*, small line "Daily patient messages · switches · what went"; retire *Follow-up WhatsApps* and *WhatsApp Approvals* (its service stopped and kept).
- **(b) The Call Console's follow-up lines (F-1322; `calls_console.py`:819 and the folded line):** "Called today N of M" large, "Reached K", "Earlier days, after the due date: x called · y reached"; only patients not visited (D893); each patient's last reached with Play (D899).
- **(c) WhatsApp awaiting (F-1323; `calls_console.py`:435–506):** per chat; an accepted reply or an answered call clears; ok / thanks / greeting after our reply does not reopen; midnight does not cut; "Done — no reply needed" and "Not a patient" with undo.
Read each live file whole from the newest bundle first (F-472); `portal.py` and `calls_console.py` are the parent's own.

**D · THEN STEP 3 — the tracker's move** (about three sessions; A-D29, D956): the lists made on the server from reception's two evening exports by the PC tracker's own rules; the follow-up log the source of dates; a replay of the past month's archived evenings before install, then one switch, the PC kept as the spare; the data folder copied once, the PC folder a frozen archive. **Step 4:** one ladder (Today · Grace 1–3 · Missed 4–10 · Long overdue 11–60), one "came back" rule (D893), "on medicines" (D919), staff outcomes closing rows, the Clinical report's extras.

**Owner-side (board):** the publish of the S443 records (named once the held close is placed) · confirm the five tests on `https://followup.dr-manoj.in/portal/messages` and send the "follow-up tomorrow" test · "After today's visit" may be switched on when he wishes; the date-based switches wait for the tracker's move · tell the four staff (the phones ring together, the 30-minute reminder, Shavez at 60) · the helpline on printed matter and JustDial · BL Computers · the packs page · fingers 20 and Arjun Dev · the template features he wants.

**Standing owner rulings:** as in `START_HERE_SESSION_443.md` and before, plus **D956** (the Clinical data report is his own export, at night or next morning — it enriches, never makes a list wait; a missing reception export comes to HIM; the folded lines show that day's calls prominently, earlier days additionally, and hold only patients not visited; Shivani the morning follow-up calls, Shavez fallback only, Alisha grace and older 4–6 pm) · **D957** (the three Step-2 screens, as on mock-up v1) · **D958** (Step 1 as built; Step 2 in a fresh session).

**Learned at S443:**
- **One program on his PC makes every list** (`processor.py`, every 5 minutes); the visits of 12-Nov waited a night because the PC pushed 58 seconds after the last hourly fold. S811 folds on arrival.
- **A two-file kit took 3 h 15 min** — the fix round of eleven points was the longest part, and a server restart cut the second look. Must-fixes only in round one.
- **Kits can be built and placed with the device shell down** (cloud workspace + the file tools) — but `close_build.py` cannot run, so the close is held.
- **A line of text on the board does not take a number** — S811 went to two chats (F-1330).

*Written at the S443 close, 13-Nov-2026.*
