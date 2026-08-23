# S198_B2 — the purchase-cycle toolset COMPLETE (bill check + corrections log + prefilled recon)

**23-Aug-2026 · Session 198.** All at `D:\dr-manoj-git\NEFT_Vendor_Master\` (outside the public
repo — vendor/bank data). Final md5s: `make_recon.py 0cdbfd31d4461bd460a734d8f7502606` ·
`make_billcheck.py 714dce77f91a9f21b1a01fbad6e80e94` (v2, vendor-grouped) · `RECON_SETUP.md
0ea86e21de31dbd22ea165ee8f1898e0` + three .bat runners + two July PROOF workbooks.

## The owner's flow (stated live; FIVE refinements folded the same hour)

Bill-wise generated → **RUN_BILLCHECK** → the bill-check sheet, **staff-friendly by owner
spec**: bills **GROUPED BY VENDOR in expandable outline rows** (matching the physical
bundles), coloured vendor header rows with subtotal + live "checked k/n" counter; large
fonts/bolds, coloured columns (blue amounts · yellow dropdown · orange correct-amount), row
gridlines; per bill a **Correct/Wrong DROPDOWN** (data validation) — picking Wrong opens
exactly two typed fields (correct amount + reason); **discrepancy recorded at BILL level**;
a second tab gives the month's **vendor purchase stats free** (bills, totals, share %,
largest bill). → **LOG_CORRECTIONS** (apply-in-Marg list + cumulative `corrections_log.csv`,
deduped; "marked Wrong but no amount" warned loudly) → corrections applied in Marg,
corrected exports regenerate → **RUN_RECON** → `Vendor_Reconciliation_<month>.xlsx` into
ToMedical (Amir's PC via the new clinic-Drive install) + locally, **both summary columns
prefilled from Marg's fortnights** (1st–15th / 16th–end); Amir types a summary ONLY where the
vendor's paper differs; rows self-flag; payable/NEFT/carry-forwards computed and chained.
Then print → Amir signs → Darpan signs → Shavez → **B1 NEFT Guard** → cheque + letter +
`sanjeevni.bly@gmail.com` bank email (human, D325) → payment → Amir reconciles in Marg.
Parked with the owner's blessing: an **item-wise purchase report** later "if it adds value".

## Safety properties (all tested)

Latest-archived-export-wins · typed-into sheets never overwritten (`_regen`) · both parsers
REFUSE on row-sum ≠ the export's own printed TOTAL (block-level for suppliers) · off-register
suppliers in a red "paid how?" section · unmapped names loud (extendable `name_map.csv`) ·
party names normalised (the export pads a city suffix — found on real bytes).

## Proof (real July 2026 archived exports)

Bill check: 103 bills = file TOTAL 476,393; vendor subtotals proven (KEDAR header 98,240,
0/8 counter); grand-total multi-area SUM = 476,393; outline levels correct (103 bills under
21 vendor headers); dropdown → OK ✓ / FIX IN MARG: -310 statuses live; harvest carries the
vendor context, logs, dedupes, and warns on incomplete rows. Recon: 20/21 vendors prefill
EXACTLY to the executed July NEFT; fortnight split verified (A.A. 3,791+5,930=9,721);
KEDAR's genuine ₹310 fires CHECK ⚠; AGARWAL SURGICALS (₹3,556, never NEFT-paid) surfaces.
Recalc clean everywhere.

## Owner setup owed (one time)

`pip install openpyxl xlrd` on manojz (then the three .bat double-clicks ARE the flow). Plus
the B1 guard paste (`GUARD_SETUP.md`) still owed.

## Housekeeping / open

The static AUG-2026 template in ToMedical overwritten with a SUPERSEDED notice. The B2
email-pack for Hemant/Shyam (one mail/month + SENT PACKS archive) remains open on the owner's
two calls: pack-only vs per-statement drip; the Tally "MARG FILE EXPORT" spec.
