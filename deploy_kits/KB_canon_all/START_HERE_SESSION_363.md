# START HERE — SESSION 363 — written at the S355 close (the Scan App project), 28-Oct-2026

**Project: Scan App — Papers & Bills.** Open in a fresh chat in this project, on manojz. First run `OPEN_ROUTINE_v1.md` (the project's custom instructions are `COMMON_START_HERE_PROMPT_v1`), then this file.

**Where things stand.** Session 355 (05:28 IST 26-Oct → the owner's "EOS" at 11:56 IST 28-Oct) **built and installed two kits**, each read cold until SAFE and read live:
- **S670_PROCROOM_SMALL_POINTS_R2** (publish `f845e36e`, DONE 05:32 IST 28-Oct) — the reviews' small points on `procroom.py`: one pre-match rule at the month end (a retired product the scan holds is its own; a slip sent twice counted once), typed rates kept across *Its scan*, `proc_use.lkey` added to an old table. S656, the same bytes, was refused by its own walk (F-1032: a check counted Shavez's real saved slips) and is frozen, never installed.
- **S674_VARIETY_FLOW** (publish `0e3af4b7`, DONE 11:09 IST 28-Oct) — **D797**, the owner's flow ruled on the mock-up `S355_STATIONERY_FLOW_MOCKUP` (https://claude.ai/artifact/1MKKotFYVnaeYLCc1AmR7P, in `03_WORKING_PAPERS\S355\`): every Variety challan scanned from 28-10-2026 lands on his Stationery page and is sorted line by line (the product typed / picked / added; For Clinic or NK); clinic lines feed the clinic stock as before, NK lines an NK ledger kept apart; the supplier account with states; the monthly statement challan-wise; their bill joined, paid once. Shavez's `/stationery/sort` (Hinglish, no rate) while his desk is on. F-1040 (a read pin from a stale copy) refused the first server line; corrected in place.

```
https://followup.dr-manoj.in/scanapp/stationery
```

**What to read:** `S355_BUILD_BRIEF.md` (for him) · `SCANAPP_SYSTEM_BOOK_v12_S355.md` §19 · the kits' READMEs (`deploy_kits/S670_PROCROOM_SMALL_POINTS_R2/`, `S674_VARIETY_FLOW/` — each holds its undo line) · `BUILD_NORM_v1.md` · the Runbook v277 §2C.

**First act:** take your session number from the System Board `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).
- *Session numbers at this close:* **363 is RESERVED for the Scan App chat.** 360 the parent's (open), 362 the Sanjeevni chat's (reserved at its S361 close), 356 the NK Pathology chat's (open).
- *Counters at this close:* **D799 · F-1041 · A-D25 · kit S676 · session 364 next.**
- *A kit number is claimed before its scratch folder is named (F-831).*

**Working rules on manojz** (as START_HERE_SESSION_355, all carried): never `git` in `device_bash` (F-511, F-833) · `.gitignore` last-match-wins (F-832) · `SANJ_CONFIG_STORE` before the number gate (F-810) · a database copy only under the session's home, removed after (F-752) · builds in the chat (D765): the walks run in the cloud workspace on the bundle's code, never a patient file (D656), and on the server inside the installer · every kit read by an independent cold review before its publish is named (F-901); a fix round read again (F-1005) · a walk's rupees are made up and its rows carry every mark the live flow writes (F-185, S651 R1) · **a walk on a live copy assumes nothing about the live rows (F-1032)** · **after a kit of the same session moves a file, every later kit re-hashes its read pins from the newest bytes (F-472, F-1040)** · his browser: sub-agents read screens; a paper's scan never passes through the assistant's workspace (D656) · `procroom.py` and `scan_checks_s441.py` read the parent's `finance.db` read only; `stationery.py` reads the parent's `vendors` table read only.

***Every time you write is read first — the clock tool, a commit stamp, a file's time or a program's own line (F-791, F-510).***

---

## 0 · THE WORK — in the owner's order

**A · THE OPEN'S FIRST WORK — short.**

1. **Verify this close's publish landed:** `.git/logs/HEAD` = `refs/remotes/origin/main`, a commit later than `0e3af4b7` (11:00:33 IST 28-Oct); the S355 canon files present at the md5s the manifest names; the gate from inside `deploy_kits/KB_canon_all/`. If not landed, say so in one line and name `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`.
2. **The System Board:** every item with a `note`, every message with `read:false` — say how many. (At this close: 0 for this project; `sanjeevni_S359_1` answered — the Sonnet-vs-Haiku shadow trial on next month's pharmacy bills is this project's to run or drop in November, his spending line in view.)
3. **`day_open.py --read`** once a day (OPEN_ROUTINE_v1 §3).
4. **The pin pass on the 29-Oct bundle:** this project's DECLARED-PENDING 3 — `procroom.py` `e51c00a1e539c3d48fd92273beecc7b8`, `stationery.py` `3a22c6bb4d0aa41ca680a79967582e8c`, `sorting_desk.py` `35fdd6c53d04d0b5740aa0e56816d422`. State match / mismatch / not-in-bundle.
5. **The four numbers · what no store holds · the cold kit when due** (last: 26-Oct, this session's open).

**B · THE WORK ITSELF.**

1. **The Variety flow's first use, read live with him:** the first challan sorted on the page (B-0235 is before the start day — the desk, if he wants it); October's statement made (15 lines on 6 papers were ready at install), sent, their estimate joined with the rates. Variety's phone on Vendors (his) for the WhatsApp button.
2. **The procedure goods flow** — Yuvika's challans to the Procedure room on the same pattern (a supplier default at the scan; the lines matched on the desk's panel), **when he says**; a mock-up first.
3. **Recent scans by scan date** (D797's analysis) — a mock-up when he asks.
4. **S651's and S633's minor points** — only when a kit touches those files (Runbook §2C items 7).

**HIS, OPEN:** the publish of this close · Variety's phone on Vendors · settling with Variety (separate challans; billing against the statement) · the shelf counts (Y157) · the gloves box size (Y145) · the Surgiwear drape (Y146) · October's month-end photos · Y147, Y136, Y120, Y121.

**NEVER:** the Runbook v277 §2C's list, whole — above all: never count a line twice (one statement, paid once); never feed an NK line into the clinic's stock; never offer a listed supplier's bill or estimate to sort; never overwrite a group a person set on the desk; never show a rate on Shavez's screen; never pin from a stale copy; never let a walk assume the live rows.

**CLOSED BY HIS WORD — DO NOT RAISE AGAIN:** everything closed at the earlier closes · the mock-ups · gloves on an ILI and the ILI injections (D782) · the tiles are the parent's (D783) · the clearer duplicate (S651) · the Stationery tab stays under clinic consumables (D730; his 07:46 ruling) · NK scans do not go through the clinic's Stationery page (his 07:48 ruling).

**Standing owner rulings (restated):** publishing is his double-click · full paths always, URLs too, each in its own copy block · one line per command; `\cp` past the alias · token-lean, never at the cost of verification · plain English, short, one step at a time · IST only; a clock time is read · mask patient numbers; never print secrets; no number in the repository (F-185) · nothing live rebuilt without his OK · sub-agents read screens · do not hand him diagnostics or technical choices · when a screen is wrong, read its code first · a new staff screen is a mock-up first, installed switched off; when he edits a mock-up the build follows his edit line by line; when he says *final* (or *build*) the mock-up is the specification · staff flows friction-free · analysis first when he says *"do not build or code anything"* · every build follows `BUILD_NORM_v1` (D704) · his board carries only what needs him and what he should know · his own items are deferred unless urgent.

## 1 · THE CURRENT CANON — the manifest wins

| what | file |
|---|---|
| Register | `KB_Register_v5_197_S355close.md` (clone only) |
| History Archive | `KB_History_Archive_v1_194_S355close.md` (§S355) |
| Fault → Action Register | `Fault_Action_Register_v2_181.md` (§7.115 — F-1032, F-1040 minted and closed; F-1013 open) |
| Runbook | `HANDOFF_RUNBOOK_2026-10-28_Session355close_v277.md` (**§2C the order**) |
| open · close routine | `OPEN_ROUTINE_v1.md` · `CLOSE_ROUTINE_v1.md` (v18's rules stand) |
| build norm | `BUILD_NORM_v1.md` (D704) |
| live pins | `live_pins_S355close.txt` (this project's DECLARED-PENDING 3) |
| build brief | `S355_BUILD_BRIEF.md` |
| the project's record | `SCANAPP_SYSTEM_BOOK_v12_S355.md` |
| the kits | `deploy_kits/S670_PROCROOM_SMALL_POINTS_R2/` · `S674_VARIETY_FLOW/` (READMEs: the undo lines); `S656_PROCROOM_SMALL_POINTS/` frozen, never installed |
| numbers | System Board `board/_numbers` — at this close: **D799 · F-1041 · A-D25 · kit S676 · session 364 next; 363 RESERVED for the Scan App chat** |

*Written at the S355 close, 28-Oct-2026.*
