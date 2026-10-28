# START HERE — SESSION 364 — written at the S362 close (the Sanjeevni chat), 28-Oct-2026 (afternoon)

**Project: Sanjeevni — Pharmacy & Marg.** Open in a fresh chat in this project, linked to manojz.
1. Follow `OPEN_ROUTINE_v1` (from the clone: `deploy_kits/KB_canon_all/OPEN_ROUTINE_v1.md`). In the device VM, `day_open.py` needs its paths: `--tools $HOME/mnt/Downloads/_kbtools --repo $HOME/mnt/dr-manoj-git/drmanoj-clinic-automation --kb $HOME/mnt/Downloads/ClaudeCowork --ssd $HOME/mnt/ClinicBackup/DrManojClinic_Automation --roots $HOME/mnt/Downloads $HOME/mnt/dr-manoj-git $HOME/mnt/ClinicBackup` (the defaults are Windows paths).
2. The rulebook for every build is **the charter v1.1 — `claude/S307_BUILD_CHARTER_v1_1.md`** beside the parent's `BUILD_NORM_v1.md` (D704). **The plan of what is left is the System Board's plan, section 9** (D800; six steps, below in §0 B). The close is `CLOSE_ROUTINE_v1` — this project's `close.json` is in `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S362\close_parts\` (copy it, change what changed).
3. The brief of this close is `S362_BUILD_BRIEF.md`; the Book is `SANJEEVNI_SYSTEM_BOOK_v1_39_S362.md` (§15AD is S362, §15AC S361); the kits `deploy_kits\S676_SECTIONS_BY_FAMILY\` and `deploy_kits\S677_RETURNS_ON_SPINE\` (both live); the returns brief `claude/S362_RETURNS_ON_SPINE_BRIEF.md` (stage 2 is the next build).

No incident is open. **S676 and S677 are live** (28-Oct 13:05, 15:50). S675 (28-Oct 09:59), S359's six and S644 (the levels model, in shadow; `order.source = marg_sheet`) are live.

*FIRST ACT: take your session number from the System Board's `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).*
- **364 is RESERVED for the Sanjeevni chat at this close.** The parent's 360 and the NK Pathology chat's 356 were open at this close; 363 is reserved for the Scan App chat. Take what the board says and say so in your first line.
- Kit numbers are claimed before the scratch folder is named (F-515); D and F numbers the moment they are minted (F-920). Read every PLANNED line on the board before touching a file it names (D646).

*Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.* Never `git` there (F-511). **Build road: in the chat itself.** **What S339–S362 learnt about building offline (keep it):** the live code = the newest bundle + the pending kits' `make_*.py` in order (the bundle is `D:\Downloads\_kbtools\vps_code\code_nightly.tar.gz`, the database copy `finance_nightly.db.gz` beside it — work in the device VM's `$HOME` / `/tmp`, never in a kit folder, F-1041); a walk's "old = new" runs the old and new bytes on the same database copy; **a walk's controls stand on its OWN rows (F-998)** — WALK-prefixed names, 2099 dates; **a walk on a live page asserts what the page always shows (F-1020)**; **the pin list is newest-first**; **the built-in browser on manojz is signed in as Shavez — the owner's view is read in his Chrome, read only**; **the spine never leaves the box** — a walk on it runs inside the installer on a COPY of the spine (`copydb`), and a rehearsal spine translated from the database copy's own `sale_bill` / `sale_line_item` finds what a made-up one cannot (F-1043); **a kit writes to the database through python (F-1036)**; **a refused kit is a NEW folder (F-512)**; **read the owner's screen after every install (F-1034)**; **Marg prints one item at different widths in different reports (F-1035) — the sale report at 20 letters**; **the box keeps NO raw sale export (F-1038)**; **rehearse on the live day's real state (F-1039)**; **a rule on a timer leaves a window (F-1037)**; **before a build is put to him, read the live file for the thing itself (F-1042)**; **an independent cold review reads every kit; measure its blockers on the live bytes before accepting them (S677 R1)**; **the device VM's `/sessions` disk is small — scratch in `/tmp`**.

---

## 0 · THE WORK — in order

**A · THE OPEN (OPEN_ROUTINE_v1)**

1. **The board** — every message `read:false`, every note; say in one line how many are this project's (at this close: none).
2. **The day's checks** — `day_open.py --read` (run it if the page is not today's).
3. **The pin pass on the 29-Oct bundle** with `live_pins_S362close.txt`: this project's DECLARED-PENDING 10 — S676's `/root/finance/section_map.py` 0e705ca1 and `stock_app.py` 5433d7b7; S677's `/root/finance/spine/spine_read.py` 38bc1013, `finance_returns_audit.py` b9dc1f9f, `returns_kinds.py` 9dd7175d, `finance_returns_escalate.py` 9944bbab, `sanjeevni_approvals.py` d063e939; S361's `day_resync.py` 00b45a15, `finance_ingest.py` ce01a9e1 (the parent's), `expiry_watch.py` 23e0a5bf. State match · declared-pending · unexplained.
4. **S676's first closings:** in the newest database copy, every name of the newest closing has a `stock_item_section` row; any `source='family'` row named by its teacher; no owner row changed.
5. **S677's first days:** the owner's approvals page Returns section and Needs-you's returns line read live in his Chrome (read only) — no "not examinable" on a credit note the spine holds; `finance_returns_escalate`'s spot-check rows for new returns carry key, name, batch.
6. **S675's first mornings** (carried): every home / procedure bill of 28-Oct onward has its `day_noncash_bill` row with an `audit_log` `noncash_sync` kit *S672 at ingest*.
7. **Amir** (carried): Vinbactum DS gone from the closing after his next visit? The two September *Bhejo* (`supplier_msg` 52, 54)?
8. **1-Nov (Sunday) 05:30:** the monthly reseed moves Deepam, Janta and L.K. Drug House to a 2-day lead; read it on 2-Nov.

**B · THE WORK — the board's plan section 9**

1. **Darpan's Vaapsi desk onto the spine** (rung 4d stage 2) — `returns_desk.py` (9 reads of `sale_line_item`: the patient's bills and lines, the item search, `_allocate`); its own `return_line.item_key` history keyed by the full name gets a one-time key migration to the spine's key; `finance_returns.py`'s `correlate_return` / `find_patient_sales` have no caller (rung 5). One kit, no screen change; the gate old = new on every visit and line of the desk since 1-Sep, on the box.
2. **The count's figures onto the spine** — the count sheet, Amir's voucher proof (`_s446_proof`), the Loss desk (`loss_piles.py`) read the spine's figure and the section table; count #1 is closed (D800) — the four late items judged in the background, gating nothing. Gate: old = new on count #1's 136 written-off lines and 170 vouchers.
3. **2-Nov, after the first levels score:** F-1028 (the fold's *last list stood on* line, the relist line in words, *carried*) and F-1025 (`spine_build.py`: a finding equal to an entered voucher classed VOUCHER). Walk with a control; the shadow score must not move.
4. **The switch, on his word at D673's bar (earliest ~22-Nov):** `order.source = system` with 4b-2's retirements, D796's parked three and Darpan's tab header line (mock first). **NEVER WRITE `order.source` FROM A KIT WITHOUT HIS WORD** (D673, D785).
5. **After the switch:** three retirement kits, one a week (the old item spine; `mi_sale_line` + the median-MRP rule + the S268 word lists; the second parser + the manojz senders); then **Sanjeevni as its own process** (P4/P5).
6. **PARKED by his word — do not start unasked:** F-802's permanent fix.
7. **The close** — `CLOSE_ROUTINE_v1`.

**NEVER RUN:** `deploy_kits\S488_DATES_AND_WAITS\deliver_S488.ps1`. **NEVER INSTALL:** `deploy_kits\S638_EXPIRY_WATCH\`, `S672_NONCASH_AT_INGEST\`, `S673_NONCASH_AT_INGEST_R2\` (frozen). **NEVER ADD TO:** Amir's *Aaj ka kaam* list (D690). **NEVER CHANGE THE EXPIRY PAGE ITSELF** without his word (D780, D793). **NO STAFF SCREEN CHANGES IN THE ARCHITECTURE'S REMAINING WORK (D800).**

**A STAFF SCREEN CARRIES ONLY "DO THIS" LINES (D708) — AND A LINE ON IT RESTS ON A FACT NOBODY CAN TAP WRONGLY (D712).** **NO FIGURE TO TYPE, EVER (charter rule 8).** **A VOUCHER NEVER TAKES MARG BELOW ZERO OR PAST THE SHELF FIGURE (D715).** **A LINE LEAVES THE ORDER LIST ONLY WHEN MARG CLOSES IT (D716); A MISSING MEDICINE GOES ON THE NEXT ORDER BY ITSELF (D757); A SUBSTITUTE NEVER CLOSES A LINE (D760).** **ONLY THE OWNER CHANGES A DEALER'S NUMBER (D731).** **A CLOSING TAKEN BEFORE THE DAY'S FIRST SALE IS THE START OF THAT DAY (D740).** **CLAUDE READS THE PHARMACY BILLS; SARVAM IS OFF (D747).** **THE BUYING MODEL IS SCORED IN SHADOW; THE SWITCH IS HIS WORD (D678, D785).** **CREPE BANDAGES AND LEUKOBAND ARE MEDICINES (D795); HIS RULING ON ONE SIZE IS HIS RULING ON ITS SISTERS (D799, S676).** **A HOME / PROCEDURE MEDICINE BILL IS DEDUCTED AT THE SALE INGEST (D798).** **A RETURN IS THE SPINE'S CREDIT NOTE; THE PATIENT IS SALE_ITEM'S (S677).**

**CLOSED BY HIS WORD — DO NOT RAISE AGAIN:** count #1 of 6-Sep (D800); the pack-change build (F-1000); the rescan's number (D759); the orthotic names as Amir typed them (D709); the learnt names (D685); Kedar's July balance; the four appliances' category; the staff's *Aaj ka kaam* lists — the parent's; the bill line's design (D712); the GST composition flow — the parent's; older purchase bills for the name list (D762); a reader for the bank's alert e-mails (D779); the expiry watch's screens (D780, D793); the shape of Kit II (D785); the S335 small list (D796); the screens of the stock check (D800 — backend only).

## 1 · THE STANDING OWNER RULINGS

1. **Publishing is HIS double-click** — `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`.
2. **Full paths ALWAYS — including URLs**, each in its own copy block. **ONE line per command.**
3. **Token-lean — never at the cost of verification.** **Plain language. Short chat (03-Sep).** **ALL-CAPS = urgent.**
4. **Mask patient numbers (last 4); never print secrets.** **Nothing live rebuilt without his OK; the manual path stays.**
5. **Sub-agents read screens. Do not hand him diagnostics. When a screen is wrong, read its code first. Never a step that is not his.**
6. **His board carries only what needs him and what he should know — every close answers what he typed there; the plan's section 9 is refreshed at every close.**
7. **His own items are deferred** — name only what has become urgent, and say why. **His approvals are few and arrive together.**
8. **Never put a technical choice to him** (03-Sep) — decide, say it in one line, carry on. **A screen for staff: the mock first (03-Oct).** **When he asks "when", the answer is "now" unless something real waits (28-Oct, 15:05).**
