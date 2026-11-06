# START HERE — SESSION 396 — written at the S393 close (the Sanjeevni chat), 06-Nov-2026 (18:1x IST)

**Project: Sanjeevni — Pharmacy & Marg.** Open in a fresh chat in this project, linked to manojz.
1. Follow `OPEN_ROUTINE_v1` (from the clone: `deploy_kits/KB_canon_all/OPEN_ROUTINE_v1.md`). In the device VM, `day_open.py` needs its paths: `--tools $HOME/mnt/Downloads/_kbtools --repo $HOME/mnt/dr-manoj-git/drmanoj-clinic-automation --kb $HOME/mnt/Downloads/ClaudeCowork --ssd $HOME/mnt/ClinicBackup/DrManojClinic_Automation --roots $HOME/mnt/Downloads $HOME/mnt/dr-manoj-git $HOME/mnt/ClinicBackup` (`--read` with the same `--tools`). **A re-run after a publish clears the day's note — write it again.** Run Python with `TMPDIR=/tmp/s396w`. **The device VM's home disk may be full (other sessions) — a database copy goes to `/tmp/s396w/`, never the cloud workspace (D656).**
2. The rulebook for every build is **the charter v1.1 — `claude/S307_BUILD_CHARTER_v1_1.md`** beside the parent's `BUILD_NORM_v1.md` (D704). The plan of record: **`S391_PURCHASE_RECONCILE_PLAN.md`** (D839, D840) with this close's D846 – D849. The close is `CLOSE_ROUTINE_v1` — this project's `close.json` is in `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S393\close_parts\` (copy it, change what changed).
3. The brief of this close is `S393_BUILD_BRIEF.md`; the Book is `SANJEEVNI_SYSTEM_BOOK_v1_48_S393.md` (§15AM: S722, S726).

No incident is open. **DECLARED-PENDING (sixteen) until a bundle newer than 06-Nov (F-1124):** S726 `scan_register.py` 57ca3088, `purchase_app.py` 4b6ea083, `porders.py` eda0a4c6; S722 `owner_notice.py` 7adbfc24, `reports_watch.py` 3b6fb83d, `marg_door.py` 565ad9c8; S711 `order_track_page.py` 4e6bd715, `porders_s454.py` 8fd445b3, `order_sheet.py` 53abf461; S714 / S716 `reports_tile.py` f44fe768, `marg_flows.py` cc68a1af, `marg_flows_pics.py` e2907c20; the parent's `finance_app.py` 15f6b32b; S708 `order_track.py` 6f4746c5; S706 `expiry_watch.py` 1ed95b6c, `marg_hand_change.py` 3b8c2160. **Medical PC (installed, confirmed by its heartbeat 15:30):** `marg_push.py` 3f5ed144, `marg_watch.py` df7736e9.

*FIRST ACT: take your session number from the System Board's `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).*
- **396 is RESERVED for the Sanjeevni chat at this close.** The parent's 394 is open; the NK Pathology chat's 365 and the Scan App chat's 395 reserved. Take what the board says and say so in your first line.
- **Kit numbers are claimed BEFORE the scratch folder is named (F-515);** the parent took S727 – S734 today — never name a future kit's number in a README before claiming it. **Re-read `_numbers` just before a pinned write.**

*Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`* — **and, for any medical-PC delivery, `H:\My Drive\Clinic Data Archive\ToMedical` (Google Drive is H: on manojz; added by the owner 15:13 IST 6-Nov; the device shell cannot mount it — use device_list_dir / stage / commit).** **Never `git` in the device shell (F-511, F-1152):** read `.git\refs\heads\main`, `.git\refs\remotes\origin\main`, `.git\logs\HEAD` as files. **Placing a kit in the repo:** a tar committed to `03_WORKING_PAPERS\S###\` then extracted with `tar --overwrite` in the device shell (a commit can silently not overwrite — read back by md5, F-1099; `rm` is refused). What S339–S393 learnt (keep it): the live code = the newest bundle + the pending kits' `make_*.py` in order; the bundle can be staged into the cloud workspace for building (code only); **a kit that re-pairs or unpairs live records is installed only after its DRY run on the box has been read (F-1153)**; `deploy_kits\NO_PHONE_NUMBERS.py --files-from <list> <repo>` before naming the publish (an md5 can trip it — reword a comment); the `.gitignore` test on every kit file; a walk's controls stand on its OWN rows; every kit read cold by an independent agent until SAFE; the screen read live after every install (a sub-agent in the built-in browser, signed in as `manoj`; read `/finance/api/whoami` first). The scan app's bill page `/scanapp/bills/<n>` carries the scan's vendor, number, date and total. The pharmacy scans (`assets.db`) are the Scan App's: READ ONLY.

---

## 0 · THE WORK — in order

**A · THE OPEN (OPEN_ROUTINE_v1)** — the board (messages `read:false` to `sanjeevni`, notes); the day's checks; the four numbers. **The newest bundle:** the sixteen pins CONFIRMED (or named); S722's beats overnight (`owner_notice` rows `medical_off` / `medical_back` — any false one?); the S726 pass at 23:59 (any `auto_link_undone` beyond today's five? any `s726_setup_error`?); the step view read live. Has Amir visited since 4-Nov (a newer `PURCHASE_BILLWISE` in `D:\Downloads\margsync\MargArchive\PURCHASE_BILLWISE\2026-11\`)?

**B · THE WORK**

1. **KIT 1, PART 2 — reception's list** (D847, on the approved mock `https://claude.ai/artifact/Mwe48BGnJcu6vb5ZPMH4tV`; his "go" was given — build it):
   - *Dobara scan karo* raised by the server itself: the scan-quality verdicts (`rescan_list`'s `redo`) and S726's *Paired, nothing read* become `scan_rescan_ask` rows with `asked_by='server'` and the reason in words that name what could not be read; the try counted by the rescan chain (`rescan_of`); after **two** tries → *You & Shavez* (his step view row 5, and Shavez's page), off reception's list. Shavez's *Scans to redo* stays for his own sends.
   - *Scan karo* (a Marg bill with no scan, days waited, *Bill nahi mil raha*); the one-tap question *Kya yeh wahi bill hai?* naming the field and what the scan read against Marg (D847).
   - The step view: row 3 *Differences* (F-1154); *Second look* buttons (the paper's figure stands → Amir corrects / the scan misread → settled), owner-only.
   - Files: `porders_s454.py` (rebuild the live bytes: bundle + `make_s708.py` + `make_s711.py`, check 8fd445b3), `scan_register.py` / `purchase_app.py` (S726's TO bytes — rebuild from the bundle with `make_s726.py`). **A staff screen: the mock is approved — build to it.**
2. **Then, each on his "go":** kit 2 Amir's correction list (amount and missing-line items; proof from his exports); kit 3 returns (Janta 21965 first); kit 4 supplier summaries, the issues list, the month lock on Marg = papers = summaries, the statements built by the server (D849), the NEFT on the suppliers' figures.
3. **F-1110's medical-PC half** — his yes first. **F-1104 "count them"** — his. **F-1145** (Kedar Rs 110 twice) — with kit 2. **The switch** on his word at D673's bar.
4. **PARKED by his word:** F-802's permanent fix; F-1133 (D837). **NOT THIS PROJECT'S:** F-1048, D803, F-1102, F-1122, F-1124 (the parent); `packs.py`'s September "2 baaki" (told). **His with Ram Singh:** F-1115.
5. **The close** — `CLOSE_ROUTINE_v1`.

**NEVER RUN:** `deploy_kits\S488_DATES_AND_WAITS\deliver_S488.ps1`. **NEVER INSTALL:** `deploy_kits\S638_EXPIRY_WATCH\`, `S672_NONCASH_AT_INGEST\`, `S673_NONCASH_AT_INGEST_R2\` (frozen). **NEVER ADD TO:** Amir's *Aaj ka kaam* list (D690). **THE EXPIRY PAGE changes only on his word** (D780, D793; D828). **NEVER CHANGE THE MEANING of a name the parent's console reads** (`supplier_msg.s454_card_facts`, `porders.shortage_summary`, `expiry_watch.newest / now_view / ym_add`, `reports_tile.status`) without a word to the parent. **THE FLOW PAGES ARE PUBLIC — FIXED TEXT AND PICTURES ONLY.** **NEVER BOOK A VOUCHER IN THE SPINE'S `sp_move`.** **NEVER SEND A SUPPLIER WHATSAPP OR TAP A STAFF BUTTON FOR HIM** without his explicit word.

**SEPTEMBER 2026 IS A PROOF ONLY — IT RAISES NOTHING TO ANYONE (D848).** **A BAD SCAN GOES STRAIGHT TO RECEPTION; TWO TRIES, THEN HIM AND SHAVEZ (D847).** **EVERY ALARM REACHES HIM BY THE CLINIC APP (D846).** **WE PAY THE SUPPLIER'S FIGURE; ONE BULK NEFT A MONTH, ONLY AFTER EVERY SUPPLIER'S ISSUE IS RESOLVED (D839).** **EVERY RUPEE BETWEEN A SCAN AND MARG IS CORRECTED IN MARG THROUGH AMIR'S WORKFLOW; A RETURN IS THE FULL BILL PLUS A PURCHASE RETURN (D839).** **HE SEES EVERY STEP UNTIL NOVEMBER IS LOCKED AND PAID (D840).** **THE ORDER LIST TIES NO SCAN BY ITSELF (D831).** **A MARG STOCK CHANGE WITH NO BILL, SALE OR VOUCHER IS TOLD HIM THE NEXT MORNING (D828).** **AMIR NEVER OPENS OR EDITS A SALE BILL (D815).** **A STAFF SCREEN CARRIES ONLY "DO THIS" LINES (D708), ON A FACT NOBODY CAN TAP WRONGLY (D712).** **NO FIGURE TO TYPE, EVER (charter rule 8).** **A SALE IS CASH OR UPI ONLY (D802).** **ONLY THE OWNER CHANGES A DEALER'S NUMBER (D731).** **THE BUYING MODEL IS SCORED IN SHADOW; THE SWITCH IS HIS WORD (D678, D785).** **NO SECOND NETWORK FOR THE MEDICAL PC UNTIL A SECOND LAN FAILURE (D837).**

**CLOSED BY HIS WORD — DO NOT RAISE AGAIN:** as `START_HERE_SESSION_391` listed. **B-0239 is his own tap.**

## 1 · THE STANDING OWNER RULINGS

1. **Publishing is HIS double-click** — `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`.
2. **Full paths ALWAYS — including URLs**, each in its own copy block. **ONE line per command.**
3. **Token-lean — never at the cost of verification.** **Plain language. Short chat.** **ALL-CAPS = urgent.**
4. **Mask patient numbers (last 4); never print secrets.** **Nothing live rebuilt without his OK; the manual path stays.**
5. **Sub-agents read screens. Do not hand him diagnostics. When a screen is wrong, read its code first. Never a step that is not his.**
6. **His board carries only what needs him and what he should know.**
7. **Never put a technical choice to him** — decide, say it in one line, carry on. **A screen for staff: the mock first.** **"Don't build now" means plan only.**
8. **His phone gets the clinic app's messages; ntfy is the fallback (D846).**
