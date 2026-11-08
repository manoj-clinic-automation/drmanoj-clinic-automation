# START HERE — SESSION 407 — written at the S406 close (the Sanjeevni chat), 08-Nov-2026 (12:0x IST)

**Project: Sanjeevni — Pharmacy & Marg.** Open it in a fresh chat in this project, linked to manojz. **Kit S750 `MONTH_END` (kit 4) is LIVE (installed 11:39 IST 8-Nov).** This session's first build is **the month-end flow completed** (D868: F-1189 pre-September *settled outside*, F-1188 the hub's count, the wording) — one small kit; then F-802's fix; then the order-list kit on his "go".

1. **The open:** follow `OPEN_ROUTINE_v1` (from the clone: `deploy_kits/KB_canon_all/OPEN_ROUTINE_v1.md`).
   - In the device VM `day_open.py` runs from `$HOME/mnt/Downloads/_kbtools` (`python3 day_open.py`, `--read`, `--note "..."`). **A re-run after a publish clears the day's note — write it again.** Run Python with `TMPDIR=/tmp/s407w`; a database copy goes to `/tmp/s407w/`, never the cloud (D656). The nightly copies: `D:\Downloads\_kbtools\vps_code\finance_nightly.db.gz`, `code_nightly.tar.gz`. **The device VM is fresh each session: `pip3 install flask` before a walk** (S406 found it absent again). A detached process dies with the call; a call is capped at three minutes — run long things in phases (S750's rehearsal shows how).
   - **The pin check (F-513):** twelve pins are DECLARED-PENDING until the 09-Nov bundle carries them — S750's six (`scan_register.py` fdb0960f · `purchase_app.py` 262cafd3 · `amir_day.py` c86bb8e5 · `porders_s454.py` a8fca8ef · the Scan App's `asset_register.py` dfa0955c · `claude_reader.py` 8e1ae6bf) and S749's `porders.py` c495f812, the parent's `month_read.py` b2d30289, `portal.py` 59b5c252 (S749's three other pins are superseded by S750's on the same files). Read the day page; confirm or say why not.
2. **The rules:** the charter v1.1 — `claude/S307_BUILD_CHARTER_v1_1.md`, beside the parent's `BUILD_NORM_v1.md` (D704). The close is `CLOSE_ROUTINE_v1`; this project's `close.json` is in `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S406\close_parts\` — copy it and change what changed.
3. **This close's papers:** the brief `S406_BUILD_BRIEF.md`; the Book **`SANJEEVNI_SYSTEM_BOOK_v1_52_S406.md`** (§15AQ: kit S750); the plan `S406_KIT4_MONTH_END_PLAN.md`; the kit's README `deploy_kits\S750_MONTH_END\README.md` (what each screen says, the reviews, the named limits).

**No incident is open. Remind him once of F-1133** (the medical PC's LAN; parked by D837) — at this open, in one line, no build.

*FIRST ACT: take your session number from the System Board's `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).*
- **407 is RESERVED for the Sanjeevni chat at this close.** The NK Pathology chat's 365 and the Scan App chat's 401 are open; the parent's 404 is reserved. Take what the board says, and say so in your first line.
- A kit number before the scratch folder is named (kit_next 751). D and F numbers at the close only. **Re-read `_numbers` just before a pinned write.** The board document is large — read it with `out_dir`, write the changed fields with `file_path`.

**Connections and machinery:**
- *Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.*
- **Never `git` in the device shell (F-511, F-1152):** read `.git\refs\heads\main`, `.git\refs\remotes\origin\main`, `.git\logs\HEAD` as files.
- **Placing a kit in the repo:** copy the folder into `deploy_kits\<KIT>\` with `cp` in the device shell; SUMS made last, `md5sum -c` read back (F-1099). `rm` is refused in a connected folder.
- **The S750 kit's pattern is the one to copy** (`deploy_kits\S750_MONTH_END\`): the live files read whole by fresh agents that return maps with verbatim anchors · appended sections + `make_*.py` anchors · `walk_*.py` on S749's fixture extended, with a CONTROL · `walk_*_app.py` on the real scan app when a Scan App file moves · the earlier walks compared (`earlier()`) · `proof_*.py` by the LIVE files and by the kit's · a cold review until SAFE (R1 found three must-fix S406's walk could not) · the installer rehearsed in phases (`rehearse_*.sh setup | dry | real | again | red`) · the screens read live by a sub-agent as manoj.
- **The live code = the 08-Nov bundle + kit S749 + kit S750** (`make_s749.py` then `make_s750.py` on the bundle's files reproduce the TO pins).

**What S339 – S406 learnt (keep it):**
- **A difference is never nobody's; one tally for every page (S749).** **A page added later reads the list the owner reads (F-1183).** **A line Marg could not name is matched by what it carries (F-1181).** **A made-up root's dates follow the clock (F-1184).** **A page reads rows, never a function written to act (F-1186).** **A hand-moved amount is re-derived from Marg every time it is shown (F-1187).** **A reader never creates a table.** **The running month has no month end (D869).**
- A live-read brief names each staff page by its route — Amir's own page is `/finance/amir/step/<n>` (a GET of `/finance/amir` runs `settle`, a write); `/finance/amir/day` is the owner's English summary; the owner's step view is `/finance/purchase/page/check?month=YYYY-MM` (the doctor only); the register `/page/scans?month=`, the audit `/page/month/<M>`, the hub `/page/hub`, the sheet `/page/pay/<M>`, **the dealer ledgers `/page/ledger`, `/page/ledger/<dealer key>`** (the doctor and the senders); reception's `/finance/porders/s454/billkaam`; the scan screen `/scanapp/intake?lane=pharmacy`.
- **A kit that re-pairs, re-ties, unpairs or re-states live records is installed only after its DRY run on the box has been read (F-1153).** A DRY line after 23:30 or before 04:00 carries `DRY=1 SKIP_WINDOW=1` (F-1163).
- **Pack only after a green walk; the SUMS packed is the build walked (F-1162).** Every server-raised row has a withdrawal for every way its cause can leave (F-1161). A credit to a person is proved by the person's own act (F-1162) — a Marg correction leaves Amir's card only by his export.
- Before naming the publish: `deploy_kits\NO_PHONE_NUMBERS.py --files-from <list> <repo>` and the `.gitignore` test on every kit file. The screen is read live after every install: a sub-agent in the built-in browser, signed in as `manoj`; read `/finance/api/whoami` first. **Never tap a button on the live site for him.**
- The pharmacy scans (`assets.db`) are the Scan App's: READ ONLY. A summary is `kind='Summary'` there; a bill `kind='Pharmacy'`; a challan `kind='Challan'`.

---

## 0 · THE WORK — in order

**A · THE OPEN (OPEN_ROUTINE_v1)** — the board (messages `read:false` to `sanjeevni`, notes); the day's checks; the twelve pins; the four numbers; the one-line F-1133 reminder. **The live picture (read only):** has reception scanned any October dealer summary with the new button (kind `Summary` in assets.db)? Did the reader read it as a summary (claude_reading doc_kind `summary`)? What does row 7 say of it — agrees, differs (and is the *why* right), unreadable, unknown dealer? Which dealers has he marked *gives no summary*? Did anything on the step view, the sheet or a ledger read wrong? Fix what the first real papers show before the planned work.

**B · THE WORK**
1. **THE MONTH-END FLOW COMPLETED — one small kit, first (D868).** (a) **F-1189:** the months before `purchase.register_from` (September and earlier) read *settled outside the system* on every ledger — paid = payable, balance ₹0, the FY block says how many months are so; a typed Paid still wins. (b) **F-1188:** `s749_month_open`'s `match` counts the accepted and confirmed bills too (the hub's and the console's words then equal the step view's row 1; the parent told at the close — the words' meaning is unchanged). (c) The wording: the ledger links' *'s* on a name ending in s; *--* → *·* on row 8, the running line and row 7's footer. Walk, control, proof, rehearsal, a cold review, his publish, his line — the S750 pattern. No mock needed (no new screen; say so).
2. **F-802'S PERMANENT FIX — its own small kit** (D867 / D868): read `deploy_kits\S500_REPORT_CHECK` (its F-802 part never installed), the medical PC's `marg_watch.py` from the newest mirror, the server's door (`/root/marg_ingest/`). The watcher says *received again, same as <stamp>*; the door records a re-receipt and lets it satisfy a duty due after a tick. Two installs (the medical PC's agent kit by its own road — read how S722's medical pair was installed; the server's door). Walk; DRY on both boxes; a cold review; no mock.
3. **THE ORDER-LIST KIT**, on his "go" (`S402_ORDER_LIST_PLAN.md`); staff screens change: **the mock first**.
4. **His:** the dealers who never send a summary — *gives no summary*, once each (row 7); Ravi 9012 *Confirm* if still open; ZUPRINOR 5; the two unsent September supplier messages; F-1110's medical-PC half; F-1104 "count them"; the switch at D673's bar; June / July's old months.
5. **PARKED by his word:** F-1133 (D837) — remind, never build unasked. **NOT THIS PROJECT'S:** F-1185 (the tile's grant), F-1048, D803, F-1102, F-1122 (the parent's); F-1174 (the Scan App's reader). **His with Ram Singh:** F-1115.
6. **The close** — `CLOSE_ROUTINE_v1`.

**NEVER:**
- **NEVER RUN** `deploy_kits\S488_DATES_AND_WAITS\deliver_S488.ps1`.
- **NEVER INSTALL** `deploy_kits\S638_EXPIRY_WATCH\`, `S672_NONCASH_AT_INGEST\` or `S673_NONCASH_AT_INGEST_R2\` (frozen).
- **NEVER ADD TO** Amir's *Aaj ka kaam* list (D690).
- **THE EXPIRY PAGE CHANGES ONLY ON HIS WORD** (D780, D793; D828).
- **NEVER CHANGE THE MEANING of a name the parent's console reads** without a word to the parent: `supplier_msg.s454_card_facts`, `porders.shortage_summary`, `expiry_watch.newest / now_view / ym_add`, `reports_tile.status`, `scan_register.s749_month_open` (its keys; S750 added `dealers`, `dealer_words` and grew `open` / `words`), `s749_lock_reasons`, `s749_month_open` / `s749_lock_reasons` (the parent's `month_read.py` reads them).
- **THE FLOW PAGES ARE PUBLIC — FIXED TEXT AND PICTURES ONLY.**
- **NEVER BOOK A VOUCHER IN THE SPINE'S `sp_move`.**
- **NEVER SEND A SUPPLIER WHATSAPP OR TAP A STAFF OR OWNER BUTTON FOR HIM** without his explicit word.
- **NEVER LET A TAP STAND FOR A MARG CORRECTION** — Amir's export is the proof (F-1162, D865).
- **NEVER LET A COUNTED DIFFERENCE BE NOBODY'S** — every open bill is on exactly one list, the one `_s749_groups` tallies (S749).
- **NEVER CALL A WRITER FROM A PAGE** (F-1186) — the ledger reads `purchase_neft_event`, never `supplier_msg.state()`.
- **NEVER CREATE A TABLE FROM A READER** — the writers and the installer make the S750 tables.

**THE RULINGS THAT STAND:** as `START_HERE_SESSION_406` listed them (D867 as revised by D868; D865, D866; D862; D859 – D861; D853; D848; D847; D846; D839; D840; D831; D828; D815; D708 / D712; charter rule 8; D802; D731; D678 / D785; D837), plus **D868 (the order: the month-end flow completed, then F-802's fix, then the order-list kit) and D869 (summary; the dealer ledger never sent routinely; the running month never awaited).**

**CLOSED BY HIS WORD — DO NOT RAISE AGAIN:** as `START_HERE_SESSION_391` listed, plus Deepam 641 (D854); the Yuvika 0774 name question and B-0239; the step view's mock (S403); **kit 4's mock (approved 09:45 8-Nov with his two words); reception's scanner report of 11:50 (working again 11:53).**

## 1 · THE STANDING OWNER RULINGS

1. **Publishing is HIS double-click** — `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`.
2. **Full paths ALWAYS — including URLs**, each in its own copy block. **ONE line per command.**
3. **Token-lean — never at the cost of verification.** **Plain language. Short chat.** **ALL-CAPS = urgent.** **"Do not build" = study and answer only.**
4. **Mask patient numbers (last 4); never print secrets.** **Nothing live is rebuilt without his OK; the manual path stays.**
5. **Sub-agents read screens. Do not hand him diagnostics. When a screen is wrong, read its code first. Never hand him a step that is not his.**
6. **His board carries only what needs him and what he should know.**
7. **Never put a technical choice to him** — decide, say it in one line, carry on. **A screen for staff or for him: the mock first.** **His own pages: PC first, the Fold phone second (D853).**
8. **His phone gets the clinic app's messages; ntfy is the fallback (D846).**
