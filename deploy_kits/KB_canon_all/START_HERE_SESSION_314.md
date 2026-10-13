# START HERE — SESSION 314 — written at the S309 close (the Scan App project), 13-Oct-2026

**Project: Scan App — Papers & Bills.** Open in a fresh chat in this project, on manojz. Run `SCANAPP_START_HERE_PROMPT_v1`'s Phase 0 (the project's custom instructions) first, then this file. **The work is §0 below — D719 first, in its order: the scan app refined so that he can make it operational beyond the pharmacy (the owner, 13-Oct 06:15: *"currently focus on the refinement of the scan app as we have decided … first fix the scan app … and then come back to the Google Apps Script part"*).** The brief is `S309_BUILD_BRIEF.md`; the build norm is `BUILD_NORM_v1.md` (D704 — binding); the project's record is `SCANAPP_SYSTEM_BOOK_v2_S306.md`; the Runbook is v231 (§2C: the order; §1L: where things are). The close routine is `END_OF_SESSION_PROMPT_v18.md`.

*FIRST ACT: take your session number from the System Board `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1). **314 is RESERVED for the Scan App chat at this close; 313 is the parent's (open since 06:13 IST 13-Oct); 312 RESERVED for the Sanjeevni chat.** Take what the board says and say so in your first line. A kit number is claimed before its scratch folder is named (F-831, F-515). At this close: D721 · F-890 · A-D25 · kit S542 · session 315 next.*

*Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`. `device_bash` worked through S309 on all three; **never run `git` in it (F-511, F-833)** — read `.git/logs/HEAD` and the refs. A `.gitignore` check is last-match-wins (F-832); it blocks `*.json` — a kit's `.json` is named `.txt` or gets its exact `!` line in the same breath. Before the number gate runs in the device shell, set `SANJ_CONFIG_STORE=$HOME/mnt/Downloads/margsync/_config` (F-810). A `pkill -f` pattern never goes in the tool shell's own command line (cleanup and rehearsal from script files). The bundle or a database copy is opened only under the session's own home and removed after (F-752).*

***Every time you write is read first — from the clock tool, a commit stamp, a file's time or a program's own line (F-791, F-510).***

---

## 0 · THE WORK — in the owner's order

**A · THE OPEN'S FIRST WORK — short.**

1. **Read the System Board:** every item document with a `note`, every message with `read:false`. Say in one line how many are waiting.
2. **Verify the S309 close's publish landed** (`.git/logs/HEAD` = `refs/remotes/origin/main`; this close's canon files in the tree; `md5sum -c MD5SUMS_ALL.txt` from inside `KB_canon_all`, with the count). If not, he has not double-clicked yet: say so, name the file.
3. **The three nightly reports** — exists · clock time · verdict, each.
4. **The pin list `live_pins_S309close.txt` against the newest bundle — this project's DECLARED-PENDING is 0** (`asset_register.py` 35f9e823 · `clinic_papers.py` 476e157c · `scanner_widget.js` 65127fcb equal to the 12-Oct bundle; `static/opencv.js` ff1e10e7 never in a bundle, F-860). State the three counts and the pending count.
5. **Owed from S306, not read at S309 — reads only, one line each:** the smart scanner's 12-Oct 08:00 reading (any phone that fell back; whole photos left) · the papers the system placed since S532 (`bill_audit` `auto_lane` / `auto_group`) and any a person changed (each a rule to tighten, never to loosen).
6. **The four numbers · what no store holds · the cap** (`project_info` at the open and the close only). The SSD mirror listed back; the sweep; the tranche if any.

**B · THE WORK ITSELF — D719, in this order (Runbook §2C item 4).**

7. **Read `asset_register.py` whole first (drift 3)** and `clinic_papers.py`'s sections; then **kit a — reception and the renames:**
   - the intake's lanes: **Clinic · Pharmacy · NK Pathology · Other document · Challan** — *Dr MK expense* leaves reception (and `LANE_DEFAULTS['manoj']`);
   - the section **Personal expenses** with sub-sections **Dr MK** / **Dr Bhavna**, for him and Shavez only; with no sub-section it counts under Dr MK (D713 (2)); the existing `owner_expense` papers and their warranties carried in, nothing lost;
   - the asset category *Medical Equipment* → **Dr MK Clinic Equipment**, the existing rows with it;
   - staff screens: reception's intake is a staff screen — **shown to him first** (its five buttons), installed with the old lane still readable.
8. **Kit b — the sorting desk, mock-up first (an artifact he can edit; the build follows his edits line by line; when he says *final*, the mock-up is the specification):** one PC page — the waiting papers · the scan large with every page · Sarvam's reading, editable · lane → section → sub-section · one Save that sorts and accepts (no pop-up, no separate approve page). Read the live papers page, bill page and approve route first (F-889).
9. **Kit c — the asset register:** parts with their own warranties; cover history (warranty, each AMC, renewal reminders; the old kept); spends opening their scanned bills; reached from the desk. Additive on `assets`, `expiries`, `service_logs`, `bill_id`.

**C · AFTER D719 — D720 (the family's documents and renewals; a dedicated Google Apps Script project; Runbook §2C item 6).** Not before D719 is done, unless he says so. The interim correction of the Janitor's list (the TVS insurance of 05-Dec, the Honda of 19-Jan, the yearly four, Dr Bhawna's licence) waits on his word — if 05-Dec comes near with no word, say it once.

**WAITS BY HIS WORD:** the clinic's purchase bills in the accountants' pack (D710 (2)) — *"should wait until it is working properly"*. **Not needed:** Sukhveer's duty line (he keeps scanning).

**NEVER:** guess a section, a sub-section or whose expense a paper is (D664); move a paper a person placed; edit `scanner_widget.js` without a PLANNED line and the seven surfaces walked (D646); install a staff screen switched on; repeat or write any ID number seen in his Google account (F-888); hand him a diagnostic or a technical choice.

**CLOSED BY HIS WORD — DO NOT RAISE AGAIN:** the smart scanner on every phone, no per-phone check (D711) · sorted = accepted (D710) · a challan amber after 15 days; Personal papers to him only · the 61 test scans stay (S468) · Sukhveer's duty line (12-Oct).

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
12. A new staff screen is shown to him as a mock-up first and installed switched off; staff pages Roman Hinglish, his English.
13. Staff flows are friction-free: no waiting on the server, no second tap.
14. Analysis first when he says so (*"do not build or code anything"*), then the build at his word.
15. His approvals are few and arrive together (D683).
16. Every build follows `BUILD_NORM_v1` (D704); patient files never pass through the assistant's workspace (D656).

## 1 · THE CURRENT CANON — the manifest wins

| what | file |
|---|---|
| Register | `KB_Register_v5_151_S309close.md` (clone only) |
| History Archive | `KB_History_Archive_v1_148_S309close.md` (§S309; D719 and D720 in full) |
| Fault → Action Register | `Fault_Action_Register_v2_136.md` (§7.70 = F-887 … F-889) |
| Runbook | `HANDOFF_RUNBOOK_2026-10-13_Session309close_v231.md` (**§2C the order; §1L where things are**) |
| close routine | `END_OF_SESSION_PROMPT_v18.md` |
| build norm | `BUILD_NORM_v1.md` (D704) |
| live pins | `live_pins_S309close.txt` (this project's DECLARED-PENDING 0) |
| build brief | `S309_BUILD_BRIEF.md` |
| the project's record | `SCANAPP_SYSTEM_BOOK_v2_S306.md` (unchanged) |
| numbers | System Board `board/_numbers` — at this close: **D721 · F-890 · A-D25 · kit S542 · session 315 next; 314 RESERVED for the Scan App chat; 313 the parent's, open; 312 RESERVED for the Sanjeevni chat** |

*Written at the S309 close, 13-Oct-2026.*

---

## THE OTHER CHATS — a pointer, not a carried section

**The parent (313, open since 06:13 IST 13-Oct):** its first build is S541_NO_SPLIT_WORD (D718). From this close: D710 (2) waits by the owner's word; D710 (3) needs no duty line — nothing is asked of it. **Sanjeevni (312, reserved):** nothing of its files is touched by D719 (the pharmacy lane stays as it is).
