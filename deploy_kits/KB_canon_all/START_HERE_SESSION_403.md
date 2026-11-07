# START HERE — SESSION 403 — written at the S402 close (the Sanjeevni chat), 08-Nov-2026 (04:3x IST)

**Project: Sanjeevni — Pharmacy & Marg.** Open it in a fresh chat in this project, linked to manojz.

1. **The open:** follow `OPEN_ROUTINE_v1` (from the clone: `deploy_kits/KB_canon_all/OPEN_ROUTINE_v1.md`).
   - In the device VM `day_open.py` runs from `$HOME/mnt/Downloads/_kbtools` (`python3 day_open.py`, `--read`, `--note "..."`). **A re-run after a publish clears the day's note — write it again.**
   - Run Python with `TMPDIR=/tmp/s403w`. **A database copy goes to `/tmp/s403w/` in the device VM, never the cloud workspace (D656).** The nightly copies: `D:\Downloads\_kbtools\vps_code\finance_nightly.db.gz`, `code_nightly.tar.gz`.
2. **The rules:** the charter v1.1 — `claude/S307_BUILD_CHARTER_v1_1.md`, beside the parent's `BUILD_NORM_v1.md` (D704).
   - **The plan of record for the next build is `S402_ORDER_LIST_PLAN.md`** (D862; F-1176, F-1177). Then `S391_PURCHASE_RECONCILE_PLAN.md` (D839, D840, D846 – D849, D853, D854, D859 – D861) for kit 4.
   - The close is `CLOSE_ROUTINE_v1`. This project's `close.json` is in `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S402\close_parts\` — copy it and change what changed.
3. **This close's papers:** the brief `S402_BUILD_BRIEF.md`; the Book is still `SANJEEVNI_SYSTEM_BOOK_v1_50_S399.md` (no app change at S402).

**No incident is open.**

**The newest bundle is 08-Nov (03:15 IST).** It CONFIRMED S740's four pins: `scan_register.py` 12e3c7cb, `amir_day.py` 42a8430b, `porders_s454.py` 37c4f3bf, `purchase_app.py` 600c96d7. **This project has nothing DECLARED-PENDING.**
- **The order-list kit's FROM bytes (08-Nov bundle):** `order_sheet.py` 53abf461 · `order_track.py` 6f4746c5 · `order_track_page.py` 4e6bd715 (+ `porders_s454.py` 37c4f3bf). Read each WHOLE before patching (F-472); check no other chat has a PLANNED line on them (D646).
- **Medical PC:** `marg_push.py` 3f5ed144, `marg_watch.py` df7736e9.

*FIRST ACT: take your session number from the System Board's `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).*
- **403 is RESERVED for the Sanjeevni chat at this close.** The parent's 400 is open; the NK Pathology chat's 365 and the Scan App chat's 401 are reserved. Take what the board says, and say so in your first line.
- **Kit numbers are claimed BEFORE the scratch folder is named (F-515).** **Re-read `_numbers` just before a pinned write.** The board document is large — read it with `out_dir`, write the changed fields with `file_path` (the claims were trimmed to 40 at S402's open).

**Connections and machinery:**
- *Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.* For any medical-PC delivery, also `H:\My Drive\Clinic Data Archive\ToMedical` (device_list_dir / stage / commit only).
- **Never `git` in the device shell (F-511, F-1152):** read `.git\refs\heads\main`, `.git\refs\remotes\origin\main`, `.git\logs\HEAD` as files.
- **Placing a kit in the repo:** a tar committed to `03_WORKING_PAPERS\S###\`, then extracted with `tar --overwrite` in the device shell. Read it back by md5 (F-1099). `rm` is refused.

**What S339 – S402 learnt (keep it):**
- The live code = the newest bundle (08-Nov now carries every kit through S740) + any later kit's `make_*.py`.
- **A live-read brief names each staff page by its route** — Amir's own page is `/finance/amir/step/<n>` (a GET of `/finance/amir` runs `settle`, a write); `/finance/amir/day` is the owner's English summary. **A contradiction is read in the code before it reaches him (F-1178).**
- **A bill whose reading cannot pick its order waits for Marg — never the oldest order (F-1176).**
- **A tracker that settles a money item is settled only by a paper that can belong to nothing else (F-1172).**
- **Pack only after a green walk; read the packed CONTROL line against the walk; quote every heredoc (F-1173).**
- **A kit that re-pairs, re-ties or unpairs live records is installed only after its DRY run on the box has been read (F-1153).** A DRY line after 23:30 or before 04:00 carries `DRY=1 SKIP_WINDOW=1` (F-1163).
- **The SUMS packed is the build walked (F-1162).** **Every server-raised row has a withdrawal for every way its cause can leave (F-1161).** **A credit to a person is proved by the person's own act (F-1162).**
- Before naming the publish: `deploy_kits\NO_PHONE_NUMBERS.py --files-from <list> <repo>` and the `.gitignore` test on every kit file.
- Every kit is read cold by an independent agent until it comes back SAFE.
- The screen is read live after every install: a sub-agent in the built-in browser, signed in as `manoj`; read `/finance/api/whoami` first. **Never tap a button on the live site for him.**
- The pharmacy scans (`assets.db`) are the Scan App's: READ ONLY.

---

## 0 · THE WORK — in order

**A · THE OPEN (OPEN_ROUTINE_v1)** — the board (messages `read:false` to `sanjeevni`, notes); the day's checks; the four numbers.

**The live picture (read only):**
- **Janta 21965** — did the revised bill's scan (Pharmacy lane) settle the return, road *revised*? If it has a new bill number or did not read, say so to him in one line.
- **ZUPRINOR 5** and **PREGHYPE NT** (Shivaaz 02-11, *Nahi mila* / billed 12 strips) — his answers on row 8.
- New reception questions, new Marg purchase returns, Amir's visit (*Wapsi baaki*, *Marg sudhar*).

**B · THE WORK**
1. **THE ORDER-LIST KIT, on his "go"** (`S402_ORDER_LIST_PLAN.md`) — his screen changes, so **the mock first**:
   - retire an old incomplete order (SHIVAAZ 12-10; YUVIKA 20-10) — never re-ordered;
   - a replacement product counts (KEDAR FLACORT 6 → FLEMCORT 6; SHIVAAZ TOLTRIS PLUS → TOLIVANT PLUS — confirm the name on the mock); another pack size counts as came;
   - scans already with reception **stay** in his view (no change; at most *with reception, N days*);
   - **F-1176**: no oldest-order fall-back; the tie follows the Marg bill's items; one bill may close several orders; a wrong tie moved (audited); a size difference is a different item; re-read B-0237, B-0262, B-0174 under it — DRY on the box first;
   - **F-1177**: Verma 20-10's scan card; B-0174 twice; Daanshi B-0151 twice; Mannat 04-11 / Essential 02-11 with no bill number; "1 days".
2. **KIT 4, on his "go":** each dealer's month summary, the issues list, the month lock on Marg = papers = summaries, the statements built by the server (D849), the one NEFT on the suppliers' figures (F-1175's net). The mock first if a staff screen changes.
3. **His:** F-1110's medical-PC half (his yes first); F-1104 "count them"; F-1145 (Kedar ₹110 — A000211 stays *You*; bill 234 the same ₹110); the switch, on his word at D673's bar.
4. **PARKED by his word:** F-802's permanent fix; F-1133 (D837). **NOT THIS PROJECT'S:** F-1048, D803, F-1102, F-1122 (the parent's); F-1174 (the Scan App's reader). **His with Ram Singh:** F-1115.
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

**THE RULINGS THAT STAND:** as `START_HERE_SESSION_402` listed them (D859 – D861 returns; D853; D848; D847; D846; D839; D840; D831; D828; D815; D708 / D712; charter rule 8; D802; D731; D678 / D785; D837), plus:
- **AN OLD ORDER IS RETIRED BY HIM; A REPLACEMENT PRODUCT COUNTS; RECEPTION'S SCANS STAY IN HIS VIEW; A SCAN'S ORDER FOLLOWS THE MARG BILL'S ITEMS, NEVER THE OLDEST ORDER (D862).**

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
