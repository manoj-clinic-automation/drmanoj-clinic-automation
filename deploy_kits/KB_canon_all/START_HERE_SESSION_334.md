# START HERE — SESSION 334 — written at the S333 close (the Sanjeevni chat), 20-Oct-2026

**Project: Sanjeevni — Pharmacy & Marg.** Open in a fresh chat in this project, on manojz.
1. Run `SANJEEVNI_START_HERE_PROMPT_v1_1`'s Phase 0 (the project's custom instructions) first, then this file.
2. The rulebook for every build is **the charter v1.1 — `claude/S307_BUILD_CHARTER_v1_1.md`** (builder's part `claude_code_briefs\SANJEEVNI_BUILD_CHARTER.md`, D707), beside the parent's `BUILD_NORM_v1.md` (D704). **The plan of work is `claude/S327_SANJEEVNI_RESTRUCTURING_PLAN.md`.**
3. The brief of this close is `S333_BUILD_BRIEF.md`; the Book is `SANJEEVNI_SYSTEM_BOOK_v1_27_S333.md` (§15R is this session); the papers are in `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S333\` (the gap analysis, S604's analysis, both R1 reads).

No incident is open. The parent's 331 is reserved; the Scan App chat's 323 is open.

*FIRST ACT: take your session number from the System Board's `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).*
- **334 is RESERVED for the Sanjeevni chat at this close.** Take it if the board still shows it reserved, otherwise what the board says, and say so in your first line.
- Kit numbers are claimed before the scratch folder is named (F-515). D and F numbers are taken the moment they are minted (F-920, F-934).
- Read every PLANNED line on the board before touching a file it names (D646).

*Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.* At S333 all three were connected; `device_bash` worked throughout (Drive folders `H:\My Drive\FinanceDB_Backups` and `H:\My Drive\Clinic Data Archive` were granted once — reachable by the file tools only). Never `git` there (F-511). The routine is `END_OF_SESSION_PROMPT_v18.md`. **Two build roads, the owner's choice per kit:** the Claude Code paste line on manojz — *"Build, install, verify and publish the kit in claude_code_briefs/S###_NAME.md (vN). Read CLAUDE.md, the charter and the brief first."* — or **the API-credit runner** — `python D:\Downloads\_kbtools\agent_build\run_build.py S###_NAME --budget N` (S604 cost $15.08 of a $80 cap; check `D:\Downloads\_kbtools\agent_build\logs\` and the server lock first). The order of a build is fixed: the brief → ONE independent read against the live bytes (a fresh sub-agent) → v2 → the owner's line → the report read → the pages read live (GETs only; **never a page whose read writes** — reception's order page and the approvals page's orthotic-shortage card, F-925; the stock-now page's `_s577_record` still judges on a GET) → the board's INSTALLED line. **Every wait in a runner brief is bounded; every path is full** (S604).

---

## 0 · THE WORK — in order

**A · THE OPEN'S FIRST WORK (v18)**

1. **Read the System Board** — every message with `read:false`, every v2-page line with a note, and `board/_page`. Say in one line how many are waiting. (At this close: none for this chat; `parent_S329_1` is the growth chat's, `sanjeevni_S332_1` the Scan App chat's.)
2. **Verify the S333 close's publish landed:** `.git/logs/HEAD` = `refs/remotes/origin/main` (read, never `git`); this close's canon at its hashes (Register v5.170, Archive v1.167, Fault v2.155, Runbook v250, this file, `S333_BUILD_BRIEF.md`, `S333_CLOSE_REPORT.md`, `live_pins_S333close.txt`, `SANJEEVNI_SYSTEM_BOOK_v1_27_S333.md`, the manifest, `OWNER_TODO_LIVE.md`, `MD5SUMS_ALL.txt`); `md5sum -c MD5SUMS_ALL.txt` from inside `KB_canon_all`, with the count. If not landed, name `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat` and read canon from the PC's clone.
3. **The three nightly reports:** exists · clock time · verdict. F-384 (one CURRENT `START_HERE_SESSION` row per open project) is expected.
4. **The pin lists against the bundles.** The 21-Oct 01:35 bundle carries **five DECLARED-PENDING rows of this project**: S603's four (`amir_day.py` 1169a3d6, `stock_app.py` 40f2c922, `stock_watch.py` f0d9092a, `amir_salts.py` fc5c1d16) and S604's `purchase_app.py` 447b745f. The medical PC's `marg_txt.py` e8a60d9d is in no bundle — its heartbeat (`D:\Downloads\margsync\medical_SendToClinic\heartbeat.txt`, *"marg_txt.py up to date (e8a60d9d)"*). State the three counts: match · declared-pending · unexplained.
5. **The witness week (4b-2's condition).** The newest `stock_figure_witness_<Day>.txt` from the bundle and `/root/finance/spine/stock_figure_witness.log`'s tail and clock: no "stays pending" line; the items a pack or more apart, each with a named reason (the 19 orthotic family lines are F-951's). Seven explained nights from 19-10 = 4b-2's start (26-10 at the earliest).
6. **September locked?** The hub's September line (`/finance/purchase/page/hub`, a GET) — *"FINAL — manoj, …"* if the owner pressed FINALISE (Y115). If not, it stays on his board; nothing to do.
7. **The first pharmacy scan Claude filled (D747)** — from the newest scan-app backup (`assets.db`): the first pharmacy-lane paper after 17:29 IST 19-Oct, its `bill_audit` `filled {by: claude}` row. None existed at S333's open.
8. **The SSD mirror · the sweep · the tranche and the measured `knowledge_size` (1,504,318 at the S333 open; + the brief and Book v1.27 at this close) · the cold kit when due · the four numbers · what no store holds** (known: `spine.db` and `order_score_latest.json` in no bundle).

**B · THE WORK**

1. **F-951 — the orthotic families' own keys.** `spine_build.rename_aliases` maps every ticked rename new20 → old20; sizes that shared one old20 must keep their own new20 key. Analysis first (`spine.db` is on the box only — read it through a read-only probe kit or the runner), then the brief, R1, v2, his line. Moves `stock_figure`'s family lines; touches no staff screen.
2. **F-957 — the walks of S598 and S603 on their own days** (rides the next kit that runs them).
3. **From Sunday 25-Oct — Step 4, Kit II — S486 B, the buying model** on S593 + S598's bytes (`order.model = fixed | levels`, default `fixed`; scored in shadow; the rhythm at read; `inputs` on every proposal; B.6 dropped; B.5 an owner door; the owner's fourth fold; the replay on `spine.db` read-only). Design: `03_WORKING_PAPERS\S328\S328_S486_REBRIEF_OUTLINE.md`, `claude/S308_S486_CHARTER_REREAD.md`. K4 only by his word.
4. **Step 3 — 4b-2** after seven explained witness nights.
5. **Step 5's second half** — the bill chain in place of the calendar on the remaining screens.
6. **Steps 6, 7, 8** as the plan.
7. **Named, small:** BILL/ITEM WISE's returns check; negative payables (page and `bank_sms.neft_portion_p`) while the advice skips them; the stale 09-01..10-01 bill-wise export; one `newest_stamps()` door in `stock_figure`; `_s577_record`'s writable Ctx on a GET; the S446 "Sarvam check" page's name; a Sonnet-vs-Haiku shadow trial on next month's pharmacy bills.
8. **PARKED by his word — do not start unasked:** F-802's permanent fix.
9. **The close** — `END_OF_SESSION_PROMPT_v18.md`.

**NEVER RUN:** `deploy_kits\S488_DATES_AND_WAITS\deliver_S488.ps1`. **NEVER ADD TO:** Amir's *Aaj ka kaam* list (D690).

**A STAFF SCREEN CARRIES ONLY "DO THIS" LINES (D708) — AND A LINE ON IT RESTS ON A FACT NOBODY CAN TAP WRONGLY (D712).** **NO FIGURE TO TYPE, EVER (charter rule 8).** **THE STOCK PROOF'S VERDICT IS THE OWNER'S LINE ONLY.** **A VOUCHER NEVER TAKES MARG BELOW ZERO OR PAST THE SHELF FIGURE; A SETTLED ITEM IS NEVER RAISED AGAIN (D715).** **A LINE LEAVES THE ORDER LIST ONLY WHEN MARG CLOSES IT (D716).** **ONLY THE OWNER CHANGES A DEALER'S NUMBER; ONE RECORD PER DEALER (D731).** **A CLOSING TAKEN BEFORE THE DAY'S FIRST SALE IS THE START OF THAT DAY, ONCE VERIFIED ITEM BY ITEM (D740).** **ONE PLACE PER SUPPLIER ON RECEPTION'S ORDER PAGE; A DONE LINE OF AN EARLIER DAY SHOWS ITS DATE (D743).** **CLAUDE READS THE PHARMACY BILLS; SARVAM IS OFF BY HIS SETTING (D747).** **DARPAN'S TAB CARRIES THE PURCHASE CUT-OFF LINE, NO STOCK-DAY LINE (D746).** **THE PAY PAGE ASKS FOR THE MONTH'S THREE REPORTS AS TEXT AND CONFIRMS EACH; THE LOCK WAITS FOR THEM AND AN AGREEING CROSS-CHECK (D748).**

**CLOSED BY HIS WORD — DO NOT RAISE AGAIN:** the orthotic names as Amir typed them (D709); the learnt names (D685); Kedar's July balance; the four appliances' category; the staff's *Aaj ka kaam* lists — the parent's; the bill line's design (D712); NORTIMER TAB in the 6-Sep count (D715 b); the ordering flow — Marg's open order (S543), fresh prints (S561); A004143 and A004144 of 12-10 — paid by UPI; the dealers' numbers — the phone book is the one place (D731); the gate "Shavez waits for Amir" (18-Oct, not built); the renames — done, 23 of 23; the bill dates of 15-10 / 18-10 — Amir corrects them in Marg (F-948); the scan reader — Claude, Sarvam off (D747); **Agarwal Surgicals' payments — one cheque for the year; September's line Carried in −400 / Paid 400; NEFT from October.**

**Standing owner rulings (restated):**
1. Publishing is his double-click — `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`.
2. Full paths always, URLs too, each in its own copy block.
3. Plain English, short; one step at a time; ALL-CAPS means urgent; IST only; a clock time is read, never estimated (F-934).
4. Mask patient numbers (last 4); never print secrets — **an account number read on a page is never repeated in chat.**
5. Nothing live is rebuilt without his OK; the manual path stays.
6. Do not hand him diagnostics or technical choices — decide, say it in one line, proceed. He weighs in on what he can SEE.
7. Fix at the root, never by a staff step (F-907); everything a staff member does sits in that person's own portal.
8. A new staff screen is shown to him as a mock-up first and installed switched off; staff pages Roman Hindi, his English.
9. His approvals are few and arrive together; keep chat short.
10. Every build follows the charter v1.1 (D707) and `BUILD_NORM_v1` (D704). **A brief adds no rule it has not computed on the store (F-929); every brief gets one independent read before the line is given.**
11. A staff screen carries only "do this" lines (D708); the staff are never asked to retype a name (D709); a staff line rests on the scan or his own tap, never another staff member's (D712).
12. When he asks for an answer only, give the answer only.
13. "It goes in by itself" is said only after the retry path is read (F-893).
14. A report that "did not land" is diagnosed from the medical PC's census and log first (F-802) — `D:\Downloads\margsync\medical_SendToClinic\marg_text_census.txt` and Drive `FromMedical\refused_text\`.
15. A line about a report names its day, and why what landed is not enough (F-910).
16. Before a technical answer that contradicts what he saw, read the store (F-910) — **and when he says a page is wrong, read it live in the browser before answering** (F-954).
17. Before a screen reader opens a page, read whether that page's read writes (F-925).
18. He wants the Sanjeevni work done "in a structured way": the plan's steps in order; the big builds from Sunday (18:09 19-Oct).
19. A confusion he names on a staff screen is ended at the root, cleanly, in its own kit.
20. A date on a staff screen is one the staff member can act on (D746).
21. Before saying what a Marg export carries, open the raw file; before crediting a stored reading to a reader, read the code that wrote it (F-949).
22. Before choosing how something is read or built, ask what it is used for (D747's assessment).
23. **Before saying where a vendor is paid from, compute the route today** (F-954).
24. **He may choose the API-credit runner for a build** ("through the API credits, which still stand") — the brief is the same; its waits are bounded and its paths full.

## 1 · THE CURRENT CANON — the manifest wins

- `CANONICAL_MANIFEST.md` (S333 close)
- `KB_Register_v5_170_S333close.md`
- `KB_History_Archive_v1_167_S333close.md` (§S333)
- `Fault_Action_Register_v2_155.md` (§7.89: F-951 … F-958)
- `HANDOFF_RUNBOOK_2026-10-20_Session333close_v250.md` (§2B is this project's)
- `live_pins_S333close.txt`
- `S333_BUILD_BRIEF.md` · `S333_CLOSE_REPORT.md`
- `SANJEEVNI_SYSTEM_BOOK_v1_27_S333.md`
- `OWNER_TODO_LIVE.md`
- `SANJEEVNI_START_HERE_PROMPT_v1_1.md` · `END_OF_SESSION_PROMPT_v18.md` · `BUILD_NORM_v1.md`
- In project knowledge: `claude/S327_SANJEEVNI_RESTRUCTURING_PLAN.md`, `claude/S308_S486_CHARTER_REREAD.md`, `claude/S333_BUILD_BRIEF.md`, `claude/SANJEEVNI_SYSTEM_BOOK_v1_27_S333.md`

The parent's: `START_HERE_SESSION_331.md` (reserved). The Scan App project's: `START_HERE_SESSION_323.md` (open).

**Gate:** `md5sum -c MD5SUMS_ALL.txt` from inside `KB_canon_all`.

## 2 · FOR THE PARENT — one line each

- **F-958:** one `.gitattributes` line (`deploy_kits/**/KIT_MANIFEST.txt -text`) — S546's and S604's CRLF manifests fail their SUMS in the clone.
- `bank_sms.neft_portion_p` sums a negative payable the bank file skips (named at S604).
- F-935 carried; `spine.db` in no backup (carried).

## 3 · NUMBERS

Board `_numbers` at this close: **D749 · F-959 · A-D25 · kit S605 · session 334 RESERVED for the Sanjeevni chat; 331 the parent's, reserved; 323 the Scan App chat's, open; 335 next unreserved.**

*Written at the S333 close, 20-Oct-2026.*
