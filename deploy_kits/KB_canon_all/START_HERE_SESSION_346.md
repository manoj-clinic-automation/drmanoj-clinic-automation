# START HERE — SESSION 346 — written at the S345 close (the Scan App project), 24-Oct-2026

**Project: Scan App — Papers & Bills.** Open in a fresh chat in this project, on manojz. First run `SCANAPP_START_HERE_PROMPT_v1`'s Phase 0 (the project's custom instructions), then this file.

**Where things stand.** Session 345 (08:13 IST 23-Oct → the owner's "EOS" at 20:34 IST 24-Oct) **built and installed D773 Kit 1 — `S634_PROCROOM_LIST`** (his publish 09:14:47 IST `4c275c79`; "DONE" 09:20 IST):
- his **Procedure room** page `https://followup.dr-manoj.in/scanapp/procroom` (the owner only) — the product list (31 now), by product, by month for the financial year, kept elsewhere, the slips with his rates, a slip from a photo, the gloves allowance;
- on the **sorting desk**, with *Procedure room* chosen, each line's product, quantity, brand and place (Procedure room · Home use · Clinic equipment · OT · Sanjeevni) — **no rupee and no rate**;
- the **April–September history** entered from his photos: April ₹3,820 · June ₹8,730 · July ₹5,675 · August ₹3,400 · September ₹5,880 — ₹27,505, equal to the S342 plan (May not found);
- Shavez's Drive sheet renamed to the list's names (32 rows).
**At 09:27 IST 23-Oct the owner paused the build until his weekly limit resets (Saturday 24-Oct, 22:30 IST): Kits 2 and 3 start only at his word.**

**What to read:** `S345_BUILD_BRIEF.md` (for him) · `SCANAPP_SYSTEM_BOOK_v9_S345.md` §16 · `deploy_kits/S634_PROCROOM_LIST/README.md` · the S342 plan `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S342\S342_PROCEDURE_ROOM_PLAN.md` (sections B–D; **his figures: never into the repository**) · the mock-ups `https://claude.ai/artifact/3Doc4wew9qUonpFxZtDD7W` (artboards 2 and 4 are Kit 3's and Kit 2's) · `BUILD_NORM_v1.md` · the Runbook v262 §2C.

The close routine is `END_OF_SESSION_PROMPT_v18.md`.

**First act:** take your session number from the System Board `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).
- *Session numbers at this close:* **346 is RESERVED for the Scan App chat.** 344 the Sanjeevni chat's (open), 343 the parent's (open).
- *Counters at this close:* **D775 · F-1017 · A-D25 · kit S635 · session 347 next.**
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
- **His browser (the built-in pane, his logged-in session):** the chat reads page text and the app's GET JSON; data he asked for is entered through his own page's doors (as the history was); sub-agents read screens. A paper's scan moves browser-to-server, never through the assistant's workspace (D656).
- The kit's walk and browser walk ran in the cloud workspace on the bundle's code (Flask installed there); the box runs the walk again on a copy of the live database.

***Every time you write is read first — the clock tool, a commit stamp, a file's time or a program's own line (F-791, F-510).***

---

## 0 · THE WORK — in the owner's order

**A · THE OPEN'S FIRST WORK — short.**

1. **Verify this close's publish landed (A16b) — the first act after the board.** `.git/logs/HEAD` = `refs/remotes/origin/main`, a commit later than `4c275c79` (09:14:47 IST 23-Oct, the S634 publish); the S345 canon files present at the md5s the manifest names; `md5sum -c MD5SUMS_ALL.txt` inside `deploy_kits/KB_canon_all/`, the count stated. If it has not landed, say so in one line and name:

```
D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat
```

2. **The System Board:** every item with a `note`, every message with `read:false` — say how many.
3. **The three nightly reports** — exists · clock time · verdict.
4. **The pin pass on the newest bundle** with `live_pins_S345close.txt`. **This project's DECLARED-PENDING is 0.** State match / mismatch / not-in-bundle.
5. **The rest of the open's work:** the SSD mirror listed back · the sweep · the tranche and the measure · the four numbers (drift `batteries.py` 4; `sorting_desk.py`, `asset_register.py` 1 each since their whole read at S634) · what no store holds · the cold kit when due (the Register and Archive bumped at this close).

**B · THE WORK ITSELF — D773, only at his word (after 22:30 IST 24-Oct).**

1. **Kit 2** — the order scan (his signed duplicate-book page as an *Order* on the desk), order ↔ delivery (*awaiting* after a few days / *no order*), the **month-end WhatsApp check** on his page (his photos read slip by slip and matched to their scans and orders: not scanned · quantity differs · rate changed · the month's total; the photo kept as the month's bill) — mock-up artboard 4. Built on `procroom.py` `a641f640` (a photo-only slip already lives in `proc_slip`). F-1012.
2. **Kit 3** — Shavez's next-morning screen (D774; Roman Hinglish; mock-up artboard 2; installed **switched off**), the allowances in use, use and stock, *Order now* under the reorder level, the month-end match. The slips (`slip_log.py`) and the procedures page (`owner_sheets.py`, `owner_service_item`) are the **parent's** — read only; a PLANNED line and the parent told before any change. Before it, a read-only look at the Sanjeevni stock's *Procedure consumables* pile. F-1011.
- Each kit: claimed first, built in the chat, walked (made-up rows, a negative control), K1 before the publish, staff screens installed switched off, read live as him and at Shavez's screen size.

**C · THEN:** B-0176's lines on the desk (by hand, never guessed) · F-1003 · his lab-bill scans → records 45, 46, 50 · S633's minor points · D761's clearer-duplicate rule.

**HIS, OPEN:**
- the publish of this close (the file above);
- how many pairs in one box of examination gloves — 50 or 100;
- the new Surgiwear drape's name (for fibre-cast patients);
- Yuvika's May 2026 slips, if he finds the WhatsApp;
- (optional) ask Yuvika about the 23-09 slip — six Gloster 5" at a lower rate;
- Y119 *Many items on one screen* ON when happy; Y121 the Fujifilm GST tax invoice; Y136 the lab-bill scans;
- waiting on papers, never guessed: the Vento's battery; the DTH lab's UPS battery bill; the second AC's bill.

**NEVER:**
- guess a section, a sub-section, a value, a quantity or whose expense a paper is (D664);
- show a vendor's rate or his rate on a staff screen (D773); put a vendor's figure, a phone, serial or account number or a vehicle registration into the repository (F-185);
- leave a bill of a consumable as a Machines record (D768);
- move a paper a person placed;
- edit `scanner_widget.js` without a PLANNED line and the seven surfaces walked (D646);
- install a staff screen switched on;
- print, paste or ask for an API key in the chat;
- send a patient's file through the assistant's workspace (D656);
- delete anything that is not his to delete;
- hand him a diagnostic, a technical choice, or a question in shorthand (F-1002);
- call a ruling built before its screen is read live (F-1011);
- start Kit 2 or Kit 3 before he says so.

**CLOSED BY HIS WORD — DO NOT RAISE AGAIN:** everything closed at S318, S323, S337, S341, S342 · the mock-ups (*"okay to start"*, 08:31 IST 23-Oct) · the 31-07 Dispo needle → the Procedure room (09:26 IST 23-Oct).

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
| Register | `KB_Register_v5_182_S345close.md` (clone only) |
| History Archive | `KB_History_Archive_v1_179_S345close.md` (§S345) |
| Fault → Action Register | `Fault_Action_Register_v2_166.md` (unchanged at S345; §7.100 = F-1011 … F-1013) |
| Runbook | `HANDOFF_RUNBOOK_2026-10-24_Session345close_v262.md` (**§2C the order**) |
| close routine | `END_OF_SESSION_PROMPT_v18.md` |
| build norm | `BUILD_NORM_v1.md` (D704) |
| live pins | `live_pins_S345close.txt` (this project's DECLARED-PENDING 0) |
| build brief | `S345_BUILD_BRIEF.md` |
| the project's record | `SCANAPP_SYSTEM_BOOK_v9_S345.md` |
| the kit | `deploy_kits/S634_PROCROOM_LIST/` (README: the undo line) |
| the plan, with figures | `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S342\S342_PROCEDURE_ROOM_PLAN.md` (out of the repository) |
| numbers | System Board `board/_numbers` — at this close: **D775 · F-1017 · A-D25 · kit S635 · session 347 next; 346 RESERVED for the Scan App chat** |

*Written at the S345 close, 24-Oct-2026.*
