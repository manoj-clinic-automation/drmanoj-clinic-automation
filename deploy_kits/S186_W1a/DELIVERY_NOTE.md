# Kit S186_W1a — F-104, the WALK-IN reclass

**Session 186 · attribution only · no money moves · gated · reversible**

## Surveyed on your box first, then built

```
open review rows           2,062    Rs 17,44,055
gap across 118 flagged days         Rs 17,36,833
per flagged day the two match TO THE RUPEE
```

The Rs 7,222 difference is review sitting on days whose gap was under the Rs 100 tolerance and so were
never flagged. Named, not hand-waved.

That is why this kit exists in this shape: at S184 the read-only survey was **the only reason** the
cash correction did not double-count Rs 16 lakh. Same discipline — the box was asked before anything
was designed.

## What it does

Legacy Marg bills with no clinic ID were parked in `sale_item_review` by the S183 backfill. They are
real sales with real amounts and no name, so 118 days shout `line_sum_vs_day_total` and ~2,062 rows
sit in a queue **nobody can ever resolve, because the name does not exist to be found**.

They are reclassified to **WALK-IN** — the bucket the schema reserved at S179 with the note
*"lines land here rather than being dropped or guessed"*. Used for exactly what it was reserved for.

Each new line keeps its original `ingest_batch_id` so lineage survives, and is marked
`source='manual'` because this is **a human ruling, not an OCR reading**.

## No money moves, and the gate proves it three ways

`day_line` byte-unchanged by **sum** and by **row count**, and **cash in hand unchanged**. The schema
says it in terms: *"attribution improving later must never be able to move the books."* This only puts
a name against money that was already counted.

## The precheck projects before it writes

It prints how many days are flagged now, how many **would be** flagged after, and — importantly — any
day that would end up *further* from balanced, which means that day's Marg lines genuinely exceed the
declared total. A real discrepancy, surfaced rather than buried in the noise of 118 identical shouts.

## Rehearsed offline

On a store built to mirror your real shape (116 days, most fully unattributed, recent days partly
named, plus a planted day whose lines exceed the total):

- precheck **4/4**, projection printed the planted bad day correctly
- verify **12/12**
- review queue 317 → 0, days flagged 115 → 2, **cash in hand unchanged**
- **idempotent** — applying twice changes nothing
- **rollback restores** the review rows, the exceptions, and leaves money untouched

## Install

```
bash /root/deploy/vps_deploy.sh S186_W1a
```

Expect the flag count to fall from 118 to a small number. **Whatever survives is the interesting
part** — those days are not legacy-no-ID, they are days where the lines and the declared total
actually disagree.
