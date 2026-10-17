# START HERE — SESSION 322 — written at the S316 close (the Sanjeevni chat), 17-Oct-2026

**Project: Sanjeevni — Pharmacy & Marg.** Open in a fresh chat in this project, on manojz.
1. Run `SANJEEVNI_START_HERE_PROMPT_v1_1`'s Phase 0 (the project's custom instructions) first, then this file.
2. **The work is §0 below — the dealers' ordering WhatsApp numbers first (the owner's ask of 16:48 IST 16-Oct), as a mock-up for him before any build.** The rulebook for every build is **the charter v1.1 — `claude/S307_BUILD_CHARTER_v1_1.md`** (builder's part `claude_code_briefs\SANJEEVNI_BUILD_CHARTER.md`, D707), beside the parent's `BUILD_NORM_v1.md` (D704).
3. The brief of this close is `S316_BUILD_BRIEF.md`; the Book is `SANJEEVNI_SYSTEM_BOOK_v1_20_S316.md` (§15K is this session).

No incident is open. At this close the parent's session 319, the Scan App chat's 318 and the Clinic & Growth chat's 321 were open (their entry points `START_HERE_SESSION_319.md`, `START_HERE_SESSION_318.md`, the Growth project's own).

*FIRST ACT: take your session number from the System Board's `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).*
- **322 is RESERVED for the Sanjeevni chat at this close.** Take it if the board still shows it reserved, otherwise what the board says, and say so in your first line.
- Kit numbers are claimed before the scratch folder is named (F-515). D and F numbers ride the close's one write unless a build needs one sooner.
- Read every PLANNED line on the board before touching a file it names (D646). This project has none standing at this close (S556 … S572 released).

*Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.*
- `device_bash` worked through S316 on all three. Never `git` there (F-511). **Drive `H:\My Drive\Clinic Data Archive\ToMedical\_kit` and `…\FromMedical\` are reached by the file tools only** (granted by the owner; the shell does not mount them). The medical PC's census and log are in `FromMedical\` (`marg_text_census.txt`, `marg_watch_log.txt`); its heartbeat is mirrored at `D:\Downloads\margsync\medical_SendToClinic\heartbeat.txt`.
- **A file sent with the transfer tool can arrive as its previous version when the same staged name is reused** (S303, S308): stage a new name, read the md5 back.
- The routine is `END_OF_SESSION_PROMPT_v18.md`.
- **THE API CREDITS ENDED 17-OCT (D727).** Unless the owner says the runner still has credit, a build goes back to the Claude Code paste line on manojz: *"Read claude_code_briefs/SANJEEVNI_BUILD_CHARTER.md first, then build, walk, install and publish kit S### exactly as claude_code_briefs/S###_NAME.md says, and write claude_code_briefs/REPORT_S###.md."* Check first with `python D:\Downloads\_kbtools\agent_build\run_build.py --check` (a call capped at $0.50) only if he asks for the runner. **Before giving any runner line, check that no other build is running** (the Scan App and the parent's chats share it: the logs in `D:\Downloads\_kbtools\agent_build\logs\`, and `/root/deploy/.claude_code_build.lock`).
- **The order of an install is fixed:** the brief → an independent read against the live bytes → the owner's ONE line, **naming the charter first** → the build, walk, install, publish and report → the chat reads the result live, **on the page the owner will read it on, before it says a word about it (F-724).**
- **The browser is signed in as the owner; a POST from it is refused by the permission layer.** Reads work; a write is his one tap.
- **The live bytes offline:** the newest bundle (`D:\Downloads\_kbtools\vps_code\code_nightly.tar.gz`) and database (`finance_nightly.db.gz`); extract them in the PC's own `/tmp`, never in a connected folder, and remove them after.

---

## 0 · THE WORK — in order

**A · THE OPEN'S FIRST WORK (v18)**

1. **Read the System Board before anything else:** every item document with a `note`, every message with `read:false`, and `board/_page`. Say in one line how many are waiting. At this close none was waiting for this project (one unread message, the parent's to the Scan App chat).
2. **Verify the S316 close's publish landed:**
   - `.git/logs/HEAD` = `refs/remotes/origin/main` (read, never `git`);
   - this close's canon files are in the tree at their hashes (Register v5.157, Archive v1.154, Fault v2.142, Runbook v237, this file, `S316_BUILD_BRIEF.md`, `S316_CLOSE_REPORT.md`, `live_pins_S316close.txt`, `SANJEEVNI_SYSTEM_BOOK_v1_20_S316.md`, the manifest, `OWNER_TODO_LIVE.md`, `MD5SUMS_ALL.txt`);
   - `md5sum -c MD5SUMS_ALL.txt` from inside `KB_canon_all`, with the count.
   If it has not landed, the owner has not double-clicked yet: say so, name the file, and read the canon from the PC's clone.
3. **The three nightly reports:** exists · clock time · verdict, each. F-384 (one CURRENT `START_HERE_SESSION` row per open project) is expected.
4. **The pin list against the newest bundle** (`live_pins_S316close.txt`, or a later one). **This project's DECLARED-PENDING at this close: 0** (every `/root` file of S543 … S570 equal to the 17-Oct bundle). State the three counts. The medical PC's `marg_watch.py` 39fa2773 and `marg_txt.py` a59a222f are read from its heartbeat, not the bundle.
5. **The SSD mirror · the sweep · the tranche and the measured `knowledge_size` · the cold kit when due · the four numbers · what no store holds** (known: `spine.db` and `/root/finance/spine/orders/order_score_latest.json` are in no code bundle).
6. **Read, live and read-only, what the night left:**
   - **Amir's card** (`/finance/stock/api/pad/amir/1` and his page): the four *Ek baar ke kaam* lines (KT ROS DT, VINBACTUM DS, FOLITRAX 15 MG TAB, OSTOVAXL DM) — ticked or not; then the hub's stage-C proof on the next closing (`/finance/stock/api/pad/hub/1`, `proof.C`) — these four corrections are judged on Marg's closings after his entries;
   - **the morning reports** — both taken (`/finance/reports/aaj`);
   - **the ordering page** as reception and as the owner — the heading, the two print buttons (a new address on every tap);
   - Darpan's spot count of ANKLE BINDER L BAMBOO (no record at the 13-Oct read).

**B · THE WORK ITSELF**

1. **THE DEALERS' ORDERING WHATSAPP NUMBERS — the owner's ask, 16:48 IST 16-Oct, verbatim:** *"Mark ordering of medicines, there is one issue that the WhatsApp some dealer want is not on the numbers which we already have, so they are giving a different number and staff is collecting those numbers. So a list where staff can add these numbers as the default WhatsApp number for ordering is required."*
   - **What is there now (read at S316, read again on the newest bundle first):** ordering's WhatsApp goes to the phone book's first number — `order_sheet._phones(con, vendor)[0]` (order_sheet.py, the WhatsApp line and the supplier cards), and `porders_s454.py`; the phone book (`purchase_vendor_contact`; page `https://followup.dr-manoj.in/finance/purchase/page/book`) is closed to staff (`_book_allowed`: the doctor and the logins named in a setting) because it carries bank accounts; the payment notices (`supplier_msg.py`) use the same first number.
   - **The design carried (show it as a MOCK-UP FIRST — his standing ruling for every staff screen; phone width; Roman Hindi; placeholder numbers only, never a real one):** one staff list *"Order ke WhatsApp number"* — dealer, its ordering WhatsApp number, who set it and when, *Badlein* / *Hatayein*; no bank field on it; reached from the ordering page (a *Number badlein* link beside each supplier's WhatsApp) and from reception's home. **Ordering uses this number first and falls back to the phone book's first number; the payment notices keep the phone book.** Every change audited (who, when, old → new) and listed for the owner. One number per dealer.
   - Then, on his OK: claim the kit, write the brief (it adds a staff duty only if he says so — DUTY_MAP rule), an independent read, his one line. Installed switched off; he turns it on.
2. **Rung 4b — stock on the spine** (the charter's step 4): one module for the Marg figure and the shelf figure; `stock_app.py` read whole (drift 9); the name-keyed `stock_snapshot` retired (F-862); the guard's renamed items read through identity (F-874); the spine's family-key miss (F-873); "never past the shelf figure" (D715 a's second half); F-841 with it.
3. **S486 Part A** (F-738, F-739, F-717, the fold) as its own kit; **S486 Part B** re-briefed on rung 4b's one stock function.
4. **Small, together:** `stockmatch` c2 and a held line (F-875); `amir_day`'s healthz tag (F-881); the five `reports.*` settings onto the owner's card; F-726 a; F-777; F-794.
5. **PARKED by his word (13:47 IST 16-Oct) — do not start unasked:** F-802's permanent fix — an unchanged Marg re-export re-confirms the day instead of being dropped as already taken. Until then, a re-export to re-confirm a day is made with that day's To-date.
6. **The close** — `END_OF_SESSION_PROMPT_v18.md`.

**NEVER RUN:** `deploy_kits\S488_DATES_AND_WAITS\deliver_S488.ps1`. **NEVER ADD TO:** Amir's *Aaj ka kaam* list (D690).

**A STAFF SCREEN CARRIES ONLY "DO THIS" LINES (D708) — AND A LINE ON IT RESTS ON A FACT NOBODY CAN TAP WRONGLY (D712).** **NO FIGURE TO TYPE, EVER (charter rule 8).** **The stock proof's verdict is the owner's line only; Amir's card gets only the Marg job.**

**A VOUCHER NEVER TAKES MARG BELOW ZERO; A SETTLED ITEM IS NEVER RAISED AGAIN (D715).** **A LINE LEAVES THE ORDER LIST ONLY WHEN MARG CLOSES IT (D716).**

**CLOSED BY HIS WORD — DO NOT RAISE AGAIN:**
- the orthotic names as Amir typed them (D709) — all 23 verified;
- the learnt names (D685);
- Kedar's July balance; the four appliances' category;
- the staff's *Aaj ka kaam* lists — the parent's;
- the bill line's design (D712) — built (S533, S536);
- NORTIMER TAB in the 6-Sep count — out (D715 b);
- the ordering flow — Marg's open order (S543), fresh prints (S561); nothing more unless he asks;
- A004143 and A004144 of 12-10 — paid by UPI;
- **"park claude vs sarvam for now"** (the Scan App chat's line, 15-Oct) — S565's sample is the record; no reading switch for medicine bills unless he asks.

**Standing owner rulings (restated):**

1. Publishing is his double-click — `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`.
2. Full paths always, URLs too, each in its own copy block.
3. Plain English, short; one step at a time; ALL-CAPS means urgent; IST only; a clock time is read, never estimated.
4. Mask patient numbers (last 4); never print secrets.
5. Nothing live is rebuilt without his OK; the manual path stays.
6. Do not hand him diagnostics or technical choices — decide, say it in one line, proceed. He weighs in on what he can SEE.
7. **Fix at the root, never by a staff step (F-907, re-earned 15-Oct);** everything a staff member does sits in that person's own portal.
8. A new staff screen is shown to him as a mock-up first and installed switched off; staff pages Roman Hindi, his English.
9. His approvals are few and arrive together; keep chat short.
10. **Every build follows the charter v1.1 (D707) and `BUILD_NORM_v1` (D704).**
11. **A staff screen carries only "do this" lines (D708); the staff are never asked to retype a name (D709); a staff line rests on the scan, not a tap (D712).**
12. **When he asks for an answer only — "check and report, don't build" — give the answer only.**
13. **"It goes in by itself" is said only after the retry path is read (F-893).**
14. **A report that "did not land" is diagnosed from the medical PC's census and log first (F-802, 16-Oct).**

## 1 · THE CURRENT CANON — the manifest wins

- `CANONICAL_MANIFEST.md` (S316 close)
- `KB_Register_v5_157_S316close.md`
- `KB_History_Archive_v1_154_S316close.md` (§S316)
- `Fault_Action_Register_v2_142.md` (§7.76: F-905 … F-907)
- `HANDOFF_RUNBOOK_2026-10-17_Session316close_v237.md` (§2B is this project's)
- `live_pins_S316close.txt`
- `S316_BUILD_BRIEF.md` · `S316_CLOSE_REPORT.md`
- `SANJEEVNI_SYSTEM_BOOK_v1_20_S316.md`
- `OWNER_TODO_LIVE.md`
- `SANJEEVNI_START_HERE_PROMPT_v1_1.md` · `END_OF_SESSION_PROMPT_v18.md` · `BUILD_NORM_v1.md`

The parent's: `START_HERE_SESSION_319.md`. The Scan App project's: `START_HERE_SESSION_318.md`.

**Gate:** `md5sum -c MD5SUMS_ALL.txt` from inside `KB_canon_all`.

## 2 · FOR THE PARENT — one line each

- `deploy_kits/PC_KITS/medical/kit.zip` (S526) carries `marg_txt.py` S490 and `marg_watch.py` S488; the medical PC runs `marg_txt.py` S546 `a59a222f` and `marg_watch.py` S556 `39fa2773`.
- `D:\dr-manoj-git\drmanoj-clinic-automation\_scratch\` grew +5,941 files in a day (the nightly of 17-Oct) — the runner's walks (this project's S56x kits among them; the Scan App chat's browser profiles named by the parent at 06:32 16-Oct).
- Carried: F-879 (a pull waits on the build lock); F-880 (`aaj_seed.py`'s voucher SQL; `amir.arrival_bill_entry`); `canon_sums.py`'s F-384 allowance.

## 3 · NUMBERS

Board `_numbers` at this close: **D731 · F-908 · A-D25 · kit S573 · session 322 RESERVED for the Sanjeevni chat; 319 the parent's, 318 the Scan App chat's and 321 the Clinic & Growth chat's open; 323 next unreserved.**

*Written at the S316 close, 17-Oct-2026.*
