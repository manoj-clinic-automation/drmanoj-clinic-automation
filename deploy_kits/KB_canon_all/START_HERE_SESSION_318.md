# START HERE — SESSION 318 — written at the S315 close (the Scan App project), 15-Oct-2026

**Project: Scan App — Papers & Bills.** Open in a fresh chat in this project, on manojz. Run `SCANAPP_START_HERE_PROMPT_v1`'s Phase 0 (the project's custom instructions) first, then this file.

**Where things stand.** Everything the owner asked for is live: the sorting desk (S551), its corrections (S555), each machine's page (S557, *"the final kit"*), one menu and one road (S559) and receipts and statements with the desk on one laptop screen (S560, D728). **No build is waiting.** This session verifies the close, settles S560's four pins on the 16-Oct bundle, and does one small round **only when he asks**. His API credits end on 17-Oct: Claude reading then falls back to Sarvam by itself, and the Agent SDK runner needs credit too.

**What to read:**
- the brief: `S315_BUILD_BRIEF.md`;
- the project's record: `SCANAPP_SYSTEM_BOOK_v4_S315.md`;
- the build norm: `BUILD_NORM_v1.md` (D704, binding);
- the Runbook v235 (§2C: the order; §1L: where things are);
- the runner's reports, when a review note is touched: `claude_code_briefs/REPORT_S551.md`, `REPORT_S555.md`, `REPORT_S557.md`, `REPORT_S559.md`, `REPORT_S560.md`.

The close routine is `END_OF_SESSION_PROMPT_v18.md`.

*FIRST ACT: take your session number from the System Board `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).*
- *Session numbers at this close: **318 is RESERVED for the Scan App chat**; 317 is the parent's (open); 316 is the Sanjeevni chat's (open).*
- *A kit number is claimed before its scratch folder is named (F-831).*
- *Counters at this close: D729 · F-903 · A-D25 · kit S561 · session 319 next.*

*Working rules on manojz:*
- *Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.*
- ***Never run `git` in `device_bash` (F-511, F-833)** — read `.git/logs/HEAD` and the refs.*
- *A `.gitignore` check is last-match-wins (F-832).*
- *Set `SANJ_CONFIG_STORE=$HOME/mnt/Downloads/margsync/_config` before the number gate (F-810).*
- *The bundle or a database copy is opened only under the session's own home and removed after (F-752).*
- *A file sent to the PC is proven by its md5 read there, never by the tool's success line (F-900).*

***Every time you write is read first — from the clock tool, a commit stamp, a file's time or a program's own line (F-791, F-510).***

---

## 0 · THE WORK — in the owner's order

**A · THE OPEN'S FIRST WORK — short (the steps v18 moved to the open).**

1. **Verify this close's publish landed (A16b) — the first act after the board.** `.git/logs/HEAD` = `refs/remotes/origin/main`; the S315 canon files in the tree at the md5s the manifest names; `md5sum -c MD5SUMS_ALL.txt` from inside `deploy_kits/KB_canon_all/`, with the count. If it has not landed, say so in one line and name the file:

```
D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat
```

2. **Read the System Board:** every item document with a `note`, every message with `read:false`. Say in one line how many are waiting.
3. **The three nightly reports** — exists · clock time · verdict, each (`D:\Downloads\_kbtools\REBUILD_REPORT_LATEST.txt`, `MAINTENANCE_REPORT_LATEST.txt`, `CANON_SUMS_LATEST.txt`). manojz may have been off at 03:10: read the time, not the date.
4. **The pin pass on the newest bundle** (`D:\Downloads\_kbtools\vps_code\code_nightly.tar.gz`, self-checking against its `MANIFEST.md5`) with `live_pins_S315close.txt`. This project's **DECLARED-PENDING is 4**, all S560 (installed 12:55 IST 15-Oct):
   - `sorting_desk.py` `a4623438`;
   - `clinic_papers.py` `88963eac`;
   - `asset_register.py` `9daed9ea`;
   - the parent's `packs.py` `048d2ad8`.
   
   On the 16-Oct bundle each should leave DECLARED-PENDING. State match / mismatch / not-in-bundle and the pending count; `static/opencv.js` is expected absent (F-860). A bundle is 01:35 evidence and nothing later.
5. **The SSD mirror** listed back (`F:\ClinicBackup\DrManojClinic_Automation\01_KB_MIRRORS\` — the newest, its date, size and file count) · **the sweep** · **the tranche and the measure** (`project_info` at the open and the close only) · **the cold kit when due** (the Register and Archive bumped at this close — it is due) · **the four numbers** (drift: `clinic_papers.py` **6** — over the line; `asset_register.py` 4; `sorting_desk.py` 4; `scanner_widget.js` 4) · **what no store holds** · **the statement road**.
6. **Claude reading — a read, one line:** the card on `https://followup.dr-manoj.in/scanapp/admin` (ON / STOPPED, calls today). After 17-Oct it is expected to say STOPPED (the credit ended) with Sarvam reading — that is by design, not a finding.

**B · THE WORK ITSELF — only when he asks.**

7. **One small round** (a kit number claimed first; a PLANNED line on any file another chat owns):
   - **F-902** — on the desk, a paper already set aside shows *"Already set aside on <date> — Restore?"*;
   - review note **N7** (a page deleted while an Adjust picture still loads) — `scanner_widget.js` is shared by seven surfaces: a PLANNED line and all seven walked (D646);
   - `/tmp/s560fix*` on the box cleared (no data);
   - the review notes listed *seen, not changed* in `REPORT_S551/S555/S557/S559/S560.md`.
   
   **`clinic_papers.py` is at drift 6: the round reads it whole and consolidates first.** The build path is his choice after 17-Oct — the chat itself, or Claude Code; the runner needs credit.
8. **Parked at his word — do not raise:** the Claude-vs-Sarvam reading comparison (`claude_code_briefs/S315_READING_COMPARE.md`, ready).

**HIS, WHEN HE WANTS (not urgent):**
- *Sorting desk for Shavez* and *Machine pages for Shavez* on the *Switches* card (owner only) of the scan app's home page — his tap on:

```
https://followup.dr-manoj.in/scanapp/
```

- Y83, the stop-gap fix of the Janitor's renewal mail (his yes);
- after 17-Oct, paid API credit — his choice.

**FOR THE PARENT (on the board, not this project's):** the portal tile *Asset Register — Clinic assets & AMC* → *Scan app & assets*; the clinic's purchase bills into the pack (D710 (2), waits by his word); Shavez's sorting duty when the desk is switched on; `packs.py` is `048d2ad8` — build only from that byte.

**NEVER:**
- guess a section, a sub-section or whose expense a paper is (D664);
- move a paper a person placed;
- edit `scanner_widget.js` without a PLANNED line and the seven surfaces walked (D646);
- install a staff screen switched on;
- print, paste or ask for an API key in the chat — he types it at a hidden prompt on the server;
- send a patient's file through the assistant's workspace (D656);
- name a runner kit's publish before an independent cold review has read it (F-901);
- hand him a diagnostic or a technical choice.

**CLOSED BY HIS WORD — DO NOT RAISE AGAIN:**
- the smart scanner on every phone (D711); reception's lane buttons ON (13-Oct);
- sorted = accepted (D710); Dr Bhawna's file in the pack (D721);
- patient implant bills go to the surgical case pack, not here (D722);
- Claude reads every scan, Sarvam the fallback (D723);
- the sorting desk to his final mock-up (D722) — live;
- receipts, statements, construction's tick and the desk on one screen (D728) — live;
- S557 was the final kit (*"make a final build now"*, 09:15 IST 14-Oct);
- the Claude-vs-Sarvam comparison — parked (*"park claude vs sarvam for now"*);
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
12. A new staff screen is shown to him as a mock-up first and installed switched off; staff pages Roman Hinglish, his English.
13. Staff flows are friction-free: no waiting on the server, no second tap.
14. Analysis first when he says so (*"do not build or code anything"*), then the build at his word.
15. His approvals are few and arrive together (D683).
16. Every build follows `BUILD_NORM_v1` (D704); patient files never pass through the assistant's workspace (D656).
17. While his API credits last (to 17-Oct), builds go through the parent's Agent SDK runner (D727); after that, the build path is his word.
18. Every runner kit is read by an independent cold review before its publish is named; a fix round revises the same kit in place (F-901).
19. A kit is finished when he can reach it from where he starts, at his screen's size (F-898).

## 1 · THE CURRENT CANON — the manifest wins

| what | file |
|---|---|
| Register | `KB_Register_v5_155_S315close.md` (clone only) |
| History Archive | `KB_History_Archive_v1_152_S315close.md` (§S315; D728 in full) |
| Fault → Action Register | `Fault_Action_Register_v2_140.md` (§7.74 = F-897 … F-902) |
| Runbook | `HANDOFF_RUNBOOK_2026-10-15_Session315close_v235.md` (**§2C the order; §1L where things are**) |
| close routine | `END_OF_SESSION_PROMPT_v18.md` |
| build norm | `BUILD_NORM_v1.md` (D704) |
| live pins | `live_pins_S315close.txt` (this project's DECLARED-PENDING 4, all S560) |
| build brief | `S315_BUILD_BRIEF.md` |
| the project's record | `SCANAPP_SYSTEM_BOOK_v4_S315.md` |
| numbers | System Board `board/_numbers` — at this close: **D729 · F-903 · A-D25 · kit S561 · session 319 next; 318 RESERVED for the Scan App chat** |

*Written at the S315 close, 15-Oct-2026.*

---

## THE OTHER CHATS — a pointer, not a carried section

**The parent (317, open):**
- `packs.py` is `048d2ad8` (S560: item 8.4; receipts, statements and awaiting challans out of every bundle) — RELEASED at install.
- `scanner_widget.js` is `1128ac97` (S559.1) — a finance kit that pins the widget reads that.
- The portal tile's name *Scan app & assets* is the parent's to change.

**Sanjeevni (316, open):**
- Claude's readings of pharmacy papers are kept in `assets.db` `claude_reading` for its use; nothing on its papers is written. The pharmacy lane is unchanged; the desk never shows a pharmacy paper.
