# START HERE — SESSION 420 — written at the S417 close (the Sanjeevni chat), 09-Nov-2026 (18:4x IST)

**Project: Sanjeevni — Pharmacy & Marg.** Open it in a fresh chat in this project, linked to manojz. **F-802 is fixed on both boxes** (kit S763_F802_AGAIN: the server 14:2x IST, the medical PC 14:26 IST — a repeat export is told as *received again* at its export moment; the salt duty reads `setting mi_again:SALT_WISE_ITEM_LIST`, D881). **Alisha's rescan list is clear** (S765: summaries never judged as bills; S766: a deleted scan's server ask withdrawn — D882). **His word at 18:33: the orthotics work in a fresh session — this one builds it FIRST** (D883).

1. **The open:** `OPEN_ROUTINE_v1` (from the clone: `deploy_kits/KB_canon_all/OPEN_ROUTINE_v1.md`).
   - In the device VM: `TMPDIR=/tmp/s419w`; flask is importable for walks via the cloud workspace (the device VM has python3.10, no flask). Run walks in the foreground. **A database copy stays in the device VM** (D656) — the 08-Nov copy was read there this session (`gunzip -c D:\Downloads\_kbtools\vps_code\<day>.finance_nightly.db.gz`).
   - **The pins:** DECLARED-PENDING of this close — `marg_door.py` fcbcfb13 · `amir_day.py` 49e1eba1 · `reports_tile.py` 4eaeadbd · `shared/scan_quality.py` 505a114f · `porders_s454.py` cd2feeb3; and S414's / S412's nine (`returns_kinds` a1b9ea77 · `darpan_app` e9e69393 · `finance_approvals.html` dcd94412 · `sanjeevni_approvals` 569c5ee4 · `shelf_figure` ae61397a · `owner_console` 27d31775 · `scan_register` 9262c5dc · `purchase_app` 8424e05b · `owner_notice` 537b7c32). The 10-Nov bundle (01:35) should CONFIRM all — read the day page; confirm or say why not.
   - **The medical PC:** the log in Drive `FromMedical\marg_watch_log.txt` (Google Drive file `1eRmOrI_tdliI4MbBZikCt8TZ2cPHWcVG`) — any `again:` line since 14:26 (*the server has it* / *EXPIRED*), no traceback.
   - **Remind him once of the packs page** (D713) **and F-1133** (D837) — one line each.
2. **S756's second day (read only):** the 10-Nov 11:30 batch — the snapshot's *Last reminder* on the October check; any dealer messaged whose summary had come is a RED.
3. **The rules:** the charter v1.1 beside the parent's `BUILD_NORM_v1.md` (D704). The close is `CLOSE_ROUTINE_v1`; this project's `close.json` is in `03_WORKING_PAPERS\S417\close_parts\` — copy it, change what changed.
4. **The papers:** the brief `S417_BUILD_BRIEF.md`; the orthotics working files `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S417\ortho\` (`ortho_ledger_v3.csv` — per orthotic item: counted 06-Sep, bought, sold, expected, Marg 08-Nov, the difference, the vouchers and hand edits, the bills); the canvas `https://claude.ai/artifact/8JhQwrXJ56WAtdCZGUUHN1` (page *Bills vs Marg* — he called it a muddle; do not build from it).

*FIRST ACT: take your session number from the System Board's `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).* **420 is RESERVED for the Sanjeevni chat at this close** (settled on the board at v1164-v1165: the parent's S418 CORRECTION 2 and this chat's acceptance; 419 and 421 are the parent's; F-1224 records this close's placements made off the board -- read those board lines at the open). The NK Pathology chat's 365 is open; the Scan App chat's 410 reserved; the parent's 418 open.

**The S763 / S765 / S766 kits are the pattern to copy now:** makers with anchored edits asserting the FROM md5 (built on the live bytes, F-472) · a walk on made-up rows and a CONTROL on the live files · a box proof on ONE copy of finance.db by both files that stops before writing on a mismatch · a rehearsal on a made-up root (dry / changed file / install / again / red) · cold reviews until SAFE, their should-fixes applied · the screens read live by a sub-agent as manoj.

---

## 0 · THE WORK — in order

**A · THE OPEN** — the board; the day's checks; the four numbers; the two reminders; S756's second day; the medical PC's `again:` lines.

**B · THE WORK**
1. **THE ORTHOTICS CLEAN-UP, ONCE (D883; F-1220, F-1221)** — papers first, no live change until he has seen them:
   - **Why:** Marg's sale report keeps 20 letters — until Amir's October renames every orthotic sale lost its size (*KNEE SUPPORT HINGED*: 8 sales since 06-Sep with no size), so no ledger by size can be rebuilt from the records; Amir's 23–25 Oct direct Marg edits are not system vouchers; 21 orthotic items differ from the record (biggest: Knee Support Hinged M and L).
   - **The count sheet:** every orthotic size Marg holds (75 names in the 08-Nov closing; the section list holds 109 incl. old names), Marg's figure today beside an empty *counted* column, grouped by type so a person counts a shelf in one pass. His word on who counts and when.
   - **Amir's one correction list** (after the count): item · Marg now · counted · the change → ONE voucher in Marg; then the four names that lose the size renamed so the size sits in the first 20 letters: BLING CONT. LS BELT XXL · CERVICAL COLLAR SOFT HOPE L · SOFT COLLAR BODY AID S · SOFT COLLAR NEOLIFE L (and the 12 with no size word looked at).
   - **The Yuvika → Marg name list:** the scan reader's 42 Yuvika wordings from 9 bills (`purchase_sarvam_check.detail` items: 14 sure, 24 to look at, 4 unmatched) completed against all 24 Yuvika bills in Marg (53 Marg names incl. old ones), one Marg name per Yuvika wording — a list for Amir and reception.
   - **Amir's reasons** for the seven 23–25 Oct medicine edits (Flemcort 6 −180 a day after +360, Nortimer +90, Gli-ME SR1 +27, Exlain A −12, Cartilox −3, Runvace TP −2, Enzomac +2) — the stock-change watch already lists them.
   - Format: the count sheet and Amir's list as a Sheets artifact (or the matching artifact type), the name list in the same; the reasons as lines on Amir's card only if he asks.
2. **Then F-1220's repair** — a bill scan never presumes the whole order arrived; the bill's own Marg lines (and its scan) decide; staff taps never judge (D883). The mock first, plain: one line per incident, never *Amir's entry pending*.
3. **The order-list kit**, on his "go", the mock first (`S402_ORDER_LIST_PLAN.md`).
4. **Small / his / staff / parked / not ours:** as `HANDOFF_RUNBOOK` v331 §2B items 4 – 7.
5. **The close** — `CLOSE_ROUTINE_v1`.

**NEVER** (whole, as the Runbook v331 §2B lists), plus: judge an arrival by a staff tap (D883); move `mi_file.received_at` (D881); let a reader's guess hide or clear work (S765).

**THE RULINGS THAT STAND:** as `START_HERE_SESSION_417` listed them, plus **D881, D882, D883**.

## 1 · THE STANDING OWNER RULINGS

1. **Publishing is HIS double-click** — `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`.
2. **Full paths ALWAYS — including URLs**, each in its own copy block. **ONE line per command.**
3. **Token-lean — never at the cost of verification.** **Plain language. Short chat. English to him.** **ALL-CAPS = urgent.** **"Only answer" / "do not build" = study and answer only.**
4. **Mask patient numbers (last 4); never print secrets.** **Nothing live is rebuilt without his OK; the manual path stays.**
5. **Sub-agents read screens. Do not hand him diagnostics. When a screen is wrong, read its code first.**
6. **Never put a technical choice to him** — decide, say it in one line. **A screen for staff or for him: the mock first — simple; he judges what he sees.** **His own pages: PC first, the Fold phone second (D853).**
