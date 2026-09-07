# S229_ITEM_SPINE — one row per product, and every name it has ever worn

**07-Sep-2026.** Two files. **Nothing existing is altered, renamed or dropped** — this adds
seven new tables and fills them. Every screen keeps working exactly as it does today.

## Why

Item identity lived in six places and each answered *"which product is this?"* privately.
Measured on the 07-Sep backup: **407 distinct product names for a shelf of 373 items**, and
**515 sale lines carrying Rs 95,611.93 of MRP value that tied to no shelf item at all.**

The cause is that Marg clips a description to a fixed width — **and the width differs by report:
20 characters in the sale report, 27 in the purchase reports.** The 27 was found only by running
this against real data; no amount of reading the sale side could have revealed it.

## The cardinal rule

**A name is resolved or it is recorded. It is never guessed.** A clip fitting two items is
written to `marg_name_unresolved` and raised as a task. It is never assigned to the first, the
biggest or the newest.

## What it does on the 07-Sep data

| | before | after |
|---|---|---|
| sale lines tied to a shelf item | 17,333 · Rs 32,37,598.97 | **17,792 · Rs 32,71,053.06** |
| still ambiguous | — | 56 lines · Rs 68,806.00, every one listed |
| shelf items with an MRP basis | 198 of 373 | **212 of 373** |
| names matching nothing at all | 26 | **0** |

Money here is **MRP value** — `amount_p` is the price of one pack, not a line total (159 of 224
items carry exactly one distinct value whatever the quantity), so it is multiplied by packs sold.

## The 24 renames are registered BEFORE they are made

The day Amir renames an item in Marg, the next export carries a name this system has never seen.
All 24 are pre-registered, so each joins itself when it lands, in any order, over any number of
days. **Simulated against the real shelf:**

```
items 374 -> 374 (not 398)   items with no name: 0   rename tasks: 24 closed by themselves
ambiguous names for NEW lines: 0        lines already billed under an old clip: still ambiguous, and said so
```

## What v1 got wrong, and how

v1 passed 44 self-tests and was **wrong in the one case this file exists to serve.** An
adversarial review against real data found that the first time a rename was applied, a second
item would be minted — because `_add_item` asked `marg_item.canonical` whether it knew the
product, and a pending rename lives in `marg_item_name`. 373 items would have become 397,
twenty-four of them nameless, every later sale credited to the pre-rename item, **and nothing
would have said so.** Five more defects came out of the same review and all are fixed. The
lesson is on the record: *a green self-test suite proves the cases you thought of.*

## Prove it

```
python marg_spine.py --selftest
```

54 checks, 0 failures. Then, against a copy — this never opens the real database for writing:

```
python marg_spine.py --db /root/finance/finance.db --dry-run
```

## Install — ONE line, and it gates itself

After the publish, on the VPS. First the clone:

```
cd /root/deploy/repo && git pull
```

Then the whole thing, in one line. It runs the 54 self-tests, rehearses the entire build on a
COPY, writes a backup of the database, and only then builds — stopping at the first doubt and
touching nothing if anything fails:

```
/root/wa/venv/bin/python3 /root/deploy/repo/deploy_kits/S229_ITEM_SPINE/marg_spine.py --db /root/finance/finance.db --install
```

It prints `1/4 … 4/4` and either `DONE` or `REFUSING: … Nothing was touched.` The refusal paths
are tested: a corrupt database and a missing file both stop at step 2, and no backup is left
behind by a run that refused.

To undo entirely, the line it prints at the end:

```
\cp /root/finance/finance.db.bak_S229_spine /root/finance/finance.db
```

**Re-runnable:** building twice changes nothing — proven on the real database, all five tables
byte-identical between runs. Nothing is copied into `/root/finance/`; the script runs from the
deploy clone, so there is only ever one copy of it.

**No service restart is needed.** Nothing reads the spine yet.

## Verify this kit

Run from INSIDE this folder — its rows are rooted here:

```
md5sum -c KIT_MANIFEST.md5
```
