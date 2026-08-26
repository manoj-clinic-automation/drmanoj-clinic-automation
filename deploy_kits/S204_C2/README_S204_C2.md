# S204_C2 — the ceiling fallback, and the literal that the file itself warned about

**Built at S204 from the LIVE bytes** (`7948cee0…`, captured by `S204_C1` — the newest copy in
the repo before that capture was from 01:36 on 26-Aug, *before* the S203 gate fix, so editing it
would have quietly reverted B2).

## Why

The owner ruled this session that **Darpan is on the same 50% rule as everyone else**. Measured on
the box: the staff ledger already said 50, and the Sanjeevni drawer had **no `advance.*` settings
rows at all**, so `advance_ceiling_p()` fell back to its coded default of **75** and was still
allowing ₹15,000. The settings rows were written on 27-Aug at the owner's instruction and the gate
is now ₹10,000.

Two things that row does not fix, and this kit does:

**1 · The coded fallback was still 75.** A rebuilt or restored database would have resurrected
₹15,000 with nothing said. **An exception belongs in a settings row, never in a fallback.**

**2 · F-207 — the file names the fault, then commits it.** At line 9886 the smoke suite's own
comment says *"a hardcoded `15,000.00` would go red the day the owner revises the base or the
pct"* — and sixteen lines below, twice, it hardcodes exactly that literal. The block around it was
deliberately made state-adaptive (the S184_F1b remedy); the ceiling figure was left behind.
**The warning and the fault are in the same function.**

The two literals sit in opposite branches of one `if`, so exactly one runs per execution.

## The five edits

| # | where | change |
|---|---|---|
| 1 | `advance_ceiling_p()` docstring | records the retired exception and why a fallback must not carry it |
| 2 | `setting(con, "advance.pct", "75")` | → `"50"` |
| 3 | `base, pct = 2000000, 75` (bad-value path) | → `50` |
| 4 | the selftest's own `_set_of("advance.pct", 75)` | → `50`, kept in step |
| 5 | **two** `== "15,000.00"` literals | → `== rupees(_want_ceil)` — the value the block already computes from the store |

Edit 5's anchor matches **twice on purpose**, and the builder asserted the count rather than
assuming it (S203: *an anchor that is not unique is not an anchor* — here it is deliberately not
unique, so the count is the check). Edits 1–4 asserted exactly one match each.

## Proofs run before delivery

- **`py_compile` and `pyflakes`.** pyflakes reports the same two pre-existing findings as the live
  file and **no new one** — compared list against list, not eyeballed.
- **Reverse-application:** undoing all five edits returns the file to **`7948cee0…`, the live pin,
  exactly.**
- **Red-proof at predicate level.** The failure is a *live-data* failure, so it cannot be
  reproduced by running the suite offline against a fresh store — that is F-195's shape and it is
  recorded rather than papered over. What was proven instead, directly:

  | settings `advance.pct` | server returns | OLD check | NEW check |
  |---|---|---|---|
  | **50** (today) | ₹10,000.00 | **FAIL** | **PASS** |
  | 75 (before) | ₹15,000.00 | PASS | PASS |

  So the new check is **state-adaptive, not a behaviour change**: it passes in both worlds, and the
  old one fails in exactly the world the owner's ruling created.

## Projection, written before installing

- The **current** live file scores **720/721** — one failing check, the F-207 literal.
  (Verified mechanically, not assumed: `selftest()` does `shutil.copyfile(live_db, tmp_db)`, so the
  throwaway store carries the live settings, including the new `advance.pct = 50`.)
- **After this kit: 721/721.** No check is added or removed — the count is unchanged, only the
  expectation is corrected.

If either number differs, stop and roll back — the rollback is an explicit command, never a trap
(S203).
