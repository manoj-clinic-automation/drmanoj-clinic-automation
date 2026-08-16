# S183_V1a — the F-97 structural fix (live-code pin verification)

**Session 183 · 16 Aug 2026 · read-only tool · nothing live is touched**

---

## What F-97 was

The KB Register records an md5 for every live file. **Nothing ever asked the box whether
that record was true.**

At S182 `/root/portal/portal.py` was pinned `da417709…` (recorded at S176) while the box
was actually running `34f038a765…` — stale by two sessions. The GitHub copy agreed with
the stale pin byte-for-byte. Two records agreed with each other and both were wrong. A
full-file replacement built on that pin would have silently deleted the medical unit's
two live finance tiles, **with every gate passing**.

The S182 mitigation — the per-kit live-file currency gate — checks *one* file, only
*while a kit is installing*, and only if a kit exists at all. Every file not currently
being replaced stays unchecked forever. That is a mitigation, not a fix.

## What this kit installs

| File | Where | What it is |
|---|---|---|
| `verify_live_pins.py` | `/root/deploy/` | the checker. Read-only. Stdlib only. |
| `live_pins.tsv` | `/root/deploy/` | the pins, **generated from KB Register v5.4** (`9506a0fe…`) |

Run it with one command, at the start of every session and again at every close:

```
python3 /root/deploy/verify_live_pins.py
```

## What it reports

Each pinned file gets one verdict:

- **MATCH** — record and reality agree.
- **DRIFT** — the box is running something else. *This is F-97.*
- **MISSING** — the record names a file that is not there.
- **UNTRACKED** — live code sitting in a pinned directory that the record never
  mentioned. This is the reverse gap, and it is how a file becomes stale in the first
  place: it changes, or appears, and the Register is never told.

Exit code **0** = every pinned file matches · **1** = drift or missing · **2** = the
checker could not run (and it says so rather than reporting a misleading pass).

**Coverage as generated from Register v5.4: 39 files checked, 5 rows that cannot be
checked from the VPS.** Those five are printed by name on *every single run* —
the two Google Apps Script files, the two applied database migrations, and the PC-side
`docterz_report.py`. They are labelled blind spots, never counted as passes. A checker
that hides what it cannot see is worse than no checker (D166 · F-99).

## Three things built in deliberately

**The pin list is generated, never hand-kept.** A hand-maintained second copy of the pins
would drift from the Register — a record quietly disagreeing with another record is
exactly the fault being closed here, and exactly what D202 warns about. `gen_live_pins.py`
derives the list from the Register's own live-file table. A row it cannot classify
**stops the run**; it is never skipped, because a silently dropped row is a live file
nobody is checking.

**The checker names its own source (F-88 applied to this tool).** Every run prints which
pin list it read, that list's md5, and the Register filename and md5 it was generated
from. A stale pin list cannot pass itself off as a clean result.

**A red verification is not a failed install.** The install succeeds or fails on whether
the *tool* is sound and got placed. The first real check runs afterwards and never rolls
anything back. If genuine drift made the install look broken, the install would get
retried and the drift waved through — the failure mode this project has already written
down twice.

## How it was tested offline

- `py_compile` clean on both files.
- Checker selftest **22/22**, generator selftest **12/12**.
- **The selftest was sabotaged four ways** — drift reported as match; missing reported as
  match; the untracked scan blinded; md5 validation removed — and went **RED on all four**.
  A check that cannot fail is not a check.
- **Rehearsed against a throwaway fake VPS twice**: once clean (39/39 MATCH, exit 0), once
  carrying a deliberate drift, a deliberate missing file, a surprise file and a `.bak`
  file — it reported exactly DRIFT 1, MISSING 1, UNTRACKED 1, ignored the backup, exit 1.
- The installer itself was rehearsed against a throwaway target before shipping, including
  a corrupted-SUMS run to watch it refuse.

## What to expect on the first run

Possibly a red, and that is the point — this is the first time the box has ever been asked.
If it is red, **the Register gets corrected from the box, never the other way round**, and
no kit is built on a drifted pin until it is.

Any UNTRACKED files it finds are a decision for you, not a fault: either the file belongs
in the Register, or it gets an `IGNORE` line in the pin list saying why it does not.

## Install

```
bash /root/deploy/vps_deploy.sh S183_V1a
```

## Still owed after this kit

- The **loaded-in-memory check** — a file on disk matching its pin does not prove the
  running service is executing those bytes (S127: `call_hook_capture.py` was replaced at
  21:55 and the worker ran the old bytes until 23:38). Named, not built.
- The **PC-side half** — `docterz_report.py` and the `clinic_writer` files on `D:`.
- `clinic-finance.service` is blind only because the Register does not record its path.
  Recording `/etc/systemd/system/clinic-finance.service` at the next Register bump would
  move it from blind to checked at no cost.

---
*S183_V1a · built offline, gated, read-only · Session 183*
