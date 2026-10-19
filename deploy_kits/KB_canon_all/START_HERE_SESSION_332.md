# START HERE — SESSION 332 — written at the S330 close (the Sanjeevni chat), 19-Oct-2026

**Project: Sanjeevni — Pharmacy & Marg.** Open in a fresh chat in this project, on manojz.
1. Run `SANJEEVNI_START_HERE_PROMPT_v1_1`'s Phase 0 (the project's custom instructions) first, then this file.
2. The rulebook for every build is **the charter v1.1 — `claude/S307_BUILD_CHARTER_v1_1.md`** (builder's part `claude_code_briefs\SANJEEVNI_BUILD_CHARTER.md`, D707), beside the parent's `BUILD_NORM_v1.md` (D704). **The plan of work is `claude/S327_SANJEEVNI_RESTRUCTURING_PLAN.md`** (step 7 has no renames — done 11-Oct).
3. The brief of this close is `S330_BUILD_BRIEF.md`; the Book is `SANJEEVNI_SYSTEM_BOOK_v1_25_S330.md` (§15P is this session).

No incident is open. The parent's 331 is reserved; the Scan App chat's 323 is open.

**The owner's last word at S330 (12:48 IST 19-Oct): "do EOS here and we will continue and finalize all this in a fresh chat in this project."** "All this" is §0 B items 1–3 below. He wants them finalized here — short answers, his decisions only where they are his.

*FIRST ACT: take your session number from the System Board's `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).*
- **332 is RESERVED for the Sanjeevni chat at this close.** Take it if the board still shows it reserved, otherwise what the board says, and say so in your first line.
- Kit numbers are claimed before the scratch folder is named (F-515). D and F numbers are taken the moment they are minted (F-920, F-934).
- Read every PLANNED line on the board before touching a file it names (D646). **The scan app (`/root/assetapp/asset_register.py`) is the Scan App chat's file** — a change to its pharmacy reader needs a PLANNED line and the settling rule.

*Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.* At S330 all three were connected; `device_bash` worked throughout. Never `git` there (F-511). The routine is `END_OF_SESSION_PROMPT_v18.md`. **The build road: the Claude Code paste line on manojz** — *"Build, install, verify and publish the kit in claude_code_briefs/S###_NAME.md (vN). Read CLAUDE.md, the charter and the brief first."* The order of a build is fixed: the brief → ONE independent read against the live bytes (a fresh sub-agent) → v2 → the owner's paste line → the report read → the pages read live by a read-only sub-agent (**never a page whose read writes — reception's order page and the approvals page's orthotic-shortage card, which calls `/finance/porders/api/state`, run `detect_supplies`, F-925**) → the board's INSTALLED line.

---

## 0 · THE WORK — in order

**A · THE OPEN'S FIRST WORK (v18)**

1. **Read the System Board** — every message with `read:false`, every v2-page line with a note, and `board/_page`. Say in one line how many are waiting.
2. **Verify the S330 close's publish landed:** `.git/logs/HEAD` = `refs/remotes/origin/main` (read, never `git`); this close's canon at its hashes (Register v5.167, Archive v1.164, Fault v2.152, Runbook v247, this file, `S330_BUILD_BRIEF.md`, `S330_CLOSE_REPORT.md`, `live_pins_S330close.txt`, `SANJEEVNI_SYSTEM_BOOK_v1_25_S330.md`, the manifest, `OWNER_TODO_LIVE.md`, `MD5SUMS_ALL.txt`); `md5sum -c MD5SUMS_ALL.txt` from inside `KB_canon_all`, with the count. If not landed, name `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat` and read canon from the PC's clone.
3. **The three nightly reports:** exists · clock time · verdict. F-384 (one CURRENT `START_HERE_SESSION` row per open project) is expected.
4. **The pin lists against the bundles.** The 20-Oct 01:35 bundle (on the PC from 05:05 20-Oct) carries **S593's five** (`order_rules.py` 8d078dbe, `porders_s454.py` 40f1755a, `order_sheet.py` 1f1e85c1, `darpan_kal.py` 325d988c, `spine/spine_read.py` 827b0040) and **S598's three** (`stock_figure.py` cb577821, `stock_watch.py` 299c3ef7, `porders.py` e5a5c4d4) and the crontab line `# S577_WITNESS`. State the three counts: match · declared-pending · unexplained. If you open on 19-Oct the PC still holds the 19-Oct bundle — then the eight are expected mismatches at their predecessor hashes.
5. **The witness week (4b-2's condition).** Read `/root/finance/spine/stock_figure_witness_<Day>.txt` for each night since 19-10 (the 20-Oct bundle carries the 19-10 file); count the items a pack or more apart and whether each has a named reason; F-943's one stderr line is expected while the 18-10 09:37 capture is pending. Seven explained nights = 4b-2's start (26-10 at the earliest).
6. **The SSD mirror · the sweep · the tranche and the measured `knowledge_size` · the cold kit when due (the Register and Archive bumped at this close) · the four numbers · what no store holds** (known: `spine.db` and `order_score_latest.json` in no bundle).

**B · THE WORK HE LEFT TO FINALIZE HERE** (his word at 12:48 — answer first, build after)

1. **Which reader fills the pharmacy bills — Claude or Sarvam.** Facts (Archive §S330; brief): **today Sarvam fills every pharmacy bill and Claude reads beside it, kept aside — each bill is paid twice** (`asset_register._s550_claude`, the pharmacy branch). On S316's 102 bills read by both: quantity faults **Claude 8 · Sarvam 32**; expiry 15 · 37; totals 94 · 91; dates 78 · 77; fully right 11 · 5. Cost: about **₹1.45 a Claude reading, about ₹0.35 Sarvam** (his "four times"); Marg carries 79–103 purchase bills a month. S330's recommendation: Claude fills, Sarvam stops on the pharmacy lane (paid once), Sarvam the fall-back; the cheaper Claude model tested on the same 102 bills first. **The decision is his (money); the test and the build are yours.** A change to `asset_register.py` is the Scan App chat's file — PLANNED line first (D646). Do not repeat F-949: the rows of `purchase_sarvam_check` are Sarvam's.
2. **F-948 — Marg's bill date is the entry day since Marg's digital entry began (15-10).** Read from the raw exports at S330 (15-10: 10 of 10; 18-10, a Sunday: 18 of 19; up to 10-10 correct). Owed: (a) the check of the 29 bills of 15-10 and 18-10 for items and quantities against their scans (S330 offered it; not run); (b) the repair — the paper's date from our scan where Marg carries the entry day, inside a window (two scans misread the year); every reader of `purchase_bill.bill_date` named in the brief; no staff step (F-907). Whether Amir is told is the owner's call only (D708).
3. **D746 — the purchase cut-off line on Darpan's order tab.** Redo the mock-up (rule 7): one grey line under his heading, the newest bill date Marg's latest purchase export holds — proposed *"Marg में खरीद 16-10 तक चढ़ी है — उसके बाद आया माल इस सूची के स्टॉक में नहीं है"*; no stock-day line (he refused it, 10:40). His "Yes" → it rides Kit II.
4. **Step 4, Kit II — S486 B, the buying model** on S593 + S598's bytes (`order.model = fixed | levels`, default `fixed`; scored in shadow; the rhythm computed at read; `inputs` on every proposal; B.6 dropped; B.5 an owner door; the owner's fourth fold; the replay on `spine.db` read-only). Design: `03_WORKING_PAPERS\S328\S328_S486_REBRIEF_OUTLINE.md`, `claude/S308_S486_CHARTER_REREAD.md`. Then K4 only by his word.
5. **Step 3 — 4b-2** after seven explained witness nights.
6. **Step 5 — rung 4c;** Amir's Kit 3 (`claude/S528_KIT3_DEFERRED.md`); F-943's small repair rides the next small kit.
7. **Steps 6, 7, 8** as the plan.
8. **PARKED by his word — do not start unasked:** F-802's permanent fix. **Named, not proposed:** the 27-letter lumps and the family split inside `shelf()` / `marg()`; the *Orders* card's 20-order reach (S598's findings); Amir's own closing-stock export on his visit days.
9. **The close** — `END_OF_SESSION_PROMPT_v18.md`.

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
20. **19-Oct (D746): a date on a staff screen is one the staff member can act on** — a date that needs explaining is the owner's line, never Darpan's.
21. **19-Oct: before saying what a Marg export carries, open the raw file** (he corrected the assistant twice, 11:56 and 12:01); **before crediting a stored scan reading to a reader, read the code that wrote that table for that lane (F-949).**


## 1 · THE CURRENT CANON — the manifest wins

- `CANONICAL_MANIFEST.md` (S330 close)
- `KB_Register_v5_167_S330close.md`
- `KB_History_Archive_v1_164_S330close.md` (§S330)
- `Fault_Action_Register_v2_152.md` (§7.86: F-948, F-949)
- `HANDOFF_RUNBOOK_2026-10-19_Session330close_v247.md` (§2B is this project's)
- `live_pins_S330close.txt`
- `S330_BUILD_BRIEF.md` · `S330_CLOSE_REPORT.md`
- `SANJEEVNI_SYSTEM_BOOK_v1_25_S330.md`
- `OWNER_TODO_LIVE.md`
- `SANJEEVNI_START_HERE_PROMPT_v1_1.md` · `END_OF_SESSION_PROMPT_v18.md` · `BUILD_NORM_v1.md`
- In project knowledge: `claude/S327_SANJEEVNI_RESTRUCTURING_PLAN.md`, `claude/S308_S486_CHARTER_REREAD.md`, `claude/S330_BUILD_BRIEF.md`, `claude/SANJEEVNI_SYSTEM_BOOK_v1_25_S330.md`

The parent's: `START_HERE_SESSION_331.md` (reserved). The Scan App project's: `START_HERE_SESSION_323.md` (open).

**Gate:** `md5sum -c MD5SUMS_ALL.txt` from inside `KB_canon_all`.

## 2 · FOR THE PARENT — one line each

- **F-948** — Marg's bill dates are entry days since 15-10; the parent's month-end packs read `purchase_bill.bill_date` too. The repair is this project's.
- **F-935** carried; `spine.db` in no backup (carried).

## 3 · NUMBERS

Board `_numbers` at this close: **D747 · F-950 · A-D25 · kit S601 · session 332 RESERVED for the Sanjeevni chat; 331 the parent's, reserved; 323 the Scan App chat's, open; 333 next unreserved.**

*Written at the S330 close, 19-Oct-2026.*
