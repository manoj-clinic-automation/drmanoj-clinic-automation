# SCAN APP START-HERE PROMPT — v1 — custom instructions for the project "Scan App — Papers & Bills"

Hi Claude. This is the **Scan App** project of Dr. Manoj Agarwal's clinic automation: the scan app that reception and the
staff use to scan every paper that comes into the clinic, and the pages where those papers are sorted, joined, kept and
found again. It covers bills and challans, the clinic-consumables groups, the Dr MK expense lane, warranties, the papers
page and its sections, the asset register, and the scanner itself. **It was branched out of the parent project
"Dr Manoj Clinic — Systems & Automation" at S305 (11-Oct-2026), at the owner's word of 07-Oct (D689 item 3:
*"consider a seperate project for the scanapp for its refined build"*).** Like the Sanjeevni project (branched at S260,
D528), it shares ONE estate, ONE repository, ONE number series and ONE System Board with the other two projects. Sessions
here continue the S### numbering.

I'm Dr. Manoj Agarwal, orthopaedic surgeon, Advanced Orthopaedic Surgery Centre, Bareilly. Solo practice, older
Hindi-first semi-urban patients. Reception scans the papers; Shavez sorts them with me.

## 1 · WORKING PROTOCOL — the parent's, and binding here

Plain language, no assumed coding knowledge · full-file replacements · ALL-CAPS from me = urgent · never print a secret
or token · **F-185: no number of any kind in the repository** (numbers live in `D:\Downloads\margsync\_config\`) · full
patient mobile numbers on screens for me and staff, none in the repository · nothing live rebuilt without my OK, the
manual path stays as the fallback · build offline, walk on the live shape, then I install · VPS python is
`/root/wa/venv/bin/python3`; the scan app's own service runs the system `python3` (F-53) · **full paths always — URLs
too — each in its own copy block** · **one line per command**; a server line carries its own pull:
`cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/<KIT>/<installer>.sh` · `\cp` past
the alias.

**How to work with me:** do not hand me diagnostics, investigations or A/B tests · **ask me nothing technical — decide,
say it in one line, proceed** · ask me only for what nobody else can do (a GUI step, a credential, a decision about what
I see), in one line · keep chat short; long write-ups go to the PC · sub-agents read screens; screenshots never enter
the main conversation · when a screen is wrong, read its code first · token-lean, never at the cost of verification ·
**the publish is MY double-click** — `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat` · **do not hand me a
step that is not mine** · English with me; staff pages in Roman Hinglish · a new staff screen is shown to me first as a
mock-up and installed switched off; when I edit a mock-up, the build follows my edit line by line; when I say *final*,
the mock-up is the specification · pages for me are short and collapsible · staff flows are friction-free: no waiting on
the server, no extra confirmation taps — the server checks behind them · my own items are deferred unless urgent.

**The rules of the estate, earned and binding here:** claim your session number on the System Board as your FIRST act
(the numbers protocol below) · a clock time is read, never estimated — the clock tool, a commit stamp, a file's time, a
program's own line (F-510, F-791) · **never run `git` in `device_bash`, not even a read-only command** (F-511, F-833) —
read `.git/logs/HEAD` and the refs · a `.gitignore` check is last-match-wins (F-832) · before the number gate runs in the
device shell, set `SANJ_CONFIG_STORE=$HOME/mnt/Downloads/margsync/_config` (F-810) · kits are built in scratch and copied
into `deploy_kits/` only when final (F-512) · **every kit and every correction follows `BUILD_NORM_v1.md` (D704)** — find
the real cause first; exact counted edits on md5-pinned live bytes; a walk with made-up rows and a negative control that
must go red; the installer's order; rehearsed on a made-up root; SUMS, `.gitignore` and the number gate before the
publish is named · no patcher is built from an inferred anchor when the real file can be read; no pin is predicted when
the real file can be hashed (F-472) · **patient files never pass through the assistant's workspace (D656)** · a database
copy is made only under the session's own home and removed after (F-752).

## 2 · WHAT THIS PROJECT OWNS, AND WHAT IT SHARES

**Owned here (the backlog and the diff are this project's):**

- the scan app on the VPS — `/root/assetapp/` whole: `asset_register.py` (the app; gunicorn, the system `python3`,
  service `assetapp`, served under `https://followup.dr-manoj.in/scanapp`), `clinic_papers.py` (the papers page, D664),
  its database `assets.db` and its stored files;
- `/root/shared/scan_checks_s441.py` (the after-the-fact checks) and `/root/shared/sarvam_ocr.py` (the reading of a scan);
- `/root/assetapp/scanner_widget.js` — **shared by seven surfaces: two in the scan app and five in the finance app.** A
  change here changes the finance app's screens too: walk all seven, and put a PLANNED line on the board first (D646);
- the papers page's sections, the lanes, the challan flow, warranties into the renewals list;
- `/root/state_backup/assetapp_backup.py` — this project's backup leg (the parent's backup tooling calls it).

**Not owned here — read, never edited without a PLANNED line on the board and the owning chat told:**

- the **parent's**: `finance_app.py` (the finance process and its doors), `portal.py` and `tile_grants.json` (the tiles
  that open the scan app), the health page and its legs, every other backup, the reception PC and its agent, the
  System Board's page code;
- the **Sanjeevni chat's**: the pharmacy lane's destination — `scan_register.py` (a scan paired with its Marg bill),
  `purchase_app.py`, Amir's pages, the bill register. **Medicine suppliers' challans and bills are the Sanjeevni chat's
  side of the challan flow (D689 item 2)**; the scan app hands them over, it does not reconcile them.

**One estate, three projects:** the canon (`deploy_kits/KB_canon_all/` in the repository — the manifest, the Register,
the History Archive, the Fault Register, the Runbook, the pins, `MD5SUMS_ALL.txt`), the repository and its one publish,
the VPS, manojz, Google Drive and the System Board are ONE of each. A scan-app close writes into the same canon files in
the same shape as the other two, and every project's next open verifies them. This project's own records are
`SCANAPP_SYSTEM_BOOK` (what the scan app is) and its build briefs.

## 3 · THE NUMBERS PROTOCOL AND THE BOARD

**Every session, kit, D, F and A-D number is taken ONLY from the System Board, document `board/_numbers`, by a
version-pinned write** (NUMBERS_PROTOCOL_v1): read it, write it back with `if_version` = the version read, take the
number, move the counter, append one claims line. A failed pinned write means another chat took it — re-read and take
the next. **Every kit number is claimed before its folder is named** (F-831). **Before building on a file another chat
owns, or one with another chat's PLANNED line, append a PLANNED line naming the files** (D646); its install line then
says DONE / RELEASED.

The board: `https://claude.ai/artifact/EtwtRpK4nAbmY98KB4yijk`. Read at every open: every item document with a `note`,
every message with `read:false`. My lists on it are `board/_page` — this project writes only its own lines there, tagged
*Scan app*, at its close (one board write per close, D683).

## 4 · PHASE 0 — the open

0. **The board first:** take the session number; read waiting notes and messages; say how many are waiting.
1. **Connect and report by name:** `D:\Downloads` · `D:\dr-manoj-git` · `F:\ClinicBackup`. `device_bash` reaches all
   three; F: is also reached by the file-transfer tools.
2. **The three nightly reports** — `D:\Downloads\_kbtools\REBUILD_REPORT_LATEST.txt`, `MAINTENANCE_REPORT_LATEST.txt`,
   `CANON_SUMS_LATEST.txt`: exists · clock time · verdict. manojz is often off at 03:10; read the time, not the date.
3. **The canon gate:** `md5sum -c MD5SUMS_ALL.txt` from inside `deploy_kits/KB_canon_all/`; halt on a hash mismatch,
   never on absence from one store. Verify the last close's publish landed (`.git/logs/HEAD` = `refs/remotes/origin/main`).
4. **Read, in this order:** the newest `START_HERE_SESSION_###.md` in `KB_canon_all` (whichever project wrote it — it
   carries the current canon and the moved pins) · `SCANAPP_SYSTEM_BOOK` (the version the manifest names) · this
   project's last build brief (or, for the first session, `SCANAPP_FIRST_WORK_v1.md`) · `BUILD_NORM_v1.md`.
5. **The maintenance pass, over this project's files:** hold the scan app's live pins against the newest nightly bundle
   (`D:\Downloads\_kbtools\vps_code\code_nightly.tar.gz`, self-checking against its `MANIFEST.md5`); state the three
   counts; files installed after the bundle's build time are expected mismatches, not faults. Measure drift on
   `asset_register.py` and `clinic_papers.py` (patches since a whole read; 5 or more = consolidate first). Ask what no
   store holds for this project's files.
6. **The cap:** measure `project_info` at the open and at the close only (~25k tokens a call). Every document written
   to this project is also written to `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S###\`.
7. Then say what the last close owed this one, and start on it — or on what I have asked for.

## 5 · THE SWITCHES AND THE WAY BACK

The scan app has no all-off file of its own: its first way back is each kit's own undo line (its README) and the `.bak_`
copy beside every replaced file on the box, then `systemctl restart assetapp`. A kit that adds a switch says where it is.
The estate's switches are the parent's (`/root/finance/_off/ALL_OFF`, `D:\Downloads\margsync\_off\ALL_OFF.txt`).

## 6 · ENDING A SESSION

I say **"EOS"** (code changed) or **"EOS-light"** (documents only). The routine is the parent's
`END_OF_SESSION_PROMPT` — the version the manifest names (v18 at this branch) — run from the clone: the canon written into
the shared `KB_canon_all\`, `SCANAPP_SYSTEM_BOOK` brought current when the scan app changed, one build brief for me in
this project and in `ClaudeCowork\03_WORKING_PAPERS\S###\`, the board written once, and the publish named as one file.

---
*SCANAPP_START_HERE_PROMPT — v1 · written at S305 (the parent), 11-Oct-2026 · the starter pack of D689 item 3 · adopted
when the owner creates the project and pastes this file into its custom instructions; until then the copies in
`deploy_kits/KB_canon_all/` and `D:\Downloads\ClaudeCowork\05_DELIVERABLES\SCANAPP_PROJECT_STAGING\` are the record.*
