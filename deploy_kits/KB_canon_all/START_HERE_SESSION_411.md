# START HERE — SESSION 411 — written at the S408 close (the Sanjeevni chat), 08-Nov-2026 (20:xx IST)

**Project: Sanjeevni — Pharmacy & Marg.** Open it in a fresh chat in this project, linked to manojz. **Kits S753 `SUMMARY_SCANS_READ` (18:58 IST 8-Nov) and S755 `SUMMARY_REMINDERS` (20:13) are LIVE; the Scan App's S754 `SUMMARY_RECOGNISE` (20:03 / 20:07) too — staff scan a dealer's month summary on the pharmacy lane like any bill and the system recognises it (D871); the awaited dealers of an ended month are on reception's list by themselves and the owner and Shavez get one line a day (D872).** This session's first build is **F-802's permanent fix** (its own small kit), then the order-list kit on his "go".

1. **The open:** follow `OPEN_ROUTINE_v1` (from the clone: `deploy_kits/KB_canon_all/OPEN_ROUTINE_v1.md`).
   - **The device shell on manojz** stopped answering at ~19:5x IST 8-Nov (*Failed to create bridge sockets*, F-1197) while the file-transfer tools, the browser and the board worked. Try it first; if it is still down, say so to the owner in one line and work as S408 did: the live code rebuilt in the cloud workspace from the newest bundle + the makers (code only — D656: no database copy there), the kits placed by the file tools and read back by hash. `day_open.py` needs the shell.
   - In the device VM `day_open.py` runs from `$HOME/mnt/Downloads/_kbtools` (`python3 day_open.py`, `--read`, `--note "..."`). Run Python with `TMPDIR=/tmp/s411w`; a database copy goes to `/tmp/s411w/`, never the cloud. **The device VM is fresh each session: `pip3 install --no-cache-dir --target /tmp/s411w/pylib flask` and `PYTHONPATH=/tmp/s411w/pylib`** (`/sessions` was full on 8-Nov — a user install failed; the target install worked). **The live code = the 09-Nov bundle** (01:35) when it has come — else the 08-Nov bundle + `make_s749.py` + `make_s750.py` + `make_s753.py` + `make_s755.py` (and the Scan App's `make_s754.py` for its three files) reproduce every live byte.
   - **The pin check (F-513):** eleven pins DECLARED-PENDING until the 09-Nov bundle — this project's `scan_register.py` 0822d308 · `purchase_app.py` e80f199c · `porders_s454.py` c463b87c · `owner_notice.py` 9096af9a · `amir_day.py` c86bb8e5 · `porders.py` c495f812; the parent's `month_read.py` b2d30289 · `portal.py` 59b5c252; the Scan App's `asset_register.py` 74043cdb · `claude_reader.py` ce3868ed · `scan_checks_s441.py` 59d5cb1c. The 09-Nov bundle should CONFIRM all eleven — read the day page; confirm or say why not.
2. **The rules:** the charter v1.1 — `claude/S307_BUILD_CHARTER_v1_1.md`, beside the parent's `BUILD_NORM_v1.md` (D704). The close is `CLOSE_ROUTINE_v1`; this project's `close.json` is in `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S408\close_parts\` — copy it and change what changed (it carries the `book` block).
3. **This close's papers:** the brief `S408_BUILD_BRIEF.md`; the Book **`SANJEEVNI_SYSTEM_BOOK_v1_53_S408.md`** (§15AR: kits S753 and S755, the Scan App's S754); the kits' READMEs `deploy_kits\S753_SUMMARY_SCANS_READ\README.md` and `deploy_kits\S755_SUMMARY_REMINDERS\README.md`; the Scan App's prompt `S408_SCANAPP_PROMPT_SUMMARY_READ.md`.

**No incident is open except F-1197 (the shell). Remind him once of F-1133** (the medical PC's LAN; parked by D837) — at this open, in one line, no build.

*FIRST ACT: take your session number from the System Board's `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).*
- **411 is RESERVED for the Sanjeevni chat at this close.** The NK Pathology chat's 365 and the parent's 404 are open; the Scan App chat's 410 reserved. Take what the board says, and say so in your first line.
- A kit number before the scratch folder is named. D and F numbers at the close only. **Re-read `_numbers` just before a pinned write.** The board document is large — read it with `out_dir`, write the changed fields with `file_path`.

**Connections and machinery:**
- *Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.*
- **Never `git` in the device shell (F-511, F-1152):** read `.git\refs\heads\main`, `.git\refs\remotes\origin\main`, `.git\logs\HEAD` as files.
- **Placing a kit in the repo:** `cp` in the device shell, or — the shell down — `device_commit_files` to `deploy_kits\<KIT>\` then stage the folder back and `md5sum -c SUMS.md5` in the cloud (S408 did; 19/19). SUMS made last (F-1099). `rm` is refused in a connected folder; `mv` within it works.
- **The S755 kit is the pattern to copy** (`deploy_kits\S755_SUMMARY_REMINDERS\`): `make_*.py` with anchored edits on the live bytes + appended sections (`sec_*.txt`) · the walk = the previous kit's walk whole + this kit's section (`assemble_*.py` re-words, by name, the earlier lines the kit changes on purpose) with a CONTROL · the earlier kits' walks compared (`earlier()`, an allow-list by name) · `proof_*.py` by the LIVE files and the kit's on the box's databases, `mode=ro` · a part cron runs checked the way cron runs it (`check_s755_cron.py`) · the installer rehearsed (`rehearse_*.sh setup | dry | real | again | red`) · a cold review until SAFE · the screens read live by a sub-agent as manoj.
- **Row 7's words live:** *On reception's list by itself since the month ended · you and Shavez are told each morning until it comes* (awaited); *Yogendra Agencies' ledger*; *Scanned 08-11 15:11 · 12 bills ₹65,357 · dealer named by its bills*. Reception's card: *<Dealer> ka October 2026 ka hisaab (summary) scan karo … October 2026 khatam — dealer ka hisaab (summary) abhi tak nahi aaya*. `owner_notice` settings: `owner_notice.summaries_hhmm` 10:30 · `owner_notice.summaries_to` manoj,shavez (written by `ensure()` at its first tick after 20:13).

**What S339 – S408 learnt (keep it):**
- **A new kind of row needs every door that serves rows read for its kind filter (F-1195); a kit that lands a new kind of row walks every door that serves it (F-1196).** **The printed name first; the bills as the fallback; never the buyer (D871); a short bill number matched equal, never as a tail.** **A part cron runs is checked the way cron runs it.** **The build does not depend on the shell (F-1197).** **Two chats, one ruling, one prompt — each touches only its files; the contract named in the prompt.**
- **A paper the system cannot name is asked about, never filed by default (F-1190 — now: recognised by its content, D871).** **A refusal on the box is read in the kit's own words before it is judged (F-1191).** **A pull right after a publish may be early.** **One paper, one Save (D870).** **A difference is never nobody's (S749).** **A page added later reads the list the owner reads (F-1183).** **A line Marg could not name is matched by what it carries (F-1181).** **A made-up root's dates follow the clock (F-1184).** **A page reads rows, never a function written to act (F-1186).** **A hand-moved amount is re-derived from Marg every time it is shown (F-1187).** **A reader never creates a table.** **The running month has no month end (D869).**
- A live-read brief names each staff page by its route — Amir's own page is `/finance/amir/step/<n>` (a GET of `/finance/amir` runs `settle`, a write); `/finance/amir/day` is the owner's English summary; the owner's step view is `/finance/purchase/page/check?month=YYYY-MM` (the doctor only); the register `/page/scans?month=`, the audit `/page/month/<M>`, the hub `/page/hub`, the sheet `/page/pay/<M>`, the dealer ledgers `/page/ledger`, `/page/ledger/<dealer key>`; reception's `/finance/porders/s454/billkaam`; the scan screen `/scanapp/intake?lane=pharmacy`; the summary viewer `/finance/purchase/api/s738/scan/<id>` (the doctor: any Pharmacy or Summary scan).
- **A kit that re-pairs, re-ties, unpairs or re-states live records is installed only after its DRY run on the box has been read (F-1153).** **Pack only after a green walk; the SUMS packed is the build walked (F-1162).** Before naming the publish: `deploy_kits\NO_PHONE_NUMBERS.py --files-from <list> <repo>` and the `.gitignore` test on every kit file. **Never tap a button on the live site for him.**
- The pharmacy scans (`assets.db`) are the Scan App's: READ ONLY. A summary is `kind='Summary'` there (whichever road put it there, D871); a bill `kind='Pharmacy'`; a challan `kind='Challan'`.

---

## 0 · THE WORK — in order

**A · THE OPEN (OPEN_ROUTINE_v1)** — the shell (F-1197); the board (messages `read:false` to `sanjeevni` — the Scan App chat's S409 close may have left one; notes); the day's checks; the eleven pins (the 09-Nov bundle should confirm them); the four numbers; the one-line F-1133 reminder. **The live picture (read only, a sub-agent as manoj):** row 7 of October — how many agree / differ / awaited now (11 · 1 · 6 at 20:15 8-Nov)? Did the daily line go after 10:30 (`owner_notice show` on the box is his; here: the step view and the board)? Any new summary scanned without the tick landed as a Summary (S754)? The four undecided `purchase_scan_state` scratch rows S754 left — do they show anywhere (the register, row 2)? Fix what the real papers show before the planned work.

**B · THE WORK**
1. **F-802'S PERMANENT FIX — its own small kit** (D867 / D868): read `deploy_kits\S500_REPORT_CHECK` (its F-802 part never installed), the medical PC's `marg_watch.py` from the newest mirror, the server's door (`/root/marg_ingest/`). The watcher says *received again, same as <stamp>*; the door records a re-receipt and lets it satisfy a duty due after a tick. Two installs (the medical PC's agent kit by its own road — read how S722's medical pair was installed; the server's door). Walk; DRY on both boxes; a cold review; no mock.
2. **THE ORDER-LIST KIT**, on his "go" (`S402_ORDER_LIST_PLAN.md`); staff screens change: **the mock first**.
3. **Small, with the next kit that touches them:** reception's S750 card's *press the summary button* sentence (`porders_s454`, moot since S754); the four scratch rows (a guarded line after a read); the two *Why:* lines' ` -- ` on row 7; F-1184.
4. **His:** the dealers who never send a summary — *gives no summary*, once each (row 7); Shavez's phone (the clinic app opened once); ZUPRINOR 5; the two unsent September supplier messages; F-1110's medical-PC half; F-1104 "count them"; the switch at D673's bar; June / July's old months. **Staff:** reception — the six awaited dealers' summaries when they come; Amir's row-2 corrections (Shivaaz 3854, Yogendra 19612) and the item-wise export; Shavez's Bass cheque.
5. **PARKED by his word:** F-1133 (D837) — remind, never build unasked. **NOT THIS PROJECT'S:** F-1185 (the tile's grant), F-1048, D803, F-1102, F-1122 (the parent's); F-1194, F-1174 (the Scan App's); F-1197 (manojz — nobody's build; watch). **His with Ram Singh:** F-1115.
6. **The close** — `CLOSE_ROUTINE_v1`.

**NEVER:**
- **NEVER RUN** `deploy_kits\S488_DATES_AND_WAITS\deliver_S488.ps1`.
- **NEVER INSTALL** `deploy_kits\S638_EXPIRY_WATCH\`, `S672_NONCASH_AT_INGEST\` or `S673_NONCASH_AT_INGEST_R2\` (frozen).
- **NEVER ADD TO** Amir's *Aaj ka kaam* list (D690).
- **THE EXPIRY PAGE CHANGES ONLY ON HIS WORD** (D780, D793; D828).
- **NEVER CHANGE THE MEANING of a name the parent's console reads** without a word to the parent: `supplier_msg.s454_card_facts`, `porders.shortage_summary`, `expiry_watch.newest / now_view / ym_add`, `reports_tile.status`, `scan_register.s749_month_open` (its keys; S755 made `match` count the accepted and confirmed bills — the parent told), `s749_lock_reasons`.
- **THE FLOW PAGES ARE PUBLIC — FIXED TEXT AND PICTURES ONLY.**
- **NEVER BOOK A VOUCHER IN THE SPINE'S `sp_move`.**
- **NEVER SEND A SUPPLIER WHATSAPP OR TAP A STAFF OR OWNER BUTTON FOR HIM** without his explicit word.
- **NEVER LET A TAP STAND FOR A MARG CORRECTION** — Amir's export is the proof (F-1162, D865).
- **NEVER LET A COUNTED DIFFERENCE BE NOBODY'S** — every open bill is on exactly one list (S749).
- **NEVER CALL A WRITER FROM A PAGE** (F-1186). **NEVER CREATE A TABLE FROM A READER.**
- **NEVER TAKE THE PHARMACY'S OWN NAME AS A DEALER; NEVER MATCH A SHORT BILL NUMBER AS A TAIL** (S753).
- **NEVER RUN S751 AGAIN**; never convert a staff scan by hand — the Scan App recognises a summary by itself (D871); a wrong recognition is undone by a person's move on its screens.

**THE RULINGS THAT STAND:** as `START_HERE_SESSION_408` listed them (D867 as revised by D868; D865, D866; D862; D859 – D861; D853; D848; D847; D846; D839; D840; D831; D828; D815; D708 / D712; charter rule 8; D802; D731; D678 / D785; D837; D868; D869; D870's *one paper, one Save* and its method for a one-off on live data), plus **D871 (the Scan App chat's — recognised by content, tick or no tick; the printed name first, the bills as the fallback; never the buyer; the month from the bills; a statement never a page 2; supersedes D870's *staff rescan it*) and D872 (the reminders — reception's cards by themselves, one line a day to him and Shavez; the *Ask reception* button retired).**

**CLOSED BY HIS WORD — DO NOT RAISE AGAIN:** as `START_HERE_SESSION_408` listed, plus the summary tick (staff need not press it — D871); the sixteen mis-kinded scans of S407 and the eight of S408 (set right by S751 / S754 — not to be raised again).

## 1 · THE STANDING OWNER RULINGS

1. **Publishing is HIS double-click** — `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`.
2. **Full paths ALWAYS — including URLs**, each in its own copy block. **ONE line per command.**
3. **Token-lean — never at the cost of verification.** **Plain language. Short chat.** **ALL-CAPS = urgent.** **"Do not build" = study and answer only.**
4. **Mask patient numbers (last 4); never print secrets.** **Nothing live is rebuilt without his OK; the manual path stays.**
5. **Sub-agents read screens. Do not hand him diagnostics. When a screen is wrong, read its code first. Never hand him a step that is not his.**
6. **His board carries only what needs him and what he should know.**
7. **Never put a technical choice to him** — decide, say it in one line, carry on. **A screen for staff or for him: the mock first.** **His own pages: PC first, the Fold phone second (D853).**
8. **His phone gets the clinic app's messages; ntfy is the fallback (D846).** **Shavez's too, for the summaries line (D872).**
