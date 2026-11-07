# START HERE — SESSION 402 — written at the S399 close (the Sanjeevni chat), 07-Nov-2026 (10:0x IST)

**Project: Sanjeevni — Pharmacy & Marg.** Open it in a fresh chat in this project, linked to manojz.

1. **The open:** follow `OPEN_ROUTINE_v1` (from the clone: `deploy_kits/KB_canon_all/OPEN_ROUTINE_v1.md`).
   - In the device VM, `day_open.py` needs its paths: `--tools $HOME/mnt/Downloads/_kbtools --repo $HOME/mnt/dr-manoj-git/drmanoj-clinic-automation --kb $HOME/mnt/Downloads/ClaudeCowork --ssd $HOME/mnt/ClinicBackup/DrManojClinic_Automation --roots $HOME/mnt/Downloads $HOME/mnt/dr-manoj-git $HOME/mnt/ClinicBackup` (`--read` with the same `--tools`).
   - **A re-run after a publish clears the day's note — write it again.**
   - Run Python with `TMPDIR=/tmp/s402w`.
   - **A database copy goes to `/tmp/s402w/` in the device VM, never the cloud workspace (D656).**
2. **The rules:** the rulebook for every build is **the charter v1.1 — `claude/S307_BUILD_CHARTER_v1_1.md`**, beside the parent's `BUILD_NORM_v1.md` (D704).
   - The plan of record is **`S391_PURCHASE_RECONCILE_PLAN.md`** (D839, D840), with D846 – D849 (S393), D853, D854 (S396) and **D859 – D861 (S399, returns)**.
   - The close is `CLOSE_ROUTINE_v1`. This project's `close.json` is in `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S399\close_parts\` — copy it and change what changed.
3. **This close's papers:** the brief is `S399_BUILD_BRIEF.md`; the Book is `SANJEEVNI_SYSTEM_BOOK_v1_50_S399.md` (§15AO: S740).

**No incident is open.**

**The newest bundle is 07-Nov 01:35.** It CONFIRMED fourteen of this project's pins (§S396).
**DECLARED-PENDING until a bundle newer than 07-Nov 09:12 IST:** `scan_register.py` 12e3c7cb, `amir_day.py` 42a8430b, `porders_s454.py` 37c4f3bf, `purchase_app.py` 600c96d7 (S740, on top of S738's three).
- **Medical PC** (installed and confirmed by its heartbeat at S393): `marg_push.py` 3f5ed144, `marg_watch.py` df7736e9.

*FIRST ACT: take your session number from the System Board's `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).*
- **402 is RESERVED for the Sanjeevni chat at this close.** The parent's 400 is open; the NK Pathology chat's 365 and the Scan App chat's 401 are reserved. Take what the board says, and say so in your first line.
- **Kit numbers are claimed BEFORE the scratch folder is named (F-515).** **Re-read `_numbers` just before a pinned write** — other chats write between yours.

**Connections and machinery:**
- *Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.* For any medical-PC delivery, also `H:\My Drive\Clinic Data Archive\ToMedical` (Google Drive is H: on manojz; the device shell cannot mount it — use device_list_dir / stage / commit).
- **Never `git` in the device shell (F-511, F-1152):** read `.git\refs\heads\main`, `.git\refs\remotes\origin\main` and `.git\logs\HEAD` as files.
- **Placing a kit in the repo:** a tar committed to `03_WORKING_PAPERS\S###\`, then extracted with `tar --overwrite` in the device shell. Read it back by md5 (F-1099). `rm` is refused.

**What S339 – S399 learnt (keep it):**
- The live code = the newest bundle + the pending kits' `make_*.py`, in order. **Now:** `make_s708` → `make_s711` → `make_s726` → `make_s736` → `make_s738` → `make_s740`, each with its FROM pins — or the box's own bytes when the kit gives them.
- **A tracker that settles a money item is settled only by a paper that can belong to nothing else (F-1172).**
- **Pack only after a green walk; read the packed CONTROL line against the walk; quote every heredoc (F-1173).**
- **A kit that re-pairs or unpairs live records is installed only after its DRY run on the box has been read (F-1153).**
- **A DRY line given after 23:30 or before 04:00 carries `DRY=1 SKIP_WINDOW=1` (F-1163).**
- **The SUMS packed is the build walked (F-1162).** **Every server-raised row has a withdrawal for every way its cause can leave (F-1161).** **A credit to a person is proved by the person's own act (F-1162).**
- Before naming the publish: `deploy_kits\NO_PHONE_NUMBERS.py --files-from <list> <repo>` and the `.gitignore` test on every kit file.
- Every kit is read cold by an independent agent until it comes back SAFE (S740 took seventeen rounds).
- The screen is read live after every install: a sub-agent in the built-in browser, signed in as `manoj`; read `/finance/api/whoami` first.
- **Never tap a button on the live site for him.** The owner taps it himself.
- The pharmacy scans (`assets.db`) are the Scan App's: READ ONLY.

---

## 0 · THE WORK — in order

**A · THE OPEN (OPEN_ROUTINE_v1)**
- the board (messages `read:false` to `sanjeevni`, notes);
- the day's checks;
- the four numbers.

**The newest bundle:** S738's three and S740's four pins CONFIRMED (or named).

**The live picture (read only):**
- **Janta 21965** — has Janta's revised bill or credit note come? Its return's stage in `s740_track` (resolved, by which road?), and row 8.
- **ZUPRINOR 5** (2 pcs short at the 7-Oct count, Janta only) — his answer on row 8, or still open.
- New reception questions (*Ek sawaal · wapsi*), new Marg purchase returns (minus bills), any *Record a return*.
- **Amir's visit** with *Wapsi baaki* and S738's cards (`s738_fix` settled only where a newer `PURCHASE_BILLWISE` arrived).
- The step view, Amir's page and reception's list read live.

**B · THE WORK**
1. **KIT 4, on his "go":** each dealer's month summary, the issues list, the month lock on Marg = papers = summaries, the statements built by the server (D849), the one NEFT on the suppliers' figures. It is F-1175's net. The mock first if a staff screen changes.
2. **His:**
   - F-1110's medical-PC half (his yes first);
   - F-1104 "count them";
   - F-1145 (Kedar ₹110 twice; A000211 stays *You*);
   - the switch, on his word at D673's bar.
3. **PARKED by his word:** F-802's permanent fix; F-1133 (D837).
   **NOT THIS PROJECT'S:** F-1048, D803, F-1102, F-1122 (the parent's); F-1174 (the Scan App's reader).
   **His with Ram Singh:** F-1115.
4. **The board's claims list** (47 entries, ≈ 90 KB at this close): trim to 40 at a quiet open, the rest archived byte-exact first.
5. **The close** — `CLOSE_ROUTINE_v1`.

**NEVER:**
- **NEVER RUN** `deploy_kits\S488_DATES_AND_WAITS\deliver_S488.ps1`.
- **NEVER INSTALL** `deploy_kits\S638_EXPIRY_WATCH\`, `S672_NONCASH_AT_INGEST\` or `S673_NONCASH_AT_INGEST_R2\` (frozen).
- **NEVER ADD TO** Amir's *Aaj ka kaam* list (D690).
- **THE EXPIRY PAGE CHANGES ONLY ON HIS WORD** (D780, D793; D828).
- **NEVER CHANGE THE MEANING of a name the parent's console reads** without a word to the parent: `supplier_msg.s454_card_facts`, `porders.shortage_summary`, `expiry_watch.newest / now_view / ym_add`, `reports_tile.status`.
- **THE FLOW PAGES ARE PUBLIC — FIXED TEXT AND PICTURES ONLY.**
- **NEVER BOOK A VOUCHER IN THE SPINE'S `sp_move`.**
- **NEVER SEND A SUPPLIER WHATSAPP OR TAP A STAFF OR OWNER BUTTON FOR HIM** without his explicit word.

**THE RULINGS THAT STAND:**
- **A RETURN SETTLES BY THE DEALER'S REVISED BILL, CREDIT NOTE OR A DEDUCTION ON A LATER BILL; EVERY PENDING RETURN STAYS ON AMIR'S PAGE AND HIS STEP VIEW UNTIL RESOLVED; A MONTH STAYS OPEN UNTIL CLEARED THE NEXT MONTH (D859).**
- **GOODS SENT BACK AT DELIVERY ARE ENTERED NET; RECEPTION ANSWERS ONE QUESTION; A RETURN FROM STOCK IS A MARG PURCHASE RETURN WHEN THE DEALER'S PAPER COMES (D860).**
- **A RETURN WITH NO PAPER IS CAUGHT BY THE COUNT SHORTAGE OR HIS OWN RECORD; THE NEFT HOLDS WHILE ANY RETURN IS PENDING (D861).**
- **AMIR'S CORRECTION LEAVES ONLY BY HIS OWN EXPORT; NOTHING FOR HIM TO TAP (D853).**
- **SEPTEMBER 2026 IS A PROOF ONLY — IT RAISES NOTHING TO ANYONE (D848).**
- **A BAD SCAN GOES STRAIGHT TO RECEPTION, SENT BY THE SERVER; TWO TRIES, THEN HIM AND SHAVEZ (D847).**
- **EVERY ALARM REACHES HIM BY THE CLINIC APP (D846).**
- **WE PAY THE SUPPLIER'S FIGURE; ONE BULK NEFT A MONTH, ONLY AFTER EVERY SUPPLIER'S ISSUE IS RESOLVED (D839).**
- **EVERY RUPEE BETWEEN A SCAN AND MARG IS CORRECTED IN MARG THROUGH AMIR'S WORKFLOW (D839).**
- **HE SEES EVERY STEP UNTIL NOVEMBER IS LOCKED AND PAID (D840).**
- **THE ORDER LIST TIES NO SCAN BY ITSELF (D831).**
- **A MARG STOCK CHANGE WITH NO BILL, SALE OR VOUCHER IS TOLD HIM THE NEXT MORNING (D828).**
- **AMIR NEVER OPENS OR EDITS A SALE BILL (D815).**
- **A STAFF SCREEN CARRIES ONLY "DO THIS" LINES (D708), ON A FACT NOBODY CAN TAP WRONGLY (D712).**
- **NO FIGURE TO TYPE, EVER (charter rule 8).**
- **A SALE IS CASH OR UPI ONLY (D802).**
- **ONLY THE OWNER CHANGES A DEALER'S NUMBER (D731).**
- **THE BUYING MODEL IS SCORED IN SHADOW; THE SWITCH IS HIS WORD (D678, D785).**
- **NO SECOND NETWORK FOR THE MEDICAL PC UNTIL A SECOND LAN FAILURE (D837).**

**CLOSED BY HIS WORD — DO NOT RAISE AGAIN:** as `START_HERE_SESSION_391` listed, plus Deepam 641 (D854). **B-0239 is his own tap.**

## 1 · THE STANDING OWNER RULINGS

1. **Publishing is HIS double-click** — `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`.
2. **Full paths ALWAYS — including URLs**, each in its own copy block. **ONE line per command.**
3. **Token-lean — never at the cost of verification.** **Plain language. Short chat.** **ALL-CAPS = urgent.**
4. **Mask patient numbers (last 4); never print secrets.** **Nothing live is rebuilt without his OK; the manual path stays.**
5. **Sub-agents read screens. Do not hand him diagnostics. When a screen is wrong, read its code first. Never hand him a step that is not his.**
6. **His board carries only what needs him and what he should know.**
7. **Never put a technical choice to him** — decide, say it in one line, carry on. **A screen for staff: the mock first.** **"Don't build now" means plan only; "a brief plan" means no mock.** **His own pages: PC first, the Fold phone second (D853).**
8. **His phone gets the clinic app's messages; ntfy is the fallback (D846).**
