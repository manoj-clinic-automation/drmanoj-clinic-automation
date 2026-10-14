# START HERE — SESSION 317 — written at the S313 close (the parent), 14-Oct-2026

**Project: Dr Manoj Clinic — Systems & Automation (the parent).** Open in a fresh chat in this project, on manojz.
1. Run `START_HERE_PROMPT_v10`'s Phase 0 (the project's custom instructions) first, then this file.
2. **The work is §0 below. Its first job is S558_RING_LIST_LINK_CALL (D726; F-896).** The owner's word at the close: *"1 any staff · 2 yes · and do eos here, and this is 1st job in fresh chat of this project".*
   - The brief is final: `claude_code_briefs/S558_RING_LIST_LINK_CALL.md` (f3deb4b5).
   - The build norm is `BUILD_NORM_v1.md` (D704 — binding).
   - The Runbook is v234 (§2A: the order; §1O: what S313 made live and S558's plan).
   - The owner's paper is `S313_BUILD_BRIEF.md`.
   - The close routine is `END_OF_SESSION_PROMPT_v18.md`.

*FIRST ACT: take your session number from the System Board `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).*
- **317 is RESERVED for the parent at this close.** 315 is the Scan App chat's (open); 316 is the Sanjeevni chat's (open). Take what the board says and say so in your first line.
- **Kit S558 is already claimed for this job (with its PLANNED line on `ring_outcome.py` and `ring_common.py`) — do not claim it again.** Any further kit is claimed before its folder is named (F-515).
- At this close: D728 · F-897 · A-D25 · kit S559 · session 318 next.

*Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.*
- `device_bash` worked through S313. **Never run `git` in it (F-511)** — read `.git/logs/HEAD` and the refs.
- `.gitignore` is last-match-wins and blocks `*.json` — ship `.json.kit`.
- Set `SANJ_CONFIG_STORE=$HOME/mnt/Downloads/margsync/_config` before the number gate runs in the device shell (F-810).

***Every time you write is read first — the clock tool, a commit stamp, a file's time or a program's own line (F-510).***

---

## 0 · THE WORK — in the owner's order

**A · THE OPEN'S FIRST WORK — short; the job waits on nothing here except a red.**

1. **Read the System Board:** every item document with a `note`, every message with `read:false`. Say in one line how many are waiting (none at this close). **Remind him of the packs page (name the 25 card shops; type the card and ICICI passwords) — every session until done (D713).**
2. **Verify the S313 close's publish landed:**
   - `.git/logs/HEAD` = `refs/remotes/origin/main`;
   - this close's canon files are in the tree: Register v5.154, Archive v1.151, Fault v2.139, Runbook v234, this file, `S313_BUILD_BRIEF.md`, `S313_CLOSE_REPORT.md`, `live_pins_S313close.txt`, the manifest, `OWNER_TODO_LIVE.md`, `MD5SUMS_ALL.txt`;
   - `claude_code_briefs/S558_RING_LIST_LINK_CALL.md` f3deb4b5;
   - `md5sum -c MD5SUMS_ALL.txt` from inside `KB_canon_all`, with the count.
   If it has not landed, he has not double-clicked yet: name the file once.
3. **The three nightly reports** — exists · clock time · verdict, each. Read the clock time, not the date (manojz is often off at 03:10).
4. **The pin list `live_pins_S313close.txt` against the newest bundle.**
   - **The parent's DECLARED-PENDING is 5** — `physio_book.py` a085fee7, `finance_app.py` 87cc4266, `clinic_money.py` 0a2085ca, `aaj_duties.json` fa5cfac5, `aaj_seed.py` a97cd07b — all installed after the 14-Oct bundle. The 15-Oct bundle should settle them.
   - State the three counts and the pending count.
   - Note: the MAINTENANCE report of 14-Oct ran against `live_pins_S311close.txt` and showed 7 *mismatches*. They are this session's S541/S542/S549 files, now pinned and equal to the 14-Oct bundle — not a fault.
5. **The punch watch (S535):** `root/finance/punch_sources_summary.json` inside `D:\Downloads\_kbtools\vps_code\code_nightly.tar.gz` — its `verdict` in one line.
6. **The rest of the open's work:**
   - the SSD mirror listed back · the sweep · the tranche with the measured project-knowledge size before and after;
   - the four numbers · what no store holds;
   - the cold kit — v18's rule decides (this close bumped the Register and Archive, so it is likely due).

**B · THE WORK ITSELF**

7. **S558_RING_LIST_LINK_CALL — FIRST (D726; F-896).**
   - **The owner, 14-Oct, on `https://followup.dr-manoj.in/portal/ring/list`:** *"patients … call from a different number … register themselves with a different number … that functionality is missing … there should be a click to call link to IVR number as the callback tracker does. For the no shows"*.
   - **His answers 09:02:** *"1 any staff · 2 yes"* — any staff may link; the second number is remembered.
   - **First,** re-hash the brief's four pins against the newest bundle: `ring_outcome.py` 7cb60aad, `ring_common.py` 4344b592, `call_api.py` 930b42c4, `portal.py` f8b059f6. If one moved, re-anchor the brief before the line.
   - Run `D:\Downloads\_kbtools\agent_build\run_build.py --check` yourself (a call capped at $0.50; never print the key).
   - Then give him the one line, in its own copy block:

```
python D:\Downloads\_kbtools\agent_build\run_build.py S558_RING_LIST_LINK_CALL
```

   - **While it runs,** read its log in `D:\Downloads\_kbtools\agent_build\logs\` (reads only).
   - **After it:**
     - read `claude_code_briefs/REPORT_S558.md`;
     - add the board line (the runner cannot write the board);
     - read the list live as `manoj`, both switches off, through a sub-agent with counts only — **no patient name or number in the main thread**;
     - **show him the two new things on the page** (*Doosre number se link* · *IVR call button*) — he switches them on;
     - then read it once as a staff login (`shavez` or `reception`, through `https://followup.dr-manoj.in/finance/api/whoami` first).
   - The credits end **17-Oct**. If the runner refuses for lack of credit, the fallback is the Claude Code paste line: `Read BUILD_NORM_v1.md first, then build, walk, install and publish kit S558 exactly as claude_code_briefs/S558_RING_LIST_LINK_CALL.md says, and write claude_code_briefs/REPORT_S558.md.`
8. **Housekeeping on the server (the assistant's):** `/tmp/s554kit` and `/tmp/s554probe` (S554's scratch; no secret, no number) — removed inside the next kit's install or by the runner. Never a line of his.
9. **The assistant's, in the background:** the console's doubled *"counter sheet not filled"* line · F-808's loud line · F-742 the finance self-test suite · the 148 transcription-only documents.
10. **Physio — PARKED at his word (D724), not raised:** the sessions in the patient 360° record · *physiotherapy advised* → Bhati's page (name, clinic ID, full mobile) · Bhati's absence tap → WABA to his clinic patients. **Spell the name Bhati (B-H-A-T-I), never "Bharti".**
11. **Punch step 2 (D713 (4))** — after about 19-Oct, only on a week of ONE MARK.

**ON HIS WORD ONLY — not raised:** a *send to Shavez* button for the bank check (D717 (1)) · the follow-up tracker on the server (*"later"*, D717 (2)).

**PARKED AT HIS WORD — NOT TO BE RAISED; he raises it:** the staff's WhatsApp alerts made loud (D692 — a topic name is a key: never in the repository, a kit, a page, the board or a chat line) · club C — the mailbox clean-up (D702) · the tracker's move (D717 (2)). **Held:** the Callback Tracker move (D634).

**Owner-side, on his board:** the publish · **the packs page (shops and passwords — remind every session)** · the Marg engineer's restore test · Ranjeet's login · the reception PC's Windows · the Docterz report export · the arms licence (November).

**CLOSED BY HIS WORD — DO NOT RAISE AGAIN:** everything listed so in `START_HERE_SESSION_313.md` stands, and two items are added:
- **the after-call list works well (14-Oct)** — only S558's two additions are wanted;
- **the WhatsApp alert is off Google (D725)** — do not bring `wa-notifier` back.

**Before any owner-only or staff-only step in the assistant's browser:** read `https://followup.dr-manoj.in/finance/api/whoami`. **The assistant does not type credentials for him.** **Patient files never pass through the assistant's workspace (D656).** **No phone number in the repository (F-185) — a walk joins made-up numbers at run time.**

**Standing owner rulings (restated):** rules 1–27 of `START_HERE_SESSION_313.md` stand whole. Three are added:

28. **While his API credits last (to 17-Oct), a build goes through the Agent SDK runner from his one line (D727).** The credits do not pay for Claude Code (F-895).
29. **A statement about what a vendor's product or credit covers is read from the vendor's own terms before it is said (F-895).**
30. **A job is watched by what it produces, not by whether its process is up (F-894).**

## 1 · THE CURRENT CANON — the manifest wins

| what | file |
|---|---|
| Register | `KB_Register_v5_154_S313close.md` (clone only, D550) |
| History Archive | `KB_History_Archive_v1_151_S313close.md` (§S313) |
| Fault → Action Register | `Fault_Action_Register_v2_139.md` (§7.73 = F-894 … F-896; F-869 closed) |
| Runbook | `HANDOFF_RUNBOOK_2026-10-14_Session313close_v234.md` (**§2A the order; §1O what S313 made live and S558's plan**) |
| close routine | `END_OF_SESSION_PROMPT_v18.md` |
| build norm | `BUILD_NORM_v1.md` (D704) |
| live pins | `live_pins_S313close.txt` (the parent's DECLARED-PENDING 5) |
| build brief | `S313_BUILD_BRIEF.md` |
| numbers | System Board `board/_numbers` — at this close: **D728 · F-897 · A-D25 · kit S559 · session 318 next; 317 RESERVED for the parent; 315 the Scan App chat's, open; 316 the Sanjeevni chat's, open; kit S558 claimed for this job** |

## 2 · WHAT THIS SESSION MADE LIVE — the short map

| what | where | state |
|---|---|---|
| No *Split* word; each line as it was paid (S541) | `https://followup.dr-manoj.in/finance/clinic/day/2026-10-12` | live 08:05 13-Oct |
| The console's money from Docterz's day total; a fresh reading on opening (S542) | the command console | live 08:05 13-Oct |
| The WhatsApp → phone alert made by the server itself (S549) | `wa-receiver` → `wa_alert.py` | live 19:27 13-Oct; his test alert came |
| Bhati's physiotherapy register, his duty line, backfill from 01-Oct (S552–S554) | `https://followup.dr-manoj.in/finance/physio/book` | live 05:29 → 07:04 14-Oct; opened for Bhati |
| The Agent SDK runner (D727) | `D:\Downloads\_kbtools\agent_build\run_build.py` | in use by all three chats |

*Written at the S313 close, 14-Oct-2026.*

---

## THE OTHER CHATS — a pointer, not a carried section

- **The Scan App (315, open):** its entry point `START_HERE_SESSION_315.md`; it builds on the runner too (S550, S551, S555).
- **Sanjeevni (316, open):** its entry point `START_HERE_SESSION_316.md`; S543 installed 08:38 IST 14-Oct on the runner.
- **For both, from this close:** the parent's `clinic_money.py` is at `0a2085ca` (S552), and `finance_app.py` at `87cc4266`. Build only from those bytes.
