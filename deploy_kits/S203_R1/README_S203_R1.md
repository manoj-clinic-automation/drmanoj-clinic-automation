# S203_R1 — the vanishing refused file

**One file changes: `marg_router.py` on manojz.** No schema change, no data touched,
nothing else on either machine.

## The fault

An `.xls` the router cannot open was refused — and then forgotten. The refusal returned
**above** the archive-and-index block, so the file was:

- **never copied to `_REFUSED`**
- **never written to `index.csv`**

`seen` is rebuilt from `index.csv` on every run. So on the next 10-minute cycle the same
file was picked up, refused again, and forgotten again — **for ever** — while the only
message went to a console `PULL_HIDDEN.vbs` discards.

**Nothing in the system could see it.** It is the one failure on the list that no check,
no health page and no heartbeat would ever have surfaced.

## The fix

The archive-and-index tail is now a function, `_archive_and_index()`, and **both** paths
call it. One definition of what archiving means, so it cannot drift — the same principle
as D349.

| | |
|---|---|
| was | `bbc50f9172211925755eeaa25920d1cf` |
| now | **`781e5ff66d4eca6b6ed4703bf692fb46`** |
| selftest | **14 → 21, exactly +7** |

## Proven, not asserted

- **The seven new checks were run against the UNFIXED file and five go RED** — copied to
  `_REFUSED`, the `.txt`, the `index.csv` row, becoming SEEN, and the second pass skipping
  it. The two that pass there were already true. A test that passes on broken code proves
  nothing.
- **Reverse application** — strip exactly what was inserted and the reconstruction hashes
  to `bbc50f9172211925755eeaa25920d1cf`, the live pin, exactly. Nothing else moved.
- `py_compile` **and `pyflakes`** clean. *(py_compile alone is not enough — twice today it
  passed a file that raised `NameError` at runtime.)*

## The gates

The installer refuses rather than guesses, and puts the original straight back if anything
fails: the live file must hash to the old pin · the replacement must hash to the new one ·
the selftest must report **exactly 21 OK and 0 FAIL** · and the installed bytes are hashed
again afterwards.

**Exactly 21** — not "contains OK". A gate that matched the bare word `OK` accepted a
degraded suite at S202 and cost an hour.

## To install

Double-click, on **manojz**:

    D:\Downloads\margsync\_kits\S203_R1\INSTALL_S203_R1.bat

If a gate fails it restores the original and prints the reason — send me that.
