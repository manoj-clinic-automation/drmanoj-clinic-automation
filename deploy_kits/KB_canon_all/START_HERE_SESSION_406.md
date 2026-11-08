# START HERE — SESSION 406 — written at the S405 close (the Sanjeevni chat), 08-Nov-2026 (08:4x IST)

**Project: Sanjeevni — Pharmacy & Marg.** Open it in a fresh chat in this project, linked to manojz. **Kit S749 `ONE_SOURCE` is LIVE (installed 08:20 IST 8-Nov).** This session's first build is **F-802's permanent fix** (his word 08:34, D867), then kit 4 on his "go".

1. **The open:** follow `OPEN_ROUTINE_v1` (from the clone: `deploy_kits/KB_canon_all/OPEN_ROUTINE_v1.md`).
   - In the device VM `day_open.py` runs from `$HOME/mnt/Downloads/_kbtools` (`python3 day_open.py`, `--read`, `--note "..."`). **A re-run after a publish clears the day's note — write it again.**
   - Run Python with `TMPDIR=/tmp/s406w` (the device VM's default `/tmp` fills — S405 saw `database or disk is full` in a walk run from `/tmp`). **A database copy goes to `/tmp/s406w/` in the device VM, never the cloud workspace (D656).** The nightly copies: `D:\Downloads\_kbtools\vps_code\finance_nightly.db.gz`, `code_nightly.tar.gz`. **flask is installed in the device VM (`pip3 install flask`, S405) — the walks run there.**
   - **The pin check (F-513):** six S749 pins are DECLARED-PENDING until the 09-Nov bundle carries them — `scan_register.py` 5b066249 · `purchase_app.py` 0d49c249 · `amir_day.py` 98c40f51 · `porders.py` c495f812 · the parent's `month_read.py` b2d30289 · `portal.py` 59b5c252. Read the day page; confirm or say why not.
2. **The rules:** the charter v1.1 — `claude/S307_BUILD_CHARTER_v1_1.md`, beside the parent's `BUILD_NORM_v1.md` (D704). The close is `CLOSE_ROUTINE_v1`; this project's `close.json` is in `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S405\close_parts\` — copy it and change what changed.
3. **This close's papers:** the brief `S405_BUILD_BRIEF.md`; the Book **`SANJEEVNI_SYSTEM_BOOK_v1_51_S405.md`** (§15AP: kit S749); the kit's README `deploy_kits\S749_ONE_SOURCE\README.md` (what each page says, the reviews, the named limits).

**No incident is open. Remind him once of F-1133** (the medical PC's LAN; parked by D837; he asked to be reminded — his memory note of 08:34) — at this open, in one line, no build.

*FIRST ACT: take your session number from the System Board's `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).*
- **406 is RESERVED for the Sanjeevni chat at this close.** The NK Pathology chat's 365 and the Scan App chat's 401 are open; the parent's 404 is reserved. Take what the board says, and say so in your first line.
- A kit number before the scratch folder is named (kit_next 750). D and F numbers at the close only. **Re-read `_numbers` just before a pinned write.** The board document is large — read it with `out_dir`, write the changed fields with `file_path`.

**Connections and machinery:**
- *Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.*
- **Never `git` in the device shell (F-511, F-1152):** read `.git\refs\heads\main`, `.git\refs\remotes\origin\main`, `.git\logs\HEAD` as files.
- **Placing a kit in the repo:** copy the folder into `deploy_kits\<KIT>\` (S405 did it with `cp` in the device shell; SUMS made last, `md5sum -c` read back). Read it back by md5 (F-1099). `rm` is refused in a connected folder.
- **The S749 kit's pattern is the one to copy** (`deploy_kits\S749_ONE_SOURCE\`): appended sections + `make_*.py` anchors · `walk_*.py` on a made-up root with a CONTROL · the earlier walks compared old against new (`earlier()`) · `proof_*.py` run by the LIVE files and by the kit's, the difference printed · a cold review until SAFE · a screen read · the installer rehearsed on a made-up root with stubs (`ROOT= APY= VPY= HEALTH_CMD= SYSTEMCTL= JOURNALCTL=/bin/false TMPW= TMPDIR=`).

**What S339 – S405 learnt (keep it):**
- The live code = the 08-Nov bundle + kit S749 (`make_s749.py` on the bundle's six files reproduces the TO pins).
- **A difference is never nobody's; one tally for every page (S749).** **A page added later reads the list the owner reads (F-1183).** **A line Marg could not name is matched by what it carries (F-1181).** **A made-up root's dates follow the clock (F-1184).**
- A live-read brief names each staff page by its route — Amir's own page is `/finance/amir/step/<n>` (a GET of `/finance/amir` runs `settle`, a write); `/finance/amir/day` is the owner's English summary; the owner's step view is `/finance/purchase/page/check?month=YYYY-MM` (the doctor only); the register `/page/scans?month=`, the audit `/page/month/<M>`, the hub `/page/hub`, the sheet `/page/pay/<M>`.
- **A kit that re-pairs, re-ties, unpairs or re-states live records is installed only after its DRY run on the box has been read (F-1153).** A DRY line after 23:30 or before 04:00 carries `DRY=1 SKIP_WINDOW=1` (F-1163).
- **Pack only after a green walk; the SUMS packed is the build walked (F-1162).** Every server-raised row has a withdrawal for every way its cause can leave (F-1161). A credit to a person is proved by the person's own act (F-1162) — a Marg correction leaves Amir's card only by his export.
- Before naming the publish: `deploy_kits\NO_PHONE_NUMBERS.py --files-from <list> <repo>` and the `.gitignore` test on every kit file. The screen is read live after every install: a sub-agent in the built-in browser, signed in as `manoj`; read `/finance/api/whoami` first. **Never tap a button on the live site for him.**
- The pharmacy scans (`assets.db`) are the Scan App's: READ ONLY.

---

## 0 · THE WORK — in order

**A · THE OPEN (OPEN_ROUTINE_v1)** — the board (messages `read:false` to `sanjeevni`, notes); the day's checks; the six pins; the four numbers; the one-line F-1133 reminder. **The live picture (read only):** has Amir's export proved any of the six differences? Ravi 9012 confirmed? Janta's paper come? ZUPRINOR 5 answered? Did reception see anything odd on *Aaj ka bill kaam* (its list follows the one band now: a ₹1 gap asks nobody)?

**B · THE WORK**
1. **F-802'S PERMANENT FIX — its own small kit (D867).** Read first: `S500`'s kit text in the repo (`deploy_kits\S500_REPORT_CHECK`, its F-802 part never installed) for the re-receipt it drafted; the medical PC's `marg_watch.py` (the live copy from manojz's mirror of `D:\SendToClinic\`, pinned 39fa2773 at S382 — read the newest mirror, F-472); the server's receiving door (`/root/marg_ingest/`, the `TXT_SEEN` / `TAKEN` verdicts, `report.txt`). Build: the watcher says *received again, same as <stamp>* (one line to the server, one census line); the door records a re-receipt (a row, audited) and a duty due after a tick is satisfied by it; the owner's duty line clears. Two installs: the medical PC's agent kit by its own road (`D:\SendToClinic\` — read how S722's medical pair was installed, `deploy_kits\S722_ALARMS_REACH_OWNER`) and the server's door. Walk on a made-up root; DRY on both boxes; a cold review; the mock is not needed (no screen changes beyond a census line) — say so.
2. **KIT 4, THE MONTH END — one kit, on his "go"** (`S391_PURCHASE_RECONCILE_PLAN.md` §4; D849; F-1175). The Scan App's *statement* kind on the pharmacy lane first — a PLANNED line on `board/_numbers`, that chat told. Then: the dealers' month statements against Marg (row 7 of the step view), the issues list, the server-built statements, the lock and the NEFT when Marg = papers = summaries — all on S749's one tally. **The mock first** (his screens change: row 7, the sheet).
3. **THE ORDER-LIST KIT**, separately, on his "go" (`S402_ORDER_LIST_PLAN.md`).
4. **His:** Ravi 9012 *Confirm*; ZUPRINOR 5; the two unsent September supplier messages; F-1110's medical-PC half; F-1104 "count them"; the switch at D673's bar; June / July's old months.
5. **PARKED by his word:** F-1133 (D837) — remind, never build unasked. **NOT THIS PROJECT'S:** F-1185 (the tile's grant), F-1048, D803, F-1102, F-1122 (the parent's); F-1174 (the Scan App's reader). **His with Ram Singh:** F-1115.
6. **The close** — `CLOSE_ROUTINE_v1`.

**NEVER:**
- **NEVER RUN** `deploy_kits\S488_DATES_AND_WAITS\deliver_S488.ps1`.
- **NEVER INSTALL** `deploy_kits\S638_EXPIRY_WATCH\`, `S672_NONCASH_AT_INGEST\` or `S673_NONCASH_AT_INGEST_R2\` (frozen).
- **NEVER ADD TO** Amir's *Aaj ka kaam* list (D690).
- **THE EXPIRY PAGE CHANGES ONLY ON HIS WORD** (D780, D793; D828).
- **NEVER CHANGE THE MEANING of a name the parent's console reads** without a word to the parent: `supplier_msg.s454_card_facts`, `porders.shortage_summary`, `expiry_watch.newest / now_view / ym_add`, `reports_tile.status`, and now **`scan_register.s749_month_open` / `s749_lock_reasons`** (the parent's `month_read.py` reads them).
- **THE FLOW PAGES ARE PUBLIC — FIXED TEXT AND PICTURES ONLY.**
- **NEVER BOOK A VOUCHER IN THE SPINE'S `sp_move`.**
- **NEVER SEND A SUPPLIER WHATSAPP OR TAP A STAFF OR OWNER BUTTON FOR HIM** without his explicit word.
- **NEVER LET A TAP STAND FOR A MARG CORRECTION** — Amir's export is the proof (F-1162, D865).
- **NEVER LET A COUNTED DIFFERENCE BE NOBODY'S** — every open bill is on exactly one list, the one `_s749_groups` tallies (S749).

**THE RULINGS THAT STAND:** as `START_HERE_SESSION_405` listed them (D865, D866; D862; D859 – D861; D853; D848; D847; D846; D839; D840; D831; D828; D815; D708 / D712; charter rule 8; D802; D731; D678 / D785; D837), plus **D867 (the build order: F-802's fix alone and first; kit 4 one kit; the order-list kit apart; F-1133 parked, reminded).**

**CLOSED BY HIS WORD — DO NOT RAISE AGAIN:** as `START_HERE_SESSION_391` listed, plus Deepam 641 (D854); the Yuvika 0774 name question and B-0239 (done by him 7-Nov); the mock's wording and layout of the step view (approved 06:04, built, read live — his one remark after: none).

## 1 · THE STANDING OWNER RULINGS

1. **Publishing is HIS double-click** — `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`.
2. **Full paths ALWAYS — including URLs**, each in its own copy block. **ONE line per command.**
3. **Token-lean — never at the cost of verification.** **Plain language. Short chat.** **ALL-CAPS = urgent.** **"Do not build" = study and answer only.**
4. **Mask patient numbers (last 4); never print secrets.** **Nothing live is rebuilt without his OK; the manual path stays.**
5. **Sub-agents read screens. Do not hand him diagnostics. When a screen is wrong, read its code first. Never hand him a step that is not his.**
6. **His board carries only what needs him and what he should know.**
7. **Never put a technical choice to him** — decide, say it in one line, carry on. **A screen for staff or for him: the mock first.** **His own pages: PC first, the Fold phone second (D853).**
8. **His phone gets the clinic app's messages; ntfy is the fallback (D846).**
