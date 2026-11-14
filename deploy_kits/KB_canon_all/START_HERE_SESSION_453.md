# START HERE — SESSION 453 — written at the S450 close (the parent), 13-Nov-2026 19:5x IST

**Project: Dr Manoj Clinic — Systems & Automation (the parent).** Open it in a fresh chat in this project, linked to manojz. *FIRST ACT: take session 453 from `board/_numbers` (RESERVED for the parent at the S450 close).* Counters at this close: **D969 · F-1378 · A-D37 · kit S821 · session 454.** `_numbers` costs about 70,000 tokens to read — send a helper; a single counter can be checked by an EMPTY query (A-D36).

1. Follow `OPEN_ROUTINE_v1` (from the clone). **The first device call is `cat` of the routine and NOTHING else (F-1312, F-1295, F-1353).** Then: does `echo ok` answer; how full is `/sessions` (builds run from `/tmp` with `TMPDIR=/tmp TZ=Asia/Kolkata`).
2. **THE S450 CLOSE IS HELD BEFORE THE BUILD — FINISH IT FIRST (§A).** If the canon already shows an S450 close, this is done.
3. Read `claude/SESSION_RECORD_S450.md` (project knowledge — the whole record) and the Runbook's §2A items 1–4.
4. **His words for this session:** 19:50 IST 13-Nov — the X-ray and blood-report plan "we will discuss it later in next session"; 19:55 "eos light" after the chat's advice that the loan-interest rule be the next session's first job (D968). **Build nothing of the X-ray plan before he has discussed it.**

## A · The held close — in order
1. **The canon as it stands:** the manifest's md5 (6671a77b at this close — this session's placing of the S447 close). **The Sanjeevni chat's S451 close is ALSO held**; if it has been placed first, re-base on it. Read `board/_numbers`' newest lines (a helper).
2. **Bring the papers to the PC:** copy `claude/SESSION_RECORD_S450.md`, `claude/S450_XRAY_LAB_FILING_STUDY.md` and `claude/S450_BUILD_BRIEF.md` into `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S450\` (the PC holds only an early copy of the record).
3. **Write the parts** into `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S450\close_parts\` in `close_build.py`'s shape — the model is `03_WORKING_PAPERS\S447\close_parts\` (11 files: `archive.md`, `brief.md`, `close.json`, `close_report.md`, `fault.md`, `man_narr.md`, `rb_section.md`, `reg_h1.md`, `reg_sections.md`, `start_here.md` = this file, `todo.md`) — from the session's record: D967, D968 · A-D36 · F-1372 … F-1377 · no kit placed, no pin moved, no live file changed (EOS-light). Versions: on top of Register v5.280 · Archive v1.277 · Fault v2.264 (§7.197) · Runbook v360 · `live_pins_S447close.txt`, unless the Sanjeevni close came first. The Runbook's file name takes the BUILD day's date.
4. **Build:** `cd /tmp && TMPDIR=/tmp TZ=Asia/Kolkata python3 -B $HOME/mnt/Downloads/_kbtools/close_build.py $HOME/mnt/Downloads/ClaudeCowork/03_WORKING_PAPERS/S450/close_parts/close.json` — read the table, fix any STOP in the parts, then the same line with `--place`.
5. **The board:** `_numbers` — the READY line; `_claude_status` — the parent's keys; **`_page`** (a helper; pinned; weighed first): Y330 done (the publish landed 18:11 IST 13-Nov) · Y331 done (he cleared the WhatsApp backlog — 0 awaiting, 31 Undo at 18:15) · **Y332 corrected** (address `https://followup.dr-manoj.in/finance/health`; the dates in the record's §7) · this close's lines · spot-check the Pharmacy and Scan app lines (F-1373).
6. **Project knowledge, by file:** the close report in; then `START_HERE_SESSION_450.md` out. The Runbook, the pin list and `OWNER_TODO_LIVE.md` stay out (A-D36) unless this close settles otherwise. The day's measure is owed.
7. **Name the publish to him, once:** `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat` on manojz.

## B · THE FIRST BUILD — kit S819_LEDGER_INTEREST_WITH_PRINCIPAL (number already taken; D963, D968; F-1367 — BEFORE NOVEMBER CLOSES, 1 December)
- **Look first** for the stopped builder's leftovers: `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S450\kit819\` (probably empty) — else start clean.
- **The file:** `/root/staff_ledger.py`, read WHOLE from the newest bundle (`D:\Downloads\_kbtools\vps_code\code_nightly.tar.gz`; 13-Nov: 85e2ab51a6a8e34e39cfcace20eac6be, 5,720 lines; check the pin still equals the bundle). The close's loan step ~:1462–1489 (`interest_due` at :1474); also every forecast / month-plan / statement function that predicts the month.
- **The rule:** no interest is taken, charged or capitalised on a loan in a month unless principal comes off the same loan that month. All or nothing: a month that cannot carry the whole instalment holds it whole — no interest, no penalty, the balance unchanged, the loan one month longer (as his April ruling). A month that can carry it behaves exactly as today; the last month closes the loan as today. Untouched: the owner's explicit skip / defer paths and their penalty rules (D250), the order of advances before the loan, interest-free advances, all stored data. The forecast for a held month shows the instalment returned on the private page and the loan standing.
- **The kit's shape:** as `deploy_kits/S614_LEDGER_ADVANCE_MAKEUP/` (also S612, S611, S609): the whole new file; an installer that refuses unless the live md5 is the FROM md5, backs up, `\cp`, `py_compile` with `/root/wa/venv/bin/python3`, restarts what S614 restarted, proves itself on a made-up root, rolls back on any failure. No staff name, no ledger figure, no number in the kit.
- **The proof (offline, old file against new, made-up ledgers):** salary left ≥ the instalment → identical · left < instalment but ≥ the interest → OLD takes interest alone (the CONTROL goes red on the old file), NEW takes nothing · left = 0 · the last month · an owner's skip and a deferred month → identical · interest-free only → identical · two months, the first held → the loan ends exactly one month later, interest paid once per month in which principal came off · each changed forecast equals what the close then does.
- Then a cold review by a second reader, placing, his publish and one server line; read live (numbers only).

## C · Then, in order
1. **The X-ray and blood-report plan — WITH HIM (D967; `claude/S450_XRAY_LAB_FILING_STUDY.md` §I).** Before the talk: read the code of the X-ray sorting page (`check_screens.py`, `records.py`), the slips desk (`slip_log.py` — the back-date search by ID only) and his X-ray sheet (`https://followup.dr-manoj.in/finance/slips/lists`) — it was NOT read at S450 (the link). Then one mock-up of the three screen changes; build only on his word. F-1372 (the notice's count) is settled by that plan's point 1.
2. **The mock-up of the two optional-deduction switches** on the staff member's private page (D963; his standing rule for salary pages).
3. **The three small kits** (D964): the Inbox line for a file MyOperator never sent (F-1358, F-1366) · the `wa-approve` service stopped and kept (F-1364) · `/root/portal/wa_awaiting.db` into the nightly backup (F-1365); then the second readers' notes (F-1368).
4. **The medical PC's set-up on the Clinic PCs page kept current** (the Sanjeevni chat's D966 to the parent; D803): the Wi-Fi dongle added, the front USB port dead.
5. **The ticket's material for MyOperator** (D938; nothing goes without him).
6. **Step 3 of the follow-up feed** — the tracker's move to the server (A-D29, D956; `S443_FOLLOWUP_FEED_PLAN.md`); the tracker's program folder is a per-session grant, asked in ONE request.

## D · At the open, also
- The day page and the 14-Nov bundle: the parent's DECLARED-PENDING 7 (`portal.py` 8f60b310, `calls_console.py` efd51956, `patient_sync_on_arrival.sh` 9b41c26f, `docterz_missing_alert.py` 9cc227e1 with three cron lines, `wa_ladder.py` c5e6a74c, `wa_ladder_send.py` d8f16f00, `portal_wa.py` 4b153e7d).
- S811_FEED_ON_ARRIVAL's first evening (13-Nov 21:45) and morning (14-Nov 08:15): did they log rightly — ask him for nothing.
- The three reads, numbers only, against S450's (the record's §2). Remind him of the packs page (D713) and BL Computers (F-1266, F-1268 — and now the medical PC's dead USB port).

**Standing rules:** as in `START_HERE_SESSION_450.md` and before, plus — **a probe never GROUPs BY a free-text column (F-1374)** · **a correction to a helper that is about to write a large document is sent BEFORE the helper is launched, not after (F-1373)** · **when the link to manojz is down, say so to him at once in one line and stop waiting on it; the cloud cannot read the repository (F-1376)**.

**Standing owner rulings:** as before, plus **D967** (the X-ray and lab filing: evening X-rays due the next afternoon; "Not in Docterz" = complimentary, not a payment gap; no new page; 9:30 am list and evening confirmation; the slips desk search by name; suggested patients for lab reports; WhatsApp not pursued — nothing built until discussed) · **D968** (the loan-interest rule first in this session).

*Written at the S450 close, 13-Nov-2026.*
