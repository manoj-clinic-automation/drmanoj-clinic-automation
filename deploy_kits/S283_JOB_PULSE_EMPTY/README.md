# S283_JOB_PULSE_EMPTY — `job_pulse.py` v1.1 → v1.2

**Session 263 · 17-Sep-2026 · VPS only · F-498, second half.**

## What this kit is for

`job_pulse.py` answers, every hour, *can each scheduled job prove it ran?* Since S280 it reads a run
table where a job keeps one. **But for a job with no run table it still read an old log and an empty
log as the same fact** — and that cost S259 an hour on `salts_refresh`, which was healthy. F-498
named this half open. This kit closes it.

## Three facts, three words

| the log is… | what it means | v1.1 said | v1.2 says |
|---|---|---|---|
| written, but not lately | the job spoke, then went quiet | LATE / SILENT | LATE / SILENT *(unchanged)* |
| **empty** | cron fired the line (the shell made the file) but the job has never printed a word; its time is only when the file was made | LATE / SILENT | **EMPTY** |
| **not there** | the line has never fired — `>>` makes the file on the first run | NO TRACE | **NEVER RAN** |

A run table still beats all three. A job whose line names no log at all is still **NO TRACE**. The
report's header now explains the three words on its face, and one list of problem verdicts is used
by the report, the summary line and the self-test, so a verdict cannot be counted in one place and
forgotten in another.

## What it touches

| path | change |
|---|---|
| `/root/finance/job_pulse.py` | replaced, v1.1 → v1.2 |
| everything else | **nothing** — the crontab is not opened; nothing else reads `job_pulse.json` (checked against the 17-Sep bundle) |

## How it was proven

- **Built from the real file**, not an inferred one: the 17-Sep 01:35 bundle's `job_pulse.py`,
  `917713f5…`, equal to the bundle's own manifest row and to the S280 to-pin. `patch_s283.py` applies
  11 exact anchors, each required once, and refuses any other starting file.
- **Self-test 33 of 33** (v1.1 had 22): an old log with words stays SILENT · an empty log is EMPTY
  and says where it was read · a missing log is NEVER RAN and is not confused with naming none · a
  run table beats an empty log · a stat that fails for another reason keeps v1.1's reading · the
  summary counts the empty and the absent · worst first.
- **Live-shape walk** on the box's own crontab (`crontab.txt` in the bundle) and the 17-Sep nightly
  database: v1.1 and v1.2 read **39 of 39 jobs identically** when every log has words, and agree
  **39 of 39** with the live 01:17 pulse. With `salts_refresh.log` and `ingest.log` made empty, only
  `salts_refresh` changes (LATE → EMPTY); `marg_ingest` still reads ALIVE from `mi_run`.
- **Installer rehearsed against a fake root:** installs · second run says *already installed* ·
  refuses a moved-on file with the reason · refuses when the self-test fails, nothing changed · a
  first run that fails **restores the old file byte-identically** (`917713f5…` read back).
- `py_compile` clean on all three `.py`; no ten-digit run in any file.

## Pins

| file | before | after |
|---|---|---|
| `/root/finance/job_pulse.py` | `917713f5269bb6af46ea355fc212ad2c` | `5eae0eb742bd79b202545fdc83cc05b2` |

## To install — one line on the VPS, after the publish

```
cd /root/deploy/repo && git pull --ff-only && /root/wa/venv/bin/python3 /root/deploy/repo/deploy_kits/S283_JOB_PULSE_EMPTY/install_s283.py
```

## To undo

```
\cp /root/finance/job_pulse.py.bak_S283_917713f5 /root/finance/job_pulse.py
```

## Files

| file | what |
|---|---|
| `job_pulse.py` | v1.2, the file that is installed |
| `install_s283.py` | pins, self-test on the box, backup, replace, first run, roll back |
| `patch_s283.py` | how v1.2 was made from v1.1 — provenance, not run at install |
| `KIT_ID.txt` · `SUMS.md5` | identity and self-gate (verify from inside this folder) |
