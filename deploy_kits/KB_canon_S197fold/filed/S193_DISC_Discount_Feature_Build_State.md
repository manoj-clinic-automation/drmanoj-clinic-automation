# S193_DISC — per-bill discount feature (build state)

**Status:** COMPLETE & LIVE (2026-08-20). Code installed GREEN (smoke 557/557 unchanged);
historical backfill applied — **3,077 / 3,162 bills** filled across 121 days. Shipped as a
tracked `.py` data module (not CSV) because the repo `.gitignore` blocks `*.csv` (patient-data guard).

## What it does (Hub Fix 5)
Adds **Gross | Disc | Net** to the Marg bill drill on `/finance/approvals`. Previously only NET
showed, so a discounted bill reconciled invisibly against a day's gap. Now works for new Marg
pushes AND for history.

## Design decisions
- **Store gross, don't compute it.** `tax_p` always 0 in this data, but Marg rounds net to whole
  rupees so `gross ≠ net + disc` for 1,312 bills. Gross is stored from the parser. Magnitudes (abs).
- **Adapter reads gross/disc DIRECTLY from the CSV row**, not via `ingest_column_map` (whose
  `our_field` CHECK allows `'discount'/'tax'` but not `'gross'`). Avoids recreating a CHECK table.

## The chain (all live)
1. `finance_schema.sql` — `sale_item` gains `gross_p`, `disc_p` (live DB via idempotent ALTER).
2. `marg_report.py` — `LINE_COLUMNS`+`write_lines_csv` emit `gross`,`disc`. Selftest 38/38.
3. `finance_ingest.py` — in-place patch: adapter_csv reads gross/disc from row; `sale_item` INSERT
   stores `gross_p,disc_p`.
4. `finance_app.py` — `_marg_bills_for_day` returns gross/disc (NULL→"—").
5. `finance_approvals.html` — in-place patch: header + row + items colspan 4→6.

## Historical backfill (two-pass, `apply_historical_discount.py` + `historical_discount_data.py`)
3,162 NON-PHI bills, Apr 1–Aug 15. **PASS 1** exact `source_ref==bill_no` (Marg-push days, 1,005).
**PASS 2** by net amount in bill order among unclaimed rows — the older days were backfilled at
**S186/F-104 with SYNTHETIC refs** (`S186-F104-576`…, `source='manual'`), same nets in bill order
(2,072). Only writes gross_p/disc_p, never booked net. Idempotent. 85 unmatched = net-₹0 bills
(never stored as sale rows) + a few empty days (04-19, 05-04, 05-27, and known 05-03).

## LIVE hashes (pin — D321(d))
- finance_app.py        `d86745b70347f47127b2fa0f933ea364`
- marg_report.py        `6411a57d4517e0a06a02e1045b354138`
- finance_ingest.py     `a4e9663f9be1c138293d6dd8311577d0`  (in-place patched)
- finance_approvals.html `ea874fec873e282c5e3c38c74bd4582e`
Pre-install (gated): finance_app d455e1aa (F-155), marg 829f4344, ingest 1f730bcd, html fbf1655f.

## Repo hygiene
Added `/_to_delete/` to `.gitignore` (device bridge can't `rm`; trash is moved there, then owner
deletes from Windows). PUBLISH_ALL guard refuses on any gitignored file under deploy_kits — that's
why the CSV had to become a `.py` module.

## NEXT project item
Full-auto ping-pong email query system (box reads owner Gmail commands, runs read-only dr_query,
replies). Needs owner-created Gmail app password + tight security scoping (read-only, trusted-sender).
