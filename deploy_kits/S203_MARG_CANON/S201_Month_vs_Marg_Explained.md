# S201 — "This month vs Marg" explained: it is the review queue, to the rupee

**25-Aug-2026 · read-only investigation, live database queried via Termius. Nothing changed.**

## The answer

The red **"This month vs Marg"** line is not an accounting discrepancy, and nothing is missing from
the books. **The difference is exactly the value of lines sitting in `sale_item_review` — bills the
parser read with confidence below 0.70, waiting for a human to identify the patient.**

| day | open review lines | review value | health page difference |
|---|---|---|---|
| 2026-08-17 | 9 | 9,990.00 | 9,990.00 |
| 2026-08-18 | 8 | 4,577.00 | 4,577.00 |
| 2026-08-19 | 7 | 3,500.00 | 3,500.00 |
| 2026-08-20 | 4 | 1,331.00 | 1,331.00 |
| 2026-08-21 | 16 | 30,045.00 | 30,045.00 |
| 2026-08-24 | 5 | 2,425.00 | 2,425.00 |
| **total** | **49** | **51,868.00** | **51,868.00** |

Every row `status='open'`, every row `reason='low confidence'`.

## What the check actually compares

`_marg_month_compare()`:

- **books** = `v_cash_ledger.revenue_p` — the day's **entire** recorded revenue.
- **Marg** = `marg_net_sql()` over `sale_item` rows from the `marg_export` batch — **only the lines
  that were attributed**.
- `days_differing` is a bare `if bp != mp` — **no tolerance**. One paisa lists a day.

So it subtracts *attributed lines* from *the whole day*. The remainder is, by definition, whatever
was parked in review. It can never be zero on a day with a single low-confidence bill.

## The rule that decides — it is NOT identity

`finance_ingest.ingest_day()`:

```python
low_conf   = ln["confidence"] < min_conf          # ingest.min_confidence, default 0.70
anonymous  = not ln["clinic_id"] and not ln["patient_name"]
structured = adapter != "sarvam_ocr"              # marg_export -> True
if low_conf or (anonymous and not (anon_to_walkin and structured)):
    -> sale_item_review
```

For a Marg export `structured` is True and `ingest.anonymous_to_walkin` defaults on, so the second
clause is **always False**. **Anonymity alone never diverts a Marg line** — that was the S186/F-114
fix, and it works. The only live gate is **confidence < 0.70**.

*An earlier inference in this session — "no clinic ID → dropped" — was wrong.* It fitted 21-Aug
(21 of 37) and 24-Aug (17 of 22) exactly and still fitted the wrong reason. 18-Aug broke it: nine
id-less bills worth 4,767, but the difference was 4,577. Bill **A003039 (₹190)** is id-less and was
**ingested** — it cleared the confidence bar. 4,767 − 190 = 4,577. **A rule that fits two days and
predicts the third wrongly is not the rule.**

## Verified live

```
18-Aug  batch 126  status=partial  22 rows  naive 23,879.00  signed net 20,599.00
21-Aug  batch 127  status=partial  21 rows
24-Aug  batch 128  status=superseded  0 rows      <- a duplicate push, correctly discarded
24-Aug  batch 129  status=partial  17 rows
books:  21-Aug 49,181.00   24-Aug 12,964.00       <- exactly the Marg reports' own totals
```

18-Aug's `23,879 / 20,599` are the very two figures `marg_net_sql`'s docstring records from the
18-Aug credit-note incident — the live data confirms that history exactly.

**`status='partial'` is the system being honest**: it ingested some rows and parked the rest.
Nothing is lost, and **the money is fully counted** — `day_line` carries the whole day. What is
missing is *attribution to a patient*, which matters to the patient spine, not to the cash.

## The faults

**F-a · The check compares two things that can never be equal.** Whole-day revenue against
attributed-only lines. Any day with one low-confidence bill differs, so the row is **permanently
red at `bad` severity** — and `bad` drives the portal tile. This is precisely the "wallpaper"
condition the S195 ruling exists to prevent: *"flags always exist, so letting them drive the tile
would light it permanently and turn the warning into wallpaper."* The same reasoning was applied to
`data_flag` and never to this row.

**F-b · The differing-day list truncates silently.**

```python
"Days differing: " + ", ".join(… for d in _mm["days_differing"][:5])
```

Five, with **no "and N more"** — unlike the `days_not_filed` line immediately above it, which does
append one. 24-Aug was differing and simply was not shown. It was found by arithmetic (books +12,964
vs Marg +10,539 while the listed five were unchanged), then confirmed in the code.

**F-c · The page describes a workable queue as an unexplained discrepancy.** 49 bills and ₹51,868
are waiting for someone to identify them. That is a job a human can do — and the line neither says
so nor links to `/finance/review`.

## What the fix should be

1. **Compare like with like.** The S201_A1FIX kit installed today put the Marg report's **own net**
   into the staged payload (`business_date` / `net_p`). The check can now compare books against the
   report's stated total — a real books-vs-Marg test that *can* go green.
2. **Report the queue as a queue**: *"₹51,868 across 49 bills is waiting to be identified"*, `warn`
   not `bad`, linking to the review page.
3. **Fix the silent truncation** — append "and N more", as the sibling line already does.

## Worth watching

- **21-Aug had 16 of 37 bills below the confidence bar (43%)** — well above the ~25% of other days.
  Worth one look at that day's report for a formatting cause.
- The queue was cleared 2,072 → 0 at S186 (F-104). The **anonymous** stream was closed then; the
  **low-confidence** stream was deliberately kept, because a human can resolve it. At ~8 lines a day
  it refills to roughly 250 a month if nobody works it.
- `ingest.min_confidence` is a **setting** (default 0.70). Whether 0.70 is right for Marg exports is
  an owner decision, not a code one.

---
*S201 · read-only; live DB opened `?mode=ro`. No patient identifiers reproduced; no tokens read or
printed.*
