# S203 — MEDICAL PC LIVE PINS (the first ever)

Read FROM the machine by `medical_census.py` S203.6 at **2026-08-26 13:04**, not from
manojz's mirror and not from any record. `md5_of()` on the machine's own files.

**Why this did not exist before.** `verify_live_pins.py` runs on the VPS and cannot
reach either PC; the Tailscale share is read-only and D:-only; and manojz's mirror is
`robocopy /E` with **no `/PURGE`**, so it keeps every file ever deleted on the medical
PC and is therefore not evidence of what is there. Drift on this machine has been
undetectable by construction since the machine was first set up.

| file | path (MEDICAL PC) | bytes | md5 | mtime |
|---|---|---|---|---|
| `SEND_TO_CLINIC.bat` | `D:\SendToClinic\` | 5491 | `e19a8a777ac22fe75a242f1eb9762185` | 2026-08-22 00:15:45 |
| `marg_watch.py` | `D:\SendToClinic\` | 12256 | `aa55cdb51521c796a9167ee7d27a368f` | 2026-08-25 15:14:50 |
| `medical_agent.py` | `D:\SendToClinic\` | 30313 | `69e60d778ab61a8d50c79394e2951309` | 2026-08-25 20:06:10 |
| `medical_census.py` | `D:\SendToClinic\` | 45014 | `a7706d60965e45545e93a4eaa94fa892` | 2026-08-26 13:04:16 |
| `xlsx_stdlib.py` | `D:\SendToClinic\` | 6392 | `bbe11a8953f66c27126c48e773cfbe35` | 2026-08-25 19:22:18 |
| `MargAgent.cmd` | `…\Start Menu\Programs\Startup\` | 102 | `edcb2f2e2ef1258d4e0d3bae9ef38460` | 2026-08-25 20:13:01 |
| `MargWatcher.cmd.replaced_by_agent.bak` | `…\Startup\` | 179 | `498235da9e4c40352b1c2f7bf843d244` | 2026-08-23 08:02:35 |

`token.txt` exists at `D:\SendToClinic\token.txt` (32 bytes) and is deliberately never
hashed, listed or mirrored (`/XF token.txt`).

`medical_agent.py` `69e60d77…` **agrees with the manifest's S201 note** — no drift.

## The launcher, verbatim

`Startup\MargAgent.cmd`:

    @echo off
    start "" /min "D:\SendToClinic\pyportable\pythonw.exe" "D:\SendToClinic\medical_agent.py"

So the agent starts **at logon only**. There is no scheduled task for it. No logon,
nothing runs — including, from S203.3, the offsite backup.

## Six things the mirror said that the machine denies

The manojz mirror never purges, so it still shows files deleted long ago. Checked
against the machine's own listing (77 files in `D:\SendToClinic`), these are **NOT on
the medical PC**: the 340 `marg_watch.py.before_*` files (the agent's prune keeps 3, and
exactly 3 are there) · `AutoHotkey64.exe` and the export macros · `xlrd\` ·
`GUARD_AND_SEND.bat`, `guard_and_send.py` and `marg_report.py` · `INSTALL_WATCHER.bat`
and `START_MARG_WATCHER.bat` · `_backup_20260822_002354\`.

**Consequence for AF-1.** AF-1 is recorded against `GUARD_AND_SEND.bat` lines 119-123
(a stale `last_response.txt` read). **That file is not on the machine.** AF-1 has been
carried as "still armed" in five places against a file that no longer exists. The
fallback D347 preserves is `SEND_TO_CLINIC.bat`, which was read and is self-contained —
it posts the report directly and never calls the guard or the parser. **The fallback
works; the fault it is said to carry cannot fire.**

## Also found, invisible to the mirror by design

The pull excludes `*.zip` and the `_old` folder, so nothing off the machine had ever
seen: `pyportable.zip` (11.9 MB) and `SCREEN REC 21 8 2026.zip` (3.4 MB) sitting in
`D:\SendToClinic`, and `D:\SendToClinic\_old\COPY_MARG_DATA.bat` — a previous round's
attempt at the very job S203 is doing, which records the fact that **Marg partitions its
FoxPro tables by financial year in the file extension** (`.c18` = FY 2026-27).

## Settled by measurement, not by argument

- **Scheduled tasks: six, all Google and OneDrive.** The S195 logon task
  *"Marg export watcher"* does **not** exist. There is no orphan second watcher.
- **Nothing in Task Scheduler or at startup runs a backup.** The automatic backup was
  never failing — it was never there.
- **Marg was running** (`margwin.exe` pid 7172) when the audit ran, so `D:\MARGERP\Data`
  is open Foxpro tables and cannot be copied consistently by any file copier.

---

## PIN MOVED — `medical_agent.py`, recorded as it moved (F-97)

| was | now | version |
|---|---|---|
| `69e60d778ab61a8d50c79394e2951309` | **`7b9a76f24abc5be369186507279cfaad`** | S201.11 → **S203.3** |

Installed by the owner via `INSTALL_AGENT.bat` v3, **confirmed by the machine's own
heartbeat at 2026-08-26 13:40:34** — `agent S203.3 on MEDICAL`, `WATCHER : ALIVE,
pid 344` (a clean restart; the installer stops everything before it writes).

**Proven on first run, not asserted:** `offsite: 38 file(s), 0.07 GB in
F:\My Drive\Clinic Data Archive\MargBackups · 145 file(s) still to copy`. The Marg
backups have left the machine that holds them for the first time.

### What the change is

One addition: the offsite backup leg. Copies closed backup files from `E:\` (and the
newest few from `D:\MARGERP\serverbackup`) into the clinic Drive, in bounded batches,
and carries the backup's age in every heartbeat with a warning past 3 days.

Deliberately does **not** copy `D:\MARGERP\Data`: Marg was running during the audit
(`margwin.exe` pid 7172) and those are open FoxPro tables. A copy taken then restores
inconsistent, and a backup that cannot be restored is not a backup.

Zero loss proven by **reverse application**: strip exactly the inserted constants, the
code block, the beat key, the heartbeat block, the loop call and the counter, and the
reconstruction hashes to `69e60d778ab61a8d50c79394e2951309` exactly.

### Two faults found by the offline rehearsal, before it went near the machine

**1. A false green, and the worst kind.** The first version reported *"newest backup 0.5
days old"* — naming a file from `serverbackup`, which is on the **same disk as the
data**. The real off-machine backup was 4.1 days old. The warning would never have
fired while the only copy that survives a dead disk quietly aged. **RULE: the age that
triggers the warning is measured on the copy that would actually be used in a disaster,
never on the nearest file that looks like a backup.** The two ages are now kept
separate and never mixed.

**2. `py_compile` is not enough, and this project's protocol says to use it.** An
`undefined name 'io'` passed `py_compile` clean and would have raised at runtime — the
same class of fault that made census S203.2 and S203.3 produce nothing at all
(`NameError: name 'say' is not defined`, from an insertion anchor that matched in two
places). **`pyflakes` catches it; syntax checking cannot.** Proposed addition to the
working protocol: *build/test offline → py_compile **AND pyflakes** → then install.*

**3. Pacing, caught by arithmetic rather than by testing.** At 8 MB per hourly pass the
first 0.4 GB catch-up would have taken fifty hours on a machine that is not always on.
Now 64 MB per pass, and while a backlog remains the next pass comes in two minutes.
