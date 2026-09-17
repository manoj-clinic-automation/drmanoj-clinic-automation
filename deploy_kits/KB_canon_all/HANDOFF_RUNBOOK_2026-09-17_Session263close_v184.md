# HANDOFF RUNBOOK — v184 · Session 263 close · 17-Sep-2026 IST

## §0 · WHAT HAPPENED

**One sitting in one chat, 07:42 → close (the parent project), beside the Sanjeevni project's S262 close.
EOS — two VPS files moved and one crontab line, three kits, every install the owner's one line and every
pin printed by its installer on the box. Times read from commit stamps and installer lines (F-510).**

**1 · The open.** Board read 07:45; all three folders mounted. Nightly (17-Sep 05:05): REBUILT 2,945 · WARN ·
canon one mismatch (`push_kit.bat`, corrected after the run). The S261 publish verified (`e216066` 07:35:56,
584/584). **The rescue check:** 276 project documents — three held nowhere, rescued to `S263_RESCUE\` (two
proven by hash, the `.docx` a same-provenance copy, F-504). **D528 step 4 batch 1:** 20 papers read back and
hashed 20/20, cold-copied to F:, deleted here; 55 remain.

**2 · `S283_JOB_PULSE_EMPTY` (F-498 closed).** Three verdicts for a log that does not move — LATE/SILENT,
EMPTY, NEVER RAN. Built from the bundle's bytes, 33/33, 39/39 on the live shape. Published `2214298` 08:38:09;
installed 08:39, `job_pulse.py` → `5eae0eb7…`.

**3 · F-511.** `git fetch` and `git status` in `device_bash` left two lock files in `.git` (the shell cannot
unlink). Moved out at 08:14 before any publish.

**4 · `S286_ASSETAPP_BACKUP`.** The bare 02:30 `tar` (no log, errors discarded, prunes regardless) replaced by
`/root/state_backup/assetapp_backup.py` — SQLite backup + integrity check, full read-back, prune only after a
verified night, one log line. Published `4701361` 09:02:17; installed 09:04 (`9fdc66a3…`). First run 204 MB,
64 photos — **15 copies on the app's disk.**

**5 · The owner's direction and D532 / `S287_ASSETAPP_DRIVE`.** Off-site = the connected Google Drive. Two
owner-owned slot files created through the Drive connector in `FinanceDB_Backups`; the verified archive shipped
through `finance_drive_backup.py`'s own calls; unchanged nights upload nothing; monthly pinned; server keeps 3
days behind a verified Drive copy. **F-512:** the rewrite began inside the S286 folder, which the owner published
meanwhile; restored from git's objects; shipped as its own kit. Published `63d4735` 10:00:02; installed 10:00
(`b816504c…`): shipped 204,157,260 B, md5 verified by Drive, monthly pinned, pruned 11 kept 4. Confirmed from the
owner's side through the connector.

**6 · The transition question and D533.** The Sanjeevni move is complete; that project runs its own sessions.
Left: 55 papers here; Book v1.3 then prompt v1.1 there. The board's page text dated from 15-Sep — renamed
**System Board**, lines tagged by place, republished (code and database unchanged); every close now refreshes it
(`END_OF_SESSION_PROMPT_v15`, A10c).

## §1 · MENTAL MODELS THIS SESSION EARNED

- **A shell that can create but not delete turns every tool that cleans up after itself into a litterer.** git
  is the loud one; any tool with lock or temp files is the same shape (F-511).
- **The publish folder is live.** The owner can double-click at any moment; a kit folder is either final or
  absent (F-512).
- **A green self-test answers the questions it was asked.** S286's first draft passed 18 checks and still let a
  flawed night overwrite a good archive — found by reading the code again, not by running it again.
- **"Off-site" was a plan the owner already held.** The first build answered the fault the job pulse showed;
  the owner's word supplied the fault nobody had measured — 15 copies, one disk.
- **Reuse the route that already works.** The Drive leg imported S213's proven calls and conf instead of a new
  credential path; the zero-quota constraint was known because S213 had paid for it.
- **A page with a live half and a static half rots on the static half.** The board's database was current all
  day; its words were two days old.

## §2 · THE LIVE BACKLOG

**Here, the assistant's (fresh chat):** hold the 18-Sep bundle against today's pins and read the first 02:30
asset-backup line · D525's seven never-fired health checks + the UPI check · D528 step 4 — 55 papers · F-496 ·
the `freshness_legs.json` diff (F-507) · the portal tile caption · the F-384 sweep.

**The Sanjeevni project's:** Book v1.3 (F-493, stale 3) **then** `SANJEEVNI_START_HERE_PROMPT_v1.1` · the first
live look at S285 · the router and the daily summary report · the item↔supplier second stage · Darpan's
day-close place (waits on the owner's corrections).

**His, deferred at his word:** `OWNER_TODO_LIVE.md` and the System Board.

## §3 · INSTALL DISCIPLINE

Three kits, each built in scratch (after F-512), gated on the live file's real md5, self-tested on the box by
its installer, with a backup beside the file and a one-line undo: `job_pulse.py.bak_S283_917713f5` ·
`crontab.bak_S286` · `assetapp_backup.py.bak_S287_9fdc66a3`. The crontab was written once (S286) and read back
whole; S287 only read it. The Drive slot files were created from the owner's account; nothing new on the server
holds a credential.

## §4 · THE BOUNDARY

The publish is the owner's double-click and is owed: Fault v2.88, Archive v1.101, Register v5.103, runbook v184,
START_HERE_SESSION_265, `END_OF_SESSION_PROMPT_v15`, brief, close report, pins, manifest, `MD5SUMS_ALL.txt`,
`OWNER_TODO_LIVE.md`. Nothing on the VPS changes; the clone pull (A8c) is named for him, not urgent.
