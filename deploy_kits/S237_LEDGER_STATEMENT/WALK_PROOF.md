# S237_LEDGER_STATEMENT — the walk

**10-Sep-2026.** No real ledger exists outside the VPS, so the walk runs against a fixture built to
carry every shape the real one has: an advance keyed wrong, contra'd and re-entered; an advance
already cleared; an interest-bearing loan with a skipped month and capitalised interest; a pending
request; and a rejected row. **19 rows, deliberately messy.**

The first run on the box is the live-shape proof, and it is read-only, so it costs nothing to be wrong.

## THE OUTPUT

```
STAFF LEDGER — read 19 rows from _proof/fixture_ledger.jsonl

------------------------------------------------------------------------------
  WHAT WAS TAKEN OUT SO THIS COULD BE READ
------------------------------------------------------------------------------
     1 reversed entries hidden, with the 1 contra rows that cancelled them
     1 rows still awaiting a checker  (NOT counted anywhere below)
     1 rejected rows                  (never counted)
     9 instalment / interest / skip rows that carry a `contra_of` and are
       NOT contras at all -- they belong to an advance. This is the thing
       that makes the raw ledger look like a mess.
    15 rows counted as live

  ! the pending rows, because they will change these numbers when decided:
      Surendra     ADVANCE ISSUED         Rs 6,000      asked for another

==============================================================================
  AMIR
==============================================================================
  nothing owed

  --- what 2026-08's close took from this person's salary ---
      Night duty                    Rs       800

==============================================================================
  DARPAN
==============================================================================

  advance of Rs 4,000 issued 2026-06-05   (instalment Rs 2,000)
     "june advance"
     2026-06    instalment recovered        Rs     2,000
     2026-07    instalment recovered        Rs     2,000
     recovered so far                       Rs     4,000
     STILL OWED                             Rs         0   <<<

  advance of Rs 15,000 issued 2026-08-17   (instalment Rs 3,000)
     "advance application 17 aug (corrected)"
     2026-08    instalment recovered        Rs     3,000
     recovered so far                       Rs     3,000
     STILL OWED                             Rs    12,000   <<<

  TOTAL STILL OWED BY DARPAN: Rs 12,000

  --- what 2026-08's close took from this person's salary ---
      instalment recovered          Rs    -3,000
      Night duty                    Rs     1,200

==============================================================================
  SURENDRA
==============================================================================

  interest-bearing loan of Rs 13,000 issued 2026-06-01   (instalment Rs 2,000)
     "loan with schedule"
     2026-06    instalment recovered        Rs     2,000
     2026-06    loan interest               Rs     1,000
     2026-07    instalment SKIPPED                -
     2026-07    interest added on skip      Rs     1,000
     2026-08    instalment recovered        Rs     2,000
     2026-08    loan interest               Rs     1,000
     recovered so far                       Rs     4,000
     interest added on skipped months       Rs     1,000
     STILL OWED                             Rs    10,000   <<<

  --- what 2026-08's close took from this person's salary ---
      instalment recovered          Rs    -2,000
      Uniform fine                  Rs       -20
      loan interest                 Rs    -1,000

==============================================================================
  TOTAL STILL OWED, ALL STAFF: Rs 22,000
==============================================================================

  (nothing was changed — this only reads)
```

## WHAT TO NOTICE

- **9 of the 19 rows carry a `contra_of` and are not contras.** Only **1** actually reverses
  anything. That ratio is the whole problem, and on a real eight-month loan it is worse.
- **Darpan's ₹25,000 never appears.** It was keyed wrong, contra'd, and re-entered as ₹15,000 —
  the reader shows the ₹15,000 and says one pair was hidden.
- **Surendra's skipped month is visible as a skip**, with the ₹1,000 interest it added to the
  balance shown on its own line rather than buried in the total.
- **The pending ₹6,000 is named and counted in nothing**, because a checker has not decided it.
- The arithmetic is `staff_ledger.py`'s own, so it cannot disagree with the ledger page.

## GATES

`py_compile` clean · **41 selftest checks, 0 failures** · this walk.

---
## REPRODUCING IT

The kit ships **no `.json` or `.jsonl` file** — the repository blocks them (F-300), and this kit was
that fault's **fourth recurrence**: the publish refused a stored fixture on 10-Sep-2026, exactly as
`KIT_ID.txt` had warned that morning. So the fixture is generated instead of stored:

```
python3 _proof/make_fixture.py /tmp/fixture_ledger.jsonl
```

```
python3 ledger_statement.py --file /tmp/fixture_ledger.jsonl --month 2026-08 --all
```

The generator was checked against the original fixture line for line before the stored copy was
removed — it reproduces all 19 rows exactly.

---
*S237_LEDGER_STATEMENT · WALK_PROOF · 10-Sep-2026. Fixture names are staff names already used
throughout this project; the amounts are invented.*
