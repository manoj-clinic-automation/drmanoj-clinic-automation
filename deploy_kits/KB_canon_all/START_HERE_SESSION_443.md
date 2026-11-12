# START HERE — SESSION 443 — written at the S442 close (the parent), 13-Nov-2026 05:3x IST

**Project: Dr Manoj Clinic — Systems & Automation (the parent).** Open it in a fresh chat in this project, linked to manojz.
1. Follow `OPEN_ROUTINE_v1` (from the clone: `deploy_kits/KB_canon_all/OPEN_ROUTINE_v1.md`). **The first device call of the open is `cat` of the routine and NOTHING else — no `git`, not even read-only (F-1312, F-1295).**
2. Read §2A items 1 and 2 of the Runbook (v353), then **`S442_FOLLOWUP_FEED_FINDINGS.md` whole** (canon; also in project knowledge).
3. **His words for this session (D949, 05:09 IST 13-Nov):** "note these here and then in the next session, do your working on this, analyze these, review these things, and tell me your final plan there. **Do not start to build anything on your own there.**"

*FIRST ACT: take session 443 from `board/_numbers` (RESERVED for the parent at the S442 close).* Counters at this close: **D951 · F-1326 · A-D26 · kit S810 · session 444 next.**

*Connected folders:* `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.

Standing rules: as in `START_HERE_SESSION_442.md` and before, plus — **before a list is built on a table, the table's road and its hour are written beside it (F-1316)**; **a date on a page is quoted with the table it comes from; "has not arrived" is said only of the road that was read (F-1321)**; **a line that needs something typed by him asks for it itself (F-1320)**; **a banner that warns is also a gate (F-1317)**; **nothing that comes back from outside is kept or shown as it came (F-1318)**; **the reviewed bytes of a kit are not touched after the review — a later point goes into a later kit, or the reviewer looks again**.

## 0 · THE WORK — in order

**A · THE OPEN.** The board; **remind him of the packs page (D713) and of BL Computers (F-1266, F-1268)**. The day page — the parent's DECLARED-PENDING 3 (wa_ladder.py c5e6a74c, wa_ladder_send.py d8f16f00, portal_wa.py 4b153e7d): the 14-Nov bundle should confirm all, with the cron line `# S808_WA_LADDER_SEND`. Whether his publish of the S442 records landed. The server's state-backup report for `wa_ladder.db` / `callback_clock.db` (still unread).

**B · THREE READS, read-only, counts only (in the browser as manoj — `https://followup.dr-manoj.in/finance/api/whoami` first; a page's own script summarises, so no name or number comes back):**
- **The sending** (`https://followup.dr-manoj.in/portal/messages/api/plan`): the switches ON, the tests confirmed, sent / tried today, `fresh.last_visit` and `fresh.last_dx`, the six counts. At 04:57 IST 13-Nov: 0 ON, 0 confirmed, 0 sent; visits and follow-up dates up to 11-Nov; 22 / 0 / 0 / 19 / 0 / 12.
- **The Inbox's send log** (`/portal/inbox/api/sendlog?days=3`, header `X-Inbox: 1`).
- **The Google Business Profile and `contact.dr-manoj.in` as a visitor:** the helpline? (The website's call links end in the helpline's last four; the old number's last four are on the WhatsApp links.)
Then three lines to him.

**C · THE FOLLOW-UP FEED — ANALYSIS, REVIEW, ONE PLAN. NO BUILD.** The findings paper is the brief. In order:
- The readers and their roads, ONE table: the PC tracker (`D:\Downloads` side; what it makes, when it pushes — `Patient_Master_Join.xlsx`, `Visit_Ledger_Join.xlsx` → `/root/wa/followup-inbox/` → `/root/finance/finance_patient_sync.py`, cron `20 8-21 * * *`), the callback tracker (Apps Script), the call console (`/root/wa/portal_console.py`, `console.db`), the callback clock (`/root/portal/callback_clock.py`), the Patients page, the staff's lists, the WhatsApp lists (`/root/portal/wa_ladder.py` — `patient_visit`, `dx_visit`, `online_booking`), the consultation report (`/root/finance/docterz_pickup.py` → `docterz_export`, `clinic_day_line`), the clinical report (`dx_feed.py` → `dx_visit`). For each: source, road, the hour it is fresh, who reads it.
- F-1322: what the call console's folded lines count as "called" — read the page's code first; the rule he wants: only a call after the due date.
- F-1323: how "awaiting WhatsApp" is decided; an answered chat; a sender who is not a patient.
- F-1324: the tiles in *Call & WhatsApp* — what each opens, which are superseded; *WhatsApp messages* to move there; its small line.
- The owner's standing direction on the two trackers (project memory: the follow-up tracker file) and the earlier papers: `S431_FABLE_BRIEF_PATIENTS_CALLS.md`, `S433_PATIENTS_STUDY.md`, `S435_FRONT_DESK_FINDINGS.md`, `S437_WHATSAPP_FINDINGS.md`, `S421_RETURN_PATTERN_ANALYSIS.md`; F-1274, F-1276; D919.
- **Then ONE plan to him, in plain words, on what he can see** (the lists, the counts, the tiles, what reception and he must do each day and by when). A mock-up where a screen changes. **Wait for his word before any kit.**

**D · IF HE ASKS (not before):** the tests and the first switch are his; the template wordings (`S442_WA_TEMPLATE_FEATURES_STUDY.md`); the Patients page (mock-up v16).

**Owner-side (board):** the publish (the S442 records; nothing follows) · the tests to his phone, when he wants; the switches stay OFF until the feed is settled · tell staff — all four phones ring, the 30-minute reminder, Shavez at 60 · the printed matter and JustDial with the helpline · BL Computers · the packs page · fingers 20 and Arjun Dev · paste the new start text (v1.1) into the four projects (the Sanjeevni chat's item).

**Standing owner rulings:** as in `START_HERE_SESSION_442.md` and before, plus **D948** (reports and X-rays are not in Docterz; the post-visit message is his new template) · **D949** (the feed: analysis and a plan, no build on its own; the WhatsApp tile to *Call & WhatsApp*).

**Learned at S442:**
- **The cold review paid three times over:** a number that had replied STOP could have been messaged; a gateway's words could have reached the page; a failed reader looked healthy. The walk was green each time. The reviewer was given the kit, the live files, the rigs — and wrote a fuzzer that checked twelve rules at the moment of each request.
- **The lists' source was never asked "by what road, at what hour":** `patient_visit` is the PC tracker's ledger. The consultation report had been on the server for eight hours.
- **Kits can be built whole in the cloud workspace** (code staged from the PC's working copies, made-up stores, Flask and Chromium present), committed to the PC, read back by md5; the base pins confirmed against the night's bundle (on the PC about 03:15 IST) by a follow-up the session set for itself.
- **A kit that changes a live file need not ship it:** S809 remakes both files on the box and places them only when their md5 equal its pins.
- **The MyOperator panel** (as him): the template list shows name, category, status, text and buttons — not the language code or the blanks' keys.

*Written at the S442 close, 13-Nov-2026.*
