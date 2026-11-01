# START HERE — SESSION 374 — written at the S373 close (the parent), 01-Nov-2026

**Project: Dr Manoj Clinic — Systems & Automation (the parent).** Open in a fresh chat in this project, linked to manojz.
1. Follow `OPEN_ROUTINE_v1` (read it from the clone: `deploy_kits/KB_canon_all/OPEN_ROUTINE_v1.md`). The project's custom instructions are `COMMON_START_HERE_PROMPT_v1`.
2. **The first work: the open (§0 A); then HIS OCTOBER FINDINGS, discussed with him (§0 B) — he moved them to this chat ("we will discuss about them in a fresh chat in this project", 06:08 IST 01-Nov); then IPD kit 4 once he has answered the mock-up (§0 C).** If he names something else, take it.
   - The Runbook is v286 (§2A). The Register §S373 holds D813 (his own X-ray & procedures page); §S372 D810–D812.
   - The newest live module: `/root/finance/clinic_lists.py` 6118ef4d, mounted by `finance_app.py` 00cc4935; the tile in `portal.py` 4ff31351. Kit `deploy_kits/S689_CLINIC_LISTS/` (copy in `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S373\`).

*FIRST ACT: take your session number from the System Board `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).*
- **374 is RESERVED for the parent.** 369 (Sanjeevni) was open at this close; 363 (Scan App) and 365 (NK Pathology) reserved.
- At this close (board v834): **D814 · F-1068 · A-D25 · kit S690 · session 375 next.** **Kit S682 is already taken** for IPD kit 4 and PLANNED on `surgery_cases.py` 89a668a9 (30-Oct 15:05); the line goes stale on 6-Nov.

*Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.* The standing rules of `START_HERE_SESSION_357.md`'s connection list stand whole: never `git` in the device shell; every commit to the PC read back by hash; a published kit folder never changes.

***Every time you write is read first: the clock tool, a commit stamp, a file's time or a program's own line (F-510).***

**Learned this session (S373):**
- **The device VM's `/sessions` (home) can be full.** Work in `/tmp/<name>` (chmod 700) and delete it before the close.
- **A background job in the device shell dies when the call returns** (nohup, setsid, disown alike). Run each step inside one call (≤ 180 s); the S689 walk with 19 mutants ran in ~110 s, an install rehearsal in ~35 s.
- **A FROM file not yet in any bundle is rebuilt, never inferred:** `finance_app.py` 2f604fee was made from the bundle's bytes by S687's then S688's own make scripts, and its md5 matched the pin (F-472).
- **Match slips by their id, or by day + number + state='ok'.** Renumbered slips leave a void twin with the same number; a first list run gave wrong IDs that way, caught by a per-patient-day cross-check before he saw it.
- **A walk asserts on made-up rows only (F-1067).** A search check over real rows would have refused the install the day a real "Dilip" had a dressing.
- **Cold reviews still find real faults on a "small" page:** R1 found two (F-1065, F-1066), R3 one (F-1067). Review again after every fix round; stop at SAFE.
- **Patient lists go to his PC, never through the chat.** The chat carried masked IDs; the names went to `03_WORKING_PAPERS\S373\OWNER_LISTS_Oct2026.html`, made in the VM.

---

## 0 · THE WORK — in the owner's order

**A · THE OPEN (`OPEN_ROUTINE_v1`).**
1. **The board:** every note, every message with `read:false`. `parent_S373_1` is S373's handover of his findings to you — read it, then mark it read. **Remind him of the packs page (D713).**
2. **The day's checks:** `day_open.py` with the VM roots (Runbook v286 §2A item 1), if the page is not today's.
3. **The 02-Nov bundle against `live_pins_S373close.txt`:** three pins must match — `finance_app.py` 00cc4935 · `clinic_lists.py` 6118ef4d · `portal.py` 4ff31351; the parent's DECLARED-PENDING 5 then becomes 2. Any other change is a halt; re-read the file whole (F-472).
4. **The finance restore drill:** its first scheduled run (Sunday 1-Nov 02:10, S661) was not read at S373 — read its leg; stale = the first work.
5. **F-1064:** confirm `/tmp/s680root`, `/tmp/s370`, `/tmp/s369`, `/tmp/s683` gone from the device VM; then close it.
6. **The film log's first counts and the 16-vs-12 film bills** (S372's asks), read as manoj by a read-only sub-agent: `https://followup.dr-manoj.in/finance/slips/film/log`.
7. **On Monday 2-Nov:** the newest `claude/AUDIT_RUN_*` (slice 5) and its *For the builder* lines; the close answers each.
8. **The rest (first open of the day only):** project knowledge measured once, never-cited %, what no store holds; **the cold kit is DUE on 2-Nov** (7 days).

**B · HIS OCTOBER FINDINGS — discuss with him, build nothing without his word (Runbook v286 §2A item 2).**
- His lists with names: `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S373\OWNER_LISTS_Oct2026.html` (re-made by `03_WORKING_PAPERS\S373\owner_lists.py <fin code> <db copy> <out>` on a fresh VM copy if he wants November too).
- **a** Shavez's Paid/Done ticks stopped after 28-Oct 10:14 IST — 27 slips 26–31 Oct open; 22 X-ray slips and all 4 procedure slips equal Docterz exactly. **b** A likely double entry (29-Oct 1431/1432, …8380). **c** X-ray on the slip, only a consultation in Docterz (26-Oct 1419 …8362 ₹1,100; 31-Oct 1444 …6246 ₹500). **d** 31-Oct 1451 …8359 ₹1,000 vs Docterz ₹1,300. **e** 5 Docterz X-ray charges with no X-ray slip line (₹2,150). **f** His idea: an automatic Paid tick each morning when Docterz equals the slip — the analysis is in the Runbook item; the mode from the bank match, Done not from Docterz.
- Ask him what he wants done for each, in plain words, one at a time; a mock-up before any changed screen; a kit number only when he says build.

**C · IPD KIT 4: THE IMPLANT BILLS DESK, THE CHEQUE, THE VENDORS' LEDGER (D807; §2A item 3; kit S682).** His three answers first (asked 30-Oct, on `https://claude.ai/artifact/D4BQUWfNKqoXHt5uZBJmcw`); then build as `START_HERE_SESSION_373` §0 C said. Re-plan after 6-Nov.

**D · THEN, in order (Runbook v286 §2A):** the next kit on `clinic_lists.py` ("14 film" → "films"; a film-size control from the X-ray tab; open on the newest month with slips) · S688's three wording notes · the Hostinger kernel update when its fix is out · kit 5 when the hospital explains the credit heads (D808) · kit 6 · watch the month jobs and the film log · his three board items of 27-Oct · F-1031 · D786's first month · the rest.

**Owner-side, on his board:** the publish · his findings (this chat) · IPD kit 4's three answers · the home medicines list and the vehicle paper dates · the opening spare boxes · the packs page (shops and passwords) · Y106 · his IPD share % · the hospital's word on the credit heads (Y181) · from 1-Nov *Approve & save* · the Marg engineer's restore test · the SBI downloads · Raghav's Zerodha papers · Ranjeet's login · the reception PC's Windows · the Docterz report export · the arms licence in November.

**Standing owner rulings:** rules 1–51 of `START_HERE_SESSION_360.md`, 52–53 of `START_HERE_SESSION_368.md`, 54–56 of `START_HERE_SESSION_370.md`, 57–59 of `START_HERE_SESSION_371.md`, 60 of `START_HERE_SESSION_372.md` and 61–63 of `START_HERE_SESSION_373.md` stand whole. Added:

64. **His X-ray & procedures page (D813):** one page, his login alone, no staff page; Procedures and X-rays from 1-Oct with amounts; a search box across everything since 1-Oct; Docterz charges with no slip shown as "Docterz only"; a slip line not marked paid is listed and marked, never hidden; the tile in his Patients folder.

## 1 · THE CURRENT CANON — the manifest wins

| what | file |
|---|---|
| Register | `KB_Register_v5_206_S373close.md` (clone only, D550) |
| History Archive | `KB_History_Archive_v1_203_S373close.md` (§S373) |
| Fault → Action Register | `Fault_Action_Register_v2_190.md` (§7.124) |
| Runbook | `HANDOFF_RUNBOOK_2026-11-01_Session373close_v286.md` (**§2A the order**) |
| open / close / prompt | `OPEN_ROUTINE_v1.md` · `CLOSE_ROUTINE_v1.md` · `COMMON_START_HERE_PROMPT_v1.md` |
| live pins | `live_pins_S373close.txt` |
| build brief | `S373_BUILD_BRIEF.md` |
| numbers | System Board `board/_numbers`. At this close: **D814 · F-1068 · A-D25 · kit S690 · session 375 next; 374 RESERVED for the parent** |

*Written at the S373 close, 01-Nov-2026.*

---

## THE OTHER CHATS — a pointer, not a carried section

- **Sanjeevni (369 open):** `purchase_app.py` 2e1e9023 (their S683) is recorded CONFIRMED in the parent's S373 pin list. Their spine gate is still theirs (`parent_S371_1`).
- **The Scan App (363 reserved):** `xray_film.py` reads `/root/assetapp/assets.db` read-only; `clinic_lists.py` reads film sizes through `xray_film.studies` (finance.db). **NK Pathology (365 reserved):** unchanged.
- **For all:** `/root/finance/finance_app.py` is now 00cc4935 and `/root/portal/portal.py` 4ff31351. A chat touching them builds on these bytes.
