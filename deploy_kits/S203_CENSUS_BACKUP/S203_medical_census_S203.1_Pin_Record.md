# S203 — medical_census.py S203.1 (the backup survey) — LIVE PIN RECORD

Recorded AS IT MOVED (F-97), not saved for the close.

## The pin

| file | machine | was | now |
|---|---|---|---|
| `medical_census.py` | MEDICAL PC, `D:\SendToClinic\medical_census.py` | `b53af03aaf16f011d3c15bb059637a5f` | **`b4eb6d94ac24085d796a017411567674`** |

Delivered to `<Drive>\My Drive\Clinic Data Archive\ToMedical\_kit\medical_census.py`.
Installed by `medical_agent.py` S201.11 with **no action on the medical PC**, and
**proven by the machine itself** — heartbeat `2026-08-26T10:19:24`:

    KIT     : F:\My Drive\Clinic Data Archive\ToMedical\_kit
                medical_census.py  up to date (b4eb6d94)

`medical_census.py` is not in `RESTART_FOR`, so the capture watcher was not
restarted: `WATCHER : ALIVE, pid 13728` before and after.

## Zero loss proven, not asserted

The change is a **pure insertion**. Reverse application — strip exactly the
inserted block, the inserted `main()` lines and the added `import re` — returns
`b53af03aaf16f011d3c15bb059637a5f`, the installed pin, exactly. Nothing of the
S201 census was altered or lost. 8,496 → 22,361 bytes.

## What was added

A read-only backup survey (F-191c), seven sections: drives and whether the stick
is even attached · the backup folders and their ages · the 25 newest files
anywhere on the stick · the Marg data a real backup must cover · Task Scheduler
and startup items · Marg's own `.ini`/`.cfg` backup settings · a verdict.

Writes `FromMedical\BACKUP.txt` and `D:\SendToClinic\BACKUP.txt`, and appends the
same text to `CENSUS.txt`. Reads only; creates nothing, deletes nothing.

## Why it lives in the census and not in a one-off .bat

`medical_census.py` is on the agent's three-name allowlist, so it installs itself
down the Drive channel. A one-off `.bat` would have needed a copy onto a machine
whose share is **read-only from manojz** (robocopy → ERROR 5, S195), and would
have been a second way to do one job. `MEDICAL_BACKUP_SURVEY.bat`, written
earlier this session before the channel was understood, was replaced in place
with a stub pointing at `MEDICAL_CENSUS.bat`.

## What the channel can and cannot do — measured, not inferred

- **CAN** deliver and install code on the medical PC unattended: `marg_watch.py`,
  `xlsx_stdlib.py`, `medical_census.py`. Compile-checked, md5-verified, backed
  up, and reported in every heartbeat.
- **CANNOT** run anything there. The agent installs; it does not execute the
  census. Nothing on manojz can start a process on the medical PC — the
  Tailscale share is `\\100.119.151.40\DDrive`, **read-only, D: only**.
- **CANNOT** see the backup stick at all. `E:` is not on that share. This is
  precisely why the survey had to run on the machine.

So one double-click of the existing `MEDICAL_CENSUS.bat` remains. The standing
fix — a backup-age line inside the 5-minute heartbeat — needs `medical_agent.py`
itself, which the agent **deliberately never self-updates** (S201.11), so that
is one `INSTALL_AGENT.bat` run, proposed separately.

---

## Pin history, continued (each recorded AS IT MOVED, F-97)

| version | md5 | installed (medical PC clock) | why |
|---|---|---|---|
| S203.1 | `b4eb6d94ac24085d796a017411567674` | 10:19:24 | the backup survey added |
| S203.2 | `8cfaf44547bacea3a5d3592ec75ff634` | 10:26:56 | **fault fix** — see below |
| S203.3 | `44c84744c2dfdf7be317329eb332d153` | 11:43:09 | two measurements added |

All three verified by the medical PC itself in its heartbeat, not asserted here.
Reverse application from S203.3 still lands on `b53af03aaf16f011d3c15bb059637a5f`,
the S201 census — every version has been a pure insertion.

## The S203.1 fault, recorded not softened — an assistant fault

S203.1's section 7 announced **"The backup target is NOT ATTACHED"** while
section 1 of the same file, in the same run, said **"E: is present"**.

Cause: variable shadowing. Section 3 bound `root` to the backup stick; section 4
then rebound it with `for root in MARG_ROOTS:`, so by the verdict `root` held
`C:\MARGERP`, which does not exist on that machine. The verdict tested the wrong
thing and said so with confidence.

**This is precisely the S202 class of fault** — a monitor reporting a state it
did not measure — committed while building a monitor to catch that class of
fault. The owner ran S203.1 at 10:24 and the false verdict is in that run's
`BACKUP.txt`. Fixed in S203.2, which derives the verdict from named, unshadowed
measurements (`stick_present`, `newest_backup_age`, `any_recent`,
`scheduled_exists`, `server_backup_age`).

**RULE: a verdict may only read variables it can name and nothing else has
touched. If two sections of one report can disagree, the report is not a
measurement.**

---

## S203.4 and S203.5 — and a CANDIDATE FINDING about the build protocol itself

| version | md5 | outcome |
|---|---|---|
| S203.3 | `44c84744c2dfdf7be317329eb332d153` | ran, **wrote no file at all** |
| S203.4 | `0721ef9854235c3f8719d52afff6d7fc` | ran, **named its own fault in the report** |
| S203.5 | `a0b01ed20cde8f35863a57655b07b7fa` | the fix |

### The fault (the assistant's, the third in this file today)

`medical_census.py` ran and raised, on the medical PC:

    NameError: name 'say' is not defined
      File "D:\SendToClinic\medical_census.py", line 259, in _marg_backup_config
        say("   MARG'S OWN INTERNAL BACKUP: %s" % _sb)

The S203.2 patch inserted a block of `say(...)` calls using the anchor
`for root in MARG_ROOTS:` with a **replace-first-occurrence**. That string
occurs **twice**: first inside `_marg_backup_config()`, a module-level helper
with no `say`, and only later inside `backup_section()`, where it belonged. It
landed in the wrong function. It also left `server_backup_age` undefined inside
`backup_section()`, which section 7's verdict reads — the next failure, queued
behind this one.

**RULE: an anchor that is not unique is not an anchor.** The corrected patch
asserts the occurrence count before replacing, and asserts the destination
anchor is unique.

### The candidate finding — the working protocol is insufficient

The project's standing rule is *"Build/test offline → `py_compile` → then I
install."* **`py_compile` proves a file PARSES. It cannot see an undefined
name.** It passed on every broken version.

`pyflakes` finds it instantly, and this was proven both ways rather than
asserted — the broken file reproduced from the fixed one:

    $ python3 -m pyflakes broken.py
    broken.py:259:17: undefined name 'say'   (x6)      exit 1
    $ python3 -m pyflakes medical_census_S203.py        exit 0
    $ python3 -m pyflakes  <the original S201 census>    exit 0

**PROPOSED RULE CHANGE: `py_compile` AND `pyflakes` (or equivalent), both
clean, before any Python file is shipped to a machine.** Offered for the
owner's ruling; not adopted unilaterally.

### What worked, and is worth keeping

S203.3 failed **silently** and produced nothing — three round trips were spent
not knowing why. S203.4 added a per-section guard and a flush after every
section; on its first run it **wrote the traceback, the file and the line into
the report itself**. The machine diagnosed the assistant's fault in one run.

**RULE: a survey that only exists if every part of it succeeds is not a survey.
Write as you go, and let a failing section report itself in place.**
