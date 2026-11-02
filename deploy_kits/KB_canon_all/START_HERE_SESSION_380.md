# START HERE — SESSION 380 — written at the S375 close (the Sanjeevni chat), 02-Nov-2026 (morning)

**Project: Sanjeevni — Pharmacy & Marg.** Open in a fresh chat in this project, linked to manojz.
1. Follow `OPEN_ROUTINE_v1` (from the clone: `deploy_kits/KB_canon_all/OPEN_ROUTINE_v1.md`). In the device VM, `day_open.py` needs its paths: `--tools $HOME/mnt/Downloads/_kbtools --repo $HOME/mnt/dr-manoj-git/drmanoj-clinic-automation --kb $HOME/mnt/Downloads/ClaudeCowork --ssd $HOME/mnt/ClinicBackup/DrManojClinic_Automation --roots $HOME/mnt/Downloads $HOME/mnt/dr-manoj-git $HOME/mnt/ClinicBackup` (the defaults are Windows paths). Its `--note` writes the day's line.
2. The rulebook for every build is **the charter v1.1 — `claude/S307_BUILD_CHARTER_v1_1.md`** beside the parent's `BUILD_NORM_v1.md` (D704). **The plan of what is left is the System Board's plan, section 9** (steps 0–2 done at this close; step 3 next). The close is `CLOSE_ROUTINE_v1` — this project's `close.json` is in `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S375\close_parts\` (copy it, change what changed).
3. The brief of this close is `S375_BUILD_BRIEF.md`; the Book is `SANJEEVNI_SYSTEM_BOOK_v1_42_S375.md` (§15AG is S375); the kits `deploy_kits\S692_SPINE_BILL_DOT\`, `S693_STOCK_ON_BATCH\`, `S694_VAAPSI_ON_SPINE\`, `S695_COUNT_ON_SPINE\` (all live). The working copies of every FROM / TO file: `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S375\`.

No incident is open. **S692, S693, S694, S695 are live** (1-Nov 08:45; 11:18; 11:19; 17:16). S683, S690, S678, S679, S676, S677, S675, S359's six and S644 (in shadow; `order.source = marg_sheet`) are live.

*FIRST ACT: take your session number from the System Board's `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).*
- **380 is RESERVED for the Sanjeevni chat at this close.** The parent's 379 is open; the Scan App chat's 363 and the NK Pathology chat's 365 are reserved. Take what the board says and say so in your first line.
- **Kit numbers are claimed BEFORE the scratch folder is named (F-515 — broken at S375, F-1087);** D and F numbers the moment they are minted (F-920). Read every PLANNED line on the board before touching a file it names (D646).
- **F-1072:** a build left to start unattended takes its kit number BEFORE it is left.

*Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.* Never `git` there (F-511). **Build road: in the chat itself.** What S339–S375 learnt about building offline (keep it): the live code = the newest bundle + the pending kits' `make_*.py` in order (`D:\Downloads\_kbtools\vps_code\code_nightly.tar.gz`, the database copy `finance_nightly.db.gz` beside it — work in the device VM's `/tmp`, never in a kit folder, F-1041; **delete every database copy before the chat ends, D656**); **the spine can be rebuilt in the VM** — `spine_evidence.py --source $HOME/mnt/Downloads/margsync/MargArchive --out /tmp/…/readings` then `spine_build.py --readings … --out /tmp/…/spine.db --finance-db <copy>`; **flask is not in the VM's python — `pip install --user flask`**; **one device call lasts at most 180 s and nothing survives it in the background — run one installer rehearsal per call**; a walk's controls stand on its OWN rows (F-998); a rehearsal's fake health script answers 302 for any path but healthz; **an installer's journal gate reads the new master's lines only (F-1088)**; a rule that hides is measured on every real bill offered as new (F-1070); a confirmation reads only figures whose day the server holds (F-1071); the pin list is newest-first; the built-in browser on manojz was signed in as `manoj` on 2-Nov (read `/finance/api/whoami` first); the medical PC's refused texts are mirrored on manojz — read their shape masked in the VM, never in the cloud (D656); an independent cold review reads every kit — **at S375 R1 found two blockers (S693's dedupe, S694's refund per unit), both real**; read the owner's screen after every install (F-1034).

---

## 0 · THE WORK — in order

**A · THE OPEN (OPEN_ROUTINE_v1)**

1. **The board** — every message `read:false` to `sanjeevni`, every note; say in one line how many are this project's (at this close: none unread).
2. **The day's checks** — `day_open.py --read` (run it if the page is not today's).
3. **The pin pass** on the newest bundle with `live_pins_S375close.txt`: this project's DECLARED-PENDING 0 (all six CONFIRMED by the 02-Nov bundle). State match · declared-pending · unexplained.
4. **The reception phone** — the card on `https://followup.dr-manoj.in/finance/porders?old=1`: "Last asked the server" within the working day? If silent in working hours, say so to the owner in one line (reception: on charge, unlocked, mobile data on) — F-1089's build is item B1.
5. **S693's first nights** — the expiry watch's run note ("N purchase line(s) since … placed on M batch(es)") and any newly named minus batch, each against its sales. Read only.

**B · THE WORK**

1. **The next small kit (server-only, one kit):** (a) **F-1089** — `porders_s454.py` / `supplier_msg.py`: the order page's disabled WhatsApp button says why ("Reception phone silent since <time> — unlock it, screen on, mobile data on"); a Needs-you line (and the board's line through the parent's ntfy path if it is one call) when `supplier_msg.phone_last` is older than 60 min between 09:00 and 20:00 on a counter day; the parent's console reads `s454_card_facts` — keep its meaning, add fields only. (b) **F-1090** — `reports_tile._month_rows`: STOCK_EXPIRY out (D822), STOCK_VALUATION stays; its selftest adjusted. (c) **F-1028 and F-1025** (section 9 step 3) — after the first scored buying week (the night of 1-Nov); the shadow score must not move. Gate: walks with controls on own rows; old = new on every other figure.
2. **Amir's first visit after S690 / S693 (read only, the owner's login):** the vouchers; the Batch Stock as the third report; the card's confirmation; whether Marg took a STOCK RECEIVE into a blank batch (if not, one line to the owner).
3. **F-1047** — the next medical-PC kit (the owner's OK first; a live PC).
4. **The switch, on his word at D673's bar (earliest ~22-Nov)** — section 9 step 4, Darpan's tab header mock first. **NEVER WRITE `order.source` FROM A KIT WITHOUT HIS WORD** (D673, D785). Then step 5 (three retirement kits) and step 6 (Sanjeevni as its own process).
5. **PARKED by his word:** F-802's permanent fix. **NOT THIS PROJECT'S (D803):** the PC and phone set-up kits (F-1048).
6. **The close** — `CLOSE_ROUTINE_v1`.

**NEVER RUN:** `deploy_kits\S488_DATES_AND_WAITS\deliver_S488.ps1`. **NEVER INSTALL:** `deploy_kits\S638_EXPIRY_WATCH\`, `S672_NONCASH_AT_INGEST\`, `S673_NONCASH_AT_INGEST_R2\` (frozen). **NEVER ADD TO:** Amir's *Aaj ka kaam* list (D690). **NEVER CHANGE THE EXPIRY PAGE ITSELF** without his word (D780, D793). **NEVER CHANGE THE MEANING of a name the parent's console reads** (`supplier_msg.s454_card_facts`, `porders.shortage_summary`, `expiry_watch.newest / now_view / ym_add`, `reports_tile.status`) without a word to the parent (parent_S377_1).

**AMIR NEVER OPENS OR EDITS A SALE BILL (D815).** **AMIR'S SCAN LIST CARRIES ONLY A BILL CLEARLY MISSING FROM MARG; NEVER A FINALISED MONTH (D814).** **A STAFF SCREEN CARRIES ONLY "DO THIS" LINES (D708) — AND A LINE ON IT RESTS ON A FACT NOBODY CAN TAP WRONGLY (D712).** **A SALE IS CASH OR UPI ONLY, NEVER A PARTY (D802).** **NO FIGURE TO TYPE, EVER (charter rule 8).** **A VOUCHER NEVER TAKES MARG BELOW ZERO OR PAST THE SHELF FIGURE (D715).** **A LINE LEAVES THE ORDER LIST ONLY WHEN MARG CLOSES IT (D716); A MISSING MEDICINE GOES ON THE NEXT ORDER BY ITSELF (D757); A SUBSTITUTE NEVER CLOSES A LINE (D760).** **ONLY THE OWNER CHANGES A DEALER'S NUMBER (D731).** **A CLOSING TAKEN BEFORE THE DAY'S FIRST SALE IS THE START OF THAT DAY (D740).** **CLAUDE READS THE PHARMACY BILLS; SARVAM IS OFF (D747).** **THE BUYING MODEL IS SCORED IN SHADOW; THE SWITCH IS HIS WORD (D678, D785).** **CREPE BANDAGES AND LEUKOBAND ARE MEDICINES (D795); HIS RULING ON ONE SIZE IS HIS RULING ON ITS SISTERS (D799).** **A HOME / PROCEDURE MEDICINE BILL IS DEDUCTED AT THE SALE INGEST (D798).** **A RETURN IS THE SPINE'S CREDIT NOTE; THE PATIENT IS SALE_ITEM'S (S677).** **BATCH STOCK UNITS ARE MARG'S LOOS FIGURE (D821).** **THE ONE MONTHLY EXPIRY INPUT IS THE BATCH STOCK (WHOLE STORE); STOCK EXPIRY IS RETIRED (D822).**

**CLOSED BY HIS WORD — DO NOT RAISE AGAIN:** count #1 of 6-Sep (D800); the pack-change build (F-1000); the rescan's number (D759); the orthotic names as Amir typed them (D709); the learnt names (D685); Kedar's July balance; the four appliances' category; the staff's *Aaj ka kaam* lists — the parent's; the bill line's design (D712); the GST composition flow — the parent's; older purchase bills for the name list (D762); a reader for the bank's alert e-mails (D779); the expiry watch's screens (D780, D793); the shape of Kit II (D785); the S335 small list (D796); the screens of the stock check (D800 — backend only); who keeps the PC set-ups current (D803); the October scan mock-up for Amir (30-Oct); D814 needs no monitoring (1-Nov); the Stock Expiry export (D822).

## 1 · THE STANDING OWNER RULINGS

1. **Publishing is HIS double-click** — `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`.
2. **Full paths ALWAYS — including URLs**, each in its own copy block. **ONE line per command.**
3. **Token-lean — never at the cost of verification.** **Plain language. Short chat (03-Sep).** **ALL-CAPS = urgent.**
4. **Mask patient numbers (last 4); never print secrets.** **Nothing live rebuilt without his OK; the manual path stays.**
5. **Sub-agents read screens. Do not hand him diagnostics. When a screen is wrong, read its code first. Never a step that is not his.**
6. **His board carries only what needs him and what he should know — every close answers what he typed there; the plan's section 9 is refreshed at every close.**
7. **His own items are deferred** — name only what has become urgent, and say why. **His approvals are few and arrive together.**
8. **Never put a technical choice to him** (03-Sep) — decide, say it in one line, carry on. **A screen for staff: the mock first (03-Oct).** **When he asks "when", the answer is "now" unless something real waits (28-Oct).** **When he says "only answer me" / "answer me first" / "do not build", answer — build nothing (29-Oct, 30-Oct, 1-Nov).** **"Start the build after <time>" — a scheduled start, its numbers taken before it is left (F-1072).**
9. **The owner can check the reception phone from anywhere** — the card on the `?old=1` page; a test message goes out only when the phone is unlocked with data (1-Nov).
