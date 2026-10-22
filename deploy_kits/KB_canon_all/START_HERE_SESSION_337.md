# START HERE — SESSION 337 — written at the S323 close (the Scan App project), 22-Oct-2026

**Project: Scan App — Papers & Bills.** Open in a fresh chat in this project, on manojz. First run `SCANAPP_START_HERE_PROMPT_v1`'s Phase 0 (the project's custom instructions), then this file.

**Where things stand.** Three kits went live at S323 (18-Oct):
- the battery first setup (S575) — the owner then set up 14 of his 16 battery places;
- the X-ray department's expenses page (S582, D736; `xray_costs.py` new);
- many stationery items on one screen (S585, D738) — **installed OFF** until he switches it on; X-ray a place; Void; Shavez's sheet as history.

He also entered, as owner, the stationery opening count (18-Oct), the FDR AMC cover and two back-dated bills (B-0203, B-0204).

**One build is waiting: S623_STATIONERY_CHALLAN_HISTORY (D756)** — the six Variety challans entered as received history, dated on each challan, before the opening count; his rulings of 12:09 IST 22-Oct are in the brief. Brief v2 is ready (R1 binding) and its PLANNED line stands on `stationery.py`. It was not run because he said *"do EOS here and then build this in the next fresh chat in this project"*.

**What to read:**
- the brief for him: `S323_BUILD_BRIEF.md`;
- the project's record: `SCANAPP_SYSTEM_BOOK_v6_S323.md` (§13 is new);
- the build norm: `BUILD_NORM_v1.md` (D704, binding);
- the Runbook v253 (§2C: the order; §1L: where things are);
- for S623: `claude_code_briefs\S623_STATIONERY_CHALLAN_HISTORY.md` (v2, `aada3d74`), its R1 `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S323\S623_BRIEF_R1.md` (`8cfeea39`, 3 BLOCKER · 7 CORRECTION · 8 NOTE — binding), the kit it copies `deploy_kits\S585_STATIONERY_ISSUE_MANY\` and `claude_code_briefs\REPORT_S585.md`.

The close routine is `END_OF_SESSION_PROMPT_v18.md`.

**First act:** take your session number from the System Board `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).
- *Session numbers at this close:* **337 is RESERVED for the Scan App chat**. 336 is the parent's (reserved) and 335 the Sanjeevni chat's (open).
- *A kit number is claimed before its scratch folder is named (F-831).* S623 is already claimed.
- *Counters at this close:* **D757 · F-981 · A-D25 · kit S624 · session 338 next.**

**Working rules on manojz:**
- Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.
- **Never run `git` in `device_bash` (F-511, F-833)** — read `.git/logs/HEAD` and the refs.
- A `.gitignore` check is last-match-wins (F-832), over every unpublished kit folder, any chat's (F-971).
- Set `SANJ_CONFIG_STORE=$HOME/mnt/Downloads/margsync/_config` before the number gate (F-810).
- Open the bundle or a database copy only under the session's own home, and remove it after (F-752).
- A file sent to the PC is proven by its md5 read there under a new staged name, never by the tool's success line (F-900, F-963).
- An interrupted runner build is resumed by a brief that first proves nothing live moved, never re-run blind (F-908).

***Every time you write is read first — from the clock tool, a commit stamp, a file's time or a program's own line (F-791, F-510).***

---

## 0 · THE WORK — in the owner's order

**A · THE OPEN'S FIRST WORK — short (the steps v18 moved to the open).**

1. **Verify this close's publish landed (A16b) — the first act after the board.**
   - `.git/logs/HEAD` = `refs/remotes/origin/main`, and the commit is later than `7b39f376` (13:25:07 IST 22-Oct — the publish that already carried the S623 brief).
   - The S323 canon files are in the tree at the md5s the manifest names, and `claude_code_briefs\S623_STATIONERY_CHALLAN_HISTORY.md` is `aada3d74`.
   - `md5sum -c MD5SUMS_ALL.txt` from inside `deploy_kits/KB_canon_all/`, with the count.

   If it has not landed, say so in one line and name the file:

```
D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat
```

2. **Read the System Board:** every item document with a `note`, every message with `read:false`. Say in one line how many are waiting.
3. **The three nightly reports** — exists · clock time · verdict, for each one (`D:\Downloads\_kbtools\REBUILD_REPORT_LATEST.txt`, `MAINTENANCE_REPORT_LATEST.txt`, `CANON_SUMS_LATEST.txt`). manojz may have been off at 03:10: read the time, not the date.
4. **The pin pass on the newest bundle** (`D:\Downloads\_kbtools\vps_code\code_nightly.tar.gz`, self-checking against its `MANIFEST.md5`) with `live_pins_S323close.txt`. **This project's DECLARED-PENDING is 0**: `batteries.py` 775471e6, `xray_costs.py` 22e59f5a, `stationery.py` 18268ff0, `sorting_desk.py` 110335ea, `clinic_papers.py` 6db07c12 and `asset_machine.py` 7d4fdffc equal the 22-Oct bundle. **Moved by the Sanjeevni chat's S618_SCAN_QUALITY (live 10:54 IST 22-Oct, after that bundle): `asset_register.py`, `scanner_widget.js`, `claude_reader.py`, and NEW `/root/shared/scan_quality.py`** — read their TO pins from that chat's board line of 22-Oct 12:22 IST (its kit's `PINS.sh` names TO `70e35b10…`, `b936f0f3…`, `10118909…`, `16fb2402…`; `claude_reread.py` read only at `ed7023d2`) and hold them against the 23-Oct bundle. The parent's `packs.py` moved by its S621 / S622 (from `e46264b8`; kit TOs `6ed8e18a`, then `94923368`) — the parent's. State match / mismatch / not-in-bundle; `static/opencv.js` is expected absent (F-860).
5. **The rest of the open's work:**
   - **The SSD mirror**, listed back.
   - **The sweep.** `D:\dr-manoj-git\_to_delete_S323\` was not present at this close (S575 K1's rendered pages were said to be moved there) — look once, say what is there; deleting is his.
   - **The tranche and the measure** (`project_info` at the open and the close only).
   - **The cold kit** — due: the Register and Archive bumped at this close.
   - **The four numbers.** Drift: `sorting_desk.py` **8** and `asset_register.py` **8 + S618**, both over the line; `scanner_widget.js` 5 + S618; `batteries.py` 2; `stationery.py` 1; `clinic_papers.py` 2.
   - **What no store holds.**

**B · THE WORK ITSELF.**

6. **S623_STATIONERY_CHALLAN_HISTORY — first.**
   - **Before giving the line,** check that no other build is running: the newest logs in `D:\Downloads\_kbtools\agent_build\logs\` (a log with no `DONE · cost` line and a recent time) and the server lock `/root/deploy/.claude_code_build.lock` as the board's lines tell it; and whether another chat's Claude Code build is open. If one is running, say so in one line and wait.
   - **Confirm the brief on the PC is v2** — its first lines say v2 and R1 `8cfeea39`, and its md5 is `aada3d74` (F-963).
   - **His one line:**

```
python D:\Downloads\_kbtools\agent_build\run_build.py S623_STATIONERY_CHALLAN_HISTORY
```

   - **Then:**
     - an independent kit review K1 against the brief, R1 and the live bytes (the installer's gates read on the box: B-0013's existing lines, each paper's group and status, the live item names, the current stocks);
     - a fix round in place if needed;
     - the publish (his double-click) and his one server line;
     - the result read live as the owner, by a sub-agent, at 1366 × 768 — the Stationery page's received history and the nine counted stocks unchanged;
     - the board's install line, DONE / RELEASED for `stationery.py`.
   - **Facts S623 rests on** (R1): one stamp per paper = its challan date 12:00 IST, B-0013's two existing lines restamped to it; each new line takes its paper's own reading line number; every written row marked (`by_whom` `history (Variety challans, S623)`) with an `--undo`; the token fix = void the one row + a new line of 1; the four uncounted items checked by their MOVE (A4 +21, File folder +3, X-ray envelope +500, Token −99); 13 new lines plus the token fix; ALREADY INSTALLED = the done-key `stationery.history_s623` is set.
7. **Then the next scan-app round** (seen, not built — offer it to him in plain words, one line each): F-976 the machine Edit form resets the purchase day to 01 · F-977 a battery past its warranty shows OK · F-978 no door to link a machine cover's paper afterwards · F-979 the stationery match ignores the item's unit · F-980 a back-dated bill counts in its scan month · the X-ray page does not net Jasoria's old-battery amount · B-0163 adds Rs 0 until its bill comes.
8. **Drift.** A kit that patches `sorting_desk.py` or `asset_register.py` reads it whole and consolidates first (F-836) — and `asset_register.py` is now at S618's byte.
9. **Parked at his word — do not raise:** the Claude-vs-Sarvam reading comparison.

**HIS, OPEN (on the board):**
- **Y118** — the publish of this close (the file above).
- **Y119** — *Many items on one screen* ON when he is happy with it: the card at the top of his Stationery page:

```
https://followup.dr-manoj.in/scanapp/stationery
```

- **Y120** — the Vento's and the DTH lab's battery dates, under *First setup*:

```
https://followup.dr-manoj.in/scanapp/batteries
```

- **Y121** — scan Fujifilm's GST tax invoice for the FDR AMC when it comes (the email went from his personal Gmail ~10:4x IST 22-Oct).
- Not urgent: the remaining *Switches* taps for Shavez (*Sorting desk*, *Machine pages*, *Batteries*); Y83.

**THE API CREDIT:** USD 185.48 at 06:4x IST 18-Oct, valid to 18-Nov-2026; the runner drew USD 25.74 for S575, S582 and S585. Read it again from his Console only when a figure is needed.

**FOR THE OTHER CHATS (on the board, not this project's):**
- the parent: `packs.py` moved by S621 / S622 — a scan-app kit never touches it; the clinic's purchase bills into the pack wait by his word; the portal tile *Scan app & assets*.
- the Sanjeevni chat: S618's three scan-app files — its rows; build only from its TO bytes.

**NEVER:**
- guess a section, a sub-section or whose expense a paper is (D664); let the system tick a machine or a battery place for X-ray;
- move a paper a person placed, including by linking it to a battery, a stationery line or an X-ray mark;
- edit `scanner_widget.js` without a PLANNED line and walking the seven surfaces (D646);
- install a staff screen switched on;
- put a vehicle registration or a phone, serial or account number, or a vendor's figure into the repository (F-185);
- print, paste or ask for an API key in the chat;
- send a patient's file through the assistant's workspace (D656);
- name a runner kit's publish before an independent cold review has read it (F-901);
- hand him a diagnostic or a technical choice.

**CLOSED BY HIS WORD — DO NOT RAISE AGAIN:**
- everything closed at S318 (D710, D711, D721, D722, D723, D728, D730; the smart scanner; reception's lane buttons; the 61 test scans stay);
- **D736** — a paper keeps its one group and may also count for the X-ray department; the X-ray page adds each rupee once — live;
- **D738** — the opening stock as he gave it; many items on one screen (OFF until he says final); Shavez's sheet as history; X-ray a place — live;
- **D756** — the six Variety challans as received history before the opening count, with his item rulings of 12:09 IST 22-Oct (the NK Pathology estimate books stay out; the token line is 1 packet) — S623 to build;
- the Claude-vs-Sarvam comparison — parked.

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
17. Builds go through the parent's Agent SDK runner on his API credit (D727). Before a runner line, check that no other build holds the server.
18. Every runner kit is read by an independent cold review before its publish is named; a fix round revises the same kit in place (F-901).
19. A kit is finished when he can reach it from where he starts, at his screen's size (F-898).
20. His board carries only what needs him and what he should know; every close answers what he typed there (D526, D684).
21. His own items are deferred unless urgent.

## 1 · THE CURRENT CANON — the manifest wins

| what | file |
|---|---|
| Register | `KB_Register_v5_173_S323close.md` (clone only) |
| History Archive | `KB_History_Archive_v1_170_S323close.md` (§S323; D736, D738, D756 in full) |
| Fault → Action Register | `Fault_Action_Register_v2_158.md` (§7.92 = F-976 … F-980, OPEN) |
| Runbook | `HANDOFF_RUNBOOK_2026-10-22_Session323close_v253.md` (**§2C the order; §1L where things are**) |
| close routine | `END_OF_SESSION_PROMPT_v18.md` |
| build norm | `BUILD_NORM_v1.md` (D704) |
| live pins | `live_pins_S323close.txt` (this project's DECLARED-PENDING 0) |
| build brief | `S323_BUILD_BRIEF.md` |
| the project's record | `SCANAPP_SYSTEM_BOOK_v6_S323.md` |
| numbers | System Board `board/_numbers` — at this close (v591): **D757 · F-981 · A-D25 · kit S624 · session 338 next; 337 RESERVED for the Scan App chat** |

*Written at the S323 close, 22-Oct-2026.*
