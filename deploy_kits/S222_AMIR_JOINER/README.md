# S222_AMIR_JOINER — closing Amir at 6/6, without lying to the register

**Session 222 · ⭐1-2 part B · 03-Sep-2026**

The owner's instruction: *"tick CREDENTIALS_SENT + STAFF_MASTER so his joiner record closes at
6/6."*

## Why this is a script and not three UPDATE statements

The joiner register exists to stop **one** failure: a person marked fully added who is invisible
to attendance, because a step was signed off that was not true. Its own selftest caught exactly
that — `STAFF_MASTER` ticked while the Emp Code was still missing, which would have let
`build_staff_master.py` skip the row while the register said the man was fully onboarded.

So this script never writes a step by hand. It imports `joiner_app` and uses **its**
`blocked_by()`, `steps_for()` and `done_steps()`, and writes the step, the event and the
`COMPLETE` transition the way `api_step()` does. Whatever the live page would refuse, this
refuses.

## The three kinds of evidence, kept apart

| step | what backs it |
|---|---|
| `STAFF_MASTER` | **measured.** The script opens `staff_master.csv` and looks for him — Emp Code first, then the name — and **refuses the tick if he is not there.** The step's own words are *"the person appears"* |
| `CREDENTIALS_SENT` | **the owner's attestation**, made at the S221 close. Written into the step's detail as an attestation, not as a measurement |
| `FIRST_LOGIN` | **an attestation nobody has made yet.** Nothing in the portal records a last login, so no file on the box can prove or disprove it. Refused unless `--first-login-attested` is passed |

That third row is the one that matters. It would have been easy to tick all three and report 6/6.
A register whose ticks mean different things without saying so is a register that stops being
worth reading, and this one was built because a paper checklist did exactly that.

## What it is proven by

`SELFTEST GREEN 21/21`, against the real `joiner_schema.sql` and the real `joiner_app.py`, running
the close script as a subprocess exactly as the box will:

1. report-only writes nothing
2. `--apply` ticks `CREDENTIALS_SENT` and stops
3. `FIRST_LOGIN` ticks once attested; `STAFF_MASTER` still refuses while he is absent from the file
4. rebuild the staff master, and the record closes at **6/6 / COMPLETE**
5. re-running says *already 6/6* and changes nothing
6. each of the three ticks carries the kind of evidence behind it in its own detail

## What it does not do

No file is patched. No service restarts. **No pin moves.** It writes rows in `joiner_step`,
`joiner_event` and `joiner`, and nothing else.
