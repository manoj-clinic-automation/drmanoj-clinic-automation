# START HERE — SESSION 352 — written at the S346 close (the Scan App project), 25-Oct-2026

**Project: Scan App — Papers & Bills.** Open in a fresh chat in this project, on manojz. First run `SCANAPP_START_HERE_PROMPT_v1`'s Phase 0 (the project's custom instructions), then this file.

**Where things stand.** Session 346 (20:47 IST 24-Oct → the owner's "eos, do your pendings in next fresh chat" at 07:4x IST 25-Oct) **built and installed three kits**, each read cold until SAFE and read live as him:
- **S635_PROCROOM_ORDERS** (D773 Kit 2; publish `d4110b93`, "done" 21:41 IST 24-Oct) — on the desk his signed order is *Dr Manoj's order* (counts nothing), a slip is joined to it and filled from it in one tap; his page shows *awaiting* / *part came* / *delivered* and *no order*; the month end `https://followup.dr-manoj.in/scanapp/procroom/month` reads Yuvika's WhatsApp photos and matches them to the scans (not scanned · quantity · rate against the last · the month's total).
- **S637_PROCROOM_MORNING** (D773 Kit 3, D774; publish `ae6227e0`, "done" 22:15 IST) — Shavez's *Kal ke procedures* `https://followup.dr-manoj.in/scanapp/procroom/morning` (Roman Hinglish, no rupee): yesterday's X-ray/Proc slips Docterz confirms, the kit pre-filled, one Save; his page: used, stock, *Order now*, the month-end match. **Switched on for Shavez by the owner, 07:0x IST 25-Oct.**
- **S643_ILI_KIT** (publish `2e48b3e6`, "Done" 06:48 IST 25-Oct) — ILI KNEE (no items on his rate page) takes the injection group's items.
- **D782** (07:11 IST): gloves are not compulsory on an ILI (he set the allowance to 0); the ILI injections are bought and billed at Sanjeevni — recorded by name only here. **D783:** the direct tiles are the parent's — it took **S646_PROCROOM_TILES** and asked this chat for a count door and October's backfill (below).

**What to read:** `S346_BUILD_BRIEF.md` (for him) · `SCANAPP_SYSTEM_BOOK_v10_S346.md` §17 · the three kits' READMEs (`deploy_kits/S635_PROCROOM_ORDERS/`, `S637_PROCROOM_MORNING/`, `S643_ILI_KIT/` — each holds its undo line) · the board message `parent_S349_1` · `BUILD_NORM_v1.md` · the Runbook v267 §2C.

The close routine is `END_OF_SESSION_PROMPT_v18.md`.

**First act:** take your session number from the System Board `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).
- *Session numbers at this close:* **352 is RESERVED for the Scan App chat.** 349 the parent's (open), 350 the Sanjeevni chat's (open), 351 the NK Pathology chat's (open — its first session under the estate's numbers, taken 07:55 IST 25-Oct).
- *Counters at this close:* **D784 · F-1025 · A-D25 · kit S648 · session 353 next.**
- *A kit number is claimed before its scratch folder is named (F-831).*

**Working rules on manojz:**
- Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.
- **Never run `git` in `device_bash` (F-511, F-833)** — read `.git/logs/HEAD` and the refs.
- A `.gitignore` check is last-match-wins (F-832).
- Set `SANJ_CONFIG_STORE=$HOME/mnt/Downloads/margsync/_config` before the number gate (F-810).
- Open the bundle or a database copy only under the session's own home, and remove it after (F-752).
- A file sent to the PC is proven by its md5 read there (F-900, F-963).
- **Builds in the chat (D765)** — every kit gets an independent cold review before its publish is named (F-901); after a blocker's fix the review reads again (F-1005). **A walk's rupees are made up (F-185).**
- A health probe names a route the changed file itself registers; the service log is read for "NOT mounted" (F-1001).
- **His browser (the built-in pane, his logged-in session):** the chat reads page text and the app's GET JSON; sub-agents read screens. A paper's scan moves browser-to-server, never through the assistant's workspace (D656).
- `procroom.py` reads the parent's `finance.db` **read only** (`mode=ro`, env `FINANCE_DB_FOR_SCANS`); its walk runs on a MADE-UP slip book, never the real finance database.

***Every time you write is read first — the clock tool, a commit stamp, a file's time or a program's own line (F-791, F-510).***

---

## 0 · THE WORK — in the owner's order

**A · THE OPEN'S FIRST WORK — short.**

1. **Verify this close's publish landed (A16b) — the first act after the board.** `.git/logs/HEAD` = `refs/remotes/origin/main`, a commit later than `61685e2a` (07:43:43 IST 25-Oct, the parent's S349 publish); the S346 canon files present at the md5s the manifest names; `md5sum -c MD5SUMS_ALL.txt` inside `deploy_kits/KB_canon_all/`, the count stated. If it has not landed, say so in one line and name:

```
D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat
```

2. **The System Board:** every item with a `note`, every message with `read:false` — say how many. The parent's S646 (the tiles) was installed at 07:54 IST 25-Oct (its claim on the board) — read Shavez's *Kal ke procedures* tile live at his phone's size.
3. **The three nightly reports** — exists · clock time · verdict.
4. **The pin pass on the newest bundle** with `live_pins_S346close.txt`. **This project's DECLARED-PENDING is 1** — `procroom.py` `7b936d6f05240f17423b93b223d73a36` (S643); the 26-Oct bundle should confirm it. State match / mismatch / not-in-bundle.
5. **The rest of the open's work:** the SSD mirror listed back · the sweep · the tranche and the measure · the four numbers (drift `batteries.py` 4, `clinic_papers.py` 3, `sorting_desk.py` 2; `procroom.py` whole) · what no store holds · the cold kit when due (the Register and Archive bumped at this close).

**B · THE WORK ITSELF — his word at the close: "do your pendings in next fresh chat".**

1. **The parent's ask (`parent_S349_1`) — first.** One kit on `procroom.py` `7b936d6f`:
   - a read-only JSON door **`GET /scanapp/procroom/morning/api/open`** for the signed-in login (shavez — a manager — and the doctor): `{ok: true, open: <days still to fill>, text: 'Kal ke procedures: <n> din baaki (<m> parchi)'}`; `open: 0` when nothing waits; a signed-out call, a refused login or the screen switched off for the staff answer **without** an `open` field (the parent reads a missing field as *door did not answer*, never as *nothing waits*);
   - *Baaki din* widened to **every day from 01-10-2026** (a floor setting, not `CATCHUP_DAYS = 7`), and `not_done_refs` bounded by the same floor; the count and the list are one computation;
   - walked with made-up slips (a day saved, a day not, a slip Docterz has not confirmed, signed out → no `open`), a control on S643's file;
   - then tell the parent on the board the exact path and fields (its FETCH line in `aaj_duties.json` follows its S645), and read it live through Shavez's tile at his phone's size (S646 installed 07:54 IST 25-Oct; F-898). Not a new screen — no mock-up; the line is in the screen he has.
2. **F-1003** — the reader's size limit (photos over about 4.5 MB fail; the month end's photos too): a smaller copy for the reader. `claude_reader.py` is this project's file; a PLANNED line first (other parts call it).
3. **D761** — keep the clearer scan of a duplicate, in the scan app's own duplicate check.
4. **The reviews' small points:** `ili_kit()` skips a retired procedure; an add-column step for `proc_use.lkey`; a retired product inside `fits()`; the month-end editor keeps typed rates across *Its scan*; S633's minor points.
- Each kit: claimed first, built in the chat, walked (made-up rows, a negative control), K1 before the publish, read live as him and at Shavez's screen size.

**C · THEN:** B-0176's lines on the desk (by hand, never guessed) · his lab-bill scans → records 45, 46, 50.

**HIS, OPEN:**
- the publish of this close (the file above);
- a shelf count for each product on his Procedure room page (*Used and in stock*) — the stock starts from it;
- how many pairs in one box of examination gloves — 50 or 100;
- the new Surgiwear drape's name, and whether the D600 drape stays on casts and slabs;
- Yuvika's May 2026 slips, if he finds the WhatsApp; (optional) ask Yuvika about the 23-09 slip;
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
- move a paper a person placed;
- edit `scanner_widget.js` without a PLANNED line and the seven surfaces walked (D646);
- install a new staff screen switched on;
- print, paste or ask for an API key in the chat;
- send a patient's file through the assistant's workspace (D656);
- delete anything that is not his to delete;
- hand him a diagnostic, a technical choice, or a question in shorthand (F-1002);
- call a ruling built before its screen is read live (F-1011).

**CLOSED BY HIS WORD — DO NOT RAISE AGAIN:** everything closed at S318, S323, S337, S341, S342, S345 · the mock-ups (*"okay to start"*, 08:31 IST 23-Oct) · gloves on an ILI and the ILI injections (D782, 07:11 IST 25-Oct) · the tiles are the parent's (D783).

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
20. His board carries only what needs him and what he should know; every close answers what he typed there (D526, D684).
21. His own items are deferred unless urgent.

## 1 · THE CURRENT CANON — the manifest wins

| what | file |
|---|---|
| Register | `KB_Register_v5_187_S346close.md` (clone only) |
| History Archive | `KB_History_Archive_v1_184_S346close.md` (§S346) |
| Fault → Action Register | `Fault_Action_Register_v2_171.md` (§7.105 — no F minted; F-1011, F-1012 closed) |
| Runbook | `HANDOFF_RUNBOOK_2026-10-25_Session346close_v267.md` (**§2C the order**) |
| close routine | `END_OF_SESSION_PROMPT_v18.md` |
| build norm | `BUILD_NORM_v1.md` (D704) |
| live pins | `live_pins_S346close.txt` (this project's DECLARED-PENDING 1) |
| build brief | `S346_BUILD_BRIEF.md` |
| the project's record | `SCANAPP_SYSTEM_BOOK_v10_S346.md` |
| the kits | `deploy_kits/S635_PROCROOM_ORDERS/` · `S637_PROCROOM_MORNING/` · `S643_ILI_KIT/` (READMEs: the undo lines) |
| the plan, with figures | `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S342\S342_PROCEDURE_ROOM_PLAN.md` (out of the repository) |
| numbers | System Board `board/_numbers` — at this close: **D784 · F-1025 · A-D25 · kit S648 · session 353 next; 352 RESERVED for the Scan App chat** |

*Written at the S346 close, 25-Oct-2026.*
