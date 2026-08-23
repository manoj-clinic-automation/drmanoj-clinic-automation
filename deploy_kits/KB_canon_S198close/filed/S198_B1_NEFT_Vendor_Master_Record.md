# S198_B1 — NEFT Vendor Master v1 + NEFT Guard (Club B · B1 COMPLETE)

**23-Aug-2026 · Session 198.** Deliverables on the owner's PC at
`D:\dr-manoj-git\NEFT_Vendor_Master\` (**deliberately OUTSIDE the git working tree** — vendor
bank data never enters the PUBLIC repo, D320/F-31 family):
`NEFT_Vendor_Master_v1.xlsx` · `Neft_Guard.gs` (md5 `89df93ec3dd0a46b8b2b329d70a5babe`) ·
`test_guard.js` (`cd6b5ba107ad003a22f4f2c25c1cb177`) · `GUARD_SETUP.md`
(`c9454c99c94ee49bb7abb4eaad9d1875`).

## Part 1 — the Vendor Master (the owner's three rulings executed)

1. **Verified FY 2026-27** — 22 vendors actually paid Apr–Jul 2026, account + IFSC exactly as
   the bank executed (leading zeros intact), per-month amounts + formula totals.
2. **Account changes** — old account kept forever with the month of change. Four real changes:
   Drug Deals (ICICI 019205500804 → YES 7484600001944, by the Jun-25 file) · Ess Kay agencies
   (HDFC0001887/50200027918298 → HDFC0008237/50200111042207 at Dec-2025) · Gunina (one-month
   deviation to 50200083799905 in Jan-25 and back).
3. **UNVERIFIED — confirm first** — BASS PHARMA DISTRIBUTORS (last Jan-25) · VINTECH REMEDIES
   (last Sep-25), flagged against silent reuse.

Verification: all 18 months' transcriptions sum exactly to their files' own printed totals
(18/18); FY account/IFSC cross-month consistency clean; the workbook's four FY column totals
recompute (recalc, 49 formulas, 0 errors) to the exact file totals.

## Part 2 — the NEFT Guard (owner: "B1 decides where the money is authorised to go")

`Neft_Guard.gs` — pastes into the **"UPI Reconciliation"** GAS project (clinic account) beside
`Neft_Draft.gs`; needs the Advanced Drive Service enabled + one `ng_setup()` run. It:
creates the Google Sheet **"NEFT AUTHORISED VENDORS"** in `SHAVEZ / SANJEEVNI MEDICOS FILES`
(seeded 22 VERIFIED + 2 BLOCKED; never overwritten if present — the Sheet is the live
authorisation list, owner/Shavez-maintained: add-a-row on change, SUPERSEDE never overwrite);
then daily ~07:00 re-checks the newest advice xlsx **only when it changed** (throwaway
converted copy, trashed in a finally) and **emails the owner ONLY on problems**, naming exact
rows across five classes: UNAUTHORISED ACCOUNT · BLOCKED VENDOR · SUPERSEDED ACCOUNT ·
**NAME MISMATCH (the April-2025 shifted-column fault class)** · IFSC DIFFERS. Verdicts logged
to the Sheet's Check-log either way. **Never blocks, edits, or sends** — the D325 boundary
holds; a cheque and signature stay in the loop.

Proof: the classifier is a **pure function inside the shipped file** (`ng_classifyRows_`) and
the node harness `test_guard.js` ran **9/9 GREEN on the exact shipped bytes** — all five
problem classes, zero-stripped account matching, quiet-on-clean, total-row/header rows ignored.

**Owner setup owed (3 min):** paste `Neft_Guard.gs` into the UPI Reconciliation project →
Services (+) → Drive API → run `ng_setup()` (per `GUARD_SETUP.md`).

## Source-data findings (in the workbook's Data notes)

- ⚠ **`NEFT ADVICE APRIL 2025.xlsx`: account column SHIFTED against its names** — if that file
  went to the bank as-is, that month's credits went to wrong accounts; worth one look at the
  April-2025 bank statement. Excluded from account evidence.
- Older files stored accounts as numbers → leading zeros lost; FY files are text and correct.
- `JULY 25` row 10: invalid IFSC `CBIN280219` (missing zero).
- `MAY PAYMENT 2025 NEFT.xlsx` ≡ `JUNE PAYMENT 2025 NEFT.xlsx` (stray copy).
- `FEB 25` SAISUN amount blank in the source (its own total excludes it).

## Context found en route

The S195 `Neft_Draft.gs` automation is LIVE (ran 23-Aug 00:00 UTC: AUGUST draft created; July
FINALs shipped to ToMedical for Amir). **Build lesson recorded: base64 re-emission through
model generation is NOT viable for file transfer** (two loud failures); the Drive text route +
per-file total verification is the standing method.
