# S186 — F-113: "not filed (refused, harmlessly)" is only harmless until the day is filed

**Session 186 · 17 Aug 2026 · found read-only, before the item-wise go-live. No live change made.**
To be folded into the Fault Register at the S186 close (append still owed from F-109).

> ### ⚠ THIS DOCUMENT WAS CORRECTED THE SAME SESSION
> The first version of it blamed a **short export** — "the file stopped at 13 Aug and the tool said
> nothing." **That was wrong**, and it was wrong in the same way the faults it describes are wrong:
> a plausible mechanism was fitted to the evidence before the evidence was complete. Both the
> original export and the driver were then tested directly, and neither behaves as claimed. The
> superseded diagnosis is kept below, struck through, because deleting it is how a record starts
> lying (F-23).

---

## The evidence

The owner ran the Marg item-wise backfill, reporting it as **1 April to 15 August**. The box:

```
2026-08-08  batch=114  marg_export  partial  read=23  acc=20  rev=3   items=20   2026-08-16T22:42
2026-08-09  batch=115  marg_export  ok       read=1   acc=1   rev=0   items=1    2026-08-16T22:42
2026-08-10  batch=116  marg_export  partial  read=34  acc=21  rev=13  items=21   2026-08-16T22:42
2026-08-11  batch=117  marg_export  partial  read=25  acc=19  rev=6   items=19   2026-08-16T22:42
2026-08-12  batch=118  marg_export  partial  read=30  acc=20  rev=10  items=20   2026-08-16T22:42
2026-08-13  batch=119  marg_export  partial  read=31  acc=23  rev=8   items=23   2026-08-16T22:42
2026-08-14  batch=None      -       NO BATCH                          items=0
2026-08-15  batch=None      -       NO BATCH                          items=0
```

## What was ruled out, by testing rather than reasoning

**~~The export was short.~~** It was not. `MARG_1_15_AUG.XLS` was read with the live
`marg_report.py` (`829f4344…`) and reports:

```
BILL WISE SALES STATEMENT FROM 01-08-2026 TO 15-08-2026     15 days found
   2026-08-14   bills=23   net=17,943.00
   2026-08-15   bills=10   net= 8,851.00
```

Both days are present, with data.

**~~The driver aborted partway.~~** It has an abort path (`got != expect_bills` → rollback and
return), so this was checked directly: the live `finance_ingest.ingest_day` was run against the real
file on a throwaway store, for 12–15 August, with 14 and 15 set to `draft` exactly as on the box.

```
DATE         STATUS    EXPECT   ROWS_READ  result
2026-08-12   submitted 30       30         ok
2026-08-13   submitted 31       31         ok
2026-08-14   draft     23       23         ok
2026-08-15   draft     10       10         ok
```

No abort, and `draft` is not a blocker.

## The actual cause

`marg_backfill.py` skips a day when **no `day_entry` row exists** for it:

```python
e = con.execute("SELECT id FROM day_entry WHERE unit=? AND business_date=?", (a.unit, iso)).fetchone()
if not e:
    print("%-12s %-11s ..." % (iso, "NOT FILED", ...))
    blocked += 1
    continue
```

and closes with

> `13 of 15 day(s) reachable · 2 not filed (refused, harmlessly)`

**At the moment of the run, 14 and 15 August had not yet been filed** — Darpan's drafts were created
afterwards. So the tool behaved correctly and reported honestly. The skip was right.

**The skip stops being harmless the moment the day is filed, and nothing revisits it.** No exception
is raised, no flag is written, no marker records that those dates were passed over. The only trace is
a line of console output from a run that finished a day earlier. The word *"harmlessly"* is doing
heavy lifting: it is true at that instant and false forever after.

## Family, and the correction to the family

**F-100** (`push_kit.bat` reported success while git dropped a file) and **F-112** (a deposit booked
on a date no statement covered). Those two are *silence about what was never reached*. This one is
different and worth separating: **the tool spoke, correctly, and the statement it made expired.** A
correct message about a temporary state, with nothing to make it durable.

## RULE

**A skip that depends on the state of the world must leave a record that outlives the run.** Console
output is not a record. If a day is passed over because it was not yet filed, that must land where
someone will meet it again — a `data_flag`, an exception row, or a re-run list — because the
condition that justified the skip is one that routinely stops being true.

## Remedies

**Immediate (owner):** simply re-run the backfill. The entries now exist, so both days will ingest.
Nothing needs re-exporting — the file already on the VPS contains them.

**Structural (owed):** `marg_backfill.py` writes a `data_flag` (or a `missing_day`-style row) for
every date it skips as NOT FILED, so a later filing surfaces it instead of leaving it to memory.
Optionally `--from`/`--to` so the requested range can be compared with what was reached.

## Also seen, not a fault

Most batches are `partial` (23 read / 20 accepted, 34/21, 30/20…). That is the legacy no-ID pattern
seen from the ingest side — the same rows kit **S186_W1a** reclassifies to WALK-IN.

## What this episode is really about

Twice in one hour a mechanism was proposed that fitted the evidence, and twice the box disagreed. The
export theory and the abort theory were each plausible, and each was wrong. **The only reason the
right answer was found is that both were tested against the real file and the real adapter rather
than argued about** — which is D172 and D188, applied to a diagnosis instead of to a hash.

---
*S186 · read-only · no live change · corrected once, in the same session · next free finding: F-114*

*(Filed to the repo at the S187 close — this document lived in project knowledge only from S186,
which is the F-107 condition its own manifest row named. Hashed as delivered here; the portal-path
remedy shipped in `S186_I1a` and the CLI remedy remains on the backlog.)*
