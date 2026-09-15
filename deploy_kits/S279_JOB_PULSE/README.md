# S279_JOB_PULSE — can each of our jobs prove it ran?

## The fault

At S259, four of the six open faults on the board were one shape: **a check built
correctly, wired correctly, and then never switched on or never looked at.** A job
that is quiet looks exactly like a job that is passing.

Counted on the box: of **38 clinic jobs**, only **8** leave a run record anyone can
read back — and **every one of the five nightly backups is in the other 30**. The
health page has a `backup` check meant to watch them, and that check is one of the
**seven that have never once fired in fourteen days**. So the thing that would save
the clinic leaves no proof, the watchman over it has never spoken, and neither
state can be told from the other.

## Why the obvious fix was rejected

Adding a "record that you ran" line to thirty live files is thirty chances to break
something that currently works, for a change that adds no function. Wrong shape.

## What this does instead

**It reads evidence that already exists and touches nothing.**

- **45 of the 46 clinic cron lines already name their own log** with `>> /path.log`.
  That path is read **out of the crontab at run time** — never inferred, never
  baked into a list that can go stale. A job added tomorrow is watched tomorrow.
- **systemd is asked directly** for the four timers, including whether each is
  enabled — the one fact the nightly backup does not carry.
- Lines sharing a log are one job: `att_mailer` morning and evening share a log and
  share a pulse.
- The allowance is **measured, not guessed**: the schedule is walked over a real
  16-day window and its widest legitimate silence is taken from that. A daytime-only
  job is not called late for being quiet overnight.

Verdicts: **ALIVE · LATE · SILENT · NO TRACE · OFF**.

## What it says about itself

> A log's timestamp proves the job WROTE SOMETHING. It does not prove the job
> succeeded, and a job that runs silently on a quiet day will read LATE without
> being broken.

That sits at the top of every report rather than being left for someone to discover.
This measures liveness — which nothing measured before — and never replaces a job's
own verdict.

## How it was proven

| walk | result |
|---|---|
| its own selftest, 17 checks | passes; the installer re-runs it **on the box** and refuses to install if it fails there |
| live shape, the box's real crontab | 46 clinic lines → 34 jobs + 4 timers = **38**, zero parse errors |
| sandboxed install | crontab backed up and read back identically, **exactly one** line added, verified from the crontab itself |
| re-run | "already installed", nothing changed |

**The selftest earned its place before shipping.** It found three real defects: a
weekly job whose gap could not be measured inside an 8-day window, a crash on the
one job that names no log (the asset-register tar, which throws its errors away),
and one case where the failing assertion was **mine** and the code was right — that
is recorded in the test rather than quietly corrected.

## To undo, afterwards

```
crontab -l | grep -v S279_JOB_PULSE | crontab - && rm -f /root/finance/job_pulse.py
```
