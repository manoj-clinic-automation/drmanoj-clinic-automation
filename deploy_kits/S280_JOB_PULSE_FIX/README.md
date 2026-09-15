# S280_JOB_PULSE_FIX — `job_pulse.py` v1.0 → v1.1

**Session 259 · 15-Sep-2026 · VPS only.**

## What this kit is for

`S279` put `job_pulse.py` on the box and gave it one hourly cron line. **Its first live run produced
two wrong answers, and this kit is the repair.** Nothing else on the machine is touched: the crontab
is not opened, no live job is edited, no database is written.

## The two faults it fixes

**F-497 — an age in the future, reported as healthy.** systemd timestamps were forced to UTC and
then shifted again, so two timers came back with ages of **−170 and −329 minutes** and v1.0 still
called them ALIVE. v1.1 asks systemd for `--timestamp=unix` and does its own arithmetic once; a
negative age now reports **`AHEAD?`** and is **counted as a problem**, never as healthy. *A clock
that reads backwards is a fault in the reader, and a reader that calls it healthy is two faults.*

**F-498 (first half) — a live job read as dead.** `marg_ingest` runs every five minutes, prints
nothing on an idle pass, and its log had not moved in **2.3 days** — while its own `mi_run` table
showed a run at 01:00 that morning. v1.1 reads the run table for the **seven jobs that keep one**
(`mi_run`, `sh_run`, `export_watch`, `marg_spine_run`, `sale_attrib_run`, `upi_match_day`,
`clinic_day_revenue`) and falls back to the log only when there is no table. **Each line says which
source answered it.**

> **F-498's second half is NOT fixed and is recorded open:** for a job with no run table, an empty
> log and a stale log are still conflated. A job that has never written anything and a job that
> stopped writing three days ago read the same.

## What it touches

| path | change |
|---|---|
| `/root/finance/job_pulse.py` | replaced, v1.0 → v1.1 |
| everything else | **nothing** |

## Gate and safety

- **Refuses unless the installed file is exactly v1.0 `cbeb6d72d09a3c8114056dfabb8f70fd`.** A file
  that has moved on is a rebuild, not a force.
- Backs the old file up beside itself before writing.
- Compiles the new file before it is put in place.
- Rolls back byte-identically if anything fails.
- Running it twice is harmless and says so plainly.

## How it was proven

**22 self-tests, including one per fix**, plus a live-shape walk against the box's own crontab and
the nightly database copy — all seven table-backed jobs resolved through their tables.

## Pins

| file | before | after |
|---|---|---|
| `/root/finance/job_pulse.py` | `cbeb6d72d09a3c8114056dfabb8f70fd` | `917713f5269bb6af46ea355fc212ad2c` |

## To install

```
/root/wa/venv/bin/python3 /root/deploy/drmanoj-clinic-automation/deploy_kits/S280_JOB_PULSE_FIX/install_s280.py
```

## To undo

```
\cp /root/finance/job_pulse.py.bak_S280 /root/finance/job_pulse.py
```

---
*⚠ **This README was written at the S259 close, after the kit had been installed.** The kit shipped
with `KIT_ID.txt` and `SUMS.md5` but **no README** — a milder recurrence of **F-492** (S258), where a
kit shipped with no self-gate at all. Following the S258 precedent it is repaired before the cold kit
is sealed, and `SUMS.md5` is regenerated to cover four files instead of three. **`install_s280.py`,
`job_pulse.py` and `KIT_ID.txt` were NOT touched** — their bytes are the bytes that were installed.
`KIT_ID.txt`'s `NUMBERS` line still reads `D525, F-494`, which was correct when it was written and is
left as written rather than rewritten after publish (F-460); the reserved numbers now live in
`START_HERE_SESSION_260.md`.*
