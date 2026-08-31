# S214_ANOMALY_BASELINE — the anomaly card's memory (⭐1.6)

**STAGED, NOT INSTALLED. Read-only against the database; writes only its own
baseline file.**

## What S212 asked for

> "Fix the anomaly baseline BEFORE that card goes near a page — across five
> runs today RATE OFF moved 2 → 156 → 345 → 0 on identical data."

The number moved because the DEFINITION moved — five variants of the rate
test in one day. The surviving definition (S211_MATCH
`finance_item_anomaly.py`, md5 `5ca8a9a42e4d4cd894fc01632f8a4ae7`, carried
here byte-identical) was proven at S214 on the real data:

| proof | result |
|---|---|
| determinism | two full scans of the 31-Aug backup (133 days, 17,146 lines): byte-identical flag sets, set md5 `b198731b…` |
| the known truth | the owner's June case (20 tubes, bill A001988, 30-Jun) IS flagged: FAR BEYOND ANYTHING SEEN |
| RATE OFF = 0 is honest | synthetic tenfold-off rate flags; 50%-off flags; 25% off (real orthotic discount territory) rightly does not |
| standing set | **344 flags** — 338 QUANTITY HIGH + 6 FAR BEYOND — mostly common tablets at ~2× their usual ceiling (a two-month course) |

## What this kit adds

`anomaly_baseline.py` — the S210_SWEEP idea applied here: freeze the 344 as
the accepted standing set once (`--rebuild`), then every later run reports
ONLY what is NEW. A card that opens on "NEW 0" is a card the owner can read.

Flag identity is `date|bill|seq|verdict|item` — bill numbers and items,
never patient numbers.

## Proof

`python3 -B selftest_anomaly_baseline.py` — **12 checks, 0 failures**,
invariant-style on a synthetic db (no frozen real snapshot, the S212 rule).

## Install (the owner's one paste, after publish + clone pull)

See `INSTALL_ONE_PASTE.txt`. It copies both files to `/root/finance/`, runs
the selftest, builds the baseline from the LIVE db, and re-runs to show
"NEW 0". Rollback: delete the two new files; nothing else is touched.

---
*S214 · 31-Aug-2026.*
