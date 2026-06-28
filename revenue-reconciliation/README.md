# Revenue Reconciliation (Marg + Lab → ledger)

**Status:** spec locked (Decision D11), build pending.
**Source sample files are PHI — they are NOT in this repo. Local handoff kit only.**

## Goal (D11)
Map maximum **correct** external revenue from 1 April. Never drop a rupee.
Doubtful rows → per-patient review list. Truly unmatchable → "Unclassified" (still counted).
Never force-assign a bill to the wrong patient.

## What already exists (don't rebuild)
The Follow-Up Tracker Flask app already has a finance dashboard — live routes
`/finance`, `/finance/patient`, `/finance/period`, `/finance/lines`, `/lab`, `/lab/add`,
`/procedure`, `/concessions`; `revenue.py` computes per-patient lifetime value +
day/month/year totals + per-source breakdown. It is trapped on the clinic PC
(migration lane M1). The gap is getting Pharmacy + Lab revenue INTO it.

## Source reality (verified)
- `revenue_ledger.csv` Source = only Consultation, X-ray, Procedure
  (X-ray = Docterz Laboratory + Radiology amount, the clinic Fuji DR).
- Lab (NK Pathology / Labmate): manual `/lab` form, Source="Lab", currently EMPTY.
- Pharmacy (Marg): corroboration signal only — `/finance` says "not yet connected."

## Two eras → two match strategies
- **Suffix era** (Marg 20-Jun onward / suffix-era Labmate): Clinic ID is a CLEAN key.
- **Pre-suffix backlog** (1 Apr → 19 Jun, all historical): name + bill-date↔visit-window fuzzy.

## Verified shapes
- Marg 20-Jun (36 bills · BILL NO · DESCRIPTION · BILL VALUE): ~80% carry a 10-digit
  mobile; ~52% carry both mobile + 4-digit Clinic ID.
- Labmate 1 Apr–18 Jun (Date · Sr · Name · Charge · Disc · Net · Receipt · Refunded · Bal;
  201 rows): 0/201 carry the Clinic-ID suffix (pre-suffix era). Total Net = ₹3,50,130,
  currently invisible to /finance. Names honorific-prefixed → matcher MUST strip
  Mr/Mrs/Smt/Sri/Shri/Km/Master/S-o/W-o/D-o/B-o, lowercase, token-SET match.

## Matching ladder (per bill)
1. Clinic ID → 2. mobile exact → 3. name + bill-date within visit window →
4. name unambiguous → 5. ambiguous → review list / no match → Unclassified.

## Output
One durable Source-tagged ledger (Pharmacy / Lab / Unclassified), each row carrying
`Match_Status`, `Match_By`, confidence, **plus** `revenue_review.csv`.
Build the fuzzy engine first (where the 1-Apr backlog money is), prove on Labmate,
then the Clinic-ID engine. Always dry-run a summary before writing anything.

## To build
`reconcile_revenue.py` — not yet written.
