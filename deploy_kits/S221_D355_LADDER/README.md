# S221_D355_LADDER — the D355 ladder runs at ingest (F-283)

**One live file moves: `/root/finance/finance_ingest.py`.** No screen changes, no new page,
nobody is asked a question. `d5ff50ad` → **`747b4a50`** (predicted offline, before install).

## The fault, in the live file's own lines

```
min_conf = float(_setting(con, "ingest.min_confidence", "0.70") or 0.70)
...
    low_conf = ln["confidence"] < min_conf
    if low_conf or (anonymous and ...):
        INSERT INTO sale_item_review ...
        continue                       # resolve_patient_checked() is BELOW this
```

A bill carrying a name and no clinic ID leaves `split_clinic_id()` at confidence **0.5**, fails
the 0.70 gate and is **parked** — before the identity chain is ever reached. D355 rules identity
**by lookup**, never by a generated confidence, and the lookup was simply never run. **7 of 27
bills on 02-Sep (26 %).** F-283: *a parked bill is a lookup not yet run, not a verdict.*

## What was measured before anything was built

On the live copy, over **every bill parked since 01-Aug** (182 of them — before August, Marg
carried a last-four on only 9 % of bills, so the older 2,166 flatter every rung):

| ladder as configured | resolved | left ambiguous |
|---|---|---|
| last-4 + name only | 75 · 41 % | 0 |
| + Docterz visit, ±3 days | 99 · 54 % | 48 |
| + Docterz visit, **same day only** | 104 · 57 % | 22 |
| **+ the full mobile** | **126 · 69 %** | **0** |

**Two findings decided the shape.**

**1 · Same-day is not the weaker setting — it is the better one, on both axes.** Of the 1,105
July–August pharmacy bills carrying a real patient, **78 % were bought on the day that patient
visited** and only 2.3 % within three days. D11's founding assumption — *"a pharmacy purchase
follows a consultation by days, not hours"* — is **false for this pharmacy**. The ±3-day window
finds *fewer* (24 vs 29) and leaves *twice* the ambiguity, because it drags in a second patient
whose name also agrees. The day's list is a median of **24** people: a short list, not a search.

**2 · The full mobile ends the ambiguity.** Every one of the 22 rows still ambiguous on a
last-four is ambiguous *only* because a last-four is shared — **1,871 last-four values in this
master belong to more than one patient, but only 719 numbers do.** Given the number, the ladder
separates **22 of 22**.

## What this kit does — the owner's shape (S221)

**Clinic ID · full mobile · name attach; what falls through goes to the same-day Docterz list;
no question is raised with anyone** — *"right now only internal match is sufficient."*

The ladder does not move money and does not touch the accept path. **It supplies the clinic ID
the bill was missing**, and the line then travels the ordinary path below it — so
`resolve_patient_checked()` and the S220 name-check still run on every ladder-named bill.
Every rung is fail-soft: no answer, and the line parks exactly as it does today.

| rung | what it needs | confidence written |
|---|---|---|
| 1 · clinic id | an ID on the bill whose master name agrees | 0.95 |
| 2 · mobile | the full number, fingerprinted **in memory** against `mobile_fp` | 0.95 |
| 3 · last-4 + name | never the last four alone | 0.85 |
| 4 · same-day visit | the day's Docterz list, **same day only** | 0.75 |

The confidence written is the **rung's own**, never a pretended 0.99 — so how a bill was named is
visible in `sale_item.confidence` as well as in the record.

**Nobody is asked, but nothing is silent.** Every attachment writes an `identity_resolution` row —
day · bill · rung · the bill's name · the master's name — UNIQUE per bill, so a re-export updates
rather than duplicates. Any one of them is answerable afterwards, and reversible.

**The baked analytics:** `v_entry_discipline` — per day: bills, keyed clean, named by the ladder,
by which rung, and still parked. It becomes a **per-person** number the moment Marg's user-wise
register reaches the router (⭐1-3); until then it is per day, which is already the discipline
signal the owner asked for.

## F-185 and D355 — no number is stored

The full mobile is fingerprinted in memory against `patient_ref.mobile_fp` and discarded. The
patch also **strips `mobile` from the raw JSON** that `sale_item_review` keeps — without that, the
column S220 added to the export would have started writing full numbers into `finance.db` through
a code path nobody changed. No ten-digit literal appears anywhere in this kit; the walk's one test
number is assembled at runtime and exists only in the copy.

## A defect this kit's own selftest caught before install

Rung 3 first **delegated** to `finance_patient_match.match_bill()`. That function reads its rows
**by column name**, so on a connection with no `sqlite3.Row` factory it raises `TypeError` — which
the ladder's fail-soft wrapper would have swallowed, leaving the rung silently dead in production.
The walk had been green only because the walk's own connection happened to have a Row factory.
Rung 3 is now written out directly, **the walk runs the ingest on a plain connection**, and a
33-row cross-check against `match_bill()` on real master rows proves the two agree and cannot
drift. (The S208 shape: green checks over a defect. Recorded, not just fixed.)

## Files

| file | what |
|---|---|
| `patch_ingest_ladder_s221.py` | finance_ingest.py — the ladder, the recording, the view (5 anchors) |
| `selftest_ladder_s221.py` | 23 checks, all of them **refusals** — synthetic master, no live db |
| `walk_ladder_s221.py` | the live-shape walk: real `ingest_day`, real master, real visit feed, plain connection — 32 checks |

## What changes on the first export after the restart

Bills that used to park for want of a clinic ID are named and counted as ordinary sales. **The
day's total does not move** — parked money already counts since F-282 — but the split between
*attributed* and *in review* does, and that is the point.
