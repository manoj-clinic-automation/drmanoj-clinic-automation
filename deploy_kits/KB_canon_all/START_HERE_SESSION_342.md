# START HERE — SESSION 342 — written at the S341 close (the Scan App project), 23-Oct-2026

**Project: Scan App — Papers & Bills.** Open in a fresh chat in this project, on manojz. First run `SCANAPP_START_HERE_PROMPT_v1`'s Phase 0 (the project's custom instructions), then this file.

**Where things stand.** Session 341 (20:27 IST 22-Oct → the owner's "eos" at 04:01 IST 23-Oct) put two kits live, **both built in the chat (D765)**, and moved the bills kept as Machines records to the desk:
- **S632** — the battery page made clean (D766): *Correct a battery entry* (owner) — a saved fitting's dates, supplier, make, Ah, set, warranty, price, old-battery amount, or *Entered by mistake — remove*; one bill may be the bill of several batteries; a fifth group *Machine batteries*; *Change this place* takes the group and the upkeep; the linked machine record's scans shown;
- **S633** — the X-ray costs page the whole financial year from April (D767): month by month; AMC and batteries spread over their months; film purchases by size with running boxes and rupees; film lines on a Machines record. Read live: April → October 2026 **₹98,011** (films ₹68,951; AMC ₹5,416.67 a month from July; batteries ₹213.33 a month from April + ₹1,966.67 from August);
- **D768 (data, his word):** thirteen bills kept as Machines records became desk papers **B-0210 … B-0222** (nine Jugnu film bills → X-ray small film; four lab bills → NK Pathology) and their records were deleted; assets 12 and 37 (duplicates) and 52 (a challan line) deleted; the Machines list renamed and tidied. The Machines list now holds machines only — except records **45, 46, 50** (lab bills with no scan), which go when he has scanned the lab consumables bills from April 2026.

**What to read:** `S341_BUILD_BRIEF.md` (for him) · `SCANAPP_SYSTEM_BOOK_v8_S341.md` (§15 is new) · `BUILD_NORM_v1.md` · the Runbook v258 (§2C, §1L) · the two kits in `deploy_kits\` (S632, S633), above all their `walk_*_app.py` — the real scan app loads in the chat's own workspace (the Book §14.6) · `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S341\S341_OPEN_ITEMS.md`.

The close routine is `END_OF_SESSION_PROMPT_v18.md`.

**First act:** take your session number from the System Board `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).
- *Session numbers at this close:* **342 is RESERVED for the Scan App chat.** 340 is the Sanjeevni chat's (opened 04:03 IST 23-Oct); 336 the parent's (open).
- *Counters at this close:* **D770 · F-1006 · A-D25 · kit S634 · session 343 next.**
- *A kit number is claimed before its scratch folder is named (F-831).*

**Working rules on manojz:**
- Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.
- **Never run `git` in `device_bash` (F-511, F-833)** — read `.git/logs/HEAD` and the refs.
- A `.gitignore` check is last-match-wins (F-832).
- Set `SANJ_CONFIG_STORE=$HOME/mnt/Downloads/margsync/_config` before the number gate (F-810).
- Open the bundle or a database copy only under the session's own home, and remove it after (F-752).
- A file sent to the PC is proven by its md5 read there (F-900, F-963).
- **Builds in the chat (D765)** — every kit gets an independent cold review before its publish is named (F-901); **after a blocker's fix the review reads again (F-1005).**
- A health probe names a route the changed file itself registers, and the service log is read for "NOT mounted" (F-1001).
- **His browser (the built-in pane, his logged-in session):** sub-agents read the screens; the chat reads page text and the app's GET JSON. A paper's scan moves browser-to-server (`/desk/add`), never through the assistant's workspace (D656). A photo over ~4.5 MB is not read (F-1003) — type its header and lines through the paper's own Edit form.

***Every time you write is read first — the clock tool, a commit stamp, a file's time or a program's own line (F-791, F-510).***

---

## 0 · THE WORK — in the owner's order

**A · THE OPEN'S FIRST WORK — short.**

1. **Verify this close's publish landed (A16b) — the first act after the board.** `.git/logs/HEAD` = `refs/remotes/origin/main`, a commit later than `2ab0e2a4` (22:32 IST 22-Oct, S633's); the S341 canon files present at the md5s the manifest names; `md5sum -c MD5SUMS_ALL.txt` inside `deploy_kits/KB_canon_all/`, the count stated. If it has not landed, say so in one line and name:

```
D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat
```

2. **The System Board:** every item with a `note`, every message with `read:false` — say how many.
3. **The three nightly reports** — exists · clock time · verdict.
4. **The pin pass on the newest bundle** with `live_pins_S341close.txt`. **This project's DECLARED-PENDING is 0** — every scan-app file was confirmed by the 23-Oct bundle. State match / mismatch / not-in-bundle.
5. **The rest of the open's work:** the SSD mirror listed back · the sweep (`03_WORKING_PAPERS\S341\` holds the code bundle used for the walks and the mock-up's files — leave them) · the tranche and the measure · the four numbers (drift: **`batteries.py` 4** — the next patch reads it whole and consolidates first) · what no store holds.

**B · THE WORK ITSELF.**

1. **PROCEDURE-ROOM CONSUMABLES — D769, the first work.** His words (22:53 IST 22-Oct): *"yuvika challan, they are mostly for procedure room consumables, and need a list of products, against which the challan quantities can be added, handwritten notes are sometimes not clear to be read by you or sarvam"*; (23:06) *"Start with procedure room consumables"*.
   - **The mock-up** (two screens: the desk's *Procedure room items on this paper* for Shavez — pick each product, type the challan's quantity, the reader's reading in grey as a hint only; and his *Procedure room consumables* page by product, every purchase with its running total, *+ Add a product*):

```
https://claude.ai/artifact/3Doc4wew9qUonpFxZtDD7W
```

   - **Its two open questions, asked once, in these words:** *"Should the list only count what is bought, or also keep a shelf count like stationery (what is in the room now)?"* and *"Which size of surgical gloves — or more than one size?"* Then his *final* — the mock-up is the specification; his edits are followed line by line.
   - **The papers already on the desk:** Kriti Medicos **B-0004** (drapes D3031 and D600); Yuvika Surgicals **B-0007**, **B-0018** (29-09-2026; plaster 5" 7), **B-0176** (16-10-2026; plaster, bandage 13 cm × 4 m, zig-zag cotton, gloves). Read their scans as the starting list; never guess a quantity the handwriting does not show.
   - **Build:** a kit in the chat (claim it first), the desk's lines stored beside the paper (the challan's quantity; the bill's rate when it comes), installed **switched off**; K1 before the publish; the result read live as the owner and as Shavez's screen size.
2. **F-1003 — the reader's size limit.** A photo over ~4.5 MB returns *"read failed"*. Offer in one line: a smaller copy for the reader (the stored scan unchanged), or the paper says *"too big to read — type it"*. `claude_reader.py` / `claude_reread.py` are shared — a PLANNED line first.
3. **His lab-bill scans (D768):** once the lab consumables bills from April 2026 are on the desk, give him the links to delete records 45, 46 (Gaurav Scientific) and 50 (Aastha Medical).
4. **The next scan-app round (seen, not built — offer in plain words, one line each):** S633's minor points (a film line with no amount; a twin later joined; the *not spread* words; sizes in centimetres; film records with no date) · D761's clearer-duplicate rule (`sanjeevni_S339_1`, a PLANNED line on `asset_register.py` and `scan_checks_s441.py`) · B-0163 ₹0 until its bill · `misread_date` 400 days vs 12 months.

**HIS, OPEN:**
- the publish of this close (the file above);
- **the two answers on the procedure-room mock-up** and his *final*;
- **scan the lab consumables bills from April 2026** (his word, 22:53 IST);
- Y119 — *Many items on one screen* ON when he is happy (the card at the top of `https://followup.dr-manoj.in/scanapp/stationery`);
- Y121 — Fujifilm's GST tax invoice for the FDR AMC when it comes;
- **waiting on papers, never guessed:** the Vento's battery (he is searching); the DTH lab's online UPS battery (B.L. Computers' bill); the second Panasonic AC's bill.

**NEVER:**
- guess a section, a sub-section, a value, a quantity or whose expense a paper is (D664);
- leave a bill of a consumable as a Machines record (D768);
- move a paper a person placed;
- edit `scanner_widget.js` without a PLANNED line and the seven surfaces walked (D646);
- install a staff screen switched on;
- put a vehicle registration, a phone, serial or account number, or a vendor's figure into the repository (F-185);
- print, paste or ask for an API key in the chat;
- send a patient's file through the assistant's workspace (D656);
- delete anything that is not his to delete — deleting is his (by his word, through his browser);
- hand him a diagnostic, a technical choice, or a question in shorthand (F-1002).

**CLOSED BY HIS WORD — DO NOT RAISE AGAIN:** everything closed at S318, S323, S337 · **D764** stands as built (*"It's fine"*, 21:45 IST 22-Oct) · **D766** done · **D767** live · asset 12 deleted · record 13 is the digital X-ray's AMC — it stays · the IFT continues without cover · the Clinic inverter is a regular inverter (not solar) · B-0105 is a clinic expense · assets 2 and 3 are two ACs · the X-ray UPS set at the NK rate.

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
18. Every kit is read by an independent cold review before its publish is named; a fix round revises the same kit in place and is read again (F-901, F-1005).
19. A kit is finished when he can reach it from where he starts, at his screen's size (F-898).
20. His board carries only what needs him and what he should know; every close answers what he typed there (D526, D684).
21. His own items are deferred unless urgent.

## 1 · THE CURRENT CANON — the manifest wins

| what | file |
|---|---|
| Register | `KB_Register_v5_178_S341close.md` (clone only) |
| History Archive | `KB_History_Archive_v1_175_S341close.md` (§S341; D766 … D769 in full) |
| Fault → Action Register | `Fault_Action_Register_v2_163.md` (§7.97 = F-1003, F-1004, F-1005) |
| Runbook | `HANDOFF_RUNBOOK_2026-10-23_Session341close_v258.md` (**§2C the order; §1L where things are**) |
| close routine | `END_OF_SESSION_PROMPT_v18.md` |
| build norm | `BUILD_NORM_v1.md` (D704) |
| live pins | `live_pins_S341close.txt` (this project's DECLARED-PENDING 0) |
| build brief | `S341_BUILD_BRIEF.md` |
| the project's record | `SCANAPP_SYSTEM_BOOK_v8_S341.md` |
| numbers | System Board `board/_numbers` — at this close: **D770 · F-1006 · A-D25 · kit S634 · session 343 next; 342 RESERVED for the Scan App chat** |

*Written at the S341 close, 23-Oct-2026.*
