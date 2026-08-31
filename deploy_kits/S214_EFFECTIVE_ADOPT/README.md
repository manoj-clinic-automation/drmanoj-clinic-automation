# S214_EFFECTIVE_ADOPT — the supersede rule adopted (⭐1.5)

**The record of an adoption done in place.** The rule itself lives in ONE
file, `deploy_kits/S212_SUPERSEDE/marg_effective.py` (unchanged, D202: no
second editable copy). At S214 the four flow-report consumers that total
across archive files were routed through it:

| consumer | sites routed |
|---|---|
| `S207_PO/po_build.py` | 1 (PURCHASE_ITEMWISE — vendor spend, quantities, rates) |
| `S207_STOCK_VPS/push_snapshot.py` | 1 (PURCHASE_ITEMWISE — rates) |
| `S208_STOCK_LEDGER/push_expected.py` | 3 (SALE_BILLWISE, PURCHASE_SUPPLIERWISE, PURCHASE_ITEMWISE) |
| `S207_RETURNS/returns_data.py` | 2 (PURCHASE_ITEMWISE) |

**Snapshot reports (STOCK_CLOSING, STOCK_EXPIRY) were deliberately NOT
routed** — there the F-235 rule holds (largest export for a date, never the
latest: a later category-filtered export must not beat the whole-shop one),
and marg_effective's later-stamp tie-break would be the wrong rule.
Measured on the real archive: it would have superseded 7 closing / 4 expiry
files, including one TOTALS→DEFAULT flavor crossing. Recorded so nobody
adopts it there by accident.

## Measured at adoption, 31-Aug-2026, on the real archive

- SALE_BILLWISE: 16 files → 13 counted; the 3 known overlaps excluded and
  named on stdout at every run.
- All 1,375 deduplicated sale line keys identical before and after; zero
  value conflicts today — **no number changed**. The rule pays the day
  Amir's month-to-date cadence begins, which is the cheap time to adopt it.
- PURCHASE_*: clean today (0 superseded), now protected.
- Each consumer's kit gate (SUMS.md5) regenerated for its one changed file,
  green from inside its folder; a CHANGED_S214.md sits beside each.

## Proof

`python3 -B selftest_adopt.py` — 19 checks: each consumer imports the rule,
routes exactly its flow-report sites, leaves snapshots alone, compiles; plus
the month-to-date collapse, same-day re-export, and never-drop invariants.

Nothing here installs anywhere — these tools run in place on manojz when
their .bat files run (PUSH_STOCK_DAILY is parked; unchanged).

---
*S214 · 31-Aug-2026.*
