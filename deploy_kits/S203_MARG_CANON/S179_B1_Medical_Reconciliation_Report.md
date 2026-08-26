# B1 — MEDICAL (SANJEEVNI) RECONCILIATION REPORT

*Session 179 · produced by `finance_import_medical.py` from the legacy Google Sheet.*
*Offline run. Nothing installed, nothing served, no live system touched, no rupee corrected.*

## 1 · What was imported

| | |
|---|---:|
| Days imported | **121** |
| Period | 2026-04-01 → 2026-08-13 |
| Sale total | ₹26,81,566.00 |
| of which UPI | ₹8,83,533.00 (32.9%) |
| of which cash | ₹17,98,033.00 |
| Expenses | ₹84,442.00 |
| Deposited to bank | ₹16,59,114.00 |

## 2 · The carry-forward breaks — itemised

Because you confirmed `Old Balance` was **meant to be yesterday's closing cash**, every
disagreement below is an unexplained movement. Each one is now a real row in the database
with status `open`, waiting for your reason. Nothing was corrected.

| | |
|---|---:|
| Breaks found | **36** of 121 days (29.8%) |
| Upward corrections | +₹4,46,090.00 |
| Downward corrections | −₹5,30,623.00 |
| **Net unexplained** | **₹-84,533.00** |

### The 15 largest, worth your attention first

| Date | Day | Adjustment | Running closing after |
|---|---|---:|---:|
| 2026-06-13 | Sat | +₹1,04,403.00 | ₹28,856.00 |
| 2026-05-30 | Sat | −₹90,538.00 | ₹24,439.00 |
| 2026-04-08 | Wed | +₹84,943.00 | ₹7,929.00 |
| 2026-08-13 | Thu | −₹74,604.00 | ₹-30,056.00 |
| 2026-05-16 | Sat | −₹55,000.00 | ₹16,802.00 |
| 2026-05-22 | Fri | +₹55,000.00 | ₹16,428.00 |
| 2026-06-18 | Thu | +₹50,000.00 | ₹25,743.00 |
| 2026-07-31 | Fri | +₹45,000.00 | ₹38,176.00 |
| 2026-07-23 | Thu | +₹42,000.00 | ₹31,281.00 |
| 2026-08-01 | Sat | −₹38,176.00 | ₹15,898.00 |
| 2026-06-07 | Sun | −₹38,000.00 | ₹6,109.00 |
| 2026-06-10 | Wed | −₹34,000.00 | ₹29,622.00 |
| 2026-06-04 | Thu | −₹30,950.00 | ₹10,221.00 |
| 2026-06-25 | Thu | −₹30,592.00 | ₹0.00 |
| 2026-04-02 | Thu | −₹24,755.00 | ₹9,668.00 |

*(All 36 are in `medical_adjustments.csv`.)*

## 3 · Open exceptions — these will keep shouting until closed

| Kind | Count | Total absolute difference |
|---|---:|---:|
| `carry_forward_break` | 36 | ₹9,76,713.00 |
| `missing_day` | 14 | ₹0.00 |
| `negative_cash` | 7 | ₹2,57,894.00 |

## 4 · Data-quality flags raised during import

| Code | Severity | Count |
|---|---|---:|
| `EXPENSE_UNKNOWN` | medium | 6 |
| `RESUBMISSION` | medium | 1 |

## 5 · Month by month

| Month | Days | Sale | Cash | UPI | Expenses | Deposited | Adjustments |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2026-04 | 26 | ₹5,75,284.00 | ₹4,09,963.00 | ₹1,65,321.00 | ₹38,520.00 | ₹3,84,752.00 | ₹13,349.00 |
| 2026-05 | 27 | ₹5,58,115.00 | ₹3,70,236.00 | ₹1,87,879.00 | ₹6,518.00 | ₹2,65,000.00 | ₹-98,758.00 |
| 2026-06 | 27 | ₹6,81,638.00 | ₹4,32,764.00 | ₹2,48,874.00 | ₹2,803.00 | ₹4,50,538.00 | ₹27,622.00 |
| 2026-07 | 28 | ₹6,07,389.00 | ₹4,30,597.00 | ₹1,76,792.00 | ₹33,800.00 | ₹4,52,000.00 | ₹86,334.00 |
| 2026-08 | 13 | ₹2,59,140.00 | ₹1,54,473.00 | ₹1,04,667.00 | ₹2,801.00 | ₹1,06,824.00 | ₹-1,13,080.00 |

## 6 · Proof the import is faithful

| Check | Result |
|---|---|
| Ledger's final closing cash | ₹-30,056.00 |
| Sheet's own last `Total Cash` | ₹-30,056.00 |
| **Do they agree?** | **YES — the import reproduces the sheet exactly** |

A second, independent check — the arithmetic the pharmacy *should* satisfy if nothing had
ever gone missing:

| | |
|---|---:|
| Cash sales − expenses − deposits | ₹54,477.00 |
| Actual closing cash per the sheet | ₹-30,056.00 |
| **Gap needing explanation** | **₹84,533.00** |

## 7 · What happens to these numbers next

Nothing automatically. Each break is an `open` row waiting for a reason. As you work down the
list, most will turn out to be recognisable — a deposit entered a day late, cash you or
Dr Bhawna took from the drawer, a correction typed over the top of an earlier figure. Those
get an explanation and close. What survives that pass is the real, irreducible number, and it
will be a great deal smaller than ₹84,533.00.

---

*B1 output. Files alongside this report: `finance.db`, `medical_daily_ledger.csv`,
`medical_adjustments.csv`, `medical_exceptions.csv`.*
