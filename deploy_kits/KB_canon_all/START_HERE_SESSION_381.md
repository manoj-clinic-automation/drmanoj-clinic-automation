# START HERE — SESSION 381 — written at the S379 close (the parent), 02-Nov-2026

**Project: Dr Manoj Clinic — Systems & Automation (the parent).** Open in a fresh chat in this project, linked to manojz.
1. Follow `OPEN_ROUTINE_v1` (read it from the clone: `deploy_kits/KB_canon_all/OPEN_ROUTINE_v1.md`). The project's custom instructions are `COMMON_START_HERE_PROMPT_v1`.
2. **The first work: S701 CALLS_R2 — the WhatsApps into each caller's timeline, the sanitised follow-up list, Call ke baad, Needs you (D819, D820; AF-36, AF-19).** The Runbook is v293 (§2A item 2 is the kit, item 3 the two after it). The spec stays the APPROVED mock-up v12; a mock-up of the WhatsApp rows on the same canvas before the build:

```
https://claude.ai/artifact/AwBDzfttkYPygGVcrQbTfD
```
   - The files, read whole from the newest bundle (`D:\Downloads\_kbtools\vps_code\code_nightly.tar.gz`, the 03-Nov one must CONFIRM S698's bytes): `/root/portal/calls_console.py` a0f58fec (NEW at S698 — the page; `build_people` / `call_item` / `person_state` are the places a WhatsApp item joins), `/root/wa/portal_console.py` 3317394c (the builder with the fold), `/root/portal/portal_inbox.py` (his Inbox, its store `/root/wa/wa_inbox/inbox.db`, read-only), `/root/portal/ring_outcome.py` 25a169bf (the Call-ke-baad list and the link store, read-only), the tracker's Followups tab (read by a script, never through the chat). The S698 kit's walk (`deploy_kits/S698_CALLS_R1/walk_s698.py`, 82 checks on made-up data) is the base to extend.
   - The papers: `claude/S377_CALL_CONSOLE_PLAN.md` (§2 Call ke baad, §4 the follow-up rule) and `claude/S378_WHATSAPP_ON_CONSOLE_PLAN.md` (§3A the timeline, §3 the five rules, §4A the staff section for S702).

*FIRST ACT: take your session number from the System Board `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).*
- **381 is RESERVED for the parent.** 380 (Sanjeevni), 363 (Scan App) and 365 (NK Pathology) reserved.
- At this close (board v882): **D823 · F-1096 · A-D25 · kit S701 · session 382 next.** Take kit S701 BEFORE the scratch folder is named (F-515; F-1094 this session).

*Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.* The standing rules of `START_HERE_SESSION_357.md`'s connection list stand whole: never `git` in the device shell; every commit to the PC read back by hash (F-1095 this session — a re-commit of the same path wrote older bytes; re-send by a fresh staged path); a published kit folder never changes (a correction is a new kit — S699, S700 this session).

***Every time you write is read first: the clock tool, a commit stamp, a file's time or a program's own line (F-510).***

**Learned this session (S379):**
- **Read the arithmetic, not only the symptom:** the doubled rows were the receiver computing a row number instead of reading the one the API wrote back. The trace on the box (99 pairs, all the same key) confirmed the code's story before the repair.
- **A repair that deletes and re-appends is simulated offline first, on a tab shaped like the real one** — the first two runs were refused by their own verify and restored (nothing lost); the third was simulated and verified. Build the pre-check into the plan, not only the verify into the apply.
- **The repository's number gate refuses any ten-digit run starting 6–9, made-up or not:** every made-up number in a kit is 5000000xxx.
- **The cold review earns its keep:** two blockers (a sort key crashing on a sentinel date; a number in a journal line) were in code the walk had passed.
- **The hook is never stopped for a repair** — a lost webhook event is worse than a messy row; the repair tolerates what arrives while it runs.

---

## 0 · THE WORK — in the owner's order

**A · THE OPEN (`OPEN_ROUTINE_v1`).** The board (every note, every unread message — ten were for other chats at S379; leave them). **Remind him of the packs page (D713).** The day page: re-run with the VM roots (Runbook v293 §2A item 1) after a publish or the 03-Nov bundle; the seven DECLARED-PENDING must CONFIRM. As manoj, read-only: the console's day count against the sheet's distinct calls once; the call-hook's journal (`v3.2`, no "no longer holds" line).

**B · S701 CALLS_R2 (Runbook v293 §2A item 2).** The WhatsApps into the timelines (his answer rules), the chip and the icons, the strip's figures, the Needs-you line; the follow-up list sanitised (one open row per patient; today · grace · overdue · lapsed; called-of per section per agent); the Call-ke-baad reading and the link store; the week's funnel completed (came to the clinic; old patient, new mobile); the two wording notes; AF-36 and the count-sanity leg. A mock-up on the canvas first; then a walk extending S698's, the control, the cold review, the rehearsal, his publish and one server line; then read live as manoj.

**C · THEN, in order (Runbook v293 §2A):** S702 (the Staff performance section) · S703 (Patients — a mock-up first) · the audit's ask 4 · watch S697, S691's first days, S682's first real case · F-1085 in the next month-page kit · the rest.

**Owner-side, on his board:** the publish · October's amber lines on The month · the film log's opening boxes · the packs page (shops and passwords) · Y106 · his IPD share % · the hospital's word on the credit heads (Y181) · the Marg engineer's restore test · the SBI downloads · Raghav's Zerodha papers · Ranjeet's login · the reception PC's Windows · the Docterz report export · the arms licence in November · his two answers (slip …1449; the wrist lines) · "clear it".

**Standing owner rulings:** rules 1–51 of `START_HERE_SESSION_360.md`, 52–53 of `START_HERE_SESSION_368.md`, 54–56 of `START_HERE_SESSION_370.md`, 57–59 of `START_HERE_SESSION_371.md`, 60 of `START_HERE_SESSION_372.md`, 61–63 of `START_HERE_SESSION_373.md`, 64 of `START_HERE_SESSION_374.md`, 65–67 of `START_HERE_SESSION_376.md`, 68 of `START_HERE_SESSION_377.md`, 69–70 of `START_HERE_SESSION_378.md` and 71 of `START_HERE_SESSION_379.md` stand whole. No new ruling this session.

## 1 · THE CURRENT CANON — the manifest wins

| what | file |
|---|---|
| Register | `KB_Register_v5_213_S379close.md` (clone only, D550) |
| History Archive | `KB_History_Archive_v1_210_S379close.md` (§S379) |
| Fault → Action Register | `Fault_Action_Register_v2_197.md` (§7.131) |
| Runbook | `HANDOFF_RUNBOOK_2026-11-02_Session379close_v293.md` (**§2A the order**) |
| open / close / prompt | `OPEN_ROUTINE_v1.md` · `CLOSE_ROUTINE_v1.md` · `COMMON_START_HERE_PROMPT_v1.md` |
| live pins | `live_pins_S379close.txt` |
| build brief | `S379_BUILD_BRIEF.md` |
| kits | `deploy_kits/S698_CALLS_R1/` (README, the walk, the make, the tools) · `S699_CALLS_TAB_REPAIR2/` · `S700_CALLS_TAB_REPAIR3/` |
| spec | the canvas v12 (above) · `claude/S377_CALL_CONSOLE_PLAN.md` · `claude/S378_WHATSAPP_ON_CONSOLE_PLAN.md` (project knowledge) |
| numbers | System Board `board/_numbers`. At this close: **D823 · F-1096 · A-D25 · kit S701 · session 382 next; 381 RESERVED for the parent** |

*Written at the S379 close, 02-Nov-2026.*

---

## THE OTHER CHATS — a pointer, not a carried section

- **Sanjeevni (380 reserved):** nothing of theirs written. Its S692–S695 six are CONFIRMED (S375 close).
- **The Scan App (363 reserved) · NK Pathology (365 reserved):** unchanged.
- **For all:** the Call_Durations tab of the Clinic Callback Tracker was rebuilt at 12:28 02-Nov (4,653 rows, every call once; the keys unchanged, the rows at new positions).
