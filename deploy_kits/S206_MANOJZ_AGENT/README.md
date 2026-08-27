# S206_MANOJZ_AGENT — the pipeline's other half

**Staged, not scheduled.** Read-only except for its own heartbeat file.

## What the 27-Aug event actually was

```
pull runs logged : 107
not-ok           : 0        <- it has NEVER failed
gaps over 15 min : 3        <- 17 min, 24 min, 191 min
```

**The pull does not fail. It sometimes does not run.** So a check on "did it fail"
would read green for ever — F-192's family. **The thing to watch is silence.**

Every gap-ending run also started off-cadence (second `:02`, `:39`, `:42` against a
normal `:09`–`:12`) — what a missed scheduled task firing on wake looks like. The
machine was asleep, the link was fine, and nothing was lost: the medical watcher
held all 95 captures and the 14:51 run swept them in.

## Install

```
python D:\dr-manoj-git\...\S206_MANOJZ_AGENT\manojz_agent.py
```
or double-click `RUN_AGENT.bat`. Then schedule it **every 15 minutes** —
and **untick "Start only if on AC power"**, which is the default that turns a
laptop into a silent pipeline.

Thresholds via environment: `PULL_STALE_WARN` (default 20 min) · `PULL_STALE_BAD` (45).

⚠ Staleness is computed against the machine's LOCAL clock, so it is only
meaningful when run **on manojz**.

## Selftest

`python selftest_manojz_agent.py` — **15 checks**, asserted on the real log,
including that the alarm both fires and stays quiet.
