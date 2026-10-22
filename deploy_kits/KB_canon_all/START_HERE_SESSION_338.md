# START HERE — SESSION 338 — written at the S335 close (the Sanjeevni chat), 22-Oct-2026

**Project: Sanjeevni — Pharmacy & Marg.** Open in a fresh chat in this project, on manojz.
1. Run `SANJEEVNI_START_HERE_PROMPT_v1_1`'s Phase 0 (the project's custom instructions) first, then this file.
2. The rulebook for every build is **the charter v1.1 — `claude/S307_BUILD_CHARTER_v1_1.md`** (builder's part `claude_code_briefs\SANJEEVNI_BUILD_CHARTER.md`, D707), beside the parent's `BUILD_NORM_v1.md` (D704). **The plan of work is `claude/S327_SANJEEVNI_RESTRUCTURING_PLAN.md`.**
3. The brief of this close is `S335_BUILD_BRIEF.md`; the Book is `SANJEEVNI_SYSTEM_BOOK_v1_29_S335.md` (§15T is this session); the papers are in `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S335\` (the two code maps, the scan audit by eye, the three briefs v1 / v2 and their R1 reviews, the mock-up).

No incident is open. The parent's 336 is **open** (since 06:20 IST 22-Oct, with its own kits from S614); the Scan App chat's 337 is **open** (since 14:07 IST 22-Oct, building S623 in its own chat).

*FIRST ACT: take your session number from the System Board's `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).*
- **338 is RESERVED for the Sanjeevni chat at this close.** Take it if the board still shows it reserved, otherwise what the board says, and say so in your first line.
- Kit numbers are claimed before the scratch folder is named (F-515). D and F numbers are taken the moment they are minted (F-920, F-934).
- Read every PLANNED line on the board before touching a file it names (D646).

*Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.* At S335 `device_bash` reached all three; `H:\My Drive\FinanceDB_Backups` was granted for the Scan App backup and is read with the file tools (it does not mount in the shell). Never `git` there (F-511). The routine is `END_OF_SESSION_PROMPT_v18.md`. **Two build roads, the owner's choice per kit:** the Claude Code paste line on manojz, or **the API-credit runner** — `python D:\Downloads\_kbtools\agent_build\run_build.py S###_NAME --budget N` (S613 $17.85, S618 $19.07, S619 $16.50). The order of a build is fixed: (code maps by sub-agents where the question is wide) → the brief → ONE independent read (a fresh sub-agent) → v2 → **the brief read back on the PC — its first line names the version, its md5 is the one the chat wrote; a file is sent under a name never used before (F-963)** → the owner's line → the report read → the pages read live (GETs only; never a page whose read writes, F-925) → the board's INSTALLED line. **One build at a time: the next line only after the previous runner prints DONE.**

---

## 0 · THE WORK — in order

**A · THE OPEN'S FIRST WORK (v18)**

1. **Read the System Board** — every message with `read:false`, every v2-page line with a note, and `board/_page`. Say in one line how many are waiting. (At this close: the owner's note `5y5my08uwric9sofgmm3` was answered as *open — on my list*; `sanjeevni_S335_1` is the parent's, `sanjeevni_S335_2` the Scan App chat's.)
2. **Verify the S335 close's publish landed:** `.git/logs/HEAD` = `refs/remotes/origin/main` (read, never `git`); this close's canon at its hashes (Register v5.174, Archive v1.171, Fault v2.159, Runbook v254, this file, `S335_BUILD_BRIEF.md`, `S335_CLOSE_REPORT.md`, `live_pins_S335close.txt`, `SANJEEVNI_SYSTEM_BOOK_v1_29_S335.md`, the manifest, `OWNER_TODO_LIVE.md`, `MD5SUMS_ALL.txt`); `md5sum -c MD5SUMS_ALL.txt` from inside `KB_canon_all`, with the count. If not landed, name `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat` and read canon from the PC's clone.
3. **The three nightly reports:** exists · clock time · verdict. F-384 (one CURRENT `START_HERE_SESSION` row per open project) is expected.
4. **The pin lists against the bundles.** This project's DECLARED-PENDING at this close: **14** — S613's, S618's and S619's thirteen `/root` files (the 23-Oct bundle should confirm them) and `/root/shared/scan_quality.py` 16fb2402 **outside every bundle** (kit-held). State the three counts: match · declared-pending · unexplained.
5. **The three kits read live, the owner's pages only** (GETs; reception's and Darpan's pages write on a read — F-925 — so read them from the newest `finance_nightly.db.gz`, `assetapp_nightly.tar.gz` and the code instead): `order_carry` rows (carried, closed, dropped); the track page's counts against the database; `scan_rescan_ask` (has the owner sent B-0181 / B-0188 back? has reception rescanned?); `scan_lie` turns; the late row's orders; the delivery line in the newest WhatsApp body (never print the number).
6. **The witness week after F-951.** The newest `stock_figure_witness_<Day>.txt` (VPS only — read through the next build's runner if needed); 4b-2's seven explained nights restart from the first night after S613.
7. **The SSD mirror · the sweep · the tranche and the measured `knowledge_size` (1,703,606 of 2,000,000 at the S335 open — the tranche is due: superseded Books v1.9 … v1.27 and old briefs in project knowledge, each proved in `KB_canon_all` or `03_WORKING_PAPERS` first) · the cold kit when due · the four numbers · what no store holds** (known: `spine.db`, `order_score_latest.json`, the whole `/root/shared` folder in no bundle).

**B · THE WORK**

1. **F-988 — Amir's bank statements vanished from his app** before the new month's (the owner's note, point 5). Read Amir's pack reader, the month it serves and when it rolls; one small kit (the pack is the parent's tooling — if the cause is there, the parent's line; the door is Amir's).
2. **The owner's note `5y5my08…` points 1–4** — Marg's expiry / near-expiry / dump monthly reports and the item list / salt list as text exports in Shavez's flow; the monthly Tally export from Marg with screenshots, doable by Shavez or Amir; Amir generating them on his first visit of the month, an intuitive flow with screenshots. **A plan and a mock-up first; nothing built without his yes.** Read the Marg text readers (`marg_txt`, S480) and Shavez's / Amir's export flows first.
3. **Kit II — S486 B, the buying model** (`order.model = fixed | levels`, default `fixed`; scored in shadow) — the scan and tracker kits are done, as he ordered. Design: `03_WORKING_PAPERS\S328\S328_S486_REBRIEF_OUTLINE.md`, `claude/S308_S486_CHARTER_REREAD.md`. K4 only by his word.
4. **F-987** — Kedar's Marg bill A000211 (15-10) carries the verdict WRONG yet reception is asked to scan it: read what the S446 verdict means and decide; no question to the owner unless it is his to see.
5. **Named, small:** the dealer-correction door for a scan saved under the wrong dealer (B-0161, B-0167 — listed on the track page with *Open the scan* only); the soft scan note's spelling match (misses about half — `s454_item_name` learnt from `bill_items`, not `claude_reading`); the purchase page's `staff_send` (any vendor; `_wa_text` without the delivery line); F-984's stock readers onto `order_track`; one scan per order; `order.lead_days` 1 beside `order.deliver_days` 2; a pay-card warning before the Bhejo backup; BILL/ITEM WISE's returns check; negative payables; the stale 09-01..10-01 bill-wise export; one `newest_stamps()` door; `_s577_record`'s writable Ctx on a GET; the S446 page's name; a Sonnet-vs-Haiku shadow trial.
6. **Step 3 — 4b-2**; **Step 5's second half**; **Steps 6, 7, 8** as the plan.
7. **PARKED by his word — do not start unasked:** F-802's permanent fix.
8. **The close** — `END_OF_SESSION_PROMPT_v18.md`.

**NEVER RUN:** `deploy_kits\S488_DATES_AND_WAITS\deliver_S488.ps1`. **NEVER ADD TO:** Amir's *Aaj ka kaam* list (D690).

**A STAFF SCREEN CARRIES ONLY "DO THIS" LINES (D708) — AND A LINE ON IT RESTS ON A FACT NOBODY CAN TAP WRONGLY (D712) — THE ONE RULED EXCEPTION: RECEPTION'S YUVIKA CARD WAITS ON DARPAN'S हाँ (D749).** **NO FIGURE TO TYPE, EVER (charter rule 8).** **THE STOCK PROOF'S VERDICT IS THE OWNER'S LINE ONLY.** **A VOUCHER NEVER TAKES MARG BELOW ZERO OR PAST THE SHELF FIGURE; A SETTLED ITEM IS NEVER RAISED AGAIN (D715).** **A LINE LEAVES THE ORDER LIST ONLY WHEN MARG CLOSES IT (D716) — AND A MEDICINE THAT DID NOT COME GOES ON THE DEALER'S NEXT ORDER BY ITSELF (D757).** **ONLY THE OWNER CHANGES A DEALER'S NUMBER; ONE RECORD PER DEALER (D731).** **A CLOSING TAKEN BEFORE THE DAY'S FIRST SALE IS THE START OF THAT DAY, ONCE VERIFIED ITEM BY ITEM (D740).** **ONE PLACE PER SUPPLIER ON RECEPTION'S ORDER PAGE; A DONE LINE OF AN EARLIER DAY SHOWS ITS DATE (D743).** **CLAUDE READS THE PHARMACY BILLS; SARVAM IS OFF BY HIS SETTING (D747).** **DARPAN'S TAB CARRIES THE PURCHASE CUT-OFF LINE, NO STOCK-DAY LINE (D746).** **THE PAY PAGE ASKS FOR THE MONTH'S THREE REPORTS AS TEXT AND CONFIRMS EACH; THE LOCK WAITS FOR THEM AND AN AGREEING CROSS-CHECK (D748).** **THE SYSTEM'S ORTHOTIC LIST GOES TO YUVIKA ONLY AFTER DARPAN'S हाँ, AND ONLY THE LINES HE KEPT (D749).** **ONE WHATSAPP PER ORDER (S605).** **ONE ORDER LIST FOR FOUR PEOPLE: RECEPTION "DO THIS" ONLY, DARPAN ONE READ-ONLY LINE, THE OWNER AND SHAVEZ THE SAME LIST; LATE AFTER TWO DAYS, SUNDAY NOT COUNTED; EVERY WHATSAPP ORDER CARRIES "KRIPYA MAAL DOPAHAR 3 SE SHAAM 6 BAJE KE BEECH, YA SUBAH 11 BAJE TAK BHEJEIN." (D757).** **EVERY PHARMACY SCAN UPRIGHT; THE OWNER AND SHAVEZ SEND A SCAN BACK, RECEPTION RESCANS (D758).**

**CLOSED BY HIS WORD — DO NOT RAISE AGAIN:** the orthotic names as Amir typed them (D709); the learnt names (D685); Kedar's July balance; the four appliances' category; the staff's *Aaj ka kaam* lists — the parent's; the bill line's design (D712); NORTIMER TAB in the 6-Sep count (D715 b); the ordering flow — Marg's open order (S543), fresh prints (S561); A004143 and A004144 of 12-10 — paid by UPI; the dealers' numbers — the phone book is the one place (D731); the gate "Shavez waits for Amir" (not built); the renames — 23 of 23; the bill dates of 15-10 / 18-10 — Amir corrects them in Marg (F-948); the scan reader — Claude, Sarvam off (D747); Agarwal Surgicals' payments — one cheque for the year; September's line Carried in −400 / Paid 400; NEFT from October; the orthotic list's yes — Darpan's (D749); the screens of S605; **September is locked (his word 14:04 22-Oct); the GST composition flow is the parent's (06:37); Darpan's flow — one read-only line, nothing to tap (06:43); the 2 days are not in the dealer's message (07:45).**

**Standing owner rulings (restated):**
1. Publishing is his double-click — `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`.
2. Full paths always, URLs too, each in its own copy block.
3. Plain English, short; one step at a time; ALL-CAPS means urgent; IST only; a clock time is read, never estimated (F-934).
4. Mask patient numbers (last 4); never print secrets — an account number read on a page is never repeated in chat.
5. Nothing live is rebuilt without his OK; the manual path stays.
6. Do not hand him diagnostics or technical choices — decide, say it in one line, proceed. He weighs in on what he can SEE — a screen, a wording, **a workflow (who does what)**.
7. Fix at the root, never by a staff step (F-907); everything a staff member does sits in that person's own portal.
8. A new staff screen is shown to him as a mock-up first and installed switched off; staff pages Roman Hindi, his English.
9. His approvals are few and arrive together; keep chat short.
10. Every build follows the charter v1.1 (D707) and `BUILD_NORM_v1` (D704). A brief adds no rule it has not computed on the store (F-929); every brief gets one independent read before the line is given; the brief that governs is read back on the PC before the line (F-963).
11. A staff screen carries only "do this" lines (D708); the staff are never asked to retype a name (D709); a staff line rests on the scan or his own tap, never another staff member's (D712) — D749 the ruled exception.
12. When he asks for an answer only, give the answer only.
13. "It goes in by itself" is said only after the retry path is read (F-893) — **and a promise about Marg's behaviour only after Marg's own export is read (F-985).**
14. A report that "did not land" is diagnosed from the medical PC's census and log first (F-802).
15. A line about a report names its day, and why what landed is not enough (F-910).
16. Before a technical answer that contradicts what he saw, read the store (F-910); when he says a page is wrong, read it live in the browser before answering (F-954).
17. Before a screen reader opens a page, read whether that page's read writes (F-925).
18. He wants the Sanjeevni work done "in a structured way": the plan's steps in order.
19. A confusion he names on a staff screen is ended at the root, cleanly, in its own kit.
20. A date on a staff screen is one the staff member can act on (D746).
21. Before saying what a Marg export carries, open the raw file; before crediting a stored reading to a reader, read the code that wrote it (F-949).
22. Before choosing how something is read or built, ask what it is used for (D747's assessment).
23. Before saying where a vendor is paid from, compute the route today (F-954).
24. He may choose the API-credit runner for a build — the brief is the same; its waits are bounded and its paths full.
25. When he reports what staff saw, read the store's own record of who did what and when before explaining it.
26. He wants every dealer's Call and WhatsApp numbers wherever staff order from — the screens and the printed sheets alike.
27. **Darpan is slow to take up a new flow and quick to worry — give him the least to read and nothing to decide (06:43 22-Oct).**
28. **Shavez pursues on the owner's behalf — whatever the owner sees of the pharmacy's orders and scans, Shavez sees too (06:43, 06:53).**
29. **A quality check that would stop good work is not built; where a device cannot tell, the server lists it and a person decides (S618 R1).**

## 1 · THE CURRENT CANON — the manifest wins

- `CANONICAL_MANIFEST.md` (S335 close)
- `KB_Register_v5_174_S335close.md`
- `KB_History_Archive_v1_171_S335close.md` (§S335)
- `Fault_Action_Register_v2_159.md` (§7.93: F-981 … F-988)
- `HANDOFF_RUNBOOK_2026-10-22_Session335close_v254.md` (§2B is this project's)
- `live_pins_S335close.txt`
- `S335_BUILD_BRIEF.md` · `S335_CLOSE_REPORT.md`
- `SANJEEVNI_SYSTEM_BOOK_v1_29_S335.md`
- `OWNER_TODO_LIVE.md`
- `SANJEEVNI_START_HERE_PROMPT_v1_1.md` · `END_OF_SESSION_PROMPT_v18.md` · `BUILD_NORM_v1.md`
- In project knowledge: `claude/S327_SANJEEVNI_RESTRUCTURING_PLAN.md`, `claude/S308_S486_CHARTER_REREAD.md`, `claude/S335_BUILD_BRIEF.md`, `claude/SANJEEVNI_SYSTEM_BOOK_v1_29_S335.md`
- The kits: `deploy_kits/S613_S605_FOLLOWUP/` (SUMS `a86bae32`), `deploy_kits/S618_SCAN_QUALITY/` (`622a4a82`), `deploy_kits/S619_ORDER_TRACKER/` (`617c5ea3`); their briefs (v2, the ones that ran) and reports in `claude_code_briefs/`.

The parent's: `START_HERE_SESSION_336.md` (its 336 open). The Scan App project's: `START_HERE_SESSION_337.md` (its 337 open since 14:07).

**Gate:** `md5sum -c MD5SUMS_ALL.txt` from inside `KB_canon_all`.

## 2 · FOR THE PARENT — one line each

- **The GST composition returns flow** — his steps in board message `sanjeevni_S335_1` (Marg's composition file → the quarter's sale amount → the GST portal → the challan from Sanjeevni's Yes Bank current account → the quarterly return by SMS OTP; the annual return within about a month after the year).
- **`/root/shared` is in no nightly code bundle** — `scan_quality.py` (S618) and `scan_checks_s441.py` need the bundle's list and the pin check.
- **`packs.py` moved 6ed8e18a → 94923368 at 09:29 IST 22-Oct** with a clinic-finance restart (seen by S618's gate; the parent's own change, recorded).
- **F-958:** one `.gitattributes` line (`deploy_kits/**/KIT_MANIFEST.txt -text`). `bank_sms.neft_portion_p` and negative payables (named). F-935 carried; `spine.db` in no backup (carried).

## 3 · NUMBERS

Board `_numbers` at this close: **D759 · F-989 · A-D25 · kit S624 · session 338 RESERVED for the Sanjeevni chat; 336 the parent's, open; 337 the Scan App chat's, open since 14:07; 339 next unreserved.**

*Written at the S335 close, 22-Oct-2026.*
