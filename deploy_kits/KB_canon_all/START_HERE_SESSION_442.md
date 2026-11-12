# START HERE — SESSION 442 — written at the S440 close (the parent), 12-Nov-2026 22:3x IST

**Project: Dr Manoj Clinic — Systems & Automation (the parent).** Open it in a fresh chat in this project **on Claude Fable**, linked to manojz.
1. Follow `OPEN_ROUTINE_v1` (from the clone: `deploy_kits/KB_canon_all/OPEN_ROUTINE_v1.md`). The custom instructions are `COMMON_START_HERE_PROMPT_v1` (v1.1 once he has pasted it). **The first device call of the open is `cat` of the routine and NOTHING else — no `git`, not even read-only (F-1312, F-1295: it has now slipped twice running).**
2. Read §2A items 1 and 2 of the Runbook (v352), then **`S440_WA_SENDING_PLAN.md` whole** (canon; also in project knowledge), then `S437_WHATSAPP_FINDINGS.md` §1–§2.
3. **His words for this session:** D940 (20:21 IST 12-Nov) "proceed with the build for sending to real patients" · D946 (21:41 IST) "Keep the templates as such and proceed." · D947 (22:21 / 22:22 IST) "Timings ok" and "Ok" to a ceiling of 150 a day, all five automatic messages built together, each with its own switch, every switch his.

*FIRST ACT: take session 442 from `board/_numbers` (RESERVED for the parent at the S440 close).* Counters at this close: **D948 · F-1316 · A-D26 · kit S808 · session 443 next.** Take a kit number BEFORE a scratch folder is named.

*Connected folders:* `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.

Standing rules: as in `START_HERE_SESSION_440.md` and before, plus — **what a request says about a patient (number, name, words) is never handed to a sender: the server's own record is**; **a claim in a kit's README is a walk check with the same sentence**; **a loop that sends is read for what a failure in the middle leaves on the screen (F-1313)**; **the cold reviewer is given the live file, the kit, the page's script and a rig, and asked to RUN probes**.

## 0 · THE WORK — in order

**A · THE OPEN.** The board; **remind him of the packs page (D713) and of BL Computers (F-1266, F-1268)**. The day page — the parent's DECLARED-PENDING 8 (portal.py 3a0f7cd1, wa_ladder.py cb197293, portal_inbox.py 973cc74f, portal_wa.py e8b27db9, callback_clock.py 70eb1197, portal_followups.py ed1121ec, waba.py 82f3503b, clinic_state_backup.py 5282b72c): the 13-Nov bundle should confirm all. **The 13-Nov state backup is the first with `wa_ladder.db` and `callback_clock.db` — read its report.** Whether his publish of the S440 records landed.

**B · THREE READS, read-only, counts only (a helper in the browser as manoj — `https://followup.dr-manoj.in/finance/api/whoami` first; never a screenshot in the main chat):**
- **The Inbox's send log since 12-Nov 15:35 IST** (`/portal/inbox/api/sendlog?days=3`, header `X-Inbox: 1`; summarised inside the page's script so no number or name comes back). At ~21:30 IST 12-Nov: 4 sent, 0 refused.
- **The show-only list** (`https://followup.dr-manoj.in/portal/messages`): the six counts (12-Nov: 15 would go, 12 for his tick, none held), the listener's last pass, the stop list.
- **The Google Business Profile and `contact.dr-manoj.in` as a visitor:** does either show the helpline? (12-Nov ~21:30: no, both.) Change nothing by hand.
Then three lines to him.

**C · THE SENDING FROM `/portal/messages` — THE BUILD (the plan is the spec).**
- The first reads, whole, on the newest bundle: `/root/portal/wa_ladder.py` (cb197293), `/root/portal/portal_wa.py` (e8b27db9 — `send()` and `_log()`), how `portal.py` reads the token and `PORTAL_WA_DRYRUN` (`_cfg_get`), the crontab (the `# S798_WA_STOP_LISTENER` line).
- A NEW file beside `wa_ladder.py` holds the sending; `wa_ladder.py` gains the page's controls and doors only. The built page follows the mock-up v2 (`https://claude.ai/artifact/7kYVwTpLj5ZsdkyiXgJPWj`).
- The plan's thirteen rules: each one a walk check and a mutation. All switches OFF at install. A test to his own phone before a switch can be turned on (his number on the server line — never in the repository).
- The page run in Chromium at 400 and 1100 px; the installer rehearsed on a stand-in root; **a cold review by a second reader BEFORE it is placed**; his publish, ONE server line, read live as manoj. **He turns the first switch on — never the assistant.**
- If it is too large for one kit: kit 1 = the store, the switches and the page (still sending nothing); kit 2 = the timed run and the sender arm. Each with its own review.

**D · THEN THE ANALYTICS PAGE (Runbook §2A item 3):** the Patients mock-up v16 — his additions, the grey figures, then "build".

**How the sending mock-up is edited:** a plain page — the file `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S440\wa_sending_mock_v2.html`; read the artifact by its url first, then publish with `url`. Every name on it is made up.

**Owner-side (board):** the publish (the S440 records; nothing follows) · look once at the old batch page — it now says LIVE and refuses the August list · tell staff — all four phones ring, the 30-minute reminder, Shavez at 60 · the printed matter and JustDial with the helpline number · BL Computers · the packs page · fingers 20 and Arjun Dev · paste the new start text (v1.1) into the four projects (the Sanjeevni chat's item).

**Standing owner rulings:** as in `START_HERE_SESSION_440.md` and before, plus **D946** (the templates stay as they are; no new template) · **D947** (the sending's terms: the timings, a ceiling of 150, every switch his).

**Learned at S440:**
- **The cold review paid again:** the walk was 36/36 while the kit's own README claimed something only half true (only the number was checked for an old tab). The reviewer ran 21 mutations and ~25 installer runs.
- **A live fault found by reading the loop, not the page:** the old send loop left every row ticked after a failure — a second press repeated sends (F-1313).
- **The page file of the batch page is not in the nightly bundle** (`/root/wa/wa_portal/`); the repository keeps a copy in `portal_kit/wa_portal/`. A kit that needs it changes the server's answer, not the file.
- **A server can change what a page sends without touching the page file:** a small script in the strip adds a header to the page's own request. If the live page ever differs, the header is missing and the door refuses — the safe side.
- **Kits may be built in the cloud workspace when no patient data is involved** (code from the bundle staged by the file tools, made-up stores, flask and Chromium present) and committed to the PC; pins by `md5sum`; read back in place.
- **`board/_page` has a hard cap (F-1311);** `_numbers` is trimmed to 40 claims before ~200 KB.
- **The MyOperator panel:** templates at `https://in.app.myoperator.com/whatsapp/templates`; no preview — the card is the text; "Create New Template" opens a first-step dialog (name, language, account, category) that makes no draft; **two WABA accounts in the selector — the live one's id ends 3538 (F-1314).**

*Written at the S440 close, 12-Nov-2026.*
