# START HERE — SESSION 391 — written at the S388 close (the Sanjeevni chat), 06-Nov-2026 (12:4x IST)

**Project: Sanjeevni — Pharmacy & Marg.** Open in a fresh chat in this project, linked to manojz.
1. Follow `OPEN_ROUTINE_v1` (from the clone: `deploy_kits/KB_canon_all/OPEN_ROUTINE_v1.md`). In the device VM, `day_open.py` needs its paths: `--tools $HOME/mnt/Downloads/_kbtools --repo $HOME/mnt/dr-manoj-git/drmanoj-clinic-automation --kb $HOME/mnt/Downloads/ClaudeCowork --ssd $HOME/mnt/ClinicBackup/DrManojClinic_Automation --roots $HOME/mnt/Downloads $HOME/mnt/dr-manoj-git $HOME/mnt/ClinicBackup` (the defaults are Windows paths). **A re-run after a publish clears the day's note — write it again.** The VM's `/sessions` disk is nearly full (F-1102): run Python with `TMPDIR=/tmp/s###w`.
2. The rulebook for every build is **the charter v1.1 — `claude/S307_BUILD_CHARTER_v1_1.md`** beside the parent's `BUILD_NORM_v1.md` (D704). The plan of what is left is the System Board's plan, section 9 (steps 0–3 done; step 4 — the switch — is the owner's word, earliest ~22-Nov). The close is `CLOSE_ROUTINE_v1` — this project's `close.json` is in `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S388\close_parts\` (copy it, change what changed).
3. The brief of this close is `S388_BUILD_BRIEF.md`; the Book is `SANJEEVNI_SYSTEM_BOOK_v1_47_S388.md` (§15AL: the wrong-dealer card, the Marg flows, the outage). **The kits' working copies: `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S388\kit711\`, `kit714\`, `flows_crop\`; the outage notes `S388_NETWORK_AND_ALERTS_NOTES.md`.**

No incident is open. **DECLARED-PENDING (eleven):** `order_track_page.py` 4e6bd715, `porders_s454.py` 8fd445b3, `order_sheet.py` 53abf461 (S711); `reports_tile.py` f44fe768, `marg_flows.py` cc68a1af, `marg_flows_pics.py` e2907c20 (S714 / S716); the parent's `finance_app.py` 15f6b32b (S714); `order_track.py` 6f4746c5 (S708); `owner_notice.py` ca5cd443, `expiry_watch.py` 1ed95b6c, `marg_hand_change.py` 3b8c2160 (S706) — until a bundle newer than 06-Nov (F-1124).

*FIRST ACT: take your session number from the System Board's `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).*
- **391 is RESERVED for the Sanjeevni chat at this close.** The Scan App chat's 363 is open; the NK Pathology chat's 365 and the parent's 390 reserved. Take what the board says and say so in your first line.
- **Kit numbers are claimed BEFORE the scratch folder is named (F-515);** D and F numbers the moment they are minted (F-920). Read every PLANNED line on the board before touching a file it names (D646). **Re-read `_numbers` just before a pinned write at a close — another chat may be closing (S388: v953 → v956).**

*Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.* **Never `git` in the device shell (F-511, F-1103, F-1116):** read `.git\refs\heads\main`, `.git\refs\remotes\origin\main`, `.git\logs\HEAD`, `.git\index` (paths) as files. **Build road: in the chat itself.** What S339–S388 learnt (keep it): the live code = the newest bundle + the pending kits' `make_*.py` in order (`D:\Downloads\_kbtools\vps_code\<date>.code_nightly.tar.gz`, the database copy beside it); **the bundle can be staged into the cloud workspace for building (code only; never a database copy, D656)** and the kit built and walked there with Flask; the walk harness needs `finance_schema.sql` and the live `mi_file` columns; **a live-shape read draws the pages READ-ONLY on a copy of the nightly database in the device VM**; a file copied to the PC is read back by md5 (F-1099); run `deploy_kits\NO_PHONE_NUMBERS.py --files-from <list> <repo>` before naming the publish (F-1098) — **binary carried as hex, not base64** (digit runs); **run the `.gitignore` test on every kit file (F-1130)**; a walk's controls stand on its OWN rows (F-998); a proof goes RED when the change did nothing (S704); every kit read cold by an independent agent until SAFE; **the screen read live after every install (F-1119)**; **an installer's journal check counts only the NEW master's lines (F-1135)**; the built-in browser on manojz is signed in as `manoj` (read `/finance/api/whoami` first).

---

## 0 · THE WORK — in order

**A · THE OPEN (OPEN_ROUTINE_v1)** — the board (messages `read:false` to `sanjeevni`, notes); the day's checks; the four numbers. **The newest bundle:** the eleven pins CONFIRMED (or named); in its database copy `owner_notice` rows with key `hand:` (none twice; none for the history), `marg_hand_change`, `hand.since`; `s711_dealer_change` and the `s708_*` tables (read, never changed); F-1114 (THIO Q AP); Amir's Batch Stock (none since 31-Oct). Is the medical PC's heartbeat fresh?

**B · THE WORK**

1. **THE BUILD — F-1134, messages that reach him (his word 12:2x 6-Nov: "build in a fresh session").** This project's `reports_watch.py` (S500) and `owner_notice.py` (S702/S706):
   - every report alarm (late / wrong twice / held) goes by `owner_notice`'s road — Web Push to `owner_notice.to` devices first, the ntfy topic only when none;
   - **"Medical PC offline — reports cannot leave it"** after ~20 min with no heartbeat / no pull inside the working window (09:00–20:00; Sunday 09:00–14:00), once per silence;
   - **"Medical PC back — N reports delivered"** when it is heard again;
   - the installer's journal check counts only the new master's lines (F-1135).
   Read the health page's own judgement in `finance_app.py` (`add("watcher" …)`, `add("medical" …)`) — read, never copied; the push road in `owner_notice.py`. Show him the message text before the install.
2. **F-1110's medical-PC half** (a refused file says its plain cause) — his yes first.
3. **F-1104 — "count them"** waits on him; **Amir's next visit** (read only); **the switch** on his word at D673's bar.
4. **PARKED by his word:** F-802's permanent fix; **F-1133 — a second network path for the medical PC only at a second LAN failure, and then automatic (D837).** **NOT THIS PROJECT'S:** F-1048, D803, F-1102, F-1122 (DUTY_MAP — the parent, with us), F-1124 (manojz's nightly — the parent). **His with Ram Singh:** F-1115 (with the flow links).
5. **The close** — `CLOSE_ROUTINE_v1`.

**NEVER RUN:** `deploy_kits\S488_DATES_AND_WAITS\deliver_S488.ps1`. **NEVER INSTALL:** `deploy_kits\S638_EXPIRY_WATCH\`, `S672_NONCASH_AT_INGEST\`, `S673_NONCASH_AT_INGEST_R2\` (frozen). **NEVER ADD TO:** Amir's *Aaj ka kaam* list (D690). **THE EXPIRY PAGE changes only on his word** (D780, D793; D828 opened it for the top section). **NEVER CHANGE THE MEANING of a name the parent's console reads** (`supplier_msg.s454_card_facts`, `porders.shortage_summary`, `expiry_watch.newest / now_view / ym_add`, `reports_tile.status`) without a word to the parent. **THE FLOW PAGES ARE PUBLIC — FIXED TEXT AND PICTURES ONLY: NO DATABASE READ, NO NAME, NO FIGURE (S714); A NEW PICTURE IS CHECKED FOR A 10-DIGIT NUMBER, MARG'S TITLE LINE AND A SUPPLIER NAME (F-185).** **NEVER BOOK A VOUCHER IN THE SPINE'S `sp_move`.** **NEVER SEND A SUPPLIER WHATSAPP OR TAP A STAFF BUTTON FOR HIM** without his explicit word — that includes S708's and S711's *This one is right*, *This is its bill*, *X is right (as saved)*, *Undo*.

**THE ORDER LIST TIES NO SCAN BY ITSELF — A PERSON PICKS (D831).** **A MARG STOCK CHANGE WITH NO BILL, SALE OR VOUCHER IS TOLD HIM THE NEXT MORNING AND KEPT ON TOP OF THE EXPIRY WATCH (D828).** **THE OWNER IS TOLD WHEN THE MARG WORK IS DONE — EVERY DAY, SUNDAYS TOO (D825); A NEW MESSAGE GOES THROUGH `owner_notice.py`, ONCE, ITS TITLE PLAIN.** **AMIR NEVER OPENS OR EDITS A SALE BILL (D815).** **A STAFF SCREEN CARRIES ONLY "DO THIS" LINES (D708) — AND A LINE ON IT RESTS ON A FACT NOBODY CAN TAP WRONGLY (D712).** **A SALE IS CASH OR UPI ONLY (D802).** **NO FIGURE TO TYPE, EVER (charter rule 8).** **A VOUCHER NEVER TAKES MARG BELOW ZERO OR PAST THE SHELF FIGURE (D715).** **A LINE LEAVES THE ORDER LIST ONLY WHEN MARG CLOSES IT (D716); A MISSING MEDICINE GOES ON THE NEXT ORDER BY ITSELF (D757); A SUBSTITUTE NEVER CLOSES A LINE (D760).** **ONLY THE OWNER CHANGES A DEALER'S NUMBER (D731).** **THE BUYING MODEL IS SCORED IN SHADOW; THE SWITCH IS HIS WORD (D678, D785).** **BATCH STOCK UNITS ARE MARG'S LOOS FIGURE (D821).** **THE ONE MONTHLY EXPIRY INPUT IS THE BATCH STOCK (WHOLE STORE) (D822).** **THE STOCK VALUATION IS WHOLE STORES, AS ON THE MONTH'S LAST DAY, ON PUR. RATE (D827).** **EVERY MARG REPORT HAS ONE PHONE-FIRST FLOW, SHAREABLE ON ITS OWN (D827, D830) — LIVE AT `/finance/flows`.** **NO SECOND NETWORK FOR THE MEDICAL PC UNTIL A SECOND LAN FAILURE; THEN AUTOMATIC (D837).**

**CLOSED BY HIS WORD — DO NOT RAISE AGAIN:** as `START_HERE_SESSION_388` listed (D829, Vinay, AMIRR, Kedar's Flemcort, scan B-0167, and those before). **B-0239 is his own tap** (he said so, 06-Nov).

## 1 · THE STANDING OWNER RULINGS

1. **Publishing is HIS double-click** — `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`.
2. **Full paths ALWAYS — including URLs**, each in its own copy block. **ONE line per command.**
3. **Token-lean — never at the cost of verification.** **Plain language. Short chat.** **ALL-CAPS = urgent.**
4. **Mask patient numbers (last 4); never print secrets.** **Nothing live rebuilt without his OK; the manual path stays** (S708's old pages at `?old=1`).
5. **Sub-agents read screens. Do not hand him diagnostics. When a screen is wrong, read its code first. Never a step that is not his.**
6. **His board carries only what needs him and what he should know — every close answers what he typed there; the plan's section 9 is refreshed at every close; all pending kept updated on the board each session (his note 08:48 6-Nov).**
7. **His own items are deferred** — name only what has become urgent, and say why. **His approvals are few and arrive together.**
8. **Never put a technical choice to him** — decide, say it in one line, carry on. **A screen for staff: the mock first.** **"Build in next session" — the next chat's first build.**
9. **His phone gets the clinic app's messages; ntfy is the fallback — and every alarm must go that way (F-1134).**
