# START HERE — SESSION 325 — written at the S319 close (the parent), 18-Oct-2026

**Project: Dr Manoj Clinic — Systems & Automation (the parent).** Open in a fresh chat in this project, on manojz.
1. Run `START_HERE_PROMPT_v10`'s Phase 0 (the project's custom instructions) first, then this file.
2. **THE FIRST JOB IS CARRIED OVER, BY HIS WORD (07:45 18-Oct): "build this as the first thing in the fresh chat in this project."** — D734, the portal-down flow automated (§0 B below; Runbook v240 §2A item 2). Do the open's short work (§0 A) first, then start D734 by asking his two decisions.
   - The Runbook is v240 (§2A: the order; §1Q: what S319 made live).
   - The owner's paper is `S319_BUILD_BRIEF.md`.
   - The build norm is `BUILD_NORM_v1.md` (D704 — binding). The close routine is `END_OF_SESSION_PROMPT_v18.md`.

*FIRST ACT: take your session number from the System Board `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).*
- **325 is RESERVED for the parent at this close.** 324 is RESERVED for the Sanjeevni chat (its S322 close, 07:5x 18-Oct); 323 is the Scan App chat's (open). Take what the board says and say so in your first line.
- At this close: D735 · F-921 · A-D25 · kit S577 · session 326 next.

*Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.*
- `device_bash` worked through S319. **Never run `git` in it (F-511)** — read `.git/logs/HEAD` and the refs.
- `.gitignore` is last-match-wins and blocks `*.json` — ship `.json.kit`.
- Set `SANJ_CONFIG_STORE=$HOME/mnt/Downloads/margsync/_config` before the number gate runs in the device shell (F-810).
- **A D or F number is taken on the board the moment it is minted, never held for the close (F-920 — S319's close had to renumber onto the Sanjeevni chat's).**
- **Do not `project_read` a large superseded document to prove its survivor** — it comes back inline at its whole size (S319 lost ~60k tokens to two). Prove survivors by the repository's gate and `MANIFEST.md5`.

***Every time you write is read first — the clock tool, a commit stamp, a file's time or a program's own line (F-510).***

---

## 0 · THE WORK — in the owner's order

**A · THE OPEN'S FIRST WORK — short, then D734.**

1. **Read the System Board:** every item document with a `note`, every message with `read:false`. Say in one line how many are waiting. **Remind him of the packs page (name the 25 card shops; type the card and ICICI passwords) — every session until done (D713).**
2. **Verify the S319 close's publish landed:**
   - `.git/logs/HEAD` = `refs/remotes/origin/main`;
   - this close's canon files are in the tree: Register v5.160, Archive v1.157, Fault v2.145, Runbook v240, this file, `S319_BUILD_BRIEF.md`, `S319_CLOSE_REPORT.md`, `live_pins_S319close.txt`, the manifest, `OWNER_TODO_LIVE.md`, `MD5SUMS_ALL.txt`;
   - `md5sum -c MD5SUMS_ALL.txt` from inside `KB_canon_all`, with the count.
   If it has not landed, he has not double-clicked yet: name the file once.
3. **The three nightly reports** — exists · clock time · verdict, each. Read the clock time, not the date.
4. **The pin list `live_pins_S319close.txt` against the newest bundle.** The parent's DECLARED-PENDING is **3** (`/root/finance/slip_log.py` 2419c536, `/root/deploy/clinic_doctor.py` af696c77, `/usr/local/bin/clinic-doctor` e22da9c9 — all installed 07:31–07:33 18-Oct, after that day's 01:35 bundle). Say which the 19-Oct bundle carries; the wrapper sits outside `/root` and may not be bundled — then it stays declared, read live once. State the three counts.
5. **The watcher's health:** in his Apps Script project *Clinic Portal Watcher*, Script Properties `lastOk` within the last 10 minutes and `pendingPush` empty. Reading it is the assistant's (the editor in the assistant's browser, his personal account) — no run needed.
6. **The punch watch (S535)** and **the SMS watch (F-903)** — one line each, as in Runbook §2A items 3 and 5.
7. **The rest of the open's work:** the SSD mirror listed back · the sweep · the tranche with the measured project-knowledge size · the four numbers · what no store holds · the cold kit (v18's rule — this close bumped the Register and Archive) · **the unattended pull** (no Drive report since 10-Oct — Runbook §2A item 7).

**B · D734 — THE FIRST BUILD.** His words, 07:43 18-Oct: *"automate the steps as much as possible, so that when I need to run it, it detects the message and the flow starts automatically till as much as it can go. And prompt me accurately for each step."*

1. **Ask him the two decisions first, in plain words, together (AskUserQuestion):**
   - may the server restart its own stuck parts every few minutes without asking him (at most once an hour per part)?
   - may the watcher start or restart the whole server through Hostinger when it is off or stuck (at most once an hour; never during a Hostinger maintenance notice)?
2. **Before building the Hostinger part:** read Hostinger's own API documentation for the VPS status / start / restart calls and confirm they exist. If they do not, say so in one line and keep guide step 4 his.
3. **If he says yes to the second:** he makes one API key in his Hostinger panel and pastes it into the watcher's Script Properties as `HOSTINGER_KEY` (his hand — the assistant does not type credentials; give the steps numbered, one action per line, rule 32). Never printed, never in the repository, a kit, a page, the board or a chat line.
4. **Build (Runbook v240 §2A item 2 has the shape):** the server-side kit (`clinic-doctor` on a systemd timer with a lock, a quiet log, and a status the watcher can read); the watcher's edit (the outside order: wait for the self-repair → Hostinger status → start / restart → re-check → tell him the outcome; an alert only when the automatic steps failed, naming the one next step and linking the guide at `#s2` / `#s4`); the guide updated so each step says what already ran automatically. Every attempt is recorded where the next chat can read it.
5. **Prove it:** the walk with simulated failures (S573's walk is the pattern), the mutants red, the rehearsal; then the publish, his one install line, and read it live. **The watcher's code is edited in his Apps Script editor by the assistant's browser, as at S319**; an OAuth consent screen (a new scope such as an outside call) is his hand.

**C · THE WORK AFTER D734 — §2A of the Runbook v240, in order, when he gives a free hand.** First the Growth chat's two server items (`growth_S320_1` — the website's mail route and the vendor's June access; read-only checks first); then the SMS watch; then the assistant's own (the Yes Bank SMS refusals, the unattended pull, the board's `_numbers` at 170 KB, `/tmp/s573kit` and `/tmp/s576kit`, the background list).

**ON HIS WORD ONLY — not raised:** a *send to Shavez* button for the bank check (D717 (1)) · the follow-up tracker on the server (*"later"*, D717 (2)) · Bhati's later features (D724) · mending `patient_ref`'s first-seen names at the tracker (F-918).

**PARKED AT HIS WORD — NOT TO BE RAISED; he raises it:** the staff's WhatsApp alerts made loud (D692 — a topic name is a key: never in the repository, a kit, a page, the board or a chat line) · club C — the mailbox clean-up (D702) · the tracker's move (D717 (2)). **Held:** the Callback Tracker move (D634).

**Owner-side, on his board:** the publish · **the packs page (shops and passwords — remind every session)** · the Marg engineer's restore test · Ranjeet's login · the reception PC's Windows · the Docterz report export · the arms licence (November).

**CLOSED BY HIS WORD — DO NOT RAISE AGAIN:** everything listed so in `START_HERE_SESSION_319.md` stands, and three are added:
- **the 16-Oct outage** — Hostinger's, not ours; the journal is persistent now;
- **the parchi's name for a Docterz ID (S576)** — fixed and read live;
- **the guide's name and pin** — *Clinic Doctor*, pinned to his sidebar.

**Before any owner-only or staff-only step in the assistant's browser:** read `https://followup.dr-manoj.in/finance/api/whoami`. **The assistant does not type credentials for him.** **An account-access grant (OAuth consent) is his hand even when he says yes in chat.** **Patient files never pass through the assistant's workspace (D656).** **No phone number in the repository (F-185) — a walk joins made-up numbers at run time.** **The bank-SMS page is refused by the assistant's browser — read the database copy in the bundle.**

**Standing owner rulings (restated):** rules 1–32 of `START_HERE_SESSION_319.md` (1–30 from `START_HERE_SESSION_317.md`, 31–32 added there) stand whole. One is added:

33. **When the portal is down, the first answer is the guide, not a diagnosis** — *Clinic Doctor*, `https://claude.ai/artifact/H5W1T3WPNm85t2peTnNnfP`; he comes to the chat only when its step 5 says so, with the photo and the time (D732).

## 1 · THE CURRENT CANON — the manifest wins

| what | file |
|---|---|
| Register | `KB_Register_v5_160_S319close.md` (clone only, D550) |
| History Archive | `KB_History_Archive_v1_157_S319close.md` (§S319) |
| Fault → Action Register | `Fault_Action_Register_v2_145.md` (§7.79 = F-917 … F-920) |
| Runbook | `HANDOFF_RUNBOOK_2026-10-18_Session319close_v240.md` (**§2A the order; §1Q what S319 made live**) |
| close routine | `END_OF_SESSION_PROMPT_v18.md` |
| build norm | `BUILD_NORM_v1.md` (D704) |
| live pins | `live_pins_S319close.txt` (the parent's DECLARED-PENDING 3) |
| build brief | `S319_BUILD_BRIEF.md` |
| numbers | System Board `board/_numbers` — at this close: **D735 · F-921 · A-D25 · kit S577 · session 326 next; 325 RESERVED for the parent; 324 RESERVED for the Sanjeevni chat; 323 the Scan App chat's, open** |

## 2 · WHAT THIS SESSION MADE LIVE — the short map

| what | where | state |
|---|---|---|
| `clinic-doctor` — checks the machine, 15 services and 5 front addresses; restarts only what is down (S573, D732) | the server: type `clinic-doctor` in Termius; log `/root/deploy/clinic_doctor.log` | live 07:31 18-Oct; ALL GOOD |
| The outside watcher — every 5 minutes; e-mail first, the phone push retried (S573, F-917) | his personal Google account, Apps Script *Clinic Portal Watcher* | live 17-Oct; his phone took the test 20:48 17-Oct |
| The guide *Clinic Doctor* | `https://claude.ai/artifact/H5W1T3WPNm85t2peTnNnfP` | pinned to his sidebar 18-Oct |
| The parchi takes Docterz's newest name for an ID (S576, D733, F-918) | `https://followup.dr-manoj.in/finance/slips/` | live 07:33 18-Oct; the reported ID read live |
| The server's journal survives a restart (F-919) | `/var/log/journal` | since 19:59 16-Oct |

*Written at the S319 close, 18-Oct-2026.*

---

## THE OTHER CHATS — a pointer, not a carried section

- **The Scan App (323, open):** its entry point `START_HERE_SESSION_323.md`.
- **Sanjeevni (324, reserved at its S322 close):** its entry point `START_HERE_SESSION_324.md` — a different chat's file; ours is `START_HERE_SESSION_325.md`.
- **The Clinic & Growth chat:** its message `growth_S320_1` is answered on the board's told list (the two server items are §0 C here).
- **For all, from this close:** the parent's `slip_log.py` is at `2419c536`; `clinic_doctor.py` at `af696c77`. Build only from those bytes.
