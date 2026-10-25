# START HERE — SESSION 355 — written at the S352 close (the Scan App project), 25-Oct-2026

**Project: Scan App — Papers & Bills.** Open in a fresh chat in this project, on manojz. First run `SCANAPP_START_HERE_PROMPT_v1`'s Phase 0 (the project's custom instructions), then this file.

**Where things stand.** Session 352 (08:37 IST → the owner's "eos" at 12:25 IST 25-Oct) **built and installed three kits**, each read cold until SAFE and read live as him:
- **S648_PROCROOM_OPEN_DOOR** (publish `ae8bd328`, "DONE" 09:04 IST) — the read-only count door for Shavez's *Aaj ka kaam* (the parent's S652 reads it, live 12:20 IST) and *Baaki din* from 01-10-2026. Live read: 17 days, 30 slips.

```
https://followup.dr-manoj.in/scanapp/procroom/morning/api/open
```

- **S649_READER_PHOTO_SIZE** (publish `a25fcba6`, "DONE" 10:04 IST) — F-1003 closed: a large phone photo is shrunk for the reader by the venv python. A paper that says *read failed* can be read again with its **Re-read** button. HEIC is still not read.
- **S651_CLEARER_DUPLICATE** (publish `9c0a549d`, "Done" 10:40 IST) — D761 for the scan app, F-992's scan-app half closed: two scans of one clinic paper — the one with item lines kept, only when the other is untouched. Three review rounds; the first was NOT SAFE (two blockers, fixed).

**What to read:** `S352_BUILD_BRIEF.md` (for him) · `SCANAPP_SYSTEM_BOOK_v11_S352.md` §18 · the three kits' READMEs (`deploy_kits/S648_PROCROOM_OPEN_DOOR/`, `S649_READER_PHOTO_SIZE/`, `S651_CLEARER_DUPLICATE/` — each holds its undo line) · `BUILD_NORM_v1.md` · the Runbook v270 §2C.

The close routine is `END_OF_SESSION_PROMPT_v18.md`.

**First act:** take your session number from the System Board `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).
- *Session numbers at this close:* **355 is RESERVED for the Scan App chat.** 354 the parent's (open), 353 the Sanjeevni chat's (open), 351 the NK Pathology chat's (open).
- *Counters at this close:* **D789 · F-1026 · A-D25 · kit S654 · session 356 next.**
- *A kit number is claimed before its scratch folder is named (F-831).*

**Working rules on manojz:**
- Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.
- **Never run `git` in `device_bash` (F-511, F-833)** — read `.git/logs/HEAD` and the refs.
- A `.gitignore` check is last-match-wins (F-832).
- Set `SANJ_CONFIG_STORE=$HOME/mnt/Downloads/margsync/_config` before the number gate (F-810).
- Open the bundle or a database copy only under the session's own home, and remove it after (F-752).
- A file sent to the PC is proven by its md5 read there (F-900, F-963).
- **Builds in the chat (D765)** — the device shell has no Flask: the walks run in the cloud workspace on the bundle's code (code only — never a patient file, D656) and on the server inside the installer. Every kit gets an independent cold review before its publish is named (F-901); after a blocker's fix the review reads again (F-1005). **A walk's rupees are made up (F-185), and its made-up rows carry every mark the live flow writes** (S651 R1).
- A health probe names a route the changed file itself registers; the service log is read for "NOT mounted" (F-1001).
- **His browser (the built-in pane, his logged-in session):** sub-agents read screens and the app's GET JSON. A paper's scan moves browser-to-server, never through the assistant's workspace (D656).
- `procroom.py` and `scan_checks_s441.py` read the parent's `finance.db` **read only**.

***Every time you write is read first — the clock tool, a commit stamp, a file's time or a program's own line (F-791, F-510).***

---

## 0 · THE WORK — in the owner's order

**A · THE OPEN'S FIRST WORK — short.**

1. **Verify this close's publish landed (A16b) — the first act after the board.** `.git/logs/HEAD` = `refs/remotes/origin/main`, a commit later than `9c0a549d` (10:39:17 IST 25-Oct); the S352 canon files present at the md5s the manifest names; `md5sum -c MD5SUMS_ALL.txt` inside `deploy_kits/KB_canon_all/`, the count stated. If it has not landed, say so in one line and name:

```
D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat
```

2. **The System Board:** every item with a `note`, every message with `read:false` — say how many.
3. **The three nightly reports** — exists · clock time · verdict.
4. **The pin pass on the newest bundle** with `live_pins_S352close.txt`. **This project's DECLARED-PENDING is 5** — `procroom.py` `f6578535ba3d85dd9c7561df0798a443` (S648), `claude_reader.py` `1277e80de5c141cf3f5f7c97b9434cb9` (S649), `/root/shared/scan_checks_s441.py` `10787cbf67b0480950134047efa74372`, `asset_register.py` `63a8b15ba74ecfe64f1062dbf35b53e0`, `sorting_desk.py` `bb206e5dfcc6bb0dff71524b68e33f5f` (S651); the 26-Oct bundle should confirm all five. State match / mismatch / not-in-bundle.
5. **The rest of the open's work — owed since S352's open, which did not take it:** the SSD mirror listed back · the sweep · the tranche and the measure · the four numbers (drift `batteries.py` 4, `sorting_desk.py` 3, `clinic_papers.py` 3, `asset_register.py` 2) · what no store holds · **the cold kit — due** (the Register and Archive bumped at S346 and S352).

**B · THE WORK ITSELF.**

1. **The reviews' small points — one kit on `procroom.py` `f6578535`:** `ili_kit()` skips a retired procedure; an add-column step for `proc_use.lkey`; a retired product inside `fits()`; the month-end editor keeps typed rates across *Its scan*; S633's minor points. A PLANNED line first.
2. **S651's minor points (Runbook §2C item 4):** M1 (the owner's *same* when the keep is already set aside onto a third), M4 (prove the running service loaded S441.2), M7 (normalise the finance stamp match), M8 (a plain `stamp` column blocking). Low; fold into a kit only when one touches those files.
- Each kit: claimed first, built in the chat, walked (made-up rows that look like live ones, a negative control), K1 before the publish, read live as him and at Shavez's screen size.

**C · THEN:** B-0176's lines on the desk (by hand, never guessed) · his lab-bill scans → records 45, 46, 50.

**HIS, OPEN:**
- the publish of this close (the file above; board Y159);
- a shelf count for each product on his Procedure room page (*Used and in stock*) — the stock starts from it (Y157);
- how many pairs in one box of examination gloves — 50 or 100 (Y145);
- the new Surgiwear drape's name, and whether the D600 drape stays on casts and slabs (Y146);
- Yuvika's May 2026 slips, if he finds the WhatsApp (Y147); (optional) ask Yuvika about the 23-09 slip (Y148);
- October's month end: Yuvika's WhatsApp photos into `https://followup.dr-manoj.in/scanapp/procroom/month`;
- Y119 *Many items on one screen* ON when happy; Y121 the Fujifilm GST tax invoice; Y136 the lab-bill scans;
- waiting on papers, never guessed: the Vento's battery; the DTH lab's UPS battery bill; the second AC's bill.

**NEVER:**
- guess a section, a sub-section, a value, a quantity or whose expense a paper is (D664);
- show a vendor's rate or his rate on a staff screen (D773); put a vendor's figure, a phone, serial or account number or a vehicle registration into the repository (F-185);
- count the ILI injections as a procedure-room purchase, or make gloves compulsory on an ILI (D782);
- build a portal tile or edit `portal.py` / `tile_grants.json` — the parent's (D783);
- write to the parent's `finance.db`;
- leave a bill of a consumable as a Machines record (D768);
- move a paper a person placed — a D761 swap only within its guards;
- edit `scanner_widget.js` without a PLANNED line and the seven surfaces walked (D646);
- install a new staff screen switched on;
- print, paste or ask for an API key in the chat;
- send a patient's file through the assistant's workspace (D656);
- delete anything that is not his to delete;
- hand him a diagnostic, a technical choice, or a question in shorthand (F-1002);
- call a ruling built before its screen is read live (F-1011).

**CLOSED BY HIS WORD — DO NOT RAISE AGAIN:** everything closed at S318, S323, S337, S341, S342, S345, S346 · the mock-ups (*"okay to start"*, 08:31 IST 23-Oct) · gloves on an ILI and the ILI injections (D782) · the tiles are the parent's (D783) · the clearer duplicate is D761, built (S651).

**Standing owner rulings (restated):**

1. Publishing is his double-click — `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`.
2. Full paths always, URLs too, each in its own copy block.
3. One line per command; `\cp` past the alias. A server line carries its own pull: `cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/<KIT>/<installer>.sh`.
4. Token-lean, never at the cost of verification — **his weekly data limit is tight: plan the session's reads before starting.**
5. Plain English, short, one step at a time, full-file replacements, ALL-CAPS = urgent. IST only; a clock time is read, never estimated.
6. Mask patient numbers (last 4); never print secrets; no number of any kind in the repository (F-185).
7. Nothing live is rebuilt without his OK; the manual path stays.
8. Sub-agents read screens; screenshots never enter the main conversation.
9. Do not hand him diagnostics or technical choices — decide, say it in one line, proceed. He weighs in on what he can SEE.
10. When a screen is wrong, read its code first.
11. Do not hand him a step that is not his.
12. A new staff screen is shown to him as a mock-up first and installed switched off; staff pages in Roman Hinglish, his in English.
13. Staff flows are friction-free: no waiting on the server, no second tap.
14. Analysis first when he says so — *"do not build or code anything"* means an answer only.
15. His approvals are few and arrive together (D683).
16. Every build follows `BUILD_NORM_v1` (D704); patient files never pass through the assistant's workspace (D656).
17. Builds are made in the chat while the API credits are low (D765); before an install line, check that no other build holds the server lock.
18. Every kit is read by an independent cold review before its publish is named; a fix round is read again (F-901, F-1005).
19. A kit is finished when he and the staff can reach it from where they start — their portal — at their screen's size (F-898, D783).
20. His board carries only what needs him and what he should know (D526, D684); every close answers what he typed there.
21. His own items are deferred unless urgent.

## 1 · THE CURRENT CANON — the manifest wins

| what | file |
|---|---|
| Register | `KB_Register_v5_190_S352close.md` (clone only) |
| History Archive | `KB_History_Archive_v1_187_S352close.md` (§S352) |
| Fault → Action Register | `Fault_Action_Register_v2_174.md` (§7.108 — no F minted; F-1003 closed, F-992's scan-app half closed) |
| Runbook | `HANDOFF_RUNBOOK_2026-10-25_Session352close_v270.md` (**§2C the order**) |
| close routine | `END_OF_SESSION_PROMPT_v18.md` |
| build norm | `BUILD_NORM_v1.md` (D704) |
| live pins | `live_pins_S352close.txt` (this project's DECLARED-PENDING 5) |
| build brief | `S352_BUILD_BRIEF.md` |
| the project's record | `SCANAPP_SYSTEM_BOOK_v11_S352.md` |
| the kits | `deploy_kits/S648_PROCROOM_OPEN_DOOR/` · `S649_READER_PHOTO_SIZE/` · `S651_CLEARER_DUPLICATE/` (READMEs: the undo lines) |
| numbers | System Board `board/_numbers` — at this close: **D789 · F-1026 · A-D25 · kit S654 · session 356 next; 355 RESERVED for the Scan App chat** |

*Written at the S352 close, 25-Oct-2026.*
