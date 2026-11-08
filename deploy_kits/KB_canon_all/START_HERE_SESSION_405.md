# START HERE — SESSION 405 — written at the S403 close (the Sanjeevni chat), 08-Nov-2026 (06:1x IST)

**Project: Sanjeevni — Pharmacy & Marg.** Open it in a fresh chat in this project, linked to manojz. **This is the build session for kit S749 `ONE_SOURCE` — his "go" is given (05:56 IST 8-Nov) and the mock approved (06:04).**

1. **The open:** follow `OPEN_ROUTINE_v1` (from the clone: `deploy_kits/KB_canon_all/OPEN_ROUTINE_v1.md`).
   - In the device VM `day_open.py` runs from `$HOME/mnt/Downloads/_kbtools` (`python3 day_open.py`, `--read`, `--note "..."`). **A re-run after a publish clears the day's note — write it again.**
   - Run Python with `TMPDIR=/tmp/s405w`. **A database copy goes to `/tmp/s405w/` in the device VM, never the cloud workspace (D656).** The nightly copies: `D:\Downloads\_kbtools\vps_code\finance_nightly.db.gz`, `code_nightly.tar.gz`.
2. **The rules:** the charter v1.1 — `claude/S307_BUILD_CHARTER_v1_1.md`, beside the parent's `BUILD_NORM_v1.md` (D704).
   - **The plan of record for this build is `S403_KIT5_ONE_SOURCE_PLAN.md`** (D865, D866; F-1181 – F-1183). After it: kit 4 (`S391_PURCHASE_RECONCILE_PLAN.md` §4 item 4, D849), then the order-list kit (`S402_ORDER_LIST_PLAN.md`).
   - **The approved mock:** the artifact `https://claude.ai/artifact/BpPSuh8Cm2gPVmkzLDwmXi`; its source `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S403\S749_mock.html`. Build to it; his one addition (06:04): **every action inline on the step view line** (the scan folded open; *Confirm*; the second-look pair; the return answers; *Not this bill → pick the right bill*; *Accept without paper*; *Ask reception to rescan*; *Undo*). **A Marg correction is proved only by Amir's export — never a tap (F-1162).**
   - The close is `CLOSE_ROUTINE_v1`. This project's `close.json` is in `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S403\close_parts\` — copy it and change what changed.
3. **This close's papers:** the brief `S403_BUILD_BRIEF.md`; the Book is still `SANJEEVNI_SYSTEM_BOOK_v1_50_S399.md` (no app change at S402 or S403) — **S749's install writes v1.51.**

**No incident is open.**

**The newest bundle is 08-Nov (03:15 IST).** This project has nothing DECLARED-PENDING. **Kit S749's FROM bytes (read each WHOLE before patching, F-472; drift +3 on two of them):** `scan_register.py` 12e3c7cb · `purchase_app.py` 600c96d7 · `amir_day.py` 42a8430b · `porders.py` (S726's eda0a4c6, confirmed) — and the parent's `portal.py`, `month_read.py` (PLANNED on the board at this close, D646; built on the bundle's bytes; the parent told in the close). **Check no other chat has a newer PLANNED line on any of the six before patching.**

*FIRST ACT: take your session number from the System Board's `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).*
- **405 is RESERVED for the Sanjeevni chat at this close.** The NK Pathology chat's 365 and the Scan App chat's 401 are open; the parent's 404 is reserved. Take what the board says, and say so in your first line.
- **Kit S749 is already claimed (v1057).** D and F numbers at the close only. **Re-read `_numbers` just before a pinned write.** The board document is large — read it with `out_dir`, write the changed fields with `file_path`.

**Connections and machinery:**
- *Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.*
- **Never `git` in the device shell (F-511, F-1152):** read `.git\refs\heads\main`, `.git\refs\remotes\origin\main`, `.git\logs\HEAD` as files.
- **Placing a kit in the repo:** a tar committed to `03_WORKING_PAPERS\S###\`, then extracted with `tar --overwrite` in the device shell. Read it back by md5 (F-1099). `rm` is refused.

**What S339 – S403 learnt (keep it):**
- The live code = the newest bundle (08-Nov carries every kit through S740) + any later kit's `make_*.py`.
- **A page added later must read the list the owner reads, or it tells him a second truth (F-1183).** **A line Marg could not name is matched by what it carries before it is called missing (F-1181).** **A page he is told to use has a way in from his app (F-1182).**
- A live-read brief names each staff page by its route — Amir's own page is `/finance/amir/step/<n>` (a GET of `/finance/amir` runs `settle`, a write); `/finance/amir/day` is the owner's English summary (F-1178).
- **A kit that re-pairs, re-ties, unpairs or re-states live records is installed only after its DRY run on the box has been read (F-1153).** S749 re-states the ₹1 bills, Kedar A000211 and the 4 clipped bills — DRY first. A DRY line after 23:30 or before 04:00 carries `DRY=1 SKIP_WINDOW=1` (F-1163).
- **Pack only after a green walk; read the packed CONTROL line against the walk; quote every heredoc (F-1173).** **The SUMS packed is the build walked (F-1162).** **Every server-raised row has a withdrawal for every way its cause can leave (F-1161).** **A credit to a person is proved by the person's own act (F-1162).**
- A bill whose reading cannot pick its order waits for Marg — never the oldest order (F-1176). A tracker that settles a money item is settled only by a paper that can belong to nothing else (F-1172).
- Before naming the publish: `deploy_kits\NO_PHONE_NUMBERS.py --files-from <list> <repo>` and the `.gitignore` test on every kit file. Every kit is read cold by an independent agent until it comes back SAFE. The screen is read live after every install: a sub-agent in the built-in browser, signed in as `manoj`; read `/finance/api/whoami` first. **Never tap a button on the live site for him.**
- The pharmacy scans (`assets.db`) are the Scan App's: READ ONLY.

---

## 0 · THE WORK — in order

**A · THE OPEN (OPEN_ROUTINE_v1)** — the board (messages `read:false` to `sanjeevni`, notes); the day's checks; the four numbers. **The live picture (read only):** Janta 21965 — revised bill come? ZUPRINOR 5 answered? New reception questions; Amir's visit.

**B · THE WORK**
1. **KIT S749 `ONE_SOURCE`** — build to `S403_KIT5_ONE_SOURCE_PLAN.md` §3 and the approved mock. In one kit, one install: (1) `scan_register.py` — one vocabulary, *Paper matches*, every difference to Amir (`band_p` → ₹0 for counted months; `s738_fixes` kind *round-off* with its Hindi do-line), the `owner` astate retired to Amir, the Ravi setting (`purchase.owner_confirm_suppliers`), the *Confirm* door and its Undo (audited), the inline actions on every line, plain words, the month strip, the read-quality and legacy folded; (2) `purchase_app.py` — the audit page's state column from the register, its Correct/Wrong hidden for the doctor, the month strip, the clipped item-wise numbers matched (F-1181), the hub's counted-month counts and status words, `_lock_gate` + the register's open rows (1 – 5, 8), Step 2 run by the server; (3) `amir_day.py` — the summary's *Marg sudhar · Wapsi baaki · proved* lines and the round-off card wording; (4) `porders.py` — `_s440_differs` follows the new band; Ravi's bills never on reception's *Scan karo*; (5) the parent's `portal.py` (the tile's url) and `month_read.py` (the *Purchase check* line and the register link per month) — PLANNED, on the bundle's bytes. **Walk on a made-up root with a CONTROL; DRY on the box; cold review SAFE; install; the five pages read live as manoj; the Book v1.51; the parent told of its two files.**
2. **KIT 4, on his "go":** the dealers' month summaries (row 6), the issues list, the server-built statements (D849), the lock and the NEFT (row 7). The Scan App's statement kind on the pharmacy lane — PLANNED line first, that chat told.
3. **THE ORDER-LIST KIT**, on his "go" (`S402_ORDER_LIST_PLAN.md`).
4. **His:** ZUPRINOR 5; the two unsent September supplier messages; F-1110's medical-PC half; F-1104 "count them"; the switch at D673's bar; June / July's old months.
5. **PARKED by his word:** F-802's permanent fix; F-1133 (D837). **NOT THIS PROJECT'S:** F-1048, D803, F-1102, F-1122 (the parent's); F-1174 (the Scan App's reader). **His with Ram Singh:** F-1115.
6. **The close** — `CLOSE_ROUTINE_v1`.

**NEVER:**
- **NEVER RUN** `deploy_kits\S488_DATES_AND_WAITS\deliver_S488.ps1`.
- **NEVER INSTALL** `deploy_kits\S638_EXPIRY_WATCH\`, `S672_NONCASH_AT_INGEST\` or `S673_NONCASH_AT_INGEST_R2\` (frozen).
- **NEVER ADD TO** Amir's *Aaj ka kaam* list (D690).
- **THE EXPIRY PAGE CHANGES ONLY ON HIS WORD** (D780, D793; D828).
- **NEVER CHANGE THE MEANING of a name the parent's console reads** without a word to the parent: `supplier_msg.s454_card_facts`, `porders.shortage_summary`, `expiry_watch.newest / now_view / ym_add`, `reports_tile.status`.
- **THE FLOW PAGES ARE PUBLIC — FIXED TEXT AND PICTURES ONLY.**
- **NEVER BOOK A VOUCHER IN THE SPINE'S `sp_move`.**
- **NEVER SEND A SUPPLIER WHATSAPP OR TAP A STAFF OR OWNER BUTTON FOR HIM** without his explicit word.
- **NEVER LET A TAP STAND FOR A MARG CORRECTION** — Amir's export is the proof (F-1162, D865).

**THE RULINGS THAT STAND:** as `START_HERE_SESSION_403` listed them (D862; D859 – D861; D853; D848; D847; D846; D839; D840; D831; D828; D815; D708 / D712; charter rule 8; D802; D731; D678 / D785; D837), plus:
- **PAPER MATCHES IS THE ONE GOOD STATE; EVERY DIFFERENCE, ₹1 INCLUDED, IS AMIR'S; THE "YOU" STATE IS GONE; ONE SOURCE, ONE LANGUAGE, ONE WAY IN; EVERYTHING INLINE ON HIS STEP VIEW; A MARG CORRECTION IS PROVED BY AMIR'S EXPORT (D865). RAVI IS OWNER-CONFIRMED (D866).**

**CLOSED BY HIS WORD — DO NOT RAISE AGAIN:** as `START_HERE_SESSION_391` listed, plus Deepam 641 (D854); the Yuvika 0774 name question and B-0239 (done by him 7-Nov).

## 1 · THE STANDING OWNER RULINGS

1. **Publishing is HIS double-click** — `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`.
2. **Full paths ALWAYS — including URLs**, each in its own copy block. **ONE line per command.**
3. **Token-lean — never at the cost of verification.** **Plain language. Short chat.** **ALL-CAPS = urgent.** **"Do not build" = study and answer only.**
4. **Mask patient numbers (last 4); never print secrets.** **Nothing live is rebuilt without his OK; the manual path stays.**
5. **Sub-agents read screens. Do not hand him diagnostics. When a screen is wrong, read its code first. Never hand him a step that is not his.**
6. **His board carries only what needs him and what he should know.**
7. **Never put a technical choice to him** — decide, say it in one line, carry on. **A screen for staff or for him: the mock first.** **His own pages: PC first, the Fold phone second (D853).**
8. **His phone gets the clinic app's messages; ntfy is the fallback (D846).**
