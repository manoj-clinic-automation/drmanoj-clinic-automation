# OPEN ROUTINE — v1 — one open for every project (adopted at S357, 26-Oct-2026; the owner's word of 07:19 IST)

**Applies to all four projects — the parent (Systems & Automation), Sanjeevni (Pharmacy & Marg), the Scan App (Papers & Bills), NK Pathology.** It replaces the open halves of `START_HERE_PROMPT_v10` (Phase 0, §1.5, the cap and the tranche), `SANJEEVNI_START_HERE_PROMPT_v1_1` §4 and `SCANAPP_START_HERE_PROMPT_v1` §4. Everything that proved a thing in those routines is still proved here — once a day by one tool, not by every chat by hand.

**Why v1.** The nightly's reports, the canon gate, the pin pass, the SSD mirror, the cold kit and the folder counts were being re-read at EVERY session's open — four chats, several opens a day, the same files. The owner (26-Oct): *"it does nighty backup rechecks at very session start, not the first one of the day."* The checks are not fewer; they are done once, written to one page, and read by every later open of the day.

---

## 0 · Connections — before anything else

`D:\Downloads` · `D:\dr-manoj-git` · `F:\ClinicBackup`. Report exactly what is connected; ask for what is missing by name; never work around a missing store. The device shell works and `F:` mounts in it (since S354); the file-transfer tools read and write all three. Never run `git` in the device shell — read `.git\refs\heads\main`, `.git\refs\remotes\origin\main` and `.git\logs\HEAD` as files (F-511, F-947, F-1019). A database copy carries patients: it stays in the device VM (`$HOME\...`), never in the cloud workspace (D656).

## 1 · FIRST ACT — the session number

From the System Board `board/_numbers`, by a version-pinned write, taking what the board says (a RESERVED number for this project if the last close reserved one) and saying it in the first line (NUMBERS_PROTOCOL_v1). Read the clock before writing (F-510). A refused write means another chat wrote first: re-read, take the next.

```
https://claude.ai/artifact/EtwtRpK4nAbmY98KB4yijk
```

## 2 · The board

Every message with `read:false`; every note on a `board/<item>` document (query `updated` since the last close). What belongs to another project is left for it, quoted. **Remind him of the packs page (the 25 card shops; the card and ICICI passwords) every session until done (D713).**

## 3 · THE DAY'S CHECKS — ONCE A DAY

```
python D:\Downloads\_kbtools\day_open.py --read
```

The page `D:\Downloads\_kbtools\DAY_OPEN_LATEST.txt` holds the day's checks. **If it is from today, written after the nightly ran (03:10, or its catch-up time), and no publish and no new bundle have come since: read it and go on.** Otherwise run the checks (about ten seconds):

```
python D:\Downloads\_kbtools\day_open.py
```

What it settles, in one page: the nightly's five reports (exist · clock time · verdict; older than 24 h = RED) · the publish landed (`main` = `origin/main`, the last commit's time) · the canon gate from inside `KB_canon_all` (count; a mismatch HALTS work, D172/D188) · the CURRENT pin list against the newest bundle (match | mismatch | DECLARED-PENDING | not in the bundle | BLIND) · the database copy's age · the SSD (the newest KB mirror with size and file count; the newest cold kit and whether it is DUE at 7 days; the briefs) · the loose files at each root against the nightly's count. **A RED on the page is the session's first work; a WARN is read and judged.**

**The first session of the day also does, and writes one line onto the page so later sessions skip them:** the measure of project knowledge (`project_info` — ~25k tokens, once a day, never between) with the never-cited percentage from `D:\Downloads\_kbtools\PAPERS.html` · what no store holds (anything only in project knowledge → `01_RESCUED_FROM_PROJECT_KNOWLEDGE\S###_RESCUE\`, hashed) · the cold kit when the page says DUE · the sweep of anything loose into `_to_delete_S###\` with a `WHY_SAFE.txt` · the pin-list mismatch reconciled if there is one.

```
python D:\Downloads\_kbtools\day_open.py --note "project knowledge 1,559,806 B of 2,000,000; never-cited 55%; nothing only in project knowledge; cold kit not due"
```

A later session of the day reads the page and its notes and does none of this again — unless it publishes (re-run after the publish lands) or a new bundle arrives (01:35).

## 4 · This project's entry point

Read the `START_HERE_SESSION_###` the manifest marks CURRENT **for this project** (several are CURRENT at once, one per project — F-384 is about the row, not the rule), then its build brief. Tier 0 only: the manifest (from the clone) · this routine · the Register · the Fault Register's last section (the four numbers) · the Runbook's section for this project (§2A the parent · §2B Sanjeevni · §2C the Scan App · the NK Pathology chat's entry point) · `OWNER_TODO_LIVE.md`'s sections for this project · any open incident. Tier 1 on demand; Tier 2 never without a waiver (D34). **On a Monday, the parent also reads the newest `claude/AUDIT_RUN_*` (the weekly auditor ran at 07:00 IST) and takes its *For the builder* lines into the session's work; its close answers each** (AUDITOR_SEED_v2 §6).

## 5 · The four numbers

Drift · dead · stale · folders — read from the Fault Register's last section and the day page; **a number over the line is the session's first work unless he waives it in one line** (drift ≥ 5 patches since a whole read; dead ≥ 3 in one file; stale ≥ 3 closes; a loose file with no owner). The owner is told the number, never handed the measuring.

## 6 · Then the work

In the entry point's order. Ask him which ONE item to start only when the open's work (a RED, a number over the line, his open question) is done — and ask in one line. The standing rules of the working protocol (the project's custom instructions) govern every reply.

---

**Carried from v10 / v1.1 / v1 unchanged, so they are not lost:** the nightly depends on manojz being awake (a catch-up run is a run; read the time, not the date) · a project-knowledge document can be hashed (F-503); a re-keying with no survivor is a transcription (F-504) · the assistant's browser works, signed in as whoever last used it (read `/finance/api/whoami` before an owner-only or staff-only page; it never types credentials for him) · computer control on manojz is click-only · the switches (`/root/finance/_off/ALL_OFF`, `/root/marg_ingest/OFF`, `D:\Downloads\margsync\_off\ALL_OFF.txt`, `D:\SendToClinic\_off\ALL_OFF.txt` — the medical PC's does not stop capture) · ClickUp is parked (D17).

*OPEN_ROUTINE_v1 · S357 · 26-Oct-2026 · the next version is written when the routine changes, by whichever project changes it, and every project reads the version the manifest marks CURRENT.*
