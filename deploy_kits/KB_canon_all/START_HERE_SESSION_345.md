# START HERE — SESSION 345 — written at the S342 close (the Scan App project), 23-Oct-2026

**Project: Scan App — Papers & Bills.** Open in a fresh chat in this project, on manojz. First run `SCANAPP_START_HERE_PROMPT_v1`'s Phase 0 (the project's custom instructions), then this file.

**Where things stand.** Session 342 (04:39 → the owner's "do EOS here" at 06:36 IST 23-Oct) **built nothing and touched no live file** — at his word it reviewed and planned the procedure-room goods whole:
- **D773 — the plan:** one product list (his: add / rename / retire / rarely used; named by what and size; brands on the line; aliases) and the Drive sheet's names made the same · every slip line in its own place (procedure room · home use · clinic equipment · OT · Sanjeevni orthotics, flagged) · order → delivery → entry (his signed duplicate-book order scanned and joined to Yuvika's estimate; the system fills, he corrects) · **rates his only**, from Yuvika's month-end WhatsApp, matched slip by slip with flags (not scanned · quantity differs · rate changed) and the month's total · history from April 2026 from his photos (expense only) · default allowances he edits · a month-end rough match for shared goods · his page by product, month and financial year;
- **D774 — Awdhesh's room work moves to Shavez:** the procedures done are the slips confirmed by the EMR (Docterz procedure billing); Shavez enters each one's consumables next morning, pre-filled with the procedure's usual kit;
- **F-1011** the consumables were named on the procedures page (D373) but no use was ever recorded · **F-1012** slips not all scanned (September 2 of 5; none of April–August) and handwritten quantities misread · **F-1013** orthotics on clinic slips (the Sanjeevni chat told).

**What to read:** `S342_BUILD_BRIEF.md` (for him) · **`D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S342\S342_PROCEDURE_ROOM_PLAN.md`** (the item table A, the five months of Yuvika's slips B with the rates, the plan C, what the code says D — **the owner's figures: never into the repository**) · the photos `03_WORKING_PAPERS\S342\yuvika_whatsapp\` · `SCANAPP_SYSTEM_BOOK_v8_S341.md` · `BUILD_NORM_v1.md` · the Runbook v261 §2C.

The close routine is `END_OF_SESSION_PROMPT_v18.md`.

**First act:** take your session number from the System Board `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).
- *Session numbers at this close:* **345 is RESERVED for the Scan App chat.** 344 the Sanjeevni chat's (reserved), 343 the parent's (reserved).
- *Counters at this close:* **D775 · F-1014 · A-D25 · kit S634 · session 346 next.**
- *A kit number is claimed before its scratch folder is named (F-831).*

**Working rules on manojz:**
- Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.
- **Never run `git` in `device_bash` (F-511, F-833)** — read `.git/logs/HEAD` and the refs.
- A `.gitignore` check is last-match-wins (F-832).
- Set `SANJ_CONFIG_STORE=$HOME/mnt/Downloads/margsync/_config` before the number gate (F-810).
- Open the bundle or a database copy only under the session's own home, and remove it after (F-752).
- A file sent to the PC is proven by its md5 read there (F-900, F-963).
- **Builds in the chat (D765)** — every kit gets an independent cold review before its publish is named (F-901); after a blocker's fix the review reads again (F-1005).
- A health probe names a route the changed file itself registers; the service log is read for "NOT mounted" (F-1001).
- **His browser (the built-in pane, his logged-in session):** the chat reads page text and the app's GET JSON; sub-agents read screens. A paper's scan moves browser-to-server (`/desk/add`), never through the assistant's workspace (D656). A photo over ~4.5 MB is not read (F-1003).
- **Google Drive** is connected: the sheet is read and written with the Drive tools.

***Every time you write is read first — the clock tool, a commit stamp, a file's time or a program's own line (F-791, F-510).***

---

## 0 · THE WORK — in the owner's order

**A · THE OPEN'S FIRST WORK — short.**

1. **Verify this close's publish landed (A16b) — the first act after the board.** `.git/logs/HEAD` = `refs/remotes/origin/main`, a commit later than `b7c694a8` (06:16:37 IST 23-Oct, the Sanjeevni chat's S340 publish); the S342 canon files present at the md5s the manifest names; `md5sum -c MD5SUMS_ALL.txt` inside `deploy_kits/KB_canon_all/`, the count stated. If it has not landed, say so in one line and name:

```
D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat
```

2. **The System Board:** every item with a `note`, every message with `read:false` — say how many.
3. **The three nightly reports** — exists · clock time · verdict.
4. **The pin pass on the newest bundle** with `live_pins_S342close.txt`. **This project's DECLARED-PENDING is 0.** State match / mismatch / not-in-bundle.
5. **The rest of the open's work:** the SSD mirror listed back · the sweep · the tranche and the measure · the four numbers (drift **`batteries.py` 4** — the next patch reads it whole) · what no store holds · the cold kit when due.

**B · THE WORK ITSELF — D773, in this order.**

0. **The Drive sheet** `DARPAN MONTHLY RECORDS LIST 2026.xlsx` (Shavez's folder SHAVEZ; tab *Procedures*): write the names of the plan's table A; take off X-ray 8×10, X-ray 11×14, MARKER and *Disposable gloves No. 7* (OT gloves); Drive keeps the old version. Tell him in one line.
1. **The mock-ups** — start from `https://claude.ai/artifact/3Doc4wew9qUonpFxZtDD7W` (S341): the desk's slip lines with a place per line and no rupees for staff; his *Procedure room* page; the month-end WhatsApp check; Shavez's next-morning screen (Roman Hinglish). His edits line by line; *final* = the specification.
2. **Kit 1** — the product list, the line places, the private rates, his page; then the April–September history entered from the photos (May when found).
3. **Kit 2** — the order scan, order ↔ delivery, the month-end WhatsApp check.
4. **Kit 3** — Shavez's next-morning screen (D774), the editable default allowances (gloves 2 pairs a cast or slab, 1 an ILI), the month-end match, reorder levels. The slips (`slip_log.py`) and the procedures page (`owner_sheets.py`, `owner_service_item`) are the **parent's** — read only; a PLANNED line and the parent told before any change; Awdhesh's *Done* reminder is the parent's file.
- Before Kits 1 and 3, a read-only look at the Sanjeevni stock's *Procedure consumables* pile — no item counted twice.
- Each kit: claimed first, built in the chat, walked (made-up rows, a negative control), K1 before the publish, staff screens installed **switched off**, read live as him and at Shavez's screen size.

**C · THEN:** F-1003 (the reader's size limit — a PLANNED line on the shared reader first) · his lab-bill scans → records 45, 46, 50 · S633's minor points · D761's clearer-duplicate rule.

**HIS, OPEN:**
- the publish of this close (the file above);
- **how many pairs in one box of examination gloves — 50 or 100;**
- **the new Surgiwear drape's name** (for fibre-cast patients);
- **Yuvika's May 2026 slips**, if he finds the WhatsApp;
- (optional) ask Yuvika about the 23-09 slip — six Gloster 5" charged below his usual rate;
- Y119 *Many items on one screen* ON when happy; Y121 the Fujifilm GST tax invoice; the lab-bill scans;
- waiting on papers, never guessed: the Vento's battery; the DTH lab's UPS battery bill; the second AC's bill.

**NEVER:**
- guess a section, a sub-section, a value, a quantity or whose expense a paper is (D664);
- show a vendor's rate on a staff screen (D773); put a vendor's figure, a phone, serial or account number or a vehicle registration into the repository (F-185);
- leave a bill of a consumable as a Machines record (D768);
- move a paper a person placed;
- edit `scanner_widget.js` without a PLANNED line and the seven surfaces walked (D646);
- install a staff screen switched on;
- print, paste or ask for an API key in the chat;
- send a patient's file through the assistant's workspace (D656);
- delete anything that is not his to delete;
- hand him a diagnostic, a technical choice, or a question in shorthand (F-1002);
- call a ruling built before its screen is read live (F-1011).

**CLOSED BY HIS WORD — DO NOT RAISE AGAIN:** everything closed at S318, S323, S337, S341 · the procedure-room mock-up's two questions (answered at S342: a month-end match, not a stationery count; examination gloves, non-sterile) · the names of S342's table A (Gloster = fibre cast; 13 cm × 4 m = Roller 6"; D3031 = the plain towel drape; Glassvan / Easy Glide = blade No. 23; Prime retired; Gypsona with a Y, rarely used) · the slip lines' places (S342 table B).

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
17. Builds are made in the chat while the API credits are low (D765); before an install line, check that no other build holds the server lock.
18. Every kit is read by an independent cold review before its publish is named; a fix round is read again (F-901, F-1005).
19. A kit is finished when he can reach it from where he starts, at his screen's size (F-898).
20. His board carries only what needs him and what he should know; every close answers what he typed there (D526, D684).
21. His own items are deferred unless urgent.

## 1 · THE CURRENT CANON — the manifest wins

| what | file |
|---|---|
| Register | `KB_Register_v5_181_S342close.md` (clone only) |
| History Archive | `KB_History_Archive_v1_178_S342close.md` (§S342; D773, D774 in full) |
| Fault → Action Register | `Fault_Action_Register_v2_166.md` (§7.100 = F-1011, F-1012, F-1013) |
| Runbook | `HANDOFF_RUNBOOK_2026-10-23_Session342close_v261.md` (**§2C the order**) |
| close routine | `END_OF_SESSION_PROMPT_v18.md` |
| build norm | `BUILD_NORM_v1.md` (D704) |
| live pins | `live_pins_S342close.txt` (this project's DECLARED-PENDING 0) |
| build brief | `S342_BUILD_BRIEF.md` |
| the project's record | `SCANAPP_SYSTEM_BOOK_v8_S341.md` (unchanged at S342) |
| the plan, with figures | `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S342\S342_PROCEDURE_ROOM_PLAN.md` (out of the repository) |
| numbers | System Board `board/_numbers` — at this close: **D775 · F-1014 · A-D25 · kit S634 · session 346 next; 345 RESERVED for the Scan App chat** |

*Written at the S342 close, 23-Oct-2026.*
