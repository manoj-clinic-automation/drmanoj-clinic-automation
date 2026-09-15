# S274_VPS_OFF — Club 3h, the VPS half

*Session 258 · 15-Sep-2026 · the four server jobs that had no way to be stopped*

## What this is

S259 gave every job on the two Windows PCs an off switch (Club C.2). The server
side of the same club was still open: `spine_cadence.py`, `sale_attribution.py`,
`export_watch.py` and `salts_refresh.py` could only be stopped by editing the
crontab or killing a process.

They now have the same switch the two PCs have, and the same one the Marg
collector has had since S240:

> **a file whose presence stops the job, and whose absence starts it again.**

Nothing is stopped, unregistered, restarted or uninstalled in either direction.
No cron line is touched. Each job reads the folder when it next comes round and
does what it finds.

## The switches — `/root/finance/_off/`

| file | stops |
|---|---|
| `ALL_OFF` | all four below |
| `SPINE_OFF` | the item spine cadence — every 30 min 09–23, and 23:50 |
| `ATTRIBUTION_OFF` | the discount attribution — every 30 min 09–23, and 23:55 |
| `EXPORT_WATCH_OFF` | the "did Amir export today" watch — 23:40 and 10:45 |
| `SALTS_REFRESH_OFF` | the salt-list refresh — every 10 min 08–22 |

A trailing `.txt` is honoured on every name, so a marker made on Windows and
copied across still reads.

One line either way, and a `status` that tells you where everything stands:

```
bash /root/finance/sanjeevni_switch.sh status
```

```
bash /root/finance/sanjeevni_switch.sh off spine
```

```
bash /root/finance/sanjeevni_switch.sh on all
```

## What is deliberately NOT in scope

- **The Marg collector and its shadow already have a switch** —
  `/root/marg_ingest/OFF`, since S240. It is untouched and keeps its own name.
  `sanjeevni_switch.sh status` reports it alongside the others so there is one
  place to look, but this kit does not manage it.
- **`finance_heal.py`, `finance_intent.py`, `bank_match.py`, the backups and the
  Docterz ingest are the clinic's jobs, not Sanjeevni's.** Club 3h names the
  spine, the attribution and the export watch. Widening a kit past what the plan
  says is how it stops being reviewable.

## Where the guard sits, and why there

After `--selftest` is handled, before the job opens a database or reads a file.

**A selftest is not a job, so it still runs when the switch is on.** That is
deliberate: the switch can then never hide a broken file. It is also what lets
the installer prove the four files are healthy *after* patching them.

## What changed in each file

Two anchored inserts, **+22 lines, and not one existing line removed or altered**
— asserted by diff in the walk, per file:

1. `_OFF_DIR`, `_OFF_NAMES` and `_off_marker()` immediately above `def main(`.
2. Four lines at the top of `main()`: if a marker is there, print one line and
   return 0.

## The proof

**`walk_s274.py` — 32 checks, 0 failures, 0 skipped**, run over the box's own
live bytes. It asserts each file's own `--selftest` says *exactly* what it said
before the patch; that each job stops on its own marker, on that marker with
`.txt`, and on `ALL_OFF`; that it does **not** stop on another job's marker or
with no marker at all; and — by unified diff — that no line was removed or
altered in any of the four.

**`prove_off_s274.py` — 32 checks**, and the installer runs it again **on the
box, against the live files**. It imports each patched file as a module and
points `_OFF_DIR` at a temporary folder of its own, so **the proof never creates
a marker in the real `_off` folder** and cannot stop a cron job that happens to
fire while it runs.

## Installing

Six gates: pin gate → patch (all-or-nothing) → compile → each file's own
selftest → the switch proof → create the folder. Any failure rolls all four
files back. A selftest that cannot run says **SKIPPED** and is counted as a skip,
never as a pass.

**The folder is created empty, so installing this switches nothing off.** Every
job keeps running exactly as it does now; it simply gains a way to be stopped.
