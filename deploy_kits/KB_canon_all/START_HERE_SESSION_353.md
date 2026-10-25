# START HERE — SESSION 353 — written at the S350 close (the Sanjeevni chat), 25-Oct-2026

**Project: Sanjeevni — Pharmacy & Marg.** Open in a fresh chat in this project, on manojz.
1. Run `SANJEEVNI_START_HERE_PROMPT_v1_1`'s Phase 0 (the project's custom instructions) first, then this file.
2. The rulebook for every build is **the charter v1.1 — `claude/S307_BUILD_CHARTER_v1_1.md`** (builder's part `claude_code_briefs\SANJEEVNI_BUILD_CHARTER.md`, D707), beside the parent's `BUILD_NORM_v1.md` (D704). **The plan of work is `claude/S327_SANJEEVNI_RESTRUCTURING_PLAN.md`.**
3. The brief of this close is `S350_BUILD_BRIEF.md`; the Book is `SANJEEVNI_SYSTEM_BOOK_v1_35_S350.md` (§15Z is S350); the plan the owner said yes to is `claude/S350_KIT_II_PLAN.md`; this session's papers in `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S350\` (the replay scripts, the walk's output, `REPORT_S644.md`; the PHI tar of MargArchive in `_to_delete\` for the owner's delete); the kit `deploy_kits\S644_BUYING_MODEL\` (frozen).

No incident is open. **S644 is live** (08:22 IST 25-Oct, `order.model = levels`): the system's list is made the new way from the 09:00 prepare of Monday 26-Oct and scored nightly; **nothing changed for the staff** (`order.source = marg_sheet`). The parent's 349 and the NK Pathology chat's 351 are **open**; the Scan App chat's 352 is **open** (08:37 IST).

*FIRST ACT: take your session number from the System Board's `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).*
- **353 is RESERVED for the Sanjeevni chat at this close.** Take it if the board still shows it reserved, otherwise what the board says, and say so in your first line.
- Kit numbers are claimed before the scratch folder is named (F-515). D and F numbers are taken the moment they are minted (F-920, F-934).
- Read every PLANNED line on the board before touching a file it names (D646).

*Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.* Never `git` there (F-511). The routine is `END_OF_SESSION_PROMPT_v18.md`. **Build road: in the chat itself** (the owner's word). **What S339, S348 and S350 learnt about building offline (keep it):** the live code = the newest bundle + the pending kits' `make_*.py` in order; the spine = `spine_evidence.py --source <MargArchive copy> --out <readings>` then `spine_build.py --readings … --out … --finance-db <copy>` (needs `xlrd`), from a tar of `D:\Downloads\margsync\MargArchive` staged into the workspace (it carries patients — it goes to `_to_delete` at the close); the engine runs offline with `FINANCE_DB` / `SPINE_DB` / `ORDER_TODAY` / `ORDER_CLOCK` and `flask` installed; a walk's "old = new" test runs the old and new bytes in two app folders on the same database copy (`walk_run.py`). **A walk's controls stand on its OWN rows, found by key (F-998) — a real row in the live data broke one of S644's first checks.** **A walk check on a live page asserts what the page always shows (F-1020).** **Read a captured Marg text's title before printing any row of it (F-1010).** The Drive `ToMedical\_kit` folder is `H:\My Drive\Clinic Data Archive\ToMedical\_kit` on manojz — ask for it once with the folder-access tool.

---

## 0 · THE WORK — in order

**A · THE OPEN'S FIRST WORK (v18)**

1. **Read the System Board** — every message with `read:false`, every v2-page line with a note, and `board/_page`. Say in one line how many are waiting for this project.
2. **Verify the S350 close's publish landed:** `.git/logs/HEAD` = `refs/remotes/origin/main` (read, never `git`), a commit later than `c79ff2e3` (08:26:20 IST 25-Oct); this close's canon at its hashes (Register v5.188, Archive v1.185, Fault v2.172, Runbook v268, this file, `S350_BUILD_BRIEF.md`, `S350_CLOSE_REPORT.md`, `live_pins_S350close.txt`, `SANJEEVNI_SYSTEM_BOOK_v1_35_S350.md`, `S350_KIT_II_PLAN.md`, the manifest, `OWNER_TODO_LIVE.md`, `MD5SUMS_ALL.txt`); `md5sum -c MD5SUMS_ALL.txt` from inside `KB_canon_all`, with the count. If not landed, name `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat` and read canon from the PC's clone.
3. **The three nightly reports:** exists · clock time · verdict. F-384 (more than one CURRENT `START_HERE_SESSION` row while four projects are open) is expected.
4. **The pin pass on the newest bundle** (`D:\Downloads\_kbtools\vps_code\code_nightly.tar.gz`, self-checking) with `live_pins_S350close.txt`. **This project's DECLARED-PENDING at this close: 6** — the six S644 files; the 26-Oct bundle (01:35 IST) should confirm every one. State the three counts: match · declared-pending · unexplained.
5. **The model's first mornings:** the 09:00 prepare of Monday 26-Oct on `levels` — in the newest database copy `order_proposal` of that day (kind, status, `lines[].model`, `lot_based`), `order_notice` slots `made_through` / `relist` / `stale`; the owner's fold read as him (`https://followup.dr-manoj.in/finance/approvals` → *Buying rules for medicines*: *the last list stood on …*, each supplier's rhythm); the proposals as the old page shows them (`https://followup.dr-manoj.in/finance/porders?old=1`). The first `levels` week is scored on the night of **1-Nov**; `order_score_latest.json` (on the box, `/root/finance/spine/orders/`, not in the bundle) carries `by_model` once a week holds two models.
6. **F-1016 — the medical agent in "user":** the booked Monday 26-Oct 10:30 IST read — `D:\Downloads\margsync\medical_SendToClinic\agent_guard.log` (a `[user]` guard running the agent once SET signs out), the morning pair CAPTURED and TAKEN. If it holds, F-1016 closes with no task; if not, its permanent half is the next small kit.
7. **Amir's work:** the four expired batches (Cartilox sachet, Exlain A, Runvace TP, Vinbactum DS) drop to zero in the daily closing the morning after his write-off vouchers — read the newest closing in the database copy after his next visit; the 30 batch corrections show only in a Batch Stock export. The two September payment messages (A.A. Pharmaceuticals, Deepam Pharma) — `supplier_msg` ids 52 and 54, still *queued* at this close.
8. **The spine's own status line** — *stock = Marg at <day> EXCEPT N item(s)* (191 at the 24-Oct 23:50 build): read `spine_compare_latest.txt` in the bundle and say whether the gap is the spine's carry or Marg's exports; it decides how far the model's quantities can be trusted before the score speaks.
9. **The one name list and the carries** — `med_name` by kind and state (an `ask` row is the owner's question); C2CALZ, FLACORT 6, XGESIC LA, LINVIZ 600.
10. **The SSD mirror · the sweep · the tranche and the measured `knowledge_size` (1,534,338 of 2,000,000 at this open) · the cold kit when due · the four numbers · what no store holds** (known: `spine.db`, `order_score_latest.json`, the orders folder).

**B · THE WORK**

1. **The shadow weeks of Kit II** — read, not built: the model's list against Darpan's sheet and against what was bought, week by week; the fifteen largest differences each Monday; **D673's bar** (three weeks at 85 % / 80 % / no more stock-outs than Darpan's sheet) decides when the switch (K4, `order.source = system`) is brought to the owner — never before, never by itself. A fault in the model is its own kit on S644's pins.
2. **F-987**; the purchase page's `staff_send`; `order.lead_days`; the S335 small list; **F-1023** (`section_map.is_orthotic` and "DYNA" — its own kit with its own walk, low).
3. **Darpan's tab header line** (B.2a: *बिक्री dd-mm तक · गिनती/क्लोज़िंग dd-mm*) — with the kit that moves `order.source` off `marg_sheet`, after its mock and his yes; not before.
4. **PARKED by his word — do not start unasked:** F-802's permanent fix.
5. **The close** — `END_OF_SESSION_PROMPT_v18.md`.

**NEVER RUN:** `deploy_kits\S488_DATES_AND_WAITS\deliver_S488.ps1`. **NEVER INSTALL:** `deploy_kits\S638_EXPIRY_WATCH\` (frozen; S642 is its live successor). **NEVER ADD TO:** Amir's *Aaj ka kaam* list (D690). **NEVER WRITE `order.source` FROM A KIT** — the switch is the owner's word on the bar (D673, D785).

**A STAFF SCREEN CARRIES ONLY "DO THIS" LINES (D708) — AND A LINE ON IT RESTS ON A FACT NOBODY CAN TAP WRONGLY (D712) — THE ONE RULED EXCEPTION: RECEPTION'S YUVIKA CARD WAITS ON DARPAN'S हाँ (D749).** **NO FIGURE TO TYPE, EVER (charter rule 8).** **THE STOCK PROOF'S VERDICT IS THE OWNER'S LINE ONLY.** **A VOUCHER NEVER TAKES MARG BELOW ZERO OR PAST THE SHELF FIGURE; A SETTLED ITEM IS NEVER RAISED AGAIN (D715).** **A LINE LEAVES THE ORDER LIST ONLY WHEN MARG CLOSES IT (D716) — AND A MEDICINE THAT DID NOT COME GOES ON THE DEALER'S NEXT ORDER BY ITSELF (D757) — A SUBSTITUTE NEVER CLOSES A LINE BY ITSELF (D760).** **A RESCAN KEEPS ITS OWN NEW NUMBER (D759).** **ONLY THE OWNER CHANGES A DEALER'S NUMBER; ONE RECORD PER DEALER (D731).** **A CLOSING TAKEN BEFORE THE DAY'S FIRST SALE IS THE START OF THAT DAY, ONCE VERIFIED ITEM BY ITEM (D740).** **CLAUDE READS THE PHARMACY BILLS; SARVAM IS OFF BY HIS SETTING (D747).** **DARPAN'S TAB CARRIES THE PURCHASE CUT-OFF LINE, NO STOCK-DAY LINE (D746).** **THE PAY PAGE ASKS FOR THE MONTH'S THREE REPORTS AS TEXT AND CONFIRMS EACH; THE LOCK WAITS FOR THEM AND AN AGREEING CROSS-CHECK (D748).** **ONE WHATSAPP PER ORDER (S605).** **ONE ORDER LIST FOR FOUR PEOPLE (D757).** **EVERY PHARMACY SCAN UPRIGHT; THE OWNER AND SHAVEZ SEND A SCAN BACK, RECEPTION RESCANS (D758).** **AMIR'S MONTH PACK STAYS UNTIL THE NEXT MONTH'S IS READY (S626).** **A MARG PACK CHANGE IS A NEW ITEM; THE OLD SOLD FIRST, THEN ZZ (D763).** **THE BATCH STOCK EXPORT IS NEVER THE CLOSING STOCK; THE EXPIRY WATCH IS READ-ONLY AND WRITES NO STOCK FIGURE (D771, D780) — ORTHOTICS APART IN THE DUMP (D777).** **THE MORNING REPORTS: SHAVEZ, AND SHIVANI WHEN HE IS AWAY; THE PAGE COUNTS THE DAY, NOT THE PERSON (D778).** **THE BUYING MODEL IS SCORED IN SHADOW; THE SWITCH OFF DARPAN'S SHEET IS THE OWNER'S WORD ON D673'S BAR (D678, D785).**

**CLOSED BY HIS WORD — DO NOT RAISE AGAIN:** the pack-change build (F-1000, "no", 04:07 23-Oct); the rescan's number (D759); the orthotic names as Amir typed them (D709); the learnt names (D685); Kedar's July balance; the four appliances' category; the staff's *Aaj ka kaam* lists — the parent's; the bill line's design (D712); NORTIMER TAB in the 6-Sep count (D715 b); the GST composition flow — the parent's; older purchase bills (Apr–Aug) for the name list (D762); a reader for the bank's alert e-mails (D779, "No"); the expiry watch's screens (D780, "yes" — change only at his word); the shape of Kit II (D785 — "what you consider to be best"; the model's rules and defaults are the replay's, not a question for him).

## 1 · THE STANDING OWNER RULINGS (END_OF_SESSION_PROMPT_v18)

1. **Publishing is HIS double-click.** Name one file, full path: `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`.
2. **Full paths ALWAYS — including URLs**, each in its own copy block.
3. **ONE line per command.** `\cp` to bypass the alias.
4. **Token-lean working — never at the cost of verification.**
5. **Plain language. One step at a time. Full-file replacements. ALL-CAPS = urgent.**
6. **Mask patient numbers (last 4) and never print secrets or tokens.**
7. **Nothing live is rebuilt without his OK; the manual path stays as fallback.**
8. **Sub-agents read screens.**
9. **Do not hand him diagnostics to run.**
10. **When a screen is wrong, read the screen's code FIRST.**
11. **Do not hand him a step that is not his.**
12. **His board carries only what needs him and what he should know — and every close answers what he typed there.**
13. **His own items are deferred** — name only what has become urgent, and say why.
14. **His approvals are few and arrive together.**
15. **Never put a technical choice to him** (03-Sep) — decide, say it in one line, carry on.
