# S238_LEDGER_RECONCILE — the walk

**10-Sep-2026.** Proven against `staff_ledger.py` md5 `802577112e6db82bcf763d142efcd00c` — byte-identical to
the live pin — and against the **owner's own 51 ledger rows** of 10-Sep-2026, transcribed from his paste.
That transcription carries real staff figures, so it is **not** in this kit (public repository); it and
its 38-check walk live in `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S238\`.

| proof | result |
|---|---|
| `py_compile` | clean |
| live-figure walk (local only) | **38 checks, 0 failures** — the problem reproduced first, then fixed |
| the shipped `--selftest`, on a copy of that ledger | **17 checks, 0 failures**, real file md5 unchanged |
| sabotage: one record line wrong by Rs 1,000 | walk **5 failures**, selftest **1 failure**, installer **RED and restored** |
| installer walk | green fresh · green over an existing install · red on wrong pin · red on wrong ExecStart · red after placing (restores this run's backups) · red on a corrupt kit — **ledger md5 unchanged through all six** |

## WHAT THE WALK MEASURED BEFORE ANY FIX — the September close on today's ledger

- the 17-Aug advance would take **its August and September steps together** — the August step was
  never collected because the advance was approved on 25-Aug, after the 20-Aug close;
- the 31-Aug advance **would collect nothing, ever**: it carries no schedule and a partial instalment,
  so it falls into the waterfall behind the interest-free tranche;
- two August day-to-day advances would be taken from September instead of August.

After the fix, the September close takes exactly the owner's figures, and a second run finds nothing to do.

## HELD — shown every run, never written

The loan's Rs 1,000 difference and April's SKIP (both wait for the loan workbook) · tranche B's terms
(the owner's decision).
