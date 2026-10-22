# START HERE — SESSION 341 — written at the S337 close (the Scan App project), 22-Oct-2026

**Project: Scan App — Papers & Bills.** Open in a fresh chat in this project, on manojz. First run `SCANAPP_START_HERE_PROMPT_v1`'s Phase 0 (the project's custom instructions), then this file.

**Where things stand.** Session 337 (14:07 → 19:52 IST 22-Oct) put four kits live, **every one built in the chat — no API runner (D765: *"Do not use API for this, because I feel the API have been pretty well exhausted by now"*)**:
- **S623** — the six Variety challans as stationery received history (D756); A4 21, DC-217 3, X-ray envelope 500, Token 1; the nine counted stocks unchanged;
- **S624** — a battery past its warranty says *Out of warranty since …* (F-977); a machine's cover / part gets its paper afterwards by a link box (F-978); packets-of-N lines questioned (F-979);
- **S625** — the machine Edit form keeps its day (F-976); a bill dated in an earlier month counts in its own month, for papers scanned from 15:2x IST 22-Oct (F-980, **his ruling D764**);
- **S627** — the *late* mark follows that rule; the desk states it.

He also had **B-0203 linked** as the FDR machine's AMC cover paper, and **deleted asset 7** himself (a duplicate of asset 6).

**What to read:** `S337_BUILD_BRIEF.md` (for him) · `SCANAPP_SYSTEM_BOOK_v7_S337.md` (§14 is new) · `BUILD_NORM_v1.md` · the Runbook v257 (§2C, §1L) · the four kits in `deploy_kits\` (S623, S624, S625, S627), above all their `walk_*_app.py` — **the real scan app can be loaded in the chat's own workspace** (§14.6 of the Book says how: `asset_register.py` at its live byte, the six parts, a made-up database, Flask's test client), and each kit's installer runs the same walk on a COPY of the live database on the box.

The close routine is `END_OF_SESSION_PROMPT_v18.md`.

**First act:** take your session number from the System Board `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).
- *Session numbers at this close:* **341 is RESERVED for the Scan App chat.** 340 is RESERVED for the Sanjeevni chat (its S339 closed 19:54 IST); 336 the parent's (open).
- *Counters at this close:* **D767 · F-1003 · A-D25 · kit S632 · session 342 next.**
- *A kit number is claimed before its scratch folder is named (F-831); the other chats take kit numbers fast (S626 went to the Sanjeevni chat between two of this chat's reads).*

**Working rules on manojz:**
- Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.
- **Never run `git` in `device_bash` (F-511, F-833)** — read `.git/logs/HEAD` and the refs.
- A `.gitignore` check is last-match-wins (F-832).
- Set `SANJ_CONFIG_STORE=$HOME/mnt/Downloads/margsync/_config` before the number gate (F-810).
- Open the bundle or a database copy only under the session's own home, and remove it after (F-752).
- A file sent to the PC is proven by its md5 read there (F-900, F-963).
- **Builds in the chat (D765)** — and every kit still gets an independent cold review (a sub-agent of the chat, given the code, not the conclusion) before its publish is named (F-901).
- **A health probe names a route the changed file itself registers, and the service log is read for "NOT mounted" (F-1001).**

***Every time you write is read first — the clock tool, a commit stamp, a file's time or a program's own line (F-791, F-510).***

---

## 0 · THE WORK — in the owner's order

**A · THE OPEN'S FIRST WORK — short.**

1. **Verify this close's publish landed (A16b) — the first act after the board.** `.git/logs/HEAD` = `refs/remotes/origin/main`, a commit later than `6d60fade` (16:19:18 IST 22-Oct, S627's); the S337 canon files present at the md5s the manifest names; `md5sum -c MD5SUMS_ALL.txt` inside `deploy_kits/KB_canon_all/`, the count stated. If it has not landed, say so in one line and name:

```
D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat
```

2. **The System Board:** every item with a `note`, every message with `read:false` — say how many. Two messages are this project's and on the list (§0 B 4).
3. **The three nightly reports** — exists · clock time · verdict (`D:\Downloads\_kbtools\REBUILD_REPORT_LATEST.txt`, `MAINTENANCE_REPORT_LATEST.txt`, `CANON_SUMS_LATEST.txt`).
4. **The pin pass on the newest bundle** (`D:\Downloads\_kbtools\vps_code\code_nightly.tar.gz`, self-checking) with `live_pins_S337close.txt`. **This project's DECLARED-PENDING is 6** — `batteries.py` b2cbb41e, `asset_machine.py` 7dbd5e0c, `stationery.py` b6ce217a, `clinic_papers.py` 89a3cd0a, `asset_register.py` 2bb28600, `sorting_desk.py` 377adbca — the 23-Oct bundle should carry all six. State match / mismatch / not-in-bundle.
5. **The rest of the open's work:** the SSD mirror listed back · the sweep (nothing named for `_to_delete_S337\`; `03_WORKING_PAPERS\S337\` holds two code tarballs and a rebuilt `asset_register.py` used for reading — leave them) · the tranche and the measure (`project_info` at the open and the close only) · **the cold kit — due** (the Register and Archive bumped) · the four numbers (drift: `asset_register.py` 1, `sorting_desk.py` 1 — both read whole today) · what no store holds.

**B · THE WORK ITSELF.**

1. **THE BATTERY PAGE MADE CLEAN — D766, the owner's words of 19:52 IST 22-Oct:** *"in a fresh chat with this project, thoroughly analyze the battery page by using your browser to log in there. Find all issues and errors and rectify them to give me a clean battery page which has all the relevant scans and fields filled in properly."* And at 19:51: *"I feel all such extra useless data needs to be deleted, and the page and all its content should be made relevant."*
   - **The page:**

```
https://followup.dr-manoj.in/scanapp/batteries
```

   - **How:** the built-in browser (his logged-in session, as owner) — sub-agents read the screens, the main chat reads page TEXT and the app's own GET JSON, never screenshots. **When a screen is wrong, read its code first** (`batteries.py` at b2cbb41e, the 23-Oct bundle). Read every place, its current fitting and every older one, each fitting's bill and card links, the warranty months, Ah / set / brand, the payer, the supplier, the machine link, the X-ray mark, the reminders on Renewals.
   - **Then make a list in plain words of every issue found** — an empty field that a scanned paper on the desk can fill; a bill or card scanned but not linked; a place with no fitting; a duplicate or useless record; a wrong payer; a date that is a placeholder; a badge that is wrong; anything the page shows that is not relevant. **Fix what is data through the page's own doors in his browser** (the forms the page offers — each is an owner action he asked for: D766); **anything that needs code is a kit** (claimed, built in the chat, reviewed cold, his publish and one server line). **Never guess:** a value no paper or record shows is asked of him in ONE short list at the end, in words he can see (F-1002 — no shorthand).
   - **His question of 19:51, answer it inside this job:** *"should I delete asset number 12 if there are no other such duplicates or issues?"* — asset 12 is the retired duplicate battery record (Jasoria Brothers set, ₹23,000, July 2026, retired 18-10). Check the machine list for every duplicate (same serial, same name + supplier + date), say plainly which are duplicates and which record each duplicates, and tell him which to delete (deleting is his, through the page's own Delete — or by his word, through his browser). Asset 7 he deleted himself at 19:5x (asset 6 stands).
   - **Facts to start from (S323/S337):** 16 places; 14 fitted, Vento and the DTH lab open (Y120 of S323); *Reception PC* → *Medical PC*, *Second PC* → *Lab PC*; *X-ray detector (FDR) battery* added; the Digital X-ray set of 8 fitted 28-04-2026; NK Pathology and the DTH lab sets of 3; B-0204 (Shail Healthcare's battery invoice, August) linked to the FDR battery fitting; the Lab analysers and the Home DVR + router now *Out of warranty*; the online UPS ask *How many batteries? — set*; B.L. Computers' UPS batteries come with a 1-year warranty and the bill comes late.
2. **His open question (F-1002, asked once, in these words):** *"A bill dated July but scanned in October now counts in July by itself. If someone picks October on that bill's own page because they want it counted in October, it stays in July. Is that fine, or should picking the scan month keep it there?"* — a yes needs nothing; a no is a one-line change in `clinic_papers.MONTH_OF`'s second test (a kit).
3. **The next scan-app round (seen, not built — offer in plain words, one line each):** the X-ray page does not net Jasoria's old-battery amount · B-0163 adds Rs 0 until its bill comes · the sorting desk's challan pre-tick and amber now follow the bill's month (S625 at work — watch the first month) · `misread_date` allows 400 days, the month rule 12 months.
4. **For this project, from the other chats (on the board, unread → read at this close):**
   - `sanjeevni_S332_1` (19-Oct): the handwritten challans of the clinic lanes are to be read by Claude too (*"it is a part of the scan app project"*) — the scan app's own backlog;
   - `sanjeevni_S339_1` (22-Oct 18:41): **D761's rule for this project's files** — when two scans are one paper, KEEP THE CLEARER ONE (the scan with item lines over one with none), in `asset_register.py` `_mark_dup` and `/root/shared/scan_checks_s441.py` `answer()`; never swap when the kept scan is linked to a Marg bill, approved, has joined pages or is a rescan; move the `scan_check_s441` verdicts with it. The case: Kedar A000211 — B-0157 kept, B-0159 set aside. A scan-app kit; PLANNED line first.

**HIS, OPEN:**
- **Y128** — the publish of this close (the file above).
- **Y119** (S323) — *Many items on one screen* ON when he is happy with it (the card at the top of `https://followup.dr-manoj.in/scanapp/stationery`).
- **Y120** (S323) — the Vento's and the DTH lab's battery dates — **folds into B 1.**
- **Y121** (S323) — scan Fujifilm's GST tax invoice for the FDR AMC when it comes.
- Not urgent: the remaining *Switches* taps for Shavez; Y83.

**NEVER:**
- guess a section, a sub-section, a value or whose expense a paper is (D664); tick a machine or battery place for X-ray by the system;
- move a paper a person placed, including by linking it to a battery, a stationery line or an X-ray mark;
- edit `scanner_widget.js` without a PLANNED line and the seven surfaces walked (D646);
- install a staff screen switched on;
- put a vehicle registration, a phone, serial or account number, or a vendor's figure into the repository (F-185);
- print, paste or ask for an API key in the chat;
- send a patient's file through the assistant's workspace (D656);
- delete anything that is not his to delete — deleting is his (by his word, through his browser or his line);
- hand him a diagnostic, a technical choice, or a question in shorthand (F-1002).

**CLOSED BY HIS WORD — DO NOT RAISE AGAIN:** everything closed at S318 and S323 · **D756** (S623 live) · **D764** (a bill counts in its own month — live) · **D765** (builds in the chat while the credits are low) · the Claude-vs-Sarvam comparison (parked).

**Standing owner rulings (restated):**

1. Publishing is his double-click — `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`.
2. Full paths always, URLs too, each in its own copy block.
3. One line per command; `\cp` past the alias. A server line carries its own pull: `cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/<KIT>/<installer>.sh`.
4. Token-lean, never at the cost of verification.
5. Plain English, short, one step at a time, full-file replacements, ALL-CAPS = urgent. IST only; a clock time is read, never estimated.
6. Mask patient numbers (last 4); never print secrets; no number of any kind in the repository (F-185).
7. Nothing live is rebuilt without his OK; the manual path stays.
8. Sub-agents read screens; screenshots never enter the main conversation.
9. Do not hand him diagnostics or technical choices — decide, say it in one line, proceed. He weighs in on what he can SEE.
10. When a screen is wrong, read its code first.
11. Do not hand him a step that is not his.
12. A new staff screen is shown to him as a mock-up first and installed switched off; staff pages in Roman Hinglish, his in English.
13. Staff flows are friction-free: no waiting on the server, no second tap.
14. Analysis first when he says so, then the build at his word.
15. His approvals are few and arrive together (D683).
16. Every build follows `BUILD_NORM_v1` (D704); patient files never pass through the assistant's workspace (D656).
17. **Builds are made in the chat while the API credits are low (D765)**; before an install line, check that no other build holds the server lock.
18. Every kit is read by an independent cold review before its publish is named; a fix round revises the same kit in place (F-901).
19. A kit is finished when he can reach it from where he starts, at his screen's size (F-898).
20. His board carries only what needs him and what he should know; every close answers what he typed there (D526, D684).
21. His own items are deferred unless urgent.

## 1 · THE CURRENT CANON — the manifest wins

| what | file |
|---|---|
| Register | `KB_Register_v5_177_S337close.md` (clone only) |
| History Archive | `KB_History_Archive_v1_174_S337close.md` (§S337; D764, D765, D766 in full) |
| Fault → Action Register | `Fault_Action_Register_v2_162.md` (§7.96 = F-1001, F-1002; F-976 … F-980 REPAIRED) |
| Runbook | `HANDOFF_RUNBOOK_2026-10-22_Session337close_v257.md` (**§2C the order; §1L where things are**) |
| close routine | `END_OF_SESSION_PROMPT_v18.md` |
| build norm | `BUILD_NORM_v1.md` (D704) |
| live pins | `live_pins_S337close.txt` (this project's DECLARED-PENDING 6) |
| build brief | `S337_BUILD_BRIEF.md` |
| the project's record | `SCANAPP_SYSTEM_BOOK_v7_S337.md` |
| numbers | System Board `board/_numbers` — at this close: **D767 · F-1003 · A-D25 · kit S632 · session 342 next; 341 RESERVED for the Scan App chat** |

*Written at the S337 close, 22-Oct-2026.*
