# Kit S184_F1b — D322 missing-day classifier + self-test state/logic split

**Session 184 · reship of F1a · live-code change · gated + reversible · restarts clinic-finance**

## Why a reship
F1a went RED at install — but NOT because of the classifier. Its `--selftest` ran on a copy of
the (now-corrected) real store and four checks failed because they asserted the **pre-S184 state**:
`legacy leaves cash negative`, `cannot build on negative legacy cash`, `cutover leaves legacy
breaks open`, `marg is present but not yet mapped`. C1a made cash positive, C2a resolved the
breaks, S183 mapped Marg — so the frozen self-test read our own corrections as failures. The gate
worked (it restored and installed nothing). **F-106**: a self-test must not freeze a data state.

## What F1b changes (on top of the D322 classifier, unchanged from F1a)
Those four checks are made **state-adaptive** — each asserts the truth for whichever state the
store is in:
- fresh store → cash negative · build blocked on negative cash · breaks open · marg unmapped
- corrected store (post-S184) → cash non-negative · build not blocked · breaks resolved · marg present
So a legitimate data correction can never fail the suite again, and the checks still verify real
behaviour on a fresh store. Nothing else in the self-test changed.

The **D322 classifier** is exactly as in F1a: Sundays + attendance clinic holidays → optional
`clinic_holiday`; weekday gaps → owed; attendance cross-read read-only + fail-soft.

## Safety (same proven pattern)
- **F-97 currency gate**: refuses unless live `finance_app.py` = `86382f62…` (F1a restored it, so it
  still is). Wrong/stale → nothing touched.
- stop → backup (`finance_app.py` + `finance.db`) → swap → py_compile → **`--selftest` on a copy of
  the REAL store** → restart on green → healthz → honest red that restores both + restarts old.
- No DB migration.

## Rehearsed offline
Classifier proven (all 5 cases + reclassify + filed-resolution + fail-soft); app boots; the two
self-test edits are targeted + py_compile-clean. The full `--selftest` runs at install on the real
store — and if any residual assertion still disagrees, the installer safely restores (as F1a did),
so a re-attempt costs nothing.

## To run
PC: `deploy/push_kit.bat`. VPS: `bash /root/deploy/vps_deploy.sh S184_F1b`
