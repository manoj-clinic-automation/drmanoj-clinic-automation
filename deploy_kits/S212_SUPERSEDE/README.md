# S212_SUPERSEDE — the rule that stops the archive double-counting

**STAGED, NOT INSTALLED. Nothing live was touched. Nothing is ever deleted.**

## The rule, specified by the owner at S206 and not built until now

> *"Amir's month-to-date export, always from the 1st — plus the **supersede
> rule** in the router. Two exports of one month are not two datasets; the later
> replaces the earlier. **Without that rule the archive double-counts
> silently.**"*
> — `S206_FINAL_PLAN_SANJEEVNI.md`, Phase 0, item 1

## Why it matters now

`marg_router.py:394` skips a file only when its **content md5** has been seen.
Right test for the same file twice; wrong test for two *different* exports of
overlapping periods — different bytes, both kept, both looking equally valid.

Under the agreed cadence — **Amir exports month-to-date on every visit** — every
export contains the previous one:

    visit 1   1–5 August
    visit 2   1–12 August     contains visit 1
    visit 3   1–20 August     contains visits 1 and 2

Anything summing "all files of this type" counts the first five days three
times. Nothing errors. The totals are simply too big, by an amount that grows
with how diligently Amir works.

**This already bit us.** The S212 stock walk over-counted on its first run for
exactly this reason, and the cause had been named at S206 five days earlier.

## What it does

`effective(paths)` returns **(kept, superseded)**. A file is superseded when
another file of the same type covers its whole span and outranks it — wider span
first, then later export stamp. Equal spans are broken by the stamp, so a
re-export of one day replaces the earlier rather than adding to it.

**A file whose span cannot be read is always KEPT**, never silently dropped.

## Measured on the owner's own archive, today

    SALE_BILLWISE        16 files -> 13 counted, 3 superseded
        18-Aug  (09:38 export)  superseded by  18-Aug  (09:29 export, later stamp)
        24-Aug  x2              superseded by  23_to_24 range
    PURCHASE_ITEMWISE     6 files ->  6 counted, 0 superseded
    PURCHASE_BILLWISE     2 files ->  2 counted, 0 superseded

The three sale overlaps are real and were found independently by hand before
this was written. **The purchase archive is clean today** — this arrives before
the problem, not after it, which is the only time a rule like this is cheap.

Corroboration: `_outbox_state.json` already marks `9fed61d7` (one of the 24-Aug
pair) as `superseded` — reached by a different route, same answer.

## Why a reader and not a router change

The router is **live** on manojz and its index is the pipeline's memory. A
read-side rule:

- touches no live file;
- fixes the archive that **already exists**, not only files arriving later;
- cannot corrupt `index.csv`.

If it is later moved into the router, the rule itself does not change. That is
the point of keeping it in one function.

## Proof

`python -B selftest_effective.py` — **12 checks, 0 failures**, including the
month-to-date collapse, the same-day re-export, the unreadable-name guard, and
both real archive assertions.

## To adopt

Any consumer that today does `glob(archive/TYPE/*/*)` calls
`marg_effective.effective_for(archive, TYPE)` and uses `kept`. The first
candidates are `push_expected.py`, `marg_purchase.py`'s callers, and anything
totalling a month.

---
*S212 · 31-Aug-2026 · built against the rule as the owner wrote it.*
