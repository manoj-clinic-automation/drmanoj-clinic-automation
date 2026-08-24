# S200_R5 — D346: THE GO-LIVE ENGINE (every S200 ruling, in code, as one kit)

## The three files

| file | was | now | version |
|---|---|---|---|
| `/root/staff_register/salary_policy.py` | `dfe67285…` | `4521f1a6320893ac24039dce5861131f` | v1.4 |
| `/root/staff_register/staff_register.py` | `7d62435a…` | `40efbac35393b1c358b3509eb806870e` | v0.11 |
| `/root/att_month_report.py` | `9ab98313…` | `0184cb139907ee11adcc78c1ecab2daa` | v2.7 |

## The rules it ships (each traced to its ruling)

- **D341 — Sunday absence at derived weight, for PAY.** Weight = that day's rostered Sunday
  minutes ÷ weekday minutes (0.5 today for half shifts), derived per staff from the shift data —
  never typed. `sunday_weight_override` setting (−1 = derive; 0..1 forces). Fail-safe: missing
  Sunday shift data ⇒ weight 1 — bad data can never silently cheapen an absence.
- **D342c — whole for the deterrent.** The ramp counts whole days; only the money is weighted.
- **D345 — the ramp.** `fine_exc = step × n(n+1)/2` beyond the person's OWN `allowed_offs`;
  `fine_ramp_step` setting (default 10). The flat `fine_excess`/`excess_free_days` are retired
  (removed from DEFAULTS and dropped from the saved settings file at install, backup kept).
  The flat-3-vs-allowance incoherence is structurally gone.
- **D342b/D345b — exempt = outside the loop.** `minutes_exempt` staff (Arjun) now skip fines
  exactly as they already skipped late money, incentive, dress/I-card.
- **D342a — the suspended hold, completed.** Improvement ≥ threshold ⇒ charge **CANCELLED**
  (note only — the money never left the packet, so nothing is "returned": the old `+release`
  in net is gone). No improvement ⇒ **`prior_collect`** joins this month's deductions, and the
  lock writes a `COLLECT` action to `hold_ledger.jsonl`, closing the hold so it can never
  charge twice. Sheet 2's hold table shows the COLLECT case.
- **D343 — divisor 30.5.** New default; the installer patches an existing saved settings file
  (30 → 30.5) with a backup.
- **D341b — the roster era is gated.** `ROSTER_FROM` now reads `ATT_ROSTER_FROM` from the
  environment, default `2099-01`. The unadopted D253 roster — including the 5th-Sunday
  full-day rule that would have hit **29 Nov 2026** unasked — waits for an explicit switch.
  The att selftest pins the era ON for its own fixture, so the dormant roster code stays proven.

## Proof done offline

- All three patched from hash-verified live bytes; every anchor asserted EXACTLY once.
- `py_compile` + `pyflakes` clean (only the pre-existing `deg_path` note).
- **policy selftest** extended and green: ramp values (0/10/60/210/280), derived weight 0.5,
  override, fail-safe, and the July acceptance numbers — Shivani's weighted leave line
  `(9 − 4×0.5 − 2) × 8600 ÷ 30.5 = 1409.84` and her ramp 280 — asserted in code.
- **att selftest 40+ checks green** (one legitimate red during the build: the fixture tests the
  roster logic the gate had just parked — the selftest now pins the era on for the fixture).
- **register selftest green** (full suite through v0.10 features).

## Install

    cd /root/deploy/repo && git pull
    bash /root/deploy/repo/deploy_kits/S200_R5/INSTALL_S200_R5.sh

Gates all three, backs up all three (+ the settings file), swaps, compiles, patches settings,
runs all three selftests on the box, restarts, probes — **rolls everything back together on any
failure.**

## After GREEN — July go-live, in this order

1. **VERIFY BEFORE ANY LOCK** — run the July dump (Claude supplies the command); the engine's
   July must now reproduce `Salary_July_2026_FINAL.xlsx` to the paisa. A mismatch = STOP, tell
   Claude the dump.
2. Settings page → **ENFORCE FROM = 2026-07** (the deliberate switch, D332/D336 §8).
3. Month-end flow 2026-07 → approve Sheet 1 + Sheet 2 → **LOCK**. The lock writes July's FINAL
   sheets on the VPS and records every suspended charge in `hold_ledger.jsonl` — the machinery
   behind the staff PDF's promise, and what August's improvement test reads.

## Pin note
Fifth, sixth and seventh live-pin moves of S200. `verify_live_pins.py` drift grows until the
S200 close regenerates the list (F-134 shape, not a fault).
