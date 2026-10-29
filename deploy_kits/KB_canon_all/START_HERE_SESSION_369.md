# START HERE — SESSION 369 — written at the S367 close (the Sanjeevni chat), 29-Oct-2026 (evening)

**Project: Sanjeevni — Pharmacy & Marg.** Open in a fresh chat in this project, linked to manojz.
1. Follow `OPEN_ROUTINE_v1` (from the clone: `deploy_kits/KB_canon_all/OPEN_ROUTINE_v1.md`). In the device VM, `day_open.py` needs its paths: `--tools $HOME/mnt/Downloads/_kbtools --repo $HOME/mnt/dr-manoj-git/drmanoj-clinic-automation --kb $HOME/mnt/Downloads/ClaudeCowork --ssd $HOME/mnt/ClinicBackup/DrManojClinic_Automation --roots $HOME/mnt/Downloads $HOME/mnt/dr-manoj-git $HOME/mnt/ClinicBackup` (the defaults are Windows paths). **S367 did not run it** (the urgent work came first); the parent's S366 ran the day's checks on 29-Oct.
2. The rulebook for every build is **the charter v1.1 — `claude/S307_BUILD_CHARTER_v1_1.md`** beside the parent's `BUILD_NORM_v1.md` (D704). **The plan of what is left is the System Board's plan, section 9** (D800). The close is `CLOSE_ROUTINE_v1` — this project's `close.json` is in `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S367\close_parts\` (copy it, change what changed).
3. The brief of this close is `S367_BUILD_BRIEF.md`; the Book is `SANJEEVNI_SYSTEM_BOOK_v1_40_S367.md` (§15AE is S367, §15AD S362); the kits `deploy_kits\S678_AMIR_PAIR_FROM_DOOR\` and `deploy_kits\S679_SALE_BILLED_TO_PARTY\` (both live; S679's medical-PC half by Drive `ToMedical\_kit`).

No incident is open. **S678 and S679 are live** (29-Oct 11:59; medical PC 17:30, server 18:12). S676, S677 (28-Oct), S675, S359's six and S644 (in shadow; `order.source = marg_sheet`) are live. **S364 was opened on 28-Oct 17:12 and shows no close on the board** — nothing of it is in canon; 367 was taken fresh.

*FIRST ACT: take your session number from the System Board's `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).*
- **369 is RESERVED for the Sanjeevni chat at this close.** The parent's 368, the Scan App chat's 363 and the NK Pathology chat's 365 are reserved. Take what the board says and say so in your first line.
- Kit numbers are claimed before the scratch folder is named (F-515); D and F numbers the moment they are minted (F-920). Read every PLANNED line on the board before touching a file it names (D646).

*Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.* Never `git` there (F-511). **Build road: in the chat itself.** What S339–S367 learnt about building offline (keep it): the live code = the newest bundle + the pending kits' `make_*.py` in order (the bundle is `D:\Downloads\_kbtools\vps_code\code_nightly.tar.gz`, the database copy `finance_nightly.db.gz` beside it — work in the device VM's `/tmp`, never in a kit folder, F-1041); a walk's "old = new" runs the old and new bytes on the same database copy; **a walk's controls stand on its OWN rows (F-998)**; **the pin list is newest-first**; **the built-in browser on manojz was signed in as `manoj` on 29-Oct** (read `/finance/api/whoami` first); **the medical PC's refused texts are mirrored on manojz** (`D:\Downloads\margsync\medical_SendToClinic\_captured_txt\refused\`) — read their shape masked in the device VM, never in the cloud (D656); **the medical PC's programs go by Drive `H:\My Drive\Clinic Data Archive\ToMedical\_kit`** (granted to this chat on 29-Oct; backups `<name>_<old VERSION>.superseded`; the manifest CRLF, then the files; read every one back by hash, F-1049); **an independent cold review reads every kit — both S367 kits' reviews found real faults**; **read the owner's screen after every install (F-1034)**; **the device VM's `/sessions` disk is small — scratch in `/tmp`**.

---

## 0 · THE WORK — in order

**A · THE OPEN (OPEN_ROUTINE_v1)**

1. **The board** — every message `read:false`, every note; say in one line how many are this project's (at this close: none).
2. **The day's checks** — `day_open.py --read` (run it if the page is not today's).
3. **The pin pass on the 30-Oct bundle** with `live_pins_S367close.txt`: this project's DECLARED-PENDING 2 — `/root/finance/amir_day.py` a0907b74 (S678) and `/root/finance/reports_tile.py` 03902a5d (S679). And S362's ten, which the 29-Oct bundle should have CONFIRMED (S676's `section_map.py` 0e705ca1, `stock_app.py` 5433d7b7; S677's `spine_read.py` 38bc1013, `finance_returns_audit.py` b9dc1f9f, `returns_kinds.py` 9dd7175d, `finance_returns_escalate.py` 9944bbab, `sanjeevni_approvals.py` d063e939; S361's `day_resync.py` 00b45a15, `finance_ingest.py` ce01a9e1 (the parent's), `expiry_watch.py` 23e0a5bf). State match · declared-pending · unexplained.
4. **The 28-Oct sale:** has a corrected export landed (A004482 no longer billed to a party)? Is 28-Oct filed? If not, the owner's one line to Shavez, nothing more.
5. **S678's first visit days:** on Amir's next visit, his step 4 read live (owner login) — a door file shows *"Server par … aa gayi"* only while manojz's leg is behind; never "Dobara banaiye" for a file the door holds.
6. **S679 on the medical PC:** the heartbeat names `marg_txt.py` aa7baee5 and `marg_watch.py` a009d2fd; any new party-billed sale shows on Shavez's tile with its bill number.
7. **Carried from 364 (not done at S367):** S676's first closings (every name of the newest closing has a `stock_item_section` row; `source='family'` rows named by their teacher); S677's first days (the owner's approvals page Returns section and Needs-you's returns line, read only); S675's mornings (`day_noncash_bill` rows with `noncash_sync` *S672 at ingest*); Amir — Vinbactum DS gone from the closing? the two September *Bhejo* (`supplier_msg` 52, 54)?
8. **1-Nov (Sunday) 05:30:** the monthly reseed moves Deepam, Janta and L.K. Drug House to a 2-day lead; read it on 2-Nov.

**B · THE WORK — the board's plan section 9, plus this close's two**

1. **F-1047** — the next medical-PC kit: a refused text whose reason changes after a reader change is noted again, so the server's row follows (`marg_watch._keep_refused` / `notes_try`). Small; the owner's OK first (a live PC).
2. **Darpan's Vaapsi desk onto the spine** (rung 4d stage 2) — `returns_desk.py`; `return_line.item_key` one-time key migration; gate old = new on every visit and line since 1-Sep, on the box.
3. **The count's figures onto the spine** — the count sheet, `_s446_proof`, `loss_piles.py`; gate old = new on count #1's 136 lines and 170 vouchers.
4. **2-Nov, after the first levels score:** F-1028 and F-1025. Walk with a control; the shadow score must not move.
5. **The switch, on his word at D673's bar (earliest ~22-Nov):** `order.source = system` with 4b-2's retirements, D796's parked three and Darpan's tab header line (mock first). **NEVER WRITE `order.source` FROM A KIT WITHOUT HIS WORD** (D673, D785).
6. **After the switch:** three retirement kits, one a week (the old item spine; `mi_sale_line` + the median-MRP rule + the S268 word lists; **the second parser + the manojz senders — the lasting cure of F-1045: the server loads the purchase lines from its own door file**); then **Sanjeevni as its own process** (P4/P5).
7. **PARKED by his word — do not start unasked:** F-802's permanent fix.
8. **NOT THIS PROJECT'S (D803):** keeping the PC and phone set-up kits current (`/finance/pcs`, F-1048) — the parent's. When the parent's scheme asks, this chat supplies the medical PC's programs as they stand on Drive `_kit`.
9. **The close** — `CLOSE_ROUTINE_v1`.

**NEVER RUN:** `deploy_kits\S488_DATES_AND_WAITS\deliver_S488.ps1`. **NEVER INSTALL:** `deploy_kits\S638_EXPIRY_WATCH\`, `S672_NONCASH_AT_INGEST\`, `S673_NONCASH_AT_INGEST_R2\` (frozen). **NEVER ADD TO:** Amir's *Aaj ka kaam* list (D690). **NEVER CHANGE THE EXPIRY PAGE ITSELF** without his word (D780, D793). **NO STAFF SCREEN CHANGES IN THE ARCHITECTURE'S REMAINING WORK (D800)** — S678 and S679 changed words on a screen only to make a wrong line right, at his ask.

**A STAFF SCREEN CARRIES ONLY "DO THIS" LINES (D708) — AND A LINE ON IT RESTS ON A FACT NOBODY CAN TAP WRONGLY (D712).** **A SALE IS CASH OR UPI ONLY, NEVER A PARTY (D802).** **NO FIGURE TO TYPE, EVER (charter rule 8).** **A VOUCHER NEVER TAKES MARG BELOW ZERO OR PAST THE SHELF FIGURE (D715).** **A LINE LEAVES THE ORDER LIST ONLY WHEN MARG CLOSES IT (D716); A MISSING MEDICINE GOES ON THE NEXT ORDER BY ITSELF (D757); A SUBSTITUTE NEVER CLOSES A LINE (D760).** **ONLY THE OWNER CHANGES A DEALER'S NUMBER (D731).** **A CLOSING TAKEN BEFORE THE DAY'S FIRST SALE IS THE START OF THAT DAY (D740).** **CLAUDE READS THE PHARMACY BILLS; SARVAM IS OFF (D747).** **THE BUYING MODEL IS SCORED IN SHADOW; THE SWITCH IS HIS WORD (D678, D785).** **CREPE BANDAGES AND LEUKOBAND ARE MEDICINES (D795); HIS RULING ON ONE SIZE IS HIS RULING ON ITS SISTERS (D799, S676).** **A HOME / PROCEDURE MEDICINE BILL IS DEDUCTED AT THE SALE INGEST (D798).** **A RETURN IS THE SPINE'S CREDIT NOTE; THE PATIENT IS SALE_ITEM'S (S677).**

**CLOSED BY HIS WORD — DO NOT RAISE AGAIN:** count #1 of 6-Sep (D800); the pack-change build (F-1000); the rescan's number (D759); the orthotic names as Amir typed them (D709); the learnt names (D685); Kedar's July balance; the four appliances' category; the staff's *Aaj ka kaam* lists — the parent's; the bill line's design (D712); the GST composition flow — the parent's; older purchase bills for the name list (D762); a reader for the bank's alert e-mails (D779); the expiry watch's screens (D780, D793); the shape of Kit II (D785); the S335 small list (D796); the screens of the stock check (D800 — backend only); who keeps the PC set-ups current (D803 — the parent).

## 1 · THE STANDING OWNER RULINGS

1. **Publishing is HIS double-click** — `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`.
2. **Full paths ALWAYS — including URLs**, each in its own copy block. **ONE line per command.**
3. **Token-lean — never at the cost of verification.** **Plain language. Short chat (03-Sep).** **ALL-CAPS = urgent.**
4. **Mask patient numbers (last 4); never print secrets.** **Nothing live rebuilt without his OK; the manual path stays.**
5. **Sub-agents read screens. Do not hand him diagnostics. When a screen is wrong, read its code first. Never a step that is not his.**
6. **His board carries only what needs him and what he should know — every close answers what he typed there; the plan's section 9 is refreshed at every close.**
7. **His own items are deferred** — name only what has become urgent, and say why. **His approvals are few and arrive together.**
8. **Never put a technical choice to him** (03-Sep) — decide, say it in one line, carry on. **A screen for staff: the mock first (03-Oct).** **When he asks "when", the answer is "now" unless something real waits (28-Oct, 15:05).** **When he says "only answer me", answer — build nothing (29-Oct).**
