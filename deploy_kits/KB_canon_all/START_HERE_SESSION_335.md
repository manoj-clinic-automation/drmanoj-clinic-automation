# START HERE — SESSION 335 — written at the S334 close (the Sanjeevni chat), 22-Oct-2026

**Project: Sanjeevni — Pharmacy & Marg.** Open in a fresh chat in this project, on manojz.
1. Run `SANJEEVNI_START_HERE_PROMPT_v1_1`'s Phase 0 (the project's custom instructions) first, then this file.
2. The rulebook for every build is **the charter v1.1 — `claude/S307_BUILD_CHARTER_v1_1.md`** (builder's part `claude_code_briefs\SANJEEVNI_BUILD_CHARTER.md`, D707), beside the parent's `BUILD_NORM_v1.md` (D704). **The plan of work is `claude/S327_SANJEEVNI_RESTRUCTURING_PLAN.md`.**
3. The brief of this close is `S334_BUILD_BRIEF.md`; the Book is `SANJEEVNI_SYSTEM_BOOK_v1_28_S334.md` (§15S is this session); the papers are in `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S334\` (the findings, the mock-up's HTML, R1, the reviewed v2 that did not run).

No incident is open. The parent's 331 is **open** (since 17:25 IST 20-Oct; kits S606 … S611); the Scan App chat's 323 is open.

*FIRST ACT: take your session number from the System Board's `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).*
- **335 is RESERVED for the Sanjeevni chat at this close.** Take it if the board still shows it reserved, otherwise what the board says, and say so in your first line.
- Kit numbers are claimed before the scratch folder is named (F-515). D and F numbers are taken the moment they are minted (F-920, F-934).
- Read every PLANNED line on the board before touching a file it names (D646).

*Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.* At S334 `device_bash` reached `D:\Downloads`, `D:\dr-manoj-git` and `C:\Users\Dr Manoj Agarwal`; `F:\ClinicBackup` was not connected this session. Never `git` there (F-511). The routine is `END_OF_SESSION_PROMPT_v18.md`. **Two build roads, the owner's choice per kit:** the Claude Code paste line on manojz, or **the API-credit runner** — `python D:\Downloads\_kbtools\agent_build\run_build.py S###_NAME --budget N` (S605 cost $32.04 of an $80 cap). The order of a build is fixed: the brief → ONE independent read (a fresh sub-agent) → v2 → **the brief read back on the PC — its first line names the version, its md5 is the one the chat wrote; a file is sent under a name never used before in the session (F-963)** → the owner's line → the report read → the pages read live (GETs only; never a page whose read writes, F-925) → the board's INSTALLED line.

---

## 0 · THE WORK — in order

**A · THE OPEN'S FIRST WORK (v18)**

1. **Read the System Board** — every message with `read:false`, every v2-page line with a note, and `board/_page`. Say in one line how many are waiting. (At this close: none for this chat; `parent_S329_1` is the growth chat's, `sanjeevni_S332_1` the Scan App chat's.)
2. **Verify the S334 close's publish landed:** `.git/logs/HEAD` = `refs/remotes/origin/main` (read, never `git`); this close's canon at its hashes (Register v5.171, Archive v1.168, Fault v2.156, Runbook v251, this file, `S334_BUILD_BRIEF.md`, `S334_CLOSE_REPORT.md`, `live_pins_S334close.txt`, `SANJEEVNI_SYSTEM_BOOK_v1_28_S334.md`, the manifest, `OWNER_TODO_LIVE.md`, `MD5SUMS_ALL.txt`); `md5sum -c MD5SUMS_ALL.txt` from inside `KB_canon_all`, with the count. If not landed, name `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat` and read canon from the PC's clone.
3. **The three nightly reports:** exists · clock time · verdict. F-384 (one CURRENT `START_HERE_SESSION` row per open project) is expected.
4. **The pin lists against the bundles.** This project's DECLARED-PENDING at this close: **0** (the 22-Oct bundle confirmed S605's eight and S333's five). State the three counts: match · declared-pending · unexplained.
5. **S605 read live, the owner's pages only** (GETs; reception's order pages and Darpan's day read write — F-925 — so read them from the newest `finance_nightly.db.gz` and the code instead): `ortho_yes` rows (has Darpan answered?); order messages since 20-Oct with status, `handed_at`, `last_error` (any `unconfirmed:`?); the owner's Needs-you lines S605 added (the impossible-figure line, the unconfirmed line).
6. **The witness week after F-951's spine change.** The newest `stock_figure_witness_<Day>.txt` and `/root/finance/spine/stock_figure_witness.log`'s tail: the 22 renamed sizes now read the family only to 10-10 (F-951's open half) — name each such line's reason; 4b-2's seven explained nights restart from the first night that explains them.
7. **September locked?** `purchase_month` 2026-09 `final` (Y115). If not, it stays on his board.
8. **The SSD mirror · the sweep · the tranche and the measured `knowledge_size` · the cold kit when due · the four numbers · what no store holds** (known: `spine.db` and `order_score_latest.json` in no bundle).

**B · THE WORK**

1. **S605's follow-up — one small kit (brief → R1 → v2 → read back → his line):**
   - **F-951's other half:** the readers that ask the spine by the 6-Sep count's old names — `stock_figure`'s shelf figure and the witness (they see the family only to 10-10), and `carried()` for order lines printed under an old name (order 20's ANKLE BINDER BAMBOO L, KNEE IMMOBILISER UNISON M, L S BELT CONT GRAY UNISON XXX) — onto the new keys from the split day, with controls on `shelf()`, `marg()`, `carried()` for the 22 sizes (R1-B4 in `03_WORKING_PAPERS\S334\S605_R1_REVIEW.md`).
   - **F-959's second door:** the old Purchase orders page's *Yuvika ko order bhejo* (`porders.api_send`, `porders.html`) still orders the raw shortage — refuse it (or limit it to Darpan's kept lines) and hide the button (D749).
   - **F-962's count:** *Aaj ke order — call karo* counts the Ho chuke rule (received orders and earlier days) — make it today's still-sent orders, computed in `home()` only.
   - **F-957's last walk:** S604's walk on its own days (a new file in the new kit; S604's folder frozen).
   - Take the rest of the reviewed v2's points the build did not meet (`03_WORKING_PAPERS\S334\S605_ORDER_FIXES_v2_reviewed_NOT_RUN.md` against REPORT_S605): the late `ok:false` on an unconfirmed order, re-queue only after the phone's own "no", the stale-list rules of the confirm screen, `_done_today` through `book_card`, numbers masked in reports.
2. **From Sunday 25-Oct — Step 4, Kit II — S486 B, the buying model** (`order.model = fixed | levels`, default `fixed`; scored in shadow). Design: `03_WORKING_PAPERS\S328\S328_S486_REBRIEF_OUTLINE.md`, `claude/S308_S486_CHARTER_REREAD.md`. K4 only by his word.
3. **Step 3 — 4b-2** after seven explained witness nights (see A.6).
4. **Step 5's second half** — the bill chain in place of the calendar on the remaining screens.
5. **Steps 6, 7, 8** as the plan.
6. **Named, small:** a pay-card warning before the Bhejo backup now that a payment message is handed to the phone once (F-702's residue); BILL/ITEM WISE's returns check; negative payables (page and `bank_sms.neft_portion_p`) while the advice skips them; the stale 09-01..10-01 bill-wise export; one `newest_stamps()` door in `stock_figure`; `_s577_record`'s writable Ctx on a GET; the S446 "Sarvam check" page's name; a Sonnet-vs-Haiku shadow trial on next month's pharmacy bills.
7. **PARKED by his word — do not start unasked:** F-802's permanent fix.
8. **The close** — `END_OF_SESSION_PROMPT_v18.md`.

**NEVER RUN:** `deploy_kits\S488_DATES_AND_WAITS\deliver_S488.ps1`. **NEVER ADD TO:** Amir's *Aaj ka kaam* list (D690).

**A STAFF SCREEN CARRIES ONLY "DO THIS" LINES (D708) — AND A LINE ON IT RESTS ON A FACT NOBODY CAN TAP WRONGLY (D712) — THE ONE RULED EXCEPTION: RECEPTION'S YUVIKA CARD WAITS ON DARPAN'S हाँ (D749).** **NO FIGURE TO TYPE, EVER (charter rule 8).** **THE STOCK PROOF'S VERDICT IS THE OWNER'S LINE ONLY.** **A VOUCHER NEVER TAKES MARG BELOW ZERO OR PAST THE SHELF FIGURE; A SETTLED ITEM IS NEVER RAISED AGAIN (D715).** **A LINE LEAVES THE ORDER LIST ONLY WHEN MARG CLOSES IT (D716).** **ONLY THE OWNER CHANGES A DEALER'S NUMBER; ONE RECORD PER DEALER (D731).** **A CLOSING TAKEN BEFORE THE DAY'S FIRST SALE IS THE START OF THAT DAY, ONCE VERIFIED ITEM BY ITEM (D740).** **ONE PLACE PER SUPPLIER ON RECEPTION'S ORDER PAGE; A DONE LINE OF AN EARLIER DAY SHOWS ITS DATE (D743).** **CLAUDE READS THE PHARMACY BILLS; SARVAM IS OFF BY HIS SETTING (D747).** **DARPAN'S TAB CARRIES THE PURCHASE CUT-OFF LINE, NO STOCK-DAY LINE (D746).** **THE PAY PAGE ASKS FOR THE MONTH'S THREE REPORTS AS TEXT AND CONFIRMS EACH; THE LOCK WAITS FOR THEM AND AN AGREEING CROSS-CHECK (D748).** **THE SYSTEM'S ORTHOTIC LIST GOES TO YUVIKA ONLY AFTER DARPAN'S हाँ, AND ONLY THE LINES HE KEPT (D749).** **ONE WHATSAPP PER ORDER: THE PHONE IS HANDED A MESSAGE ONCE; "SAB KO WHATSAPP BHEJO" ASKS ONCE; EVERY DEALER LINE AND BOTH PRINTED SHEETS CARRY THE CALL AND WHATSAPP NUMBERS (S605).**

**CLOSED BY HIS WORD — DO NOT RAISE AGAIN:** the orthotic names as Amir typed them (D709); the learnt names (D685); Kedar's July balance; the four appliances' category; the staff's *Aaj ka kaam* lists — the parent's; the bill line's design (D712); NORTIMER TAB in the 6-Sep count (D715 b); the ordering flow — Marg's open order (S543), fresh prints (S561); A004143 and A004144 of 12-10 — paid by UPI; the dealers' numbers — the phone book is the one place (D731); the gate "Shavez waits for Amir" (18-Oct, not built); the renames — done, 23 of 23; the bill dates of 15-10 / 18-10 — Amir corrects them in Marg (F-948); the scan reader — Claude, Sarvam off (D747); Agarwal Surgicals' payments — one cheque for the year; September's line Carried in −400 / Paid 400; NEFT from October; **the orthotic list's yes — Darpan's (D749); the screens of S605 as the mock-up v3 showed them.**

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
10. Every build follows the charter v1.1 (D707) and `BUILD_NORM_v1` (D704). **A brief adds no rule it has not computed on the store (F-929); every brief gets one independent read before the line is given; the brief that governs is read back on the PC before the line (F-963).**
11. A staff screen carries only "do this" lines (D708); the staff are never asked to retype a name (D709); a staff line rests on the scan or his own tap, never another staff member's (D712) — D749 the ruled exception.
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
23. Before saying where a vendor is paid from, compute the route today (F-954).
24. He may choose the API-credit runner for a build — the brief is the same; its waits are bounded and its paths full.
25. **When he reports what staff saw, read the store's own record of who did what and when before explaining it** (S334: the "automatic" WhatsApp was Alisha's 12:43:59 tap, sent from 13:25 when the phone was unlocked).
26. **He wants every dealer's Call and WhatsApp numbers wherever staff order from — the screens and the printed sheets alike** (15:28 and 15:54 IST 20-Oct).

## 1 · THE CURRENT CANON — the manifest wins

- `CANONICAL_MANIFEST.md` (S334 close)
- `KB_Register_v5_171_S334close.md`
- `KB_History_Archive_v1_168_S334close.md` (§S334)
- `Fault_Action_Register_v2_156.md` (§7.90: F-959 … F-963)
- `HANDOFF_RUNBOOK_2026-10-22_Session334close_v251.md` (§2B is this project's)
- `live_pins_S334close.txt`
- `S334_BUILD_BRIEF.md` · `S334_CLOSE_REPORT.md`
- `SANJEEVNI_SYSTEM_BOOK_v1_28_S334.md`
- `OWNER_TODO_LIVE.md`
- `SANJEEVNI_START_HERE_PROMPT_v1_1.md` · `END_OF_SESSION_PROMPT_v18.md` · `BUILD_NORM_v1.md`
- In project knowledge: `claude/S327_SANJEEVNI_RESTRUCTURING_PLAN.md`, `claude/S308_S486_CHARTER_REREAD.md`, `claude/S334_BUILD_BRIEF.md`, `claude/SANJEEVNI_SYSTEM_BOOK_v1_28_S334.md`
- The kit: `deploy_kits/S605_ORDER_FIXES/` (SUMS `018a68ad`), `claude_code_briefs/S605_ORDER_FIXES.md` (v1 — **the one that ran**, `2f440975`), `claude_code_briefs/REPORT_S605.md` (`d39fb420`).

The parent's: `START_HERE_SESSION_331.md` (its 331 open). The Scan App project's: `START_HERE_SESSION_323.md` (open).

**Gate:** `md5sum -c MD5SUMS_ALL.txt` from inside `KB_canon_all`.

## 2 · FOR THE PARENT — one line each

- **F-958:** one `.gitattributes` line (`deploy_kits/**/KIT_MANIFEST.txt -text`) — S546's and S604's CRLF manifests fail their SUMS in the clone (REPORT_S605 saw it again).
- **S605 moved the duty map** (`DUTY_MAP.json` v16 → v17: Darpan's orthotic duty is now "say yes / no on Kal ka hisaab"; `reception.medicine_orders`' `due_sql` has never counted the orthotic card).
- `bank_sms.neft_portion_p` sums a negative payable the bank file skips (named at S604). F-935 carried; `spine.db` in no backup (carried).

## 3 · NUMBERS

Board `_numbers` at this close: **D750 · F-964 · A-D25 · kit S613 · session 335 RESERVED for the Sanjeevni chat; 331 the parent's, open; 323 the Scan App chat's, open; 336 next unreserved.**

*Written at the S334 close, 22-Oct-2026.*
