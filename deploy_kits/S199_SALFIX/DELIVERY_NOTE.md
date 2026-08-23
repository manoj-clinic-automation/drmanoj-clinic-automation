# S199_SALFIX — restore the salary Net / Old(shadow) / Delta columns

## The problem you saw
On /register/salary the last three columns (Net amount, Old shadow, Delta) were
blank, with: *"ledger SALARY_EXCLUDED changed (… ADVANCE_DEFER … CAPACITY_HOLD …)
— refusing to compute salary against a drifted rule set."*

## Cause (pre-existing since S192 — NOT the scenario kit)
D332/SL6 added two Rs 0 marker rows to the ledger — ADVANCE_DEFER ("collection
deferred") and CAPACITY_HOLD ("held — salary could not bear it"). The ledger lists
them as non-salary money; salary_engine.py keeps its own copy of that list and was
never updated, so its safety guard (which refuses rather than mis-pay when the two
lists differ) hid the computed columns.

## Fix
One constant: add ADVANCE_DEFER and CAPACITY_HOLD to salary_engine.py's
SALARY_EXCLUDED so it matches the ledger. Both are Rs 0 — no figure changes; the
guard simply passes and the columns compute again.

## Proven offline
- py_compile + pyflakes clean.
- With the ledger's real 7-item set, the patched engine's guard PASSES (module
  resolves, no error).
- The UNPATCHED live engine reproduces your exact "drifted" refusal against the
  same 7-item set — confirming this is the cause and the cure.
- The engine's own --selftest reads the real ledger, so it runs ON THE BOX in the
  installer, which rolls back on any failure.

## File (one), currency-gated
| File | To | Base pin | New pin |
|---|---|---|---|
| salary_engine.py | /root/staff_register/salary_engine.py | 5514918067243e3f39e7074144ee7db4 | ca37c615a421d984bb2d8a2f89782ca2 |

## Install (VPS, after PUBLISH_ALL + git pull)
    bash /root/deploy/repo/deploy_kits/S199_SALFIX/INSTALL.sh

Refuses unless the box holds the live bytes; backs up; copies; runs the engine
--selftest on the box (restores on failure); restarts staff-register.

## For the S199 close
salary_engine.py ca37c615a421d984bb2d8a2f89782ca2 (Register-pinned; base 5514918067243e3f39e7074144ee7db4).
Finding candidate: F-174 — a ledger category set grew (S192) without its salary-engine
mirror; the guard caught it (worked as designed), latent until the first live salary view.
