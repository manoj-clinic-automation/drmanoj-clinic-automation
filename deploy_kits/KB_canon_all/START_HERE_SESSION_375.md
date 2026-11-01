# START HERE — SESSION 375 — written at the S369 close (the Sanjeevni chat), 01-Nov-2026 (morning)

**Project: Sanjeevni — Pharmacy & Marg.** Open in a fresh chat in this project, linked to manojz.
1. Follow `OPEN_ROUTINE_v1` (from the clone: `deploy_kits/KB_canon_all/OPEN_ROUTINE_v1.md`). In the device VM, `day_open.py` needs its paths: `--tools $HOME/mnt/Downloads/_kbtools --repo $HOME/mnt/dr-manoj-git/drmanoj-clinic-automation --kb $HOME/mnt/Downloads/ClaudeCowork --ssd $HOME/mnt/ClinicBackup/DrManojClinic_Automation --roots $HOME/mnt/Downloads $HOME/mnt/dr-manoj-git $HOME/mnt/ClinicBackup` (the defaults are Windows paths). Its `--note` writes the day's line.
2. The rulebook for every build is **the charter v1.1 — `claude/S307_BUILD_CHARTER_v1_1.md`** beside the parent's `BUILD_NORM_v1.md` (D704). **The plan of what is left is the System Board's plan, section 9** (D800), plus this close's item B2. The close is `CLOSE_ROUTINE_v1` — this project's `close.json` is in `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S369\close_parts\` (copy it, change what changed).
3. The brief of this close is `S369_BUILD_BRIEF.md`; the Book is `SANJEEVNI_SYSTEM_BOOK_v1_41_S369.md` (§15AF is S369); the kits `deploy_kits\S683_AMIR_SCANS_TRUE_ONLY\` and `deploy_kits\S690_AMIR_BATCH_FIX\` (both live). The mock-up S690 was built to: `https://claude.ai/artifact/21JkxRFCaqVL9J2eGDbXYV`.

No incident is open. **S683 and S690 are live** (30-Oct 18:26; 1-Nov 06:59). S678, S679, S676, S677, S675, S359's six and S644 (in shadow; `order.source = marg_sheet`) are live.

*FIRST ACT: take your session number from the System Board's `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).*
- **375 is RESERVED for the Sanjeevni chat at this close.** The parent's 374 is open; the Scan App chat's 363 and the NK Pathology chat's 365 are reserved. Take what the board says and say so in your first line.
- Kit numbers are claimed before the scratch folder is named (F-515); D and F numbers the moment they are minted (F-920). Read every PLANNED line on the board before touching a file it names (D646).
- **F-1072:** a build left to start unattended takes its kit number BEFORE it is left — an unattended board write waits on an approval nobody can give.

*Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.* Never `git` there (F-511). **Build road: in the chat itself.** What S339–S369 learnt about building offline (keep it): the live code = the newest bundle + the pending kits' `make_*.py` in order (`D:\Downloads\_kbtools\vps_code\code_nightly.tar.gz`, the database copy `finance_nightly.db.gz` beside it — work in the device VM's `/tmp`, never in a kit folder, F-1041); **the spine can be rebuilt in the VM** — `spine_evidence.py --source $HOME/mnt/Downloads/margsync/MargArchive --out /tmp/…/readings` then `spine_build.py --readings … --out /tmp/…/spine.db --finance-db <copy>` (S369: the gate refused on the purchase witness, the `.failed` spine is real-shape and was used read-only); **flask is not in the VM's python — `pip install --user flask`**; a walk's controls stand on its OWN rows (F-998); **a rule that hides is measured on every real bill offered as new** (F-1070); **a confirmation reads only figures whose day the server holds** (F-1071); the pin list is newest-first; the built-in browser on manojz was signed in as `manoj` on 1-Nov (read `/finance/api/whoami` first); the medical PC's refused texts are mirrored on manojz (`D:\Downloads\margsync\medical_SendToClinic\_captured_txt\refused\`) — read their shape masked in the VM, never in the cloud (D656); an independent cold review reads every kit — **both S369 kits' reviews found a blocker**; read the owner's screen after every install (F-1034); scratch in the VM's `/tmp`.

---

## 0 · THE WORK — in order

**A · THE OPEN (OPEN_ROUTINE_v1)**

1. **The board** — every message `read:false`, every note; say in one line how many are this project's (at this close: none).
2. **The day's checks** — `day_open.py --read` (run it if the page is not today's).
3. **The pin pass on the 02-Nov bundle** with `live_pins_S369close.txt`: this project's DECLARED-PENDING 2 — `/root/finance/expiry_watch.py` b68cda86 and `/root/finance/amir_day.py` 10a5f9c4 (S690). `purchase_app.py` 2e1e9023 (S683) is CONFIRMED (31-Oct bundle). State match · declared-pending · unexplained.
4. **S690's cron line:** `/root/finance/spine/near_expiry.log` (in the bundle if it carries it, else ask nothing — read the owner's expiry page) shows `run` lines between nights only when a Batch Stock arrived; the nightly 23:57 run still writes. If no S690 run line exists by 2-Nov, read why before anything else.

**B · THE WORK**

1. **Amir's first visit after S690 (read only, the owner's login):** step 3 — the vouchers; step 4 — the Batch Stock as the third report; after it lands, the card's *"Batch Stock mil gayi"* line, the done list, any *Issue baaki / Receive baaki*; the next morning, the Issues confirmed. **Whether Marg took a STOCK RECEIVE into a blank batch** — if the blank-batch minus is unchanged after his visit and he keyed it, ask the owner one line (what Marg showed Amir).
2. **The purchase-batch tie** (plan of 30-Oct, step 3) — server-only: place new stock on its batch from the purchase item report where the clipped batch ties to ONE Batch Stock batch (exact, or the report's batch a 4+-character suffix; 83 % of October's 1,276 lines; the ambiguous 5 % and the sold-out 11 % stay as today), so the watch names a counter sale into a minus batch for every medicine. Gate: the expiry lists old = new on the real data except the newly named minuses, each read against its sale; a control.
3. **F-1047** — the next medical-PC kit (the owner's OK first; a live PC).
4. **Darpan's Vaapsi desk onto the spine** (rung 4d stage 2) — `returns_desk.py`; gate old = new since 1-Sep.
5. **The count's figures onto the spine** — the count sheet, `_s446_proof`, `loss_piles.py`; gate old = new on count #1.
6. **2-Nov, after the first levels score:** F-1028 and F-1025; the shadow score must not move. **1-Nov 05:30's reseed** (Deepam, Janta, L.K. Drug House to a 2-day lead) read on 2-Nov.
7. **The switch, on his word at D673's bar (earliest ~22-Nov).** **NEVER WRITE `order.source` FROM A KIT WITHOUT HIS WORD** (D673, D785). Then three retirement kits; then Sanjeevni as its own process.
8. **PARKED by his word:** F-802's permanent fix. **NOT THIS PROJECT'S (D803):** the PC and phone set-up kits (F-1048).
9. **The close** — `CLOSE_ROUTINE_v1`.

**NEVER RUN:** `deploy_kits\S488_DATES_AND_WAITS\deliver_S488.ps1`. **NEVER INSTALL:** `deploy_kits\S638_EXPIRY_WATCH\`, `S672_NONCASH_AT_INGEST\`, `S673_NONCASH_AT_INGEST_R2\` (frozen). **NEVER ADD TO:** Amir's *Aaj ka kaam* list (D690). **NEVER CHANGE THE EXPIRY PAGE ITSELF** without his word (D780, D793) — S690 added one line to its section 4 on his approval of the plan.

**AMIR NEVER OPENS OR EDITS A SALE BILL (D815).** **AMIR'S SCAN LIST CARRIES ONLY A BILL CLEARLY MISSING FROM MARG; NEVER A FINALISED MONTH (D814).** **A STAFF SCREEN CARRIES ONLY "DO THIS" LINES (D708) — AND A LINE ON IT RESTS ON A FACT NOBODY CAN TAP WRONGLY (D712).** **A SALE IS CASH OR UPI ONLY, NEVER A PARTY (D802).** **NO FIGURE TO TYPE, EVER (charter rule 8).** **A VOUCHER NEVER TAKES MARG BELOW ZERO OR PAST THE SHELF FIGURE (D715).** **A LINE LEAVES THE ORDER LIST ONLY WHEN MARG CLOSES IT (D716); A MISSING MEDICINE GOES ON THE NEXT ORDER BY ITSELF (D757); A SUBSTITUTE NEVER CLOSES A LINE (D760).** **ONLY THE OWNER CHANGES A DEALER'S NUMBER (D731).** **A CLOSING TAKEN BEFORE THE DAY'S FIRST SALE IS THE START OF THAT DAY (D740).** **CLAUDE READS THE PHARMACY BILLS; SARVAM IS OFF (D747).** **THE BUYING MODEL IS SCORED IN SHADOW; THE SWITCH IS HIS WORD (D678, D785).** **CREPE BANDAGES AND LEUKOBAND ARE MEDICINES (D795); HIS RULING ON ONE SIZE IS HIS RULING ON ITS SISTERS (D799).** **A HOME / PROCEDURE MEDICINE BILL IS DEDUCTED AT THE SALE INGEST (D798).** **A RETURN IS THE SPINE'S CREDIT NOTE; THE PATIENT IS SALE_ITEM'S (S677).**

**CLOSED BY HIS WORD — DO NOT RAISE AGAIN:** count #1 of 6-Sep (D800); the pack-change build (F-1000); the rescan's number (D759); the orthotic names as Amir typed them (D709); the learnt names (D685); Kedar's July balance; the four appliances' category; the staff's *Aaj ka kaam* lists — the parent's; the bill line's design (D712); the GST composition flow — the parent's; older purchase bills for the name list (D762); a reader for the bank's alert e-mails (D779); the expiry watch's screens (D780, D793); the shape of Kit II (D785); the S335 small list (D796); the screens of the stock check (D800 — backend only); who keeps the PC set-ups current (D803); the October scan mock-up for Amir (not wanted, 30-Oct — "he is doing well otherwise").

## 1 · THE STANDING OWNER RULINGS

1. **Publishing is HIS double-click** — `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`.
2. **Full paths ALWAYS — including URLs**, each in its own copy block. **ONE line per command.**
3. **Token-lean — never at the cost of verification.** **Plain language. Short chat (03-Sep).** **ALL-CAPS = urgent.**
4. **Mask patient numbers (last 4); never print secrets.** **Nothing live rebuilt without his OK; the manual path stays.**
5. **Sub-agents read screens. Do not hand him diagnostics. When a screen is wrong, read its code first. Never a step that is not his.**
6. **His board carries only what needs him and what he should know — every close answers what he typed there; the plan's section 9 is refreshed at every close.**
7. **His own items are deferred** — name only what has become urgent, and say why. **His approvals are few and arrive together.**
8. **Never put a technical choice to him** (03-Sep) — decide, say it in one line, carry on. **A screen for staff: the mock first (03-Oct).** **When he asks "when", the answer is "now" unless something real waits (28-Oct).** **When he says "only answer me" / "answer me first" / "do not build", answer — build nothing (29-Oct, 30-Oct).** **"Start the build after <time>" — a scheduled start, its numbers taken before it is left (F-1072).**
