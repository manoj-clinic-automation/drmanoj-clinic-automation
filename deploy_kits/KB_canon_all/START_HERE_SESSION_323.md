# START HERE — SESSION 323 — written at the S318 close (the Scan App project), 18-Oct-2026

**Project: Scan App — Papers & Bills.** Open in a fresh chat in this project, on manojz. First run `SCANAPP_START_HERE_PROMPT_v1`'s Phase 0 (the project's custom instructions), then this file.

**Where things stand.** Four kits went live at S318:
- the tidy round (S563);
- the last fixes (S566);
- *Stationery & packaging* and its stock, with the accountants' pack taking bills and invoices only (S568, D730);
- the Batteries page (S571, D730).

**One build is waiting: S575_BATTERY_SETUP.** It is the owner's ask of 06:02 IST 18-Oct: record old batteries that have only a date, link older bills, and give each online UPS its count. Its brief v2 is ready (R1 binding) and its PLANNED line stands on `batteries.py`. It was not run at the close because the Sanjeevni chat's build held the server.

**What to read:**
- the brief: `S318_BUILD_BRIEF.md`;
- the project's record: `SCANAPP_SYSTEM_BOOK_v5_S318.md`;
- the build norm: `BUILD_NORM_v1.md` (D704, binding);
- the Runbook v238 (§2C: the order; §1L: where things are);
- for S575: `claude_code_briefs\S575_BATTERY_SETUP.md`, its R1 `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S318\S575_BRIEF_R1.md`, and `REPORT_S571.md`.

The close routine is `END_OF_SESSION_PROMPT_v18.md`.

**First act:** take your session number from the System Board `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).
- *Session numbers at this close:* **323 is RESERVED for the Scan App chat**. 322 is the Sanjeevni chat's and 319 the parent's (both open).
- *A kit number is claimed before its scratch folder is named (F-831).* S575 is already claimed.
- *Counters at this close:* D731 · F-910 · A-D25 · kit S577 · session 324 next.

**Working rules on manojz:**
- Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.
- **Never run `git` in `device_bash` (F-511, F-833)** — read `.git/logs/HEAD` and the refs.
- A `.gitignore` check is last-match-wins (F-832).
- Set `SANJ_CONFIG_STORE=$HOME/mnt/Downloads/margsync/_config` before the number gate (F-810).
- Open the bundle or a database copy only under the session's own home, and remove it after (F-752).
- A file sent to the PC is proven by its md5 read there under a new staged name, never by the tool's success line (F-900).
- An interrupted runner build is resumed by a brief that first proves nothing live moved, never re-run blind (F-908).

***Every time you write is read first — from the clock tool, a commit stamp, a file's time or a program's own line (F-791, F-510).***

---

## 0 · THE WORK — in the owner's order

**A · THE OPEN'S FIRST WORK — short (the steps v18 moved to the open).**

1. **Verify this close's publish landed (A16b) — the first act after the board.**
   - `.git/logs/HEAD` = `refs/remotes/origin/main`.
   - The S318 canon files are in the tree at the md5s the manifest names, and `claude_code_briefs\S575_BATTERY_SETUP.md` is `9cf7fc7f`.
   - `md5sum -c MD5SUMS_ALL.txt` from inside `deploy_kits/KB_canon_all/`, with the count.

   If it has not landed, say so in one line and name the file:

```
D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat
```

2. **Read the System Board:** every item document with a `note`, every message with `read:false`. Say in one line how many are waiting.
3. **The three nightly reports** — exists · clock time · verdict, for each one (`D:\Downloads\_kbtools\REBUILD_REPORT_LATEST.txt`, `MAINTENANCE_REPORT_LATEST.txt`, `CANON_SUMS_LATEST.txt`). manojz may have been off at 03:10: read the time, not the date.
4. **The pin pass on the newest bundle** (`D:\Downloads\_kbtools\vps_code\code_nightly.tar.gz`, self-checking against its `MANIFEST.md5`) with `live_pins_S318close.txt`. This project's **DECLARED-PENDING is 0**: all eight files equal the 18-Oct bundle. They are `sorting_desk.py` 110335ea, `asset_register.py` c39c084e, `batteries.py` 9a0054ac, `clinic_papers.py` 6db07c12, `stationery.py` d11d7183, `asset_machine.py` 7d4fdffc, `scanner_widget.js` 10a8bb29 and the parent's `packs.py` e46264b8. State match / mismatch / not-in-bundle; `static/opencv.js` is expected absent (F-860).
5. **The rest of the open's work:**
   - **The SSD mirror**, listed back.
   - **The sweep.** `D:\dr-manoj-git\_to_delete_S318\_scratch\` holds this project's six runner folders; deleting them is his.
   - **The tranche and the measure** (`project_info` at the open and the close only).
   - **The cold kit**, when due. The Register and Archive bumped at this close, so it is due.
   - **The four numbers.** Drift: `sorting_desk.py` **8** and `asset_register.py` **8**, both over the line; `scanner_widget.js` 5; `clinic_papers.py` 2.
   - **What no store holds.**

**B · THE WORK ITSELF.**

6. **S575_BATTERY_SETUP — first.**
   - **Before giving the line,** check that no other build is running: the newest logs in `D:\Downloads\_kbtools\agent_build\logs\` (a log with no `DONE · cost` line and a recent time), and ask whether a Claude Code build of another chat is open. If one is running, say so in one line and wait.
   - **His one line:**

```
python D:\Downloads\_kbtools\agent_build\run_build.py S575_BATTERY_SETUP
```

   - **Then:**
     - an independent kit review K1 against the brief, R1 and the live bytes;
     - a fix round in place if needed, and K2;
     - the publish (his double-click) and his one server line;
     - the result read live as the owner, by a sub-agent, at 1366 × 768;
     - the board's install line, DONE / RELEASED for `batteries.py`.
   - **Then tell him, in plain words,** that he can record his batteries under *First setup* on the Batteries page:

```
https://followup.dr-manoj.in/scanapp/batteries
```

   - **Facts S575 rests on** (from R1, read on the 18-Oct bundle):
     - "Old battery — no bill" is stored as `bill_id=NULL` with `bill_created_at='none:old-battery'`;
     - `candidates()` and `_pickable()` stay unchanged;
     - the stamp normaliser is `sorting_desk._s566_stamp_form`;
     - the walk uses N=4 and expects 2024's warranty to have passed.
7. **Drift.** The next kit that patches `sorting_desk.py` or `asset_register.py` reads it whole and consolidates first (F-836). S575 touches `batteries.py` only.
8. **Parked at his word — do not raise:** the Claude-vs-Sarvam reading comparison (`claude_code_briefs/S315_READING_COMPARE.md`, ready).

**HIS, WHEN HE WANTS (not urgent):**
- These are taps on the *Switches* card (owner only) of the scan app's home page: *Sorting desk for Shavez* · *Machine pages for Shavez* · *Batteries for Shavez* · *Stationery diya for managers*:

```
https://followup.dr-manoj.in/scanapp/
```

- Y83, the stop-gap fix of the Janitor's renewal mail (his yes).
- The DTH lab's battery payer (shown as *"to confirm"*) — only if he raises it.

**THE API CREDIT:** USD 185.48 at 06:4x IST 18-Oct, valid to 18-Nov-2026. Claude reads scans while it lasts; the runner uses it too.

**FOR THE PARENT (on the board, not this project's):**
- `packs.py` is `e46264b8` (S568): build only from that byte.
- The portal tile *Asset Register — Clinic assets & AMC* → *Scan app & assets*.
- The clinic's purchase bills into the pack (D710 (2)) wait by his word.
- Shavez's sorting duty, when the desk is switched on.
- The Aumni Crafts invoice pickup from his Gmail is the Janitor's.

**NEVER:**
- guess a section, a sub-section or whose expense a paper is (D664); guess the DTH lab's payer;
- move a paper a person placed, including by linking it to a battery or a stationery line;
- edit `scanner_widget.js` without a PLANNED line and walking the seven surfaces (D646);
- install a staff screen switched on;
- put a vehicle registration or a phone, serial or account number into the repository (F-185);
- print, paste or ask for an API key in the chat;
- send a patient's file through the assistant's workspace (D656);
- name a runner kit's publish before an independent cold review has read it (F-901);
- hand him a diagnostic or a technical choice.

**CLOSED BY HIS WORD — DO NOT RAISE AGAIN:**
- the smart scanner on every phone (D711); reception's lane buttons ON;
- sorted = accepted (D710); Dr Bhawna's file in the pack (D721);
- patient implant bills go to the surgical case pack (D722);
- Claude reads every scan, with Sarvam as the fallback (D723);
- the sorting desk (D722) and receipts, statements and construction's tick (D728) — live;
- batteries: reception untouched, B.L. for UPS (1-year warranty, the bill with the battery), Jasoria for the rest (bill, warranty card, old battery paid) — D730, live;
- stationery: general stationery is a clinic expense tracked from quantities; Elegans carry bags are a clinic expense; Aumni Crafts is a Sanjeevni pharmacy expense; estimates are internal only — D730, live;
- the Claude-vs-Sarvam comparison — parked;
- the 61 test scans stay.

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
14. Analysis first when he says so (*"don't build or code anything now"*), then the build at his word.
15. His approvals are few and arrive together (D683).
16. Every build follows `BUILD_NORM_v1` (D704); patient files never pass through the assistant's workspace (D656).
17. Builds go through the parent's Agent SDK runner on his API credit (D727). Before a runner line, check that no other build holds the server.
18. Every runner kit is read by an independent cold review before its publish is named; a fix round revises the same kit in place (F-901).
19. A kit is finished when he can reach it from where he starts, at his screen's size (F-898).

## 1 · THE CURRENT CANON — the manifest wins

| what | file |
|---|---|
| Register | `KB_Register_v5_158_S318close.md` (clone only) |
| History Archive | `KB_History_Archive_v1_155_S318close.md` (§S318; D730 in full) |
| Fault → Action Register | `Fault_Action_Register_v2_143.md` (§7.77 = F-908, F-909) |
| Runbook | `HANDOFF_RUNBOOK_2026-10-18_Session318close_v238.md` (**§2C the order; §1L where things are**) |
| close routine | `END_OF_SESSION_PROMPT_v18.md` |
| build norm | `BUILD_NORM_v1.md` (D704) |
| live pins | `live_pins_S318close.txt` (this project's DECLARED-PENDING 0) |
| build brief | `S318_BUILD_BRIEF.md` |
| the project's record | `SCANAPP_SYSTEM_BOOK_v5_S318.md` |
| numbers | System Board `board/_numbers` — at this close: **D731 · F-910 · A-D25 · kit S577 · session 324 next; 323 RESERVED for the Scan App chat** |

*Written at the S318 close, 18-Oct-2026.*

---

## THE OTHER CHATS — a pointer, not a carried section

**The parent (319, open):**
- `packs.py` is `e46264b8` (S568: `build_bundle` takes bills and invoices only), RELEASED at install.
- `scanner_widget.js` is `10a8bb29` (S563); a finance kit that pins the widget reads that.

**Sanjeevni (322, open):**
- Aumni Crafts papers are kind *Pharmacy expense* on the pharmacy lane, so they never enter its Marg pairing.
- Claude's readings of pharmacy papers stay in `assets.db` `claude_reading` for its use.
