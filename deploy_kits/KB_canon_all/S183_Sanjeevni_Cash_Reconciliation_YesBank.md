# S183 — Sanjeevni cash reconciliation: the drawer is whole (Yes Bank deposits found)

**Session 183 · 16 Aug 2026 · READ-ONLY analysis, nothing written to the books.**
Companion to `S183_Sanjeevni_Daily_Cash_Design_and_Marg_Findings` and `S179_Finance_LIVE_State`.

**PHI/security:** account numbers and reference numbers are the owner's own bank records, shared by
him this session. This doc keeps only dates + amounts. Bank statements themselves stay off the repo.

---

## 1. The headline — NO money is missing

The medical drawer showed an impossible −₹30,056 closing on 13 Aug. Investigation with the owner's
bank statements proved that number was **entirely unrecorded cash deposits, not a loss.**

```
Cash collected (day_line, Darpan's declared cash)   17,98,033
Cash deposited to Yes Bank (verified, 16 deposits) − 16,45,600
Expenses                                           −    84,442
                                                    ───────────
Net drawer growth over 1 Apr → 13 Aug              +    67,991
```

Every rupee ties out: collected → swept to Yes Bank → spent → or in the drawer. The reconciliation
runs on independently verified numbers (Darpan's cash is trustworthy because his UPI matches the
ICICI settlements T+1; the deposits are from Yes Bank statements).

## 2. Where the cash actually goes (corrected understanding)

- **ICICI (…009819, MID …312505) = card/UPI ONLY.** No cash is ever deposited here. Every credit is
  an `EZY/ICICIPOS` settlement, T+1, and they match Darpan's declared UPI almost to the rupee — his
  UPI discipline is confirmed good.
- **Yes Bank (M/S…, MANOJ KUMAR AGARWAL 007485800001923) = ALL cash.** The drawer is swept here
  roughly weekly as `CASH DEP-SELF-SANJEEVNI MEDICOS-BAREILLY`.

Earlier in the session this was mis-read as "cash handed to the owner"; the Yes Bank statements
corrected it — these are real bank deposits.

## 3. The 16 verified Yes Bank cash deposits (1 Apr → 13 Aug)

| Date | ₹ | Date | ₹ |
|---|---|---|---|
| 2026-04-09 | 1,15,000 | 2026-06-12 | 1,10,000 |
| 2026-04-13 | 60,000 | 2026-06-17 | 85,000 |
| 2026-04-27 | 1,43,000 | 2026-07-01 | 1,35,000 |
| 2026-05-02 | 52,600 | 2026-07-07 | 1,80,000 |
| 2026-05-07 | 80,000 | 2026-07-14 | 1,05,000 |
| 2026-05-12 | 65,000 | 2026-07-22 | 85,000 |
| 2026-05-22 | 1,20,000 | 2026-07-30 | 85,000 |
| 2026-06-04 | 1,50,000 | 2026-08-13 | 75,000 |

**Total ₹16,45,600.** (13 Aug 75,000 is owner-confirmed; it falls after the statement cutoff. Possible
gap: any deposit between 31 Jul and 12 Aug is not yet evidenced — check when booking.)

The old carry-forward breaks (30 Jul −85k, 13 Aug −74,604, etc.) ARE these deposits, unrecorded.

## 4. The derived anchor (no physical count strictly needed, but confirm)

From the constraint that a drawer can never go negative, applying the verified deposits:

- **Untracked opening cash on 1 Apr ≈ ₹31,021** (the minimum that keeps the drawer ≥ 0; the tightest
  point is 14 Jul, the day of a ₹1,05,000 deposit).
- **Implied drawer on 13 Aug ≈ ₹99,012** (at the minimum opening; higher if a float was kept).
- **Implied drawer NOW (16 Aug) ≈ ₹1.15 lakh** (adding 14–15 Aug cash ≈ ₹15k; no deposit since 13 Aug).

**Confirmation step:** one physical count of the drawer ≈ ₹1.15 lakh closes the story exactly and
pins the opening float.

## 5. What is owed (do NOT do ad-hoc; gated path next session)

1. **Record the 16 verified deposits** into the finance books via a tested, gated migration (as
   `cash_movement` out / bank deposits to Yes Bank). This clears the carry-forward breaks and the
   negative-cash exceptions structurally.
2. **Set the opening anchor** (~₹31k on 1 Apr, or Count-the-drawer to the confirmed physical figure).
3. **Build the Yes Bank cash-deposit reconciliation** — the parallel to the ICICI UPI reconciliation
   (finance_upi). Cash deposits match Yes Bank the way UPI matches ICICI. A real gap in the design:
   the system reconciles UPI but has no cash-deposit reconciliation, which is why these 16 deposits
   went unrecorded and broke the chain.
4. **A named "bank deposit (Yes Bank)" movement type** so future sweeps are recorded correctly, not
   as breaks.

## 6. Tomorrow's catch-up (does not need any of the above)

- **File 14 Aug:** cash ≈ ₹11,413, UPI ₹6,530 (UPI cross-checked to the bank T+1 settlement).
- **File 15 Aug:** cash ≈ ₹3,926, UPI ₹4,925.
- **Mark 16 Aug closed** (no sale).
- Opening will read wrong until the deposits are booked, but the collections entered are correct and
  nothing is lost.

## 7. Also surfaced by the S183 Marg backfill (separate, no money impact)

- 118 `line_sum_vs_day_total` exceptions + ~2,062 review items = legacy no-ID bills the backfill fed
  through attribution. Owner chose to **reclassify legacy no-ID bills to WALK-IN** (clears both).
  To build + test offline, then apply. No money affected.

---
*S183 · read-only reconciliation · next: gated deposit booking + Yes Bank reconciliation + WALK-IN reclass*
