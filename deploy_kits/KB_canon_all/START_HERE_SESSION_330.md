# START HERE — SESSION 330 — written at the S328 close (the Sanjeevni chat), 19-Oct-2026

**Project: Sanjeevni — Pharmacy & Marg.** Open in a fresh chat in this project, on manojz.
1. Run `SANJEEVNI_START_HERE_PROMPT_v1_1`'s Phase 0 (the project's custom instructions) first, then this file.
2. The rulebook for every build is **the charter v1.1 — `claude/S307_BUILD_CHARTER_v1_1.md`** (builder's part `claude_code_briefs\SANJEEVNI_BUILD_CHARTER.md`, D707), beside the parent's `BUILD_NORM_v1.md` (D704). **The plan of work is `claude/S327_SANJEEVNI_RESTRUCTURING_PLAN.md`** (eight sections, eight steps) **as corrected at S328: step 7 has no renames** (the 22 compulsory orthotic renames were keyed 11-Oct, 23 of 23 verified — D676, D709); step 7 is count #1 closes → rung 4f → count #2 by section.
3. The brief of this close is `S328_BUILD_BRIEF.md`; the Book is `SANJEEVNI_SYSTEM_BOOK_v1_24_S328.md` (§15O is this session).

No incident is open. The parent's session 329 and the Scan App chat's 323 were open at this close (`START_HERE_SESSION_329.md`, `START_HERE_SESSION_323.md` are theirs).

*FIRST ACT: take your session number from the System Board's `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).*
- **330 is RESERVED for the Sanjeevni chat at this close** (board v522). Take it if the board still shows it reserved, otherwise what the board says, and say so in your first line.
- Kit numbers are claimed before the scratch folder is named (F-515). D and F numbers are taken **the moment they are minted** (F-920, F-934) — kept at S328 (D743 v510; F-942 v514; F-943 v518).
- Read every PLANNED line on the board before touching a file it names (D646). This project's at this close: **S598_ARRIVALS_BY_LINE, PLANNED on `stock_figure.py` 92367a19 and `porders.py` 78ea72be (v519)** — standing until its INSTALLED line.

*Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.* At S328 all three were connected at the open; `device_bash` worked throughout. Never `git` there (F-511). The routine is `END_OF_SESSION_PROMPT_v18.md`. **The build road: the Claude Code paste line on manojz** — *"Build, install, verify and publish the kit in claude_code_briefs/S###_NAME.md (vN). Read CLAUDE.md, the charter and the brief first."* Before giving any line, check that no other build is running (`D:\Downloads\_kbtools\agent_build\logs\`; the runner itself waits on `/root/deploy/.claude_code_build.lock`). **The order of a build is fixed:** the brief → ONE independent read against the live bytes (a fresh sub-agent; S328's three briefs carried six, two and two blockers) → v2 → the owner's paste line → the report read → the pages read live by a read-only sub-agent (**never a page whose read writes — reception's order page runs `detect_supplies` on every read, F-925**) → the board's INSTALLED line. **A spine handle passed into `stock_figure` is `stock_watch.Spine` (the one with `.ok`); an order line's quantity is packs, never the spine's units (S593 R1).**

---

## 0 · THE WORK — in order

**A · THE OPEN'S FIRST WORK (v18)**

1. **Read the System Board** — every message with `read:false`, every **v2-page** line with a note, and `board/_page`. Say in one line how many are waiting.
2. **Verify the S328 close's publish landed:** `.git/logs/HEAD` = `refs/remotes/origin/main` (read, never `git`); this close's canon at its hashes (Register v5.165, Archive v1.162, Fault v2.150, Runbook v245, this file, `S328_BUILD_BRIEF.md`, `S328_CLOSE_REPORT.md`, `live_pins_S328close.txt`, `SANJEEVNI_SYSTEM_BOOK_v1_24_S328.md`, the manifest, `OWNER_TODO_LIVE.md`, `MD5SUMS_ALL.txt`); `md5sum -c MD5SUMS_ALL.txt` from inside `KB_canon_all`, with the count. If not landed, name `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat` and read canon from the PC's clone.
3. **S598_ARRIVALS_BY_LINE — the carried build.** Its brief v2 (59e5d370) is published; the paste line was given at 09:2x IST 19-Oct and **had not been run at this close**. If `claude_code_briefs\REPORT_S598.md` exists: read it (the seven marks re-judged — the XL mark undone, the before/after table; the owner's three Needs-you lines each naming the bill that carried other sizes; `Orthotic shortages` 4 → 3; line 3 of order 1 open again on reception's *Orders* card — the pre-08:03 state, no word changes), read the owner's pages live (read-only; not reception's page), write the INSTALLED line on the board with the TO pins (`stock_figure.py`, `porders.py`), and close F-942. If it does not exist: give the owner the line again, in one sentence — `Build, install, verify and publish the kit in claude_code_briefs/S598_ARRIVALS_BY_LINE.md (v2). Read CLAUDE.md, the charter and the brief first.`
4. **The three nightly reports:** exists · clock time · verdict. F-384 (one CURRENT `START_HERE_SESSION` row per open project) is expected.
5. **The pin lists against the bundles.** The 19-Oct 01:35 bundle (on the PC since 05:05 20-Oct — if you open on 19-Oct the PC still holds the 18-Oct bundle) carries S327's **17** (`live_pins_S327close.txt` / Register §S327) — all installed 18-Oct before 01:35, so all should match it, **except `order_sheet.py` f00f0163 and `porders_s454.py` 83079763, superseded by S593 on 19-Oct (they match the 19-Oct bundle, not the live box)**. The 20-Oct bundle carries S593's **6** (`order_rules.py` 8d078dbe, `porders.py` 78ea72be, `porders_s454.py` 40f1755a, `order_sheet.py` 1f1e85c1, `darpan_kal.py` 325d988c, `spine/spine_read.py` 827b0040 — DECLARED-PENDING until then) and the crontab line `# S577_WITNESS` in its `crontab.txt`; S598's two TO pins once it is installed. State the three counts: match · declared-pending · unexplained.
6. **The witness week (4b-2's condition).** Read `/root/finance/spine/stock_figure_witness_<Day>.txt` for each night since 19-10 (the 20-Oct bundle carries the 19-10 file) — count the items a pack or more apart and whether each has a named reason; **F-943's one stderr line** (*"stays pending: attempt to write a readonly database"*) in `stock_figure_witness.log` is expected while the 18-10 09:37 capture is pending. Seven explained nights = 4b-2's start (26-10 at the earliest).
7. **The SSD mirror · the sweep · the tranche and the measured `knowledge_size` (1,402,172 B at the S328 open; the close's figure in `S328_CLOSE_REPORT.md`) · the cold kit when due (the Register and Archive bumped at this close) · the four numbers · what no store holds** (known: `spine.db` and `/root/finance/spine/orders/order_score_latest.json` in no bundle).
8. **Read, live and read-only** (F-925):
   - **the 18-10 09:37 start capture's verdict** (`stock_start_capture`): `accepted` once the 18-10 sale report and a purchase export after Amir's 09:35 tap are in — until Amir's next visit it stays `pending`, and that is correct; the engine's `as_on` reads 16-10 meanwhile (`inputs` on the owner's `api/day`, once the web process has made a plan);
   - the stock check's hub: the four corrected items (KT ROS DT, VINBACTUM DS, FOLITRAX 15 MG TAB, OSTOVAXL DM) read *"Amir marked it done 18-10 09:2x — judged on the next closing taken after it"* until a usable capture after 09:25 exists;
   - the owner's approvals page: the arrival lines (11 at S328's read: S583's nine + ANKLE BINDER BAMBOO L + KNEE SUPPORT HINGED XXL; after S598 three with the bill named) and *Orthotic shortages* (4 before S598, 3 after).

**B · THE WORK ITSELF** (the plan's steps; one kit per sitting)

1. **Step 4, Kit II — S486 B, the buying model** on S593's bytes: `order.model = fixed | levels` (default `fixed`), B.3's levels, B.1's rhythm computed at read from `spine_read.purchases_by_supplier` (stored columns display-only, stamped), the rate's two windows ending on the spine's last sale day, `inputs` on every proposal and the relist on any input moving (the owner's fold says "stale"), B.6 dropped, B.5 an owner door through `book_card`, the owner's fourth fold on the approvals page, the replay re-run on the box against `spine.db` read-only, `fixed` retired after four scored `levels` weeks. **A mock-up of Darpan's one header line first** (rule 7); the brief's design is `03_WORKING_PAPERS\S328\S328_S486_REBRIEF_OUTLINE.md` and `claude/S308_S486_CHARTER_REREAD.md` (iv, v, vi). Then K4 only by his word when the bar on his card is met three weeks running.
2. **Step 3 — 4b-2** after seven explained witness nights: retire `stock_watch.expected_units`, the PC's `PUSH_STOCK_DAILY.bat` / `push_expected.py`, the server's shadow, `engine_source = tables` and the four `purchase_app` table reads.
3. **Step 5 — rung 4c:** Amir's flow safe on no-sale days; the bill chain in place of the calendar on the remaining screens (the reports banner, the export watch, Darpan's "kal", the health page); **Amir's Kit 3** (`claude/S528_KIT3_DEFERRED.md`; the D712 gap closed). **F-943's small repair** (the judge skipped on a read-only connection) rides the next small kit.
4. **Step 6 — rungs 4d and 4e:** the returns desk, Darpan's returns and the claim queue onto the spine; the near-expiry screen; discount attribution.
5. **Step 7 — count #1 closes → rung 4f → count #2 by section.**
6. **Step 8 — rung 5 → P4/P5.**
7. **PARKED by his word — do not start unasked:** F-802's permanent fix (13:47 IST 16-Oct). **Named, not proposed:** Amir's own closing-stock export on his visit days; a latest-hour bound for a start capture; a re-judge rule for an accepted start capture; the 27-letter lumps (L S BELT XXL / XXX) and the family split inside `shelf()` / `marg()` (S598's Left).
8. **The close** — `END_OF_SESSION_PROMPT_v18.md`.

**NEVER RUN:** `deploy_kits\S488_DATES_AND_WAITS\deliver_S488.ps1`. **NEVER ADD TO:** Amir's *Aaj ka kaam* list (D690).

**A STAFF SCREEN CARRIES ONLY "DO THIS" LINES (D708) — AND A LINE ON IT RESTS ON A FACT NOBODY CAN TAP WRONGLY (D712).** **NO FIGURE TO TYPE, EVER (charter rule 8).** **THE STOCK PROOF'S VERDICT IS THE OWNER'S LINE ONLY.** **A VOUCHER NEVER TAKES MARG BELOW ZERO OR PAST THE SHELF FIGURE; A SETTLED ITEM IS NEVER RAISED AGAIN (D715).** **A LINE LEAVES THE ORDER LIST ONLY WHEN MARG CLOSES IT (D716).** **ONLY THE OWNER CHANGES A DEALER'S NUMBER; ONE RECORD PER DEALER (D731).** **A CLOSING TAKEN BEFORE THE DAY'S FIRST SALE IS THE START OF THAT DAY, ONCE VERIFIED ITEM BY ITEM (D740).** **ONE PLACE PER SUPPLIER ON RECEPTION'S ORDER PAGE; A DONE LINE OF AN EARLIER DAY SHOWS ITS DATE (D743).**

**CLOSED BY HIS WORD — DO NOT RAISE AGAIN:** the orthotic names as Amir typed them (D709); the learnt names (D685); Kedar's July balance; the four appliances' category; the staff's *Aaj ka kaam* lists — the parent's; the bill line's design (D712); NORTIMER TAB in the 6-Sep count (D715 b); the ordering flow — Marg's open order (S543), fresh prints (S561); A004143 and A004144 of 12-10 — paid by UPI; "park claude vs sarvam for now"; the dealers' numbers — the phone book is the one place (D731); the gate "Shavez waits for Amir" (18-Oct, not built); **the renames — done, 23 of 23 (do not list them as pending again).**

**Standing owner rulings (restated):**
1. Publishing is his double-click — `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`.
2. Full paths always, URLs too, each in its own copy block.
3. Plain English, short; one step at a time; ALL-CAPS means urgent; IST only; a clock time is read, never estimated (F-934).
4. Mask patient numbers (last 4); never print secrets.
5. Nothing live is rebuilt without his OK; the manual path stays.
6. Do not hand him diagnostics or technical choices — decide, say it in one line, proceed. He weighs in on what he can SEE (18-Oct: a mock-up answered "Yes" in one word; 19-Oct: "can you do it yourself" — yes, when the rule's record is named).
7. Fix at the root, never by a staff step (F-907); everything a staff member does sits in that person's own portal.
8. A new staff screen is shown to him as a mock-up first and installed switched off; staff pages Roman Hindi, his English.
9. His approvals are few and arrive together; keep chat short.
10. Every build follows the charter v1.1 (D707) and `BUILD_NORM_v1` (D704). **A brief adds no rule it has not computed on the store (F-929); every brief gets one independent read before the paste line.**
11. A staff screen carries only "do this" lines (D708); the staff are never asked to retype a name (D709); a staff line rests on the scan or his own tap, never another staff member's (D712).
12. When he asks for an answer only — "check and report", "only evaluate" — give the answer only.
13. "It goes in by itself" is said only after the retry path is read (F-893).
14. A report that "did not land" is diagnosed from the medical PC's census and log first (F-802).
15. A line about a report names its day, and why what landed is not enough (F-910).
16. Before a technical answer that contradicts what he saw, read the store (F-910).
17. Before a screen reader opens a page, read whether that page's read writes (F-925).
18. **He wants the Sanjeevni work done "in a structured way" on Fable:** the plan's steps in order, one big reading per sitting within the week's limit (27-Sep: no extra usage bought), the analysis and briefs here, the builds by Claude Code.
19. **19-Oct: a confusion he names on a staff screen is ended at the root, cleanly, in its own kit** ("I want this … confusion to end so that this becomes clean") — not explained away.

## 1 · THE CURRENT CANON — the manifest wins

- `CANONICAL_MANIFEST.md` (S328 close)
- `KB_Register_v5_165_S328close.md`
- `KB_History_Archive_v1_162_S328close.md` (§S328)
- `Fault_Action_Register_v2_150.md` (§7.84: F-942, F-943)
- `HANDOFF_RUNBOOK_2026-10-19_Session328close_v245.md` (§2B is this project's)
- `live_pins_S328close.txt`
- `S328_BUILD_BRIEF.md` · `S328_CLOSE_REPORT.md`
- `SANJEEVNI_SYSTEM_BOOK_v1_24_S328.md`
- `OWNER_TODO_LIVE.md`
- `SANJEEVNI_START_HERE_PROMPT_v1_1.md` · `END_OF_SESSION_PROMPT_v18.md` · `BUILD_NORM_v1.md`
- In project knowledge: `claude/S327_SANJEEVNI_RESTRUCTURING_PLAN.md` (the plan; step 7 corrected in the Book §15O), `claude/S308_S486_CHARTER_REREAD.md` (Kit II's design, with `03_WORKING_PAPERS\S328\S328_S486_REBRIEF_OUTLINE.md`)

The parent's: `START_HERE_SESSION_329.md` (open). The Scan App project's: `START_HERE_SESSION_323.md` (open).

**Gate:** `md5sum -c MD5SUMS_ALL.txt` from inside `KB_canon_all`.

## 2 · FOR THE PARENT — one line each

- **S594 added one line to the root crontab** (`# S577_WITNESS`, 23:58 nightly, read-only; backup `/root/finance/crontab.bak_S594_20261019_082748`) — the parent's record; read `deploy_kits/S594_WITNESS_CRON/README.md` at its next open. The witness line is no longer the parent's open item.
- **F-935 (the publish's):** carried — the gate should refuse a kit folder without `KIT_ID.txt` / `SUMS.md5`.
- `spine.db` is still in no backup.
- The health page (`/finance/health`, read 08:12 19-Oct) shows no row named "spine"; the spine's rows are the parent's freshness legs — a look at its next open.

## 3 · NUMBERS

Board `_numbers` at this close (v522): **D745 · F-944 · A-D25 · kit S601 · session 330 RESERVED for the Sanjeevni chat; 329 the parent's and 323 the Scan App chat's, open; 331 next unreserved.** S598 (kit S598) is claimed and PLANNED, not installed.

*Written at the S328 close, 19-Oct-2026.*
