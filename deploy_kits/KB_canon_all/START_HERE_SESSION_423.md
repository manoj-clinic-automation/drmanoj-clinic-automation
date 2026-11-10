# START HERE — SESSION 423 — written at the S420 close (the Sanjeevni chat), 10-Nov-2026 (10:4x IST)

**Project: Sanjeevni — Pharmacy & Marg.** Open it in a fresh chat in this project, linked to manojz. **The section count is live** (kit S768, 07:19 IST): Stock milaan → *Orthotics ginti* → `/finance/stockmatch/count`. **The Stock check hub lists every count** (kit S769, 10:3x IST): `/finance/stock/page/hub` — templates, counts in progress, *Who may count*, 06-Sep folded. **His word at 09:32 – 09:34: the *Orthotic bills this month* card is next — differing lines kept highlighted and their bills flagged** (D886).

1. **The open:** `OPEN_ROUTINE_v1` (from the clone: `deploy_kits/KB_canon_all/OPEN_ROUTINE_v1.md`).
   - In the device VM: `/tmp/s420w` held the 10-Nov database copy and code bundle; make your own (`gunzip -c D:\Downloads\_kbtools\vps_code\<day>.finance_nightly.db.gz`, `tar xzf …code_nightly.tar.gz`). **A database copy stays in the device VM** (D656). The device VM has no flask: stub it for a read (as `proof_s768.py` does) or walk in the cloud workspace on code only.
   - **The pins:** DECLARED-PENDING of this close — `stockmatch.py` 57d04d3e · `stockmatch.html` 0ec2e32d · `section_count.py` d69e1681 · `section_count.html` 1580a6d3 · `stock_hub.html` 90da7707 · the parent's `/root/portal/tile_grants.json` 66de5e20 (v45). The 11-Nov bundle (01:35) should CONFIRM all — read the day page; confirm or say why not.
   - **The medical PC:** Drive `FromMedical\marg_watch_log.txt` (file `1eRmOrI_tdliI4MbBZikCt8TZ2cPHWcVG`) — no traceback.
   - **Remind him once of the packs page** (D713) **and F-1133** (D837) — one line each.
2. **S756 (read only):** the 10-Nov 11:30 batch was due after this close — read the snapshot's *Last reminder* on the October check; a dealer messaged whose summary had come is a RED.
3. **The rules:** the charter v1.1 beside the parent's `BUILD_NORM_v1.md` (D704). The close is `CLOSE_ROUTINE_v1`; this project's `close.json` is in `03_WORKING_PAPERS\S420\close_parts\` — copy it, change what changed.
4. **The papers:** the brief `S420_BUILD_BRIEF.md`; the orthotics paper (Docs) `https://claude.ai/artifact/73xoqtxatWrwiFXqjVKuMg`; the mocks (canvas) `https://claude.ai/artifact/Nq1CFQmJ4G3ckeVqEg8ppJ`; the kits `deploy_kits\S768_SECTION_COUNT\`, `deploy_kits\S769_STOCK_HUB_COUNTS\` (their walks, makers, the preview harness `serve_s769.py` in `03_WORKING_PAPERS\S420\kit769\` is not shipped).

*FIRST ACT: take your session number from the System Board's `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).* **423 is RESERVED for the Sanjeevni chat at this close** (v1177). The NK Pathology chat's 365 is open; the Scan App chat's 410 reserved; the parent's 422 reserved.

**The S768 / S769 kits are the pattern to copy now:** a maker asserting every FROM md5 (built on the live bytes, F-472) · a walk on made-up rows and a CONTROL on the live files · a proof on ONE copy of finance.db · a rehearsal on a made-up root (dry / changed file / install / again / red) · screen reviews on a local preview and cold reviews until SAFE · the screens read live by a sub-agent as manoj after install (read-only — never Start, Cancel, a switch or Send) · **the kit folder listed against `.gitignore` before the publish is named (F-1230)**.

---

## 0 · THE WORK — in order

**A · THE OPEN** — the board; the day's checks; the four numbers; the two reminders; S756; the medical PC.

**B · THE WORK**
1. **THE ORTHOTIC BILLS THIS MONTH CARD (D886)** — on the Stock check hub; **the mock first**, his eyes on it:
   - **One line per bill** of an orthotics dealer this month (Yuvika first; the dealers are those whose Marg purchase lines carry a name of the section — `section_count.section_dealers`): *agrees* / *N lines differ*; a flagged bill stays flagged until every differing line is settled.
   - **Tap a bill:** the scan's lines (`purchase_sarvam_check.detail` items) beside the bill's own Marg lines (`purchase_line`, one export per bill — `section_count.purchases`), matched by the name map; a differing line (another size, another brand, another quantity, missing on one side) stays **highlighted** until Marg is fixed (the next export shows it) or the doctor clears it.
   - **The name map:** `s454_item_name` corrected (*TY ELASTIC WRIST SPLINT RT-(L)* is mapped to a LEFT name — wrong) and kept; a name follows Amir's renames (`marg_item_rename`); the reader's misreads (*Hinged-V*, *Arm Sling-St*, *G-MN*, *Long St*, *Tytor*) settled by the bill's own Marg lines.
   - **Feeds the count:** a differing line stars its item at the next section count (`record_flags` / `owner_flags` path — a new source, frozen at the start).
   - **New orthotics:** a suggested Marg name with the size inside 20 letters, checked against every 20-letter cut (`section_count.rename_for`).
   - **The 7 lines of the S420 paper to check:** bill 585 (Neo-XL entered as M), 634 (Unison immobiliser M entered as Tynor), 571 (Right M entered as Left M), 672 (Tynor ankle L entered as Bamboo), YS/0706 07-Oct (three lines; its Marg item lines never reached the server — Amir's October item-wise re-export brings them).
2. **The first orthotics count** — when he names who and when: if staff other than Darpan count, he switches them on in *Who may count*; read the correction after the count day's closing; his figures for by-hand lines; *Send to Amir's card*; then the 4 renames; then confirm Marg agrees at the next closing.
3. **F-1232** — read `_s524_hub_proof` and the stage C state on the box (the 06-Sep proof waiting since 15-Oct); ZIBON EXTRA +21 needs his word; the three orthotic −1 lines are covered by the count.
4. **Then F-1220's repair** — a bill scan never presumes the whole order arrived (D883); the mock first.
5. **The order-list kit**, on his "go", the mock first (`S402_ORDER_LIST_PLAN.md`).
6. **Small / his / staff / parked / not ours:** as `HANDOFF_RUNBOOK` v334 §2B items 6 – 9.
7. **The close** — `CLOSE_ROUTINE_v1`.

**NEVER** (whole, as the Runbook v334 §2B lists), plus: write to the 06-Sep `stock_count`; send a correction the arithmetic could not settle; count a box whose bill is not in Marg (D885); ship a `.json` in a kit (F-1230).

**THE RULINGS THAT STAND:** as `START_HERE_SESSION_420` listed them, plus **D885, D886**.

## 1 · THE STANDING OWNER RULINGS

1. **Publishing is HIS double-click** — `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`.
2. **Full paths ALWAYS — including URLs**, each in its own copy block. **ONE line per command.**
3. **Token-lean — never at the cost of verification.** **Plain language. Short chat. English to him.** **ALL-CAPS = urgent.** **"Only answer" / "do not build" = study and answer only.**
4. **Mask patient numbers (last 4); never print secrets.** **Nothing live is rebuilt without his OK; the manual path stays.**
5. **Sub-agents read screens. Do not hand him diagnostics. When a screen is wrong, read its code first.**
6. **Never put a technical choice to him** — decide, say it in one line. **A screen for staff or for him: the mock first — simple; he judges what he sees.** **His own pages: PC first, the Fold phone second (D853).**
