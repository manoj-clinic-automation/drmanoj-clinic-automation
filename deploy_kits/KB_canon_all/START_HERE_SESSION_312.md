# START HERE — SESSION 312 — written at the S310 close (the Sanjeevni chat), 13-Oct-2026

**Project: Sanjeevni — Pharmacy & Marg.** Open in a fresh chat in this project, on manojz.
1. Run `SANJEEVNI_START_HERE_PROMPT_v1_1`'s Phase 0 (the project's custom instructions) first, then this file.
2. **The work is §0 below — the carryover first (D716).** The rulebook for every build is **the charter v1.1 — `claude/S307_BUILD_CHARTER_v1_1.md`** (builder's part `claude_code_briefs\SANJEEVNI_BUILD_CHARTER.md`, D707), beside the parent's `BUILD_NORM_v1.md` (D704).
3. The brief of this close is `S310_BUILD_BRIEF.md`; the Book is `SANJEEVNI_SYSTEM_BOOK_v1_18_S310.md` (§15I is this session).

No incident is open. The parent's own entry point is `START_HERE_SESSION_311.md` (its session 311 open since 07:3x IST 12-Oct); the Scan App chat's is `START_HERE_SESSION_309.md` (its session 309 open since 06:32 IST 12-Oct).

*FIRST ACT: take your session number from the System Board's `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).*
- **312 is RESERVED for the Sanjeevni chat at this close.** Take it if the board still shows it reserved, otherwise what the board says, and say so in your first line.
- Kit numbers are claimed before the scratch folder is named (F-515). The carryover has no number yet — claim one (S542 is next free at this close) before its brief is written.
- D and F numbers ride the close's one write unless a build needs one sooner.
- Read every PLANNED line on the board before touching a file it names (D646). **S486's PLANNED lines lapse 18-Oct and were NOT renewed.**

*Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.*
- `device_bash` worked through S310 on all three. Never `git` there (F-511).
- **A file sent with the transfer tool can arrive as its previous version when the same staged name is reused** (S303, S308): stage a new name, read the md5 back. **Writing over a file another read has just touched can fail with "modified since read"** (S310): keep the old as `_v1` and write a new name.
- The routine is `END_OF_SESSION_PROMPT_v18.md`.
- **The order of an install is fixed:** the brief → two independent reads against the live bytes, a second-round read of the corrected brief → the owner's ONE paste line to Claude Code on manojz, **naming the charter first** → Claude Code builds, walks, installs, publishes and reports → the chat reads the result live, **on the page the owner will read it on, before it says a word about it (F-724).** At S310 this caught eight blockers before two pastes (F-882); all four kits went live green on their first install.
- **The browser is signed in as the owner; a POST from it is refused by the permission layer.** Reads work; a write is his one tap.
- **The live bytes offline:** the newest bundle (`D:\Downloads\_kbtools\vps_code\code_nightly.tar.gz`) carries every file; extract it in the session's own `/tmp` on manojz, never in a connected folder, and remove it after.

---

## 0 · THE WORK — in order

**A · THE OPEN'S FIRST WORK (v18)**

1. **Read the System Board before anything else:** every item document with a `note`, every message with `read:false`, and `board/_page`. Say in one line how many are waiting. At this close none was waiting; the September notes stand with their replies.
2. **Verify the S310 close's publish landed:**
   - `.git/logs/HEAD` = `refs/remotes/origin/main` (read, never `git`);
   - this close's canon files are in the tree at their hashes (Register v5.149, Archive v1.146, Fault v2.134, Runbook v229, this file, `S310_BUILD_BRIEF.md`, `S310_CLOSE_REPORT.md`, `live_pins_S310close.txt`, `SANJEEVNI_SYSTEM_BOOK_v1_18_S310.md`, the manifest, `OWNER_TODO_LIVE.md`, `MD5SUMS_ALL.txt`);
   - `md5sum -c MD5SUMS_ALL.txt` from inside `KB_canon_all`, with the count.
   If it has not landed, the owner has not double-clicked yet: say so, name the file, and read the canon from the PC's clone.
3. **The three nightly reports:** exists · clock time · verdict, each. The canon check's F-384 (three `START_HERE_SESSION` rows CURRENT — 309, 311, 312, one per open project) is expected until the parent's tool allows three.
4. **The pin list against the newest bundle** (`live_pins_S310close.txt`, or the parent's later one). **This project's DECLARED-PENDING at this close: 0** — all nine S533/S536/S537 `/root` files were held equal to the 13-Oct bundle. State the three counts.
5. **What no store holds** — ask it of anything pinned since. Known: `spine.db` and `/root/finance/spine/orders/order_score_latest.json` are in no code bundle; the S533/S537/S539 tables come back from `finance_nightly.db.gz`.
6. **The cap:** measure `project_info` at the open (at this close: see `S310_CLOSE_REPORT.md`).
7. **Read, live and read-only, what the night left:**
   - the spine: `spine_state.json` passed, gate 13 of 13, `last_success` this morning;
   - **Amir's card and board** (`/finance/stock/api/pad/amir/1`): count #1 at stage C; how many of the 12 released medicine vouchers he has entered; whether the next lot of 12 (voucher 30 among them) has opened; nothing held by the guard (Needs-you shows no *not given to Amir* line);
   - Darpan's spot count of ANKLE BINDER L BAMBOO (S537's ask) — counted or still open;
   - Needs-you: the *Count #1* line; *"live orthotic ordering can start"* shows only for two days from the first stage-C release (12-10) — gone by 15-10 is right.

**B · THE WORK ITSELF**

1. **THE CARRYOVER — D716 (the owner, 05:24 IST 13-Oct): the ordering sheet's system faults removed, the flow otherwise as it is, and Marg's own purchase-order PDF beside the system's.** Claim the kit number first. Read whole before the brief: `/root/finance/porders_s454.py` (9c463e7c in the 13-Oct bundle — the screen `/finance/porders/s454/order`, the *Order sheet print karo* button at line 597, the route `/s454/sheet.pdf` at 1005), `/root/finance/order_sheet.py` (012e21c9), `/root/finance/order_sheet_pdf.py` (6e7a5e1a), and how `porders.py` / the collector take the ORDER_PENDING export. What it builds:
   - **A line leaves the list only when Marg closes it** — never on the system's own guess (an arrival tap, a match): COCYP-type drops (F-876), UPRISE shown under old pending while Marg carries it today, Ravi's "arrived" and the CHYMORAL "awaited" lines kept past Marg's closing (F-877).
   - **The heading counts what is shown** (22 on the sheet against 24 cards, F-876); **units on every line** as Marg carries them (F-878).
   - **A second button beside *Order sheet print karo*** — *Marg ka order (PDF)* — printing Marg's own PENDING ORDERS (PURCHASE) export as Marg printed it (the newest captured export; its capture time on the paper), so the staff print both and compare. Roman Hindi on the screen; nothing else on the screen moves.
   - **Not this kit:** the layout of his 13-Oct question (today's order under a bold *Purchase order dated dd-mm-yyyy*, up to three earlier orders under *Old pending orders dated dd-mm-yyyy*) — the shape the sheet takes when it is next rebuilt; say so in the brief, do not build it.
   - The test data: `D:\Downloads\margsync\MargArchive\ORDER_PENDING\2026-10\ORDER_PENDING_TEXT__2026-10-12__20261012-143518__074c4f6d.XLS` (26 lines, OP-0343 … OP-0354, OP-0334 of 06-10, OP-0293 of 09-09) and whatever Darpan has exported since — the walk proves every Marg line on the screen and on the sheet, and the control is red on the old files.
   - BASS and DAANSHI have no number in the phone book — the owner's or Shavez's to give; never in the repository (F-185).
2. **Rung 4b — stock on the spine** (the charter's step 4): one module for the Marg figure and the shelf figure; `stock_app.py` read whole (drift 8); the name-keyed `stock_snapshot` retired (F-862); the guard's renamed items read through identity (F-874); the spine's family-key miss (F-873); "never past the shelf figure" (D715 a's second half); F-841 with it.
3. **S486 Part A** (F-738, F-739, F-717, the fold) as its own kit — parked behind the carryover and rung 4b.
4. **S486 Part B re-briefed** on rung 4b's one stock function (the re-read §4.3).
5. **Small, together:** `stockmatch` c2 and a held line (F-875); `amir_day`'s healthz tag (F-881); F-802 and the medical-PC kit; the five `reports.*` settings onto the owner's card; F-726 a; F-777; F-794.
6. **The close** — `END_OF_SESSION_PROMPT_v18.md`.

**NEVER RUN:** `deploy_kits\S488_DATES_AND_WAITS\deliver_S488.ps1`. **NEVER ADD TO:** Amir's *Aaj ka kaam* list (D690).

**A STAFF SCREEN CARRIES ONLY "DO THIS" LINES (D708) — AND A LINE ON IT RESTS ON A FACT NOBODY CAN TAP WRONGLY (D712).** **NO FIGURE TO TYPE, EVER (charter rule 8).**

**A VOUCHER NEVER TAKES MARG BELOW ZERO; A SETTLED ITEM IS NEVER RAISED AGAIN (D715).** **A LINE LEAVES THE ORDER LIST ONLY WHEN MARG CLOSES IT (D716).**

**CLOSED BY HIS WORD — DO NOT RAISE AGAIN:**
- the orthotic names as Amir typed them (D709) — all 23 verified;
- the learnt names (D685);
- Kedar's July balance; the four appliances' category;
- the staff's *Aaj ka kaam* lists — the parent's;
- the bill line's design (D712) — built (S533, S536);
- **NORTIMER TAB in the 6-Sep count — out (D715 b);** any surplus later by a fresh count and a new voucher, not raised now;
- **the ordering flow — stays as it is except D716's fixes and the second PDF.**

**Standing owner rulings (restated):**

1. Publishing is his double-click — `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`.
2. Full paths always, URLs too, each in its own copy block.
3. Plain English, short; one step at a time; ALL-CAPS means urgent; IST only; a clock time is read, never estimated.
4. Mask patient numbers (last 4); never print secrets.
5. Nothing live is rebuilt without his OK; the manual path stays.
6. Do not hand him diagnostics or technical choices — decide, say it in one line, proceed. He weighs in on what he can SEE.
7. Fix at the root, never by a staff step; everything a staff member does sits in that person's own portal.
8. A new staff screen is shown to him as a mock-up first and installed switched off; staff pages Roman Hindi, his English.
9. His approvals are few and arrive together; keep chat short.
10. **Every build follows the charter v1.1 (D707) and `BUILD_NORM_v1` (D704).**
11. **A staff screen carries only "do this" lines (D708); the staff are never asked to retype a name (D709); a staff line rests on the scan, not a tap (D712).**
12. **When he asks for an answer only, give the answer only — no build, no code.**

## 1 · THE CURRENT CANON — the manifest wins

- `CANONICAL_MANIFEST.md` (S310 close)
- `KB_Register_v5_149_S310close.md`
- `KB_History_Archive_v1_146_S310close.md` (§S310)
- `Fault_Action_Register_v2_134.md` (§7.68: F-872 … F-882; F-863, F-864 repaired)
- `HANDOFF_RUNBOOK_2026-10-13_Session310close_v229.md` (§2B is this project's)
- `live_pins_S310close.txt`
- `S310_BUILD_BRIEF.md` · `S310_CLOSE_REPORT.md`
- `SANJEEVNI_SYSTEM_BOOK_v1_18_S310.md`
- `OWNER_TODO_LIVE.md`
- `SANJEEVNI_START_HERE_PROMPT_v1_1.md` · `END_OF_SESSION_PROMPT_v18.md` · `BUILD_NORM_v1.md`

The parent's: `START_HERE_SESSION_311.md`, `S305_BUILD_BRIEF.md`. The Scan App project's: `START_HERE_SESSION_309.md`, `S306_BUILD_BRIEF.md`, `SCANAPP_SYSTEM_BOOK_v2_S306.md`.

**Gate:** `md5sum -c MD5SUMS_ALL.txt` from inside `KB_canon_all`.

## 2 · FOR THE PARENT — one line each

- **F-879:** your chat pulled `/root/deploy/repo` at 05:43:44 IST 12-Oct inside S533's build lock — a pull checks `/root/deploy/.claude_code_build.lock` first and waits.
- **F-880:** `aaj_seed.py`'s copy of the voucher-count SQL lacks DUTY_MAP v12's void filter; its PEOPLE map has no line for `amir.arrival_bill_entry` (a filter, not a new line on Amir's list — D690).
- `clinic-finance` restarted at 08:38:12 IST 12-Oct — not S537's, not S539's; your S538 is the likely one: confirm it in your close.
- `canon_sums.py`'s CURRENT-row check allows two `START_HERE_SESSION` rows; three projects keep three (309, 311, 312) — it prints F-384 at every run until the allowance is three (your tool).
- `BUILD_NORM` v2 is proposed in `claude/S307_CHARTER_AND_NORM_REVIEW.md` §3 — yours to write; S310's briefs followed its §7.

## 3 · NUMBERS

Board `_numbers` at this close: **D717 · F-883 · A-D25 · kit S542 · session 312 RESERVED for the Sanjeevni chat; 311 the parent's, open; 309 the Scan App chat's, open; 313 next unreserved.** Kits S533, S536, S537, S539 used (live). No kit claimed for the carryover yet.

*Written at the S310 close, 13-Oct-2026.*
