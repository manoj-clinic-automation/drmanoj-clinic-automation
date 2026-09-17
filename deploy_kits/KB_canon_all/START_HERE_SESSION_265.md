# START HERE — THE NEXT SESSION (numbered 264) · written at the S263 close

Hi Claude. Continuing Dr. Manoj Agarwal's clinic-automation work. **This file supersedes
`START_HERE_SESSION_264.md`** (written at the S262 close while this project's S263 was still open — it told you
to read this one if it exists). **The next session to open, in either project, is Session 264**; claim it on the
board first (rule 14) — the one after is 265. The evergreen rules are `START_HERE_PROMPT_v10.md` (parent) /
`SANJEEVNI_START_HERE_PROMPT_v1` (Sanjeevni), the projects' custom instructions.

## §0 — THE STANDING OWNER RULINGS (restated every close)

1. **Publishing is HIS double-click.** Name one file, full path.
2. **Full paths ALWAYS — including URLs**, each in its own copy block.
3. **ONE line per command.** Use `\cp` to bypass the alias.
4. **Token-lean working — never at the cost of verification.** `project_info` at the open and close only.
5. **Plain language. One step at a time. Full-file replacements. ALL-CAPS = urgent.**
6. **Mask patient numbers (last 4) and never print secrets or tokens.**
7. **Nothing live is rebuilt without his OK; the manual path stays as fallback.**
8. **Sub-agents read screens** — screenshots never enter the main conversation.
9. **Do not hand him diagnostics to run.** Ask for the one action nobody else can do, in one line.
10. **When a screen is wrong, read the screen's code FIRST.**
11. **Do not hand him a step that is not his.** If the assistant can do it, the assistant does it.
12. **His board carries only what needs him and what he should know (D526)** — and every close refreshes its page (D533).
13. **His own items are deferred** (17-Sep: *"until and unless urgently required"*). Name only what has become urgent, and say why.
14. **Claim your session number on the board as your FIRST act** (F-509). Two sessions can be open at once; the board is the lock.
15. **⭐ NEW AT S263 — no `git` command in `device_bash` against a connected folder (F-511)**; read `.git/logs/HEAD` and the refs instead. **Clock times are read, never estimated (F-510).** **Kits are built in scratch; a publishable kit folder is frozen (F-512).**

## §1 — PHASE 0, IN ORDER

**0. The board first** — the **System Board**:

```
https://claude.ai/artifact/EtwtRpK4nAbmY98KB4yijk
```

`board` and `messages`; write `_claude_status.session` with your number and the time read from a clock; answer on
the lines; set `read: true`; update `lastRead`.

1. **Connect and report by name:** `D:\Downloads` · `D:\dr-manoj-git` · `F:\ClinicBackup`. `device_bash` mounted all three at S261–S263.
2. **Read the three nightly reports** — exists · clock time · verdict:

```
D:\Downloads\_kbtools\REBUILD_REPORT_LATEST.txt
```

```
D:\Downloads\_kbtools\MAINTENANCE_REPORT_LATEST.txt
```

```
D:\Downloads\_kbtools\CANON_SUMS_LATEST.txt
```

   **The 18-Sep run should read REBUILT with the S262/S263 papers, snapshots and rescues added (S263 rowed six by hand; they should show as neither added nor changed), OK or WARN on the counts, and canon sums 100 % with 0 uncovered.** Anything else is a finding.
3. **The canon gate:** `md5sum -c MD5SUMS_ALL.txt` from inside `KB_canon_all\` (clone in the cloud workspace, or read the PC's copy — **not git in the PC shell**). **If the gate does not show v2.88 / v1.101 / v5.103, the owner has not published yet**: say so, name the file, and read the canon from the PC's `D:\dr-manoj-git\…\KB_canon_all\`.
4. **Open `CANONICAL_MANIFEST.md` FROM THE CLONE** (D528).
5. **Read Tier 0 only:** the manifest · `KB_Register_v5_103_S263close.md` · `HANDOFF_RUNBOOK_2026-09-17_Session263close_v184.md` · `OWNER_TODO_LIVE.md` · this file · and in the Sanjeevni project `S262_BUILD_BRIEF`.
6. **The job pulse:** `/root/finance/job_pulse.json` inside the bundle. **Expected on the 18-Sep bundle: the `tar` row gone and `assetapp_backup.py` in its place, ALIVE** — 37 alive · 1 late (`salts_refresh`, quiet by nature) · 1 silent (`records_worker`, a separate app) · 0 no-trace of 39. An `EMPTY` or `NEVER RAN` verdict is a finding (S283's new words).
7. **Run §1.5**, then the cap routine, then ask which one item to start.

## §1.5 — THE MAINTENANCE PASS

Verify, do not perform: the bundle in reach, the SSD mirror, the folder counts. **Hold the live pins against the 18-Sep 01:35 bundle — the VPS WAS touched at S262 and S263.** It should carry `job_pulse.py` `5eae0eb742bd79b202545fdc83cc05b2` (S283), **`state_backup/assetapp_backup.py` `b816504c89fa127b7519d29a77e54658` (S287 — a new file, carried by the `root/state_backup *.py` entry)**, `purchase_app.py` `d1476f80…` and `amir_day.py` `b3c20319…` (S262), `freshness_legs.json` `eaa97691…`. State the three counts. **And read the first 02:30 line of `/root/backups/assetapp_backup.log`** — it is not in the bundle (`*.log` excluded), so read it through the job pulse's `last_seen` and, if needed, one line from the owner: expected **OK … drive unchanged … keep 3 days** unless the register changed. **Four numbers at the S263 close: drift 0 · dead 1 · stale 3 (the Sanjeevni Book, that project's first job) · folders per the 05:05 report.**

## §2 — RESERVED NUMBERS

**Next free: D534 · F-513 · A-D25 · kit S288 · Session 264** — *after checking the board and the clone for a later close (rule 14).* D532 · D533, F-511 · F-512 and kits S283 · S286 · S287 were used at S263.

## §3 — THE CURRENT CANON

| | |
|---|---|
| KB Register | `KB_Register_v5_103_S263close.md` |
| History Archive | `KB_History_Archive_v1_101_S263close.md` |
| Fault Register | `Fault_Action_Register_v2_88.md` (F-0 … F-512) |
| Runbook | `HANDOFF_RUNBOOK_2026-09-17_Session263close_v184.md` |
| Live pins | `live_pins_S263close.txt` |
| Build brief | `S263_BUILD_BRIEF.md` (parent) · `S262_BUILD_BRIEF.md` (Sanjeevni) |
| Sanjeevni Book | `SANJEEVNI_SYSTEM_BOOK_v1_2_S258.md` — frozen repository row; **v1.3 owed in the Sanjeevni project, before the v1.1 prompt** |
| Close-out routine | **`END_OF_SESSION_PROMPT_v15.md`** (adds A10c the board, A11c kits in scratch, F-510/F-511 rules) |
| Evergreen prompts | `START_HERE_PROMPT_v10.md` (parent) · `SANJEEVNI_START_HERE_PROMPT_v1` (Sanjeevni) |

## §4 — THE PINS THAT MOVED AT S263

On the VPS: `/root/finance/job_pulse.py` `917713f5…` → **`5eae0eb742bd79b202545fdc83cc05b2`** (S283, 08:39) ·
`/root/state_backup/assetapp_backup.py` NEW `9fdc66a3…` (S286, 09:04) → **`b816504c89fa127b7519d29a77e54658`**
(S287, 10:00) · root's crontab line 31 swapped (S286; backup `/root/finance/crontab.bak_S286`). Google Drive:
`assetapp_nightly.tar.gz` and `assetapp_monthly.tar.gz` in `FinanceDB_Backups` (owner-owned slots, D532).
Nothing on manojz or the medical PC.

## §5 — WHAT IS WAITING ON HIM

Deferred at his word (rule 13). `OWNER_TODO_LIVE.md` and the System Board. Owed from this close: the publish and,
not urgently, the VPS clone pull. **Nothing became urgent** — the 27-Sep arms-licence renewal is on his board as
its own line because nothing sends a reminder.

## §6 — WHAT THIS CLOSE OWES THE NEXT ONE

- **The publish** — verify landed (A16b) by reading `.git/logs/HEAD` and `refs/remotes/origin/main`, not git.
- **The bundle proof** of the five pins above, and **the first 02:30 asset-backup line**.
- **This project:** D525's seven never-fired health checks + the UPI check · D528 step 4 (55 papers) · F-496 ·
  the `freshness_legs.json` diff (F-507) · the tile caption · the F-384 sweep.
- **The Sanjeevni project:** Book v1.3 **then** `SANJEEVNI_START_HERE_PROMPT_v1.1` · S285's first live look.
- **At every close, either project:** refresh the System Board's page (A10c).

## §7 — THE SWITCHES

```
bash /root/finance/sanjeevni_switch.sh status
```

VPS `/root/finance/_off/` · VPS `/root/marg_ingest/OFF` · manojz `D:\Downloads\margsync\_off\` ·
medical `D:\SendToClinic\_off\`. **⚠ `ALL_OFF` on the medical PC does not stop capture, by design.**

---
*START_HERE_SESSION_265 · written at the S263 close, 17-Sep-2026. The manifest wins on what is current.*
