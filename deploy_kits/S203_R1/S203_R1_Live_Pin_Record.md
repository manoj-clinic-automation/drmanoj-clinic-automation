# S203_R1 — LIVE PIN RECORD

Recorded as it moved (F-97), not saved for the close.

| file | machine | was | now |
|---|---|---|---|
| `marg_router.py` | manojz, `D:\Downloads\margsync\MargPull\` | `bbc50f9172211925755eeaa25920d1cf` | **`781e5ff66d4eca6b6ed4703bf692fb46`** |

Installed by the owner, **26-Aug-2026 18:27 IST**. All five gates passed, reported by the
installer itself: live file verified · replacement verified · backup taken ·
**selftest 21 OK, 0 FAIL** · installed bytes re-hashed and matching.
Backup kept at `marg_router.py.bak_S203_R1_20260826182712`.

Selftest **14 → 21, exactly +7**, the projection written before the build.

## What it fixes

An `.xls` the router could not open was refused and then forgotten: the refusal returned
**above** the archive-and-index block, so the file was never copied to `_REFUSED` and never
written to `index.csv`. `seen` is rebuilt from `index.csv` on every run, so the same file
was picked up and refused again on the next 10-minute cycle — **for ever** — and the only
message went to a console `PULL_HIDDEN.vbs` discards.

**It was the one failure mode on the S203 list that nothing in the system could detect.**

## The fix, and why it is shaped this way

The archive-and-index tail became `_archive_and_index()`, called by **both** paths. One
definition of what archiving means, so the two cannot drift — the same principle as D349.
The alternative, inlining a second copy of the archive logic into the refusal branch, would
have created exactly the two-definitions fault this project keeps paying for.

## Proven before it was installed

- **The seven new checks were run against the UNFIXED file: five went RED** — copied to
  `_REFUSED`, the `.txt`, the `index.csv` row, becoming SEEN, and the second pass skipping
  it. The two that passed there were already true. *A test that passes on broken code
  proves nothing.*
- **Reverse application**: strip exactly what was inserted — the function, the call, the
  refusal branch, the checks — and the reconstruction hashes to
  `bbc50f9172211925755eeaa25920d1cf`, the live pin, exactly.
- `py_compile` **and `pyflakes`**. Twice on 26-Aug `py_compile` passed a file that raised
  `NameError` at runtime; syntax checking cannot catch that class. **Proposed protocol
  change: build/test offline → py_compile AND pyflakes → then install.**
- The gate demanded **exactly 21 OK and 0 FAIL**, never a bare `OK` match — the gate shape
  that accepted a degraded suite at S202.

## Consequence to watch

From the next pull, any unreadable file appears **once** in `MargArchive\_REFUSED` with a
`.txt` beside it saying why, and once in `index.csv`. If several appear at once, they are
the backlog of everything that has been silently refused until now — that is the fix
working, not a new fault.
