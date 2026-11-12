# START HERE — SESSION 440 — written at the S439 close (the parent), 12-Nov-2026 20:5x IST

**Project: Dr Manoj Clinic — Systems & Automation (the parent).** Open it in a fresh chat in this project **on Claude Fable**, linked to manojz.
1. Follow `OPEN_ROUTINE_v1` (from the clone: `deploy_kits/KB_canon_all/OPEN_ROUTINE_v1.md`). The custom instructions are `COMMON_START_HERE_PROMPT_v1`. **The first call of the open reads the routine and nothing else — no `git` (F-1295).**
2. Read §2A items 1 and 2 of the Runbook (v350), then `S437_WHATSAPP_FINDINGS.md` §1–§2 if the sending is built.
3. **His words for this session (D940, 20:21 IST 12-Nov):** "Keep the Hindi callback recording, busy message for callers parked, proceed with the sending and the helpline in the appointment reminder, and then proceed with the build for sending to real patients … you can check there also before building anything." **And (D941, 20:48 IST):** "Appointment reminder template must be approved in the My Operator panel. So we would like to see that template first and then decide."

*FIRST ACT: take session 440 from `board/_numbers` (RESERVED for the parent at the S439 close).* Counters at this close: **D942 · F-1303 · A-D26 · kit S807 · session 441 next.** Take a kit number BEFORE a scratch folder is named.

*Connected folders:* `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.

Standing rules: as in `START_HERE_SESSION_439.md` and before, plus — **a cold review by a second reader on every kit that touches a sender, a stop list or a patient's message**; **a pin goes into a kit from `md5sum` by the shell, never typed (F-1298)**; **a live file with account notes is read by its code lines (F-1302)**; **the owner pastes only the LAST line of a server run — what must be known is in that line, or is read live**.

## 0 · THE WORK — in order

**A · THE OPEN.** The board; **remind him of the packs page (D713) and of BL Computers (F-1266, F-1268)**. The day page — the parent's DECLARED-PENDING 7 (portal.py 3a0f7cd1, wa_ladder.py cb197293, portal_inbox.py 973cc74f, portal_wa.py e8b27db9, callback_clock.py 70eb1197, waba.py 82f3503b, clinic_state_backup.py 5282b72c): the 13-Nov bundle should confirm all. **The 13-Nov state backup is the first with `wa_ladder.db` and `callback_clock.db` — read its report.** Whether his publish of the S439 records landed.

**B · THREE READS, read-only, counts only (the browser as manoj — `https://followup.dr-manoj.in/finance/api/whoami` first; a helper, never a screenshot in the main chat):**
- **The Inbox's send log since 12-Nov 15:35 IST** (`/portal/inbox/api/sendlog?days=3`, header `X-Inbox: 1`). At 18:19 IST 12-Nov: 3 sent, 0 refused. A refusal with HTTP 500 after the fix is news.
- **The show-only list** (`https://followup.dr-manoj.in/portal/messages`): the six counts (12-Nov: 15 would go, 12 for his tick, none held), the listener's last pass, the stop list, the taken-off list.
- **The Google Business Profile and `contact.dr-manoj.in` as a visitor:** does either show the helpline? (12-Nov 18:19: no, both.) Change nothing by hand.
Then three lines to him.

**C · THE APPOINTMENT REMINDER TEMPLATE — SHOW IT TO HIM FIRST (D941).** A helper reads his MyOperator panel read-only (WhatsApp → templates): `appointment_reminder_1day_ortho` — its exact text, category, language, buttons, status, and how a new one is submitted there. He sees it (his own screen or a faithful copy in the chat). Then his wording with the helpline number — the one put to him at S439 was the present text plus "For any help, call the clinic helpline …". **A new template is submitted in his account only on his word**; approval takes a few days; `portal_wa.py`'s template list and `wa_ladder.py`'s `LISTS` take the new name only after it is approved.

**D · F-1301 — THE OLD BATCH PAGE.** `https://followup.dr-manoj.in/portal/wa/followups` is LIVE, unlabelled, on a list of 13-Aug (120 sendable rows). Its own kit: `portal_followups.py` (7,866 B in the 11-Nov bundle) and the page file in `/root/wa/wa_portal/` read whole; the page refuses a list whose date is not today's and says LIVE or TEST on its face. His word first (one line); he has been told not to use "Send selected" there.

**E · THE SENDING FROM `/portal/messages` (his "build").** A mock-up for him first (a Design canvas or a plain page): one switch per message type, all OFF to start; the time each goes; the daily cap; what went / what was held; "long overdue" on his tick. Then the kit(s), in `wa_ladder.py`'s shape: the rules already there; **never twice for the same follow-up date whichever page sent it** (read the portal's send log — its file and columns are read on the box by a dry line first, F-1291); a test to his own number before the first real send; `http.client`, one request, never a second after it has gone out (F-1297); the stop list read at the moment of sending; a switch that is OFF sends nothing. The first type: "follow-up is tomorrow". Cold review on every kit.

**F · THEN THE ANALYTICS PAGE (Runbook §2A item 3):** the Patients mock-up v16 — his additions, the grey figures, then "build".

**How the mock-up is edited:** as in `START_HERE_SESSION_439.md`.

**Owner-side (board):** the publish (the S439 records; nothing follows) · do not use "Send selected" on the old batch page · look once at the WhatsApp messages page (the new buttons show when someone has said STOP) · tell staff — all four phones ring, the 30-minute reminder, Shavez at 60 · the printed matter and JustDial with the helpline number · BL Computers · the packs page · fingers 20 and Arjun Dev.

**Standing owner rulings:** as in `START_HERE_SESSION_439.md` and before, plus **D940** (the call-back recording and the busy step parked; the sending and the reminder with the helpline are a go) · **D941** (he sees the template in MyOperator first, then decides).

**Learned at S439:**
- **A cold review pays for itself:** two of three kits had a must-fix a walk of my own had passed — a second send after a late answer (S804), a read outside the write lock (S805).
- **The portal's sender is LIVE.** Nothing on `/portal/wa` or `/portal/wa/followups` says so. `GET /portal/wa/templates` and `/portal/wa/followups/data` answer `dry: false`.
- **In the device VM:** flask is not installed — `python3 -m pip install --target /tmp/<x>/pylib flask` and `PYTHONPATH`; a stand-in gateway or portal is a small `http.server` started and killed by `$!` inside ONE call; a rehearsal of more than about two minutes is split (the call's limit is three); a leftover listener is found with `ss -ltnp`.
- **The board's `_numbers` and `_page`** are written through a file (`get` with `out_dir`, a script, `update` / `batch` with `file_path`), pinned; the other chat writes too — a refused write is re-read, not forced.
- **The stop list:** a removal is a row in `optout_removed` with `upto_rid` (the listener's place then); `restop` puts a number back with source "put back by …"; the older file's numbers come back if that file's time is newer than the removal.

*Written at the S439 close, 12-Nov-2026.*
