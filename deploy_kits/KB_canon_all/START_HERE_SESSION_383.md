# START HERE — SESSION 383 — written at the S380 close (the Sanjeevni chat), 03-Nov-2026 (late morning)

**Project: Sanjeevni — Pharmacy & Marg.** Open in a fresh chat in this project, linked to manojz.
1. Follow `OPEN_ROUTINE_v1` (from the clone: `deploy_kits/KB_canon_all/OPEN_ROUTINE_v1.md`). In the device VM, `day_open.py` needs its paths: `--tools $HOME/mnt/Downloads/_kbtools --repo $HOME/mnt/dr-manoj-git/drmanoj-clinic-automation --kb $HOME/mnt/Downloads/ClaudeCowork --ssd $HOME/mnt/ClinicBackup/DrManojClinic_Automation --roots $HOME/mnt/Downloads $HOME/mnt/dr-manoj-git $HOME/mnt/ClinicBackup` (the defaults are Windows paths). Its `--note` writes the day's line.
2. The rulebook for every build is **the charter v1.1 — `claude/S307_BUILD_CHARTER_v1_1.md`** beside the parent's `BUILD_NORM_v1.md` (D704). **The plan of what is left is the System Board's plan, section 9** (steps 0–2 done; step 3 next — this session's build). The close is `CLOSE_ROUTINE_v1` — this project's `close.json` is in `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S380\close_parts\` (copy it, change what changed).
3. The brief of this close is `S380_BUILD_BRIEF.md`; the Book is `SANJEEVNI_SYSTEM_BOOK_v1_43_S380.md` (§15AH is S380); the kit `deploy_kits\S702_OWNER_REPORT_NOTICES\` (live). Its working copy: `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S380\kit\`.

No incident is open. **S702 is live** (11:08 3-Nov). S692 – S695, S683, S690, S678, S679, S676, S677, S675, S359's six and S644 (in shadow; `order.source = marg_sheet`) are live.

*FIRST ACT: take your session number from the System Board's `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).*
- **383 is RESERVED for the Sanjeevni chat at this close.** The parent's 382 is open; the Scan App chat's 363 and the NK Pathology chat's 365 are reserved. Take what the board says and say so in your first line.
- **Kit numbers are claimed BEFORE the scratch folder is named (F-515);** D and F numbers the moment they are minted (F-920). Read every PLANNED line on the board before touching a file it names (D646).

*Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.* Never `git` there (F-511, F-1103 — read `.gitignore` as a file). **Build road: in the chat itself.** What S339–S380 learnt about building offline (keep it): the live code = the newest bundle + the pending kits' `make_*.py` in order (`D:\Downloads\_kbtools\vps_code\<date>.code_nightly.tar.gz`, the database copy `<date>.finance_nightly.db.gz` beside it); **the device VM's `/sessions` disk can be full — work in `/tmp/s###w` (chmod 700), never in a kit folder (F-1041); delete every database copy before the chat ends (D656)**; **flask for the VM python: `python3 -m pip install --no-cache-dir --target /tmp/s###w/py flask`, then `PYTHONPATH`**; one device call lasts at most 180 s; **a file written in the cloud and copied to the PC is read back by md5 before use (F-1099)**; **run `deploy_kits\NO_PHONE_NUMBERS.py --files-from <list> <repo>` on the kit's files before naming the publish (F-1098)**; a walk's controls stand on its OWN rows (F-998) and a walk must drop its own folder from `sys.path` so the kit's copy never answers for the root's; an installer's journal gate reads the new master's lines only (F-1088); the built-in browser on manojz is signed in as `manoj` (read `/finance/api/whoami` first); an independent cold review reads every kit — **at S380 it found the one BLOCKER (F-1100)**; read the owner's screen after every install (F-1034).

---

## 0 · THE WORK — in order

**A · THE OPEN (OPEN_ROUTINE_v1)**

1. **The board** — every message `read:false` to `sanjeevni`, every note; say in one line how many are this project's (at this close: none unread).
2. **The day's checks** — `day_open.py --read` (run it if the page is not today's).
3. **The pin pass** on the newest bundle with the CURRENT pin list: this project's DECLARED-PENDING 4 (`reports_tile.py` 0598072c, `reports_watch.py` adbb21be, `porders_s454.py` 5de2a4b8, `owner_notice.py` 2bc96912) — the 04-Nov bundle should confirm them; the crontab line `owner_notice.py tick` in the bundle's `crontab.txt`. State match · declared-pending · unexplained.
4. **S702's first days** — on the bundle's database copy in the VM: `owner_notice` rows (made / sent / how — every row sent once, by the clinic app; none given up); `owner_notice.log` if the bundle carries it. Read only. The salt list overdue line went on 3-Nov; the valuation reminder at 20:00 each evening until it is in.

**B · THE WORK**

1. **The buying model's step-3 kit (server-only) — the owner's word at the S380 close: "build in next session":** **F-1028** (the fold's "last list stood on" line) and **F-1025** (the spine's voucher classing), now that the first scored buying week has run (scored the night of 1-Nov). Gate: walks with controls on own rows; the shadow score must not move; old = new on every other figure. **NEVER WRITE `order.source` FROM A KIT WITHOUT HIS WORD** (D673, D785).
2. **Amir's first visit after S690 / S693 (read only, the owner's login):** the vouchers; the Batch Stock as the third report; the card's confirmation; whether Marg took a STOCK RECEIVE into a blank batch (if not, one line to the owner). His "Amir's work ✓" message says when he came.
3. **F-1047** — the next medical-PC kit (the owner's OK first; a live PC).
4. **The switch, on his word at D673's bar (earliest ~22-Nov)** — section 9 step 4, Darpan's tab header mock first. Then step 5 (three retirement kits) and step 6 (Sanjeevni as its own process).
5. **PARKED by his word:** F-802's permanent fix. **NOT THIS PROJECT'S:** the PC and phone set-up kits (F-1048, D803); the device VM's `/tmp` left-overs (F-1102, the parent's).
6. **The close** — `CLOSE_ROUTINE_v1`.

**NEVER RUN:** `deploy_kits\S488_DATES_AND_WAITS\deliver_S488.ps1`. **NEVER INSTALL:** `deploy_kits\S638_EXPIRY_WATCH\`, `S672_NONCASH_AT_INGEST\`, `S673_NONCASH_AT_INGEST_R2\` (frozen). **NEVER ADD TO:** Amir's *Aaj ka kaam* list (D690). **NEVER CHANGE THE EXPIRY PAGE ITSELF** without his word (D780, D793). **NEVER CHANGE THE MEANING of a name the parent's console reads** (`supplier_msg.s454_card_facts`, `porders.shortage_summary`, `expiry_watch.newest / now_view / ym_add`, `reports_tile.status`) without a word to the parent (parent_S377_1).

**THE OWNER IS TOLD WHEN THE MARG WORK IS DONE — EVERY DAY, SUNDAYS TOO (D825); A NEW MESSAGE GOES THROUGH `owner_notice.py`, ONCE, ITS TITLE PLAIN.** **AMIR NEVER OPENS OR EDITS A SALE BILL (D815).** **AMIR'S SCAN LIST CARRIES ONLY A BILL CLEARLY MISSING FROM MARG; NEVER A FINALISED MONTH (D814).** **A STAFF SCREEN CARRIES ONLY "DO THIS" LINES (D708) — AND A LINE ON IT RESTS ON A FACT NOBODY CAN TAP WRONGLY (D712).** **A SALE IS CASH OR UPI ONLY, NEVER A PARTY (D802).** **NO FIGURE TO TYPE, EVER (charter rule 8).** **A VOUCHER NEVER TAKES MARG BELOW ZERO OR PAST THE SHELF FIGURE (D715).** **A LINE LEAVES THE ORDER LIST ONLY WHEN MARG CLOSES IT (D716); A MISSING MEDICINE GOES ON THE NEXT ORDER BY ITSELF (D757); A SUBSTITUTE NEVER CLOSES A LINE (D760).** **ONLY THE OWNER CHANGES A DEALER'S NUMBER (D731).** **A CLOSING TAKEN BEFORE THE DAY'S FIRST SALE IS THE START OF THAT DAY (D740).** **CLAUDE READS THE PHARMACY BILLS; SARVAM IS OFF (D747).** **THE BUYING MODEL IS SCORED IN SHADOW; THE SWITCH IS HIS WORD (D678, D785).** **CREPE BANDAGES AND LEUKOBAND ARE MEDICINES (D795); HIS RULING ON ONE SIZE IS HIS RULING ON ITS SISTERS (D799).** **A HOME / PROCEDURE MEDICINE BILL IS DEDUCTED AT THE SALE INGEST (D798).** **A RETURN IS THE SPINE'S CREDIT NOTE; THE PATIENT IS SALE_ITEM'S (S677).** **BATCH STOCK UNITS ARE MARG'S LOOS FIGURE (D821); THE BATCH STOCK IS AMIR'S THIRD REPORT EVERY VISIT (S690).** **THE ONE MONTHLY EXPIRY INPUT IS THE BATCH STOCK (WHOLE STORE); STOCK EXPIRY IS RETIRED (D822).**

**CLOSED BY HIS WORD — DO NOT RAISE AGAIN:** count #1 of 6-Sep (D800); the pack-change build (F-1000); the rescan's number (D759); the orthotic names as Amir typed them (D709); the learnt names (D685); Kedar's July balance; the four appliances' category; the staff's *Aaj ka kaam* lists — the parent's; the bill line's design (D712); the GST composition flow — the parent's; older purchase bills for the name list (D762); a reader for the bank's alert e-mails (D779); the expiry watch's screens (D780, D793); the shape of Kit II (D785); the S335 small list (D796); the screens of the stock check (D800 — backend only); who keeps the PC set-ups current (D803); the October scan mock-up for Amir (30-Oct); D814 needs no monitoring (1-Nov); the Stock Expiry export (D822); how and when he is told of the Marg work (D825).

## 1 · THE STANDING OWNER RULINGS

1. **Publishing is HIS double-click** — `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`.
2. **Full paths ALWAYS — including URLs**, each in its own copy block. **ONE line per command.**
3. **Token-lean — never at the cost of verification.** **Plain language. Short chat (03-Sep).** **ALL-CAPS = urgent.**
4. **Mask patient numbers (last 4); never print secrets.** **Nothing live rebuilt without his OK; the manual path stays.**
5. **Sub-agents read screens. Do not hand him diagnostics. When a screen is wrong, read its code first. Never a step that is not his.**
6. **His board carries only what needs him and what he should know — every close answers what he typed there; the plan's section 9 is refreshed at every close.**
7. **His own items are deferred** — name only what has become urgent, and say why. **His approvals are few and arrive together.**
8. **Never put a technical choice to him** (03-Sep) — decide, say it in one line, carry on. **A screen for staff: the mock first (03-Oct).** **When he asks "when", the answer is "now" unless something real waits (28-Oct).** **When he says "only answer me" / "answer me first" / "do not build", answer — build nothing.** **"Build in next session" — the next chat's first build (3-Nov).**
9. **His phone gets the clinic app's messages (3-Nov); ntfy is the fallback.** His login is on the call-ring list — if the rings bother him, the parent takes him off it.
