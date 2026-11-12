# START HERE — SESSION 439 — written at the S437 close (the parent), 12-Nov-2026 17:5x IST

**Project: Dr Manoj Clinic — Systems & Automation (the parent).** Open it in a fresh chat in this project **on Claude Fable**, linked to manojz.
1. Follow `OPEN_ROUTINE_v1` (from the clone: `deploy_kits/KB_canon_all/OPEN_ROUTINE_v1.md`). The custom instructions are `COMMON_START_HERE_PROMPT_v1`.
2. **Read `S437_WHATSAPP_FINDINGS.md` (canon and project knowledge)**, then §2A items 1 to 3 of the Runbook.
3. **His order for this session (D939, his words 17:32 IST 12-Nov):** "First, set up the WhatsApp items in the fresh session, and then we will proceed for the analytics page."

*FIRST ACT: take session 439 from `board/_numbers` (RESERVED for the parent at the S437 close).* Counters at this close: **D940 · F-1295 · A-D26 · kit S804 (S803 taken by the Sanjeevni chat's S438 at 17:55 IST) · session 440 next.** Take a kit number BEFORE a scratch folder is named (the Sanjeevni chat's 438 is reserved and mints too).

*Connected folders:* `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.

Standing rules: **never run `git` in the device shell (F-1289)**; **a `_config` file is never printed — a value is read by its key inside the program that uses it (F-1290)**; a device commit over an existing file is read back by md5 (F-1262); scratch in the device VM's `/tmp` with `TMPDIR`; every script written to `03_WORKING_PAPERS\S439\` as it is made; patient rows stay on manojz or inside the page being read — counts only come out (D656); read the clock before a time is written anywhere (F-510, F-1283); a gate on a live answer is written from a read of that answer (F-1265); a public page is checked the way a visitor gets it (F-1286); a program of the box is tried before it is trusted (F-1285); a background helper is read back (F-1287); no number in the repository, and **no copy of a live file that holds one in a kit (F-185, F-1293)**; **where a kit's data comes from is read on the box by its own dry line (F-1291)**; **no repair kit for a fault at somebody else's service before one read-only table from the box shows the mechanism (F-1292)**.

## 0 · THE WORK — in order

**A · THE OPEN.** The board; **remind him of the packs page (D713) and of BL Computers (F-1266, F-1268)**. The day page — the parent's DECLARED-PENDING 5 (portal.py 3a0f7cd1, wa_ladder.py ca0334b4, portal_inbox.py 973cc74f, portal_wa.py e8b27db9, callback_clock.py 70eb1197): the 13-Nov bundle should confirm all. Confirm the S437 close's canon placed and whether his publish landed. The project-knowledge measure if this is the day's first open (88% on 12-Nov before the close's tranche).

**B · THREE READS, ten minutes, read-only, counts only (the browser as manoj — `https://followup.dr-manoj.in/finance/api/whoami` first):**
- **The Inbox's send log since 12-Nov 15:35 IST** (`/portal/inbox/api/sendlog?days=3`, header `X-Inbox: 1`): first tries ok / refused, retries, by route. At 17:16 IST 12-Nov: 2 sent, 0 refused. A refusal with HTTP 500 after the fix is news — read its row before anything else.
- **The show-only list** (`https://followup.dr-manoj.in/portal/messages`): today's six counts, rows held and why, the listener's last pass, the stop list.
- **The Google Business Profile and `contact.dr-manoj.in` as a visitor:** does either show the helpline? (12-Nov 11:35: no, both.) Change nothing by hand.
Then three lines to him.

**C · THE WHATSAPP ITEMS (Runbook §2A item 2), in order:** (a) `waba.py` onto the new road — F-1294, its own kit on S802's pattern; (b) the show-only list watched; (c) a way to take a number off the STOP list; (d) `wa_ladder.db` into the state backup; (e) his four decisions, one line each — when sending starts, the Hindi "we will call you back" wording, a busy step in the call flow, the appointment reminder with the helpline; (f) the sending itself **only on "build"**, one message type at a time.

**D · MYOPERATOR'S TICKET 691386 (D938):** after 1 or 2 days of B's reads, the whole picture to him — the Inbox, the tracker's relay, the approve page — and the ticket's text decided with him. **Nothing is sent to MyOperator before he says.** The finding to offer: their authorizer refuses the company header when its name arrives in another letter-case (the proof table is in the findings paper).

**E · THEN THE ANALYTICS PAGE (Runbook §2A item 3):** the Patients mock-up v16 — his additions, the grey figures, then "build".

**How the mock-up is edited:** a Design canvas — read `project/Main.dc.html` AND read the artifact by its url first (a publish is refused otherwise), save under one root folder, change, publish with `url`, `root`, `file_path` (small changes as `edits`); `project/canvas.json` carries the board's height. Strings inside its script are single-quoted: no plain apostrophe in them.

**Owner-side (board):** the publish (the S437 records; nothing follows) · look at the WhatsApp messages list once · his four decisions (C e) · tell staff — all four phones ring, the 30-minute reminder, Shavez at 60 · the printed matter and JustDial with the helpline number · BL Computers · the packs page · fingers 20 and Arjun Dev.

**Standing owner rulings:** as in `START_HERE_SESSION_437.md` and before, plus **D937** (the show-only list and its order; the profile and contact page left to change by themselves) · **D938** (nothing to MyOperator until he decides the text) · **D939** (the WhatsApp items first, then the analytics page).

**Learned at S437:**
- **urllib re-cases header names; `http.client` does not.** MyOperator's gateway cares. Anything new that calls their API is written on `http.client`.
- **The Inbox's own send log is the instrument:** `/portal/inbox/api/sendlog?days=N` gives every try with its route, status and retry count; a number needed for a send can be taken inside the page from a row and never printed.
- **The device shell and the cloud cannot reach MyOperator's API host** — a probe of it runs on the server, inside a kit, sending nothing (fresh made-up keys get a clean 401/403 from a healthy road).
- **`patient_ref.mobile` holds the last four digits only, on the box too;** the full mobile for a patient is in `/root/wa/console.db` `patients` (the Call Console's list).
- **Background processes in the device shell die between calls, and `pkill -f` on a string in its own command line kills the shell** — start and stop a stand-in by `$!` inside one call; an installer run takes about a minute, so two per call.

*Written at the S437 close, 12-Nov-2026.*
