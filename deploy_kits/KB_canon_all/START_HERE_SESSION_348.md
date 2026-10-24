# START HERE — SESSION 348 — written at the S344 close (the Sanjeevni chat), 24-Oct-2026

**Project: Sanjeevni — Pharmacy & Marg.** Open in a fresh chat in this project, on manojz.
1. Run `SANJEEVNI_START_HERE_PROMPT_v1_1`'s Phase 0 (the project's custom instructions) first, then this file.
2. The rulebook for every build is **the charter v1.1 — `claude/S307_BUILD_CHARTER_v1_1.md`** (builder's part `claude_code_briefs\SANJEEVNI_BUILD_CHARTER.md`, D707), beside the parent's `BUILD_NORM_v1.md` (D704). **The plan of work is `claude/S327_SANJEEVNI_RESTRUCTURING_PLAN.md`.**
3. The brief of this close is `S344_BUILD_BRIEF.md` — **its Part B adds D777 to `S340_BUILD_BRIEF.md` Part B; together they are the specification of the next build**; the Book is `SANJEEVNI_SYSTEM_BOOK_v1_33_S344.md` (§15X is S344, §15W is S340); the four real Marg files of 23-Oct and the owner's seventeen screenshots are in `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S340\`; this session's papers in `…\S344\`.

No incident is open. **F-1016 is repaired for now** (the owner's enable in "user", 15:35 IST 24-Oct) — read it at the open (§0 A 5). The parent's 347 is **reserved** (its S343 closed 20:5x IST 24-Oct); the Scan App chat's 346 is **open** (since 20:47 IST 24-Oct; its S345 closed 20:42, kit S634 live).

*FIRST ACT: take your session number from the System Board's `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).*
- **348 is RESERVED for the Sanjeevni chat at this close.** Take it if the board still shows it reserved, otherwise what the board says, and say so in your first line.
- Kit numbers are claimed before the scratch folder is named (F-515). D and F numbers are taken the moment they are minted (F-920, F-934).
- Read every PLANNED line on the board before touching a file it names (D646).

*Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.* Never `git` there (F-511). The routine is `END_OF_SESSION_PROMPT_v18.md`. **Build road: in the chat itself** (the owner's word). **What S339 learnt about building offline (keep it):** the live code = the newest bundle + the pending kits' `make_*.py` in order (none pending at this close); the spine = `spine_evidence.py --source <MargArchive copy>` then `spine_build.py` (needs `xlrd`), from a tar of `D:\Downloads\margsync\MargArchive` staged into the workspace; the real finance app renders offline with the bundle's `/root/portal` plus the repository's `launcher/clinic_users.py`. **A walk's controls stand on its OWN rows (F-998).** **Read a captured Marg text's title before printing any row of it — a sales report carries patients (F-1010).**

---

## 0 · THE WORK — in order

**A · THE OPEN'S FIRST WORK (v18)**

1. **Read the System Board** — every message with `read:false`, every v2-page line with a note, and `board/_page`. Say in one line how many are waiting for this project.
2. **Verify the S344 close's publish landed:** `.git/logs/HEAD` = `refs/remotes/origin/main` (read, never `git`), a commit later than `4c275c7` (09:14:47 IST 23-Oct); this close's canon at its hashes (Register v5.184, Archive v1.181, Fault v2.168, Runbook v264, this file, `S344_BUILD_BRIEF.md`, `S344_CLOSE_REPORT.md`, `live_pins_S344close.txt`, `SANJEEVNI_SYSTEM_BOOK_v1_33_S344.md`, the manifest, `OWNER_TODO_LIVE.md`, `MD5SUMS_ALL.txt`); `md5sum -c MD5SUMS_ALL.txt` from inside `KB_canon_all`, with the count. If not landed, name `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat` and read canon from the PC's clone.
3. **The three nightly reports:** exists · clock time · verdict. F-384 (more than one CURRENT `START_HERE_SESSION` row while three projects are open) is expected.
4. **The pin pass on the newest bundle** (`D:\Downloads\_kbtools\vps_code\code_nightly.tar.gz`, self-checking) with `live_pins_S344close.txt`. **This project's DECLARED-PENDING at this close: 0.** State the three counts: match · declared-pending · unexplained.
5. **F-1016 — the medical agent in "user":** `D:\Downloads\margsync\medical_SendToClinic\agent_guard.log` (a `[user]` guard running the agent after a restart), `marg_watch.log` / `push.log` (the morning pair and Darpan's order sheet CAPTURED and TAKEN), the census. If the booked Monday read already reported, cite it. Also: the two unconfirmed September messages (A.A. PHARMACEUTICALS, DEEPAM PHARMA) — `supplier_msg` in the newest database copy.
6. **The one name list and the carries** — `med_name` by kind and state in the newest `finance_nightly.db.gz` (an `ask` row is the owner's question); LINVIZ 600 (7 strips of 10 — F-1000 declined, reception corrects it), C2CALZ, FLACORT 6, XGESIC LA; whether any rode an order made after 22-Oct.
7. **The witness week after F-951** — the newest `stock_figure_witness_<Day>.txt` (in the bundle under `/root/finance/spine/`).
8. **The SSD mirror · the sweep · the tranche and the measured `knowledge_size` · the cold kit when due · the four numbers · what no store holds** (known: `spine.db`, `order_score_latest.json`).

**B · THE WORK**

1. **D771 + D777 — the expiry, near-expiry, wrong-batch and dump flow, widened (dump in two parts: orthotics, medicines · new products this month · out of stock — waiting / arrived again), with F-1014, F-1015, F-1016's permanent half and Shivani's tile (D778) riding along. THE MOCK-UP FIRST** (the owner, 05:19: *"a very simple system to follow, build and execute … multiple refinement sessions … I do not want for this part"*): the owner's English page (four sections), Darpan's one line, Amir's one line and the monthly export card (the how-to from the screenshots, D772). Show it; on his yes, **one kit**, read-only, tested on the four real files of 23-Oct, with the proof that every item's stock figure is unchanged with the report present. The specification is `S340_BUILD_BRIEF.md` Part B plus `S344_BUILD_BRIEF.md` Part B. It closes F-1008, F-1009, F-1014 (an SMS-seen NEFT had no path to the messages), F-1015 (the late card's names) and F-1016 (the agent started with the PC). **Before 1-Nov** the owner holds REEBORN D, RIFAVAX 550, VOM L; before 1-Dec INTACOXIA-60 — say so if the build is not live by then.
2. **Kit II — S486 B, the buying model** (`order.model = fixed | levels`, default `fixed`; scored in shadow). K4 only by his word.
3. **F-987**; the purchase page's `staff_send`; `order.lead_days`; the S335 small list.
4. **PARKED by his word — do not start unasked:** F-802's permanent fix.
5. **The close** — `END_OF_SESSION_PROMPT_v18.md`.

**NEVER RUN:** `deploy_kits\S488_DATES_AND_WAITS\deliver_S488.ps1`. **NEVER ADD TO:** Amir's *Aaj ka kaam* list (D690).

**A STAFF SCREEN CARRIES ONLY "DO THIS" LINES (D708) — AND A LINE ON IT RESTS ON A FACT NOBODY CAN TAP WRONGLY (D712) — THE ONE RULED EXCEPTION: RECEPTION'S YUVIKA CARD WAITS ON DARPAN'S हाँ (D749).** **NO FIGURE TO TYPE, EVER (charter rule 8).** **THE STOCK PROOF'S VERDICT IS THE OWNER'S LINE ONLY.** **A VOUCHER NEVER TAKES MARG BELOW ZERO OR PAST THE SHELF FIGURE; A SETTLED ITEM IS NEVER RAISED AGAIN (D715).** **A LINE LEAVES THE ORDER LIST ONLY WHEN MARG CLOSES IT (D716) — AND A MEDICINE THAT DID NOT COME GOES ON THE DEALER'S NEXT ORDER BY ITSELF (D757) — A SUBSTITUTE NEVER CLOSES A LINE BY ITSELF (D760).** **A RESCAN KEEPS ITS OWN NEW NUMBER (D759).** **ONLY THE OWNER CHANGES A DEALER'S NUMBER; ONE RECORD PER DEALER (D731).** **A CLOSING TAKEN BEFORE THE DAY'S FIRST SALE IS THE START OF THAT DAY, ONCE VERIFIED ITEM BY ITEM (D740).** **CLAUDE READS THE PHARMACY BILLS; SARVAM IS OFF BY HIS SETTING (D747).** **DARPAN'S TAB CARRIES THE PURCHASE CUT-OFF LINE, NO STOCK-DAY LINE (D746).** **THE PAY PAGE ASKS FOR THE MONTH'S THREE REPORTS AS TEXT AND CONFIRMS EACH; THE LOCK WAITS FOR THEM AND AN AGREEING CROSS-CHECK (D748).** **ONE WHATSAPP PER ORDER (S605).** **ONE ORDER LIST FOR FOUR PEOPLE (D757).** **EVERY PHARMACY SCAN UPRIGHT; THE OWNER AND SHAVEZ SEND A SCAN BACK, RECEPTION RESCANS (D758).** **AMIR'S MONTH PACK STAYS UNTIL THE NEXT MONTH'S IS READY (S626).** **A MARG PACK CHANGE IS A NEW ITEM; THE OLD SOLD FIRST, THEN ZZ (D763).** **THE BATCH STOCK EXPORT IS NEVER THE CLOSING STOCK; THE EXPIRY FLOW IS ONE EXPORT, ONE LIST, ONE READ-ONLY BUILD (D771) — ORTHOTICS APART IN THE DUMP (D777).** **THE MORNING REPORTS: SHAVEZ, AND SHIVANI WHEN HE IS AWAY; THE PAGE COUNTS THE DAY, NOT THE PERSON (D778).**

**CLOSED BY HIS WORD — DO NOT RAISE AGAIN:** the pack-change build (F-1000, "no", 04:07 23-Oct); the rescan's number (D759); the orthotic names as Amir typed them (D709); the learnt names (D685); Kedar's July balance; the four appliances' category; the staff's *Aaj ka kaam* lists — the parent's; the bill line's design (D712); NORTIMER TAB in the 6-Sep count (D715 b); the GST composition flow — the parent's; older purchase bills (Apr–Aug) for the name list (D762); a reader for the bank's alert e-mails (D779, "No").

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
