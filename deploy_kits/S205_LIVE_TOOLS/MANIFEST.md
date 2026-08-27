# S205_LIVE_TOOLS — MANIFEST

**Captured 27-Aug-2026, at the S205 open.** The manojz and medical halves of D350 §4:
the **bytes**, plus the two reinstall documents that say what to do with them.

| | |
|---|---|
| `manojz\` | **19 files** — the live `D:\Downloads\margsync\MargPull\` tooling |
| `medical\` | **5 files** — from `D:\SendToClinic\`, via the read-only mirror on manojz |
| `SUMS.md5` | 26 rows (24 files + the 2 documents) |
| `REINSTALL_MANOJZ.md` · `REINSTALL_MEDICAL.md` | install order, files, credentials (never values), scheduled tasks and Run-As, and the checks that prove it worked |

## HOW THIS CAPTURE WAS VERIFIED — and why it is not `md5sum -c`

`md5sum -c SUMS.md5` passes. **That proves nothing about whether these are the files that
are running**, because it hashes the kit against itself. Its predecessor,
`S203_LIVE_TOOLS`, passed that check while three of its ten files held **pre-fix bytes**
(F-215).

So every file here was **additionally compared against its live source**:

```
24 files checked against D:\Downloads\margsync\MargPull\ and
   D:\Downloads\margsync\medical_SendToClinic\   ->   0 drift, 24 identical
```

**That independent check is the one that matters, and it is the one the next capture must
also run.**

## WHAT THIS SNAPSHOT IS, AND WHEN IT GOES STALE

These are the bytes **as at the S205 open**, i.e. **before** the S205 kits are installed.
The moment the S205 `pipeline_status.py` and `PULL_FROM_MEDICAL.bat` go on to manojz,
**two of these 24 files are stale** — which is exactly how `S203_LIVE_TOOLS` came to hold
the pre-fix bytes.

**So: re-capture at the S205 close, and verify against the live source again.** A capture
step that is not a numbered step in the close-out routine is a capture step that will be
forgotten — which is the whole history of F-184, F-200 and F-215.

## PERMISSIONS (F-210)

Nothing here is executable-by-mode: these are Windows files, and Windows carries no
executable bit. **The F-210 hazard does not apply to this kit** — it applies to the VPS
kits, where `finance_backup.sh` and `email_agent.py` lost `100755` in transit and a
restore from git gives the bytes but not the mode. Said explicitly so the absence of
`chmod` lines here reads as *checked*, not as *forgotten*.

*S205_LIVE_TOOLS · D350 §4 · NOT YET REHEARSED — a recovery document nobody has followed
is a guess.*
