# PURCHASE PORTAL — **D335 · SIGNED CONTRACT** (S198 · 23-Aug-2026 · v8 final · build starts S199)

**SIGNED by the owner 23-Aug-2026 ("signed · build in next session"). This workflow table IS
the spec. Next free decision: D336.**

**The owner's vision:** the purchase-payment cycle moves INTO the system. Reports are
generated on the medical PC and consumed by the existing capture pipeline; the work happens
in a portal scoped to each person; the owner's dial shows who is working, what has been done,
and the sheet's status; the final NEFT excel is one tap away — shareable, downloadable,
printable — and the bank letter comes prefilled with exactly three variables: **date (picker)
· amount (prefilled) · cheque number (the one typed field)**. The S198 xlsx toolset stays as
the manual fallback (standing rule).

> **AUDIT-TRAIL SCOPE: INTERNAL ONLY. NO trail reaches the accountant or the bank.**
> External outputs are CLEAN — the exact formats they already know.

> **SCAN-AT-ARRIVAL:** each purchase bill (~80/month) is scanned AT ARRIVAL via the
> **existing asset-app intake** (scanner widget · monotonic stamp `B-####` · Sarvam
> extraction · reception fail-closed to intake-only). The scan is a witness;
> `kind='pharma_purchase'` keeps the volume out of the asset approval queue (PP0).

## THE WORKFLOW (owner-dictated — the portal's state machine)

| # | state | who acts | what happens |
|---|---|---|---|
| 0 | SCANNED AT ARRIVAL | **reception / Darpan** | bill stamped + scanned via the asset intake; Sarvam extracts vendor/bill_no/date/amount |
| 1 | INGESTED | pipeline | bill-wise + supplier-wise pushed from the medical PC, staged, applied (survey-first) |
| 1a | SCAN-LINK | system | Marg bills ↔ arrival scans auto-matched, graded confidence (D315); unmatched scans AND unscanned bills both surface |
| 2 | CHECKING | **reception (alisha, shivani) + Darpan** | per-bill Correct/Wrong (+amount+reason), vendor-grouped; **📷 the scan beside the Marg amount** |
| 3 | AMIR PASS (compulsory) | **Amir** | reviews every check; corrections in Marg; bills flagged **correct / corrected** |
| 4 | REGENERATED (if needed) | pipeline | corrected exports re-pushed; verdicts + scan-links survive; deltas surface |
| 5 | FINAL APPROVAL | **Amir** | ONLINE, identity + time |
| 6 | COUNTERSIGN | **Darpan** | ONLINE |
| 7 | NEFT EXCEL | one tap | **CLEAN Sheet2 bank format**; guard enforced server-side; trail INTERNAL |
| 8 | SHAVEZ APPROVAL | **Shavez** | approves the payment excel |
| 9 | OWNER OK | **Dr Manoj** | sheet + internal trail; **physical bills attached to the bill-wise printout for archiving**; OK recorded |
| 10 | CHEQUE | **Shavez** (authorised BY the OK) | cheque made; number + date filled in the system |
| 11 | LETTER | **Dr Manoj** | CLEAN prefilled letter (date picker · amount auto · cheque no) → print, sign |
| 12 | SUBMITTED | human | bank + the `sanjeevni.bly@gmail.com` mail — NEVER automated (D325) |
| 13 | PAID → MARG RECON | **Amir** | post-payment reconciliation in Marg; marked done |
| 14 | ACCOUNTANT PACK | pipeline | the month's clean pack |

Every transition stored with who + when = **the owner's dial** (INTERNAL).

## Build stages (S199 onward)

**PP0** asset-app companion (pharma kind, auto-approve lane, recall search) · **PP1**
ingestion + schema + scan-link · **PP2** check + Amir pass · **PP3** online approvals +
fortnight recon · **PP4** outputs + dial. (Parsers proven at S198; REFUSE on total mismatch;
additive schema; D322-pattern cross-DB reads.)

## FIRST OWNER ACTION (signed with the contract): the first ITEM-WISE Marg purchase export, from 1st AUGUST

Whoever is at the medical PC (Amir on his next visit is natural): in Marg, generate the
**item-wise purchase report for 01-08-2026 → today**, export it as the other reports are
exported. The watcher captures it within ~10 minutes. **Expected: it files under `_UNKNOWN`
in MargArchive** — the router has no signature for this type yet; that is the sample Club 3
has been waiting for, NOT a fault. S199 adds its signature from those real bytes and August
becomes the first item-level month in the system.

## PHASE 2 — THE INVENTORY HORIZON (built after PP4)

**TWO INDEPENDENT ITEM-LEVEL WITNESSES:** Witness A — our own scans (Sarvam item-line
extraction, its own trial first, D172; staff verify against the physical bill at entry).
Witness B — Marg's item-wise purchase export (the pipeline gains one signature). **The
cross-check runs at ENTRY POINT** — a wrong reading on either side is flagged the day it
happens, never at month-end.

**Where it SHOWS:** the Sanjeevni page carries the purchase/stock analytics — scanned-bill
status, **expiry · reorder · surplus stock** — beside its sale cards; **Darpan gets the same
at his portal**; the owner's dial rolls it up.

**Export cadence — Amir's work rhythm, not a calendar:** every time Amir works in Marg, his
closing act is generating the purchase report(s); the watcher captures within ~10 minutes
and ingestion is event-driven. The dial's "last purchase ingest N days ago" line is the only
watchdog.

The chain: item purchases feed the Sanjeevni system → purchase ↔ sale cross-verification at
item level (`sale_line_item` already live, 15,574+ lines) → purchase order book →
surplus/expired/nearing-expiry (STOCK_CLOSING + STOCK_EXPIRY already captured) → **rotating
physical stock verification** (a nominated few items at a time, cycled) → physical stock
audit → **the entire sale-purchase chain mapped**.

**Phase-2 gates — both FAIL-SAFE:** (1) the Marg scan-intake trial (~₹3.5/bill): if it
fails, Amir enters purchases with the physical bill in front of him and the month-end sheets
feed PP1–PP4 unchanged — the trial only decides whether Amir types or checks. (2) the Sarvam
item-line trial: if line items don't extract reliably, Witness B alone delivers the item
layer — our-scan items are an accuracy bonus, not a dependency.

## Boundaries held

Nothing sends anything (D325). External outputs CLEAN. Marg never WRITTEN by our system.
finance.db out of the repo (F-31). The xlsx toolset stays the fallback. Parallel first
month; owner decides cutover. Amir: own portal login, browser on the medical PC.

*D335 · SIGNED 23-Aug-2026 · build = the S199 flagship (PP0 → PP4, gated kits). Eight
same-day revisions, every owner ruling in its own words. Next free: D336 · F-170.*
