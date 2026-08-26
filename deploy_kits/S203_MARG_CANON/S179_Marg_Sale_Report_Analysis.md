# MARG SALE REPORT — ANALYSIS

**Session 179 · file: `SANJEEVNI AUG SALE REPORT UPTO 13 AUGUST 2026.XLS` (Marg ERP 9+, 345 bills,
1–14 Aug 2026) · plus one Marg backup archive**
*No phone number or patient name appears in this document. Figures and shapes only.*

---

## 1 · The headline: your pharmacy's typing is perfect

Marg's day total against what was typed into the Google Sheet, for all thirteen days:

| Date | Marg net | Sheet total | Difference |
|---|---:|---:|---:|
| 01 Aug | ₹28,119 | ₹28,119 | **0** |
| 02 Aug | ₹3,310 | ₹3,310 | **0** |
| 03 Aug | ₹21,668 | ₹21,668 | **0** |
| 04 Aug | ₹15,955 | ₹15,955 | **0** |
| 05 Aug | ₹33,873 | ₹33,873 | **0** |
| 06 Aug | ₹18,088 | ₹18,088 | **0** |
| 07 Aug | ₹15,825 | ₹15,825 | **0** |
| 08 Aug | ₹16,972 | ₹16,972 | **0** |
| 09 Aug | ₹1,235 | ₹1,235 | **0** |
| 10 Aug | ₹32,273 | ₹32,273 | **0** |
| 11 Aug | ₹20,412 | ₹20,412 | **0** |
| 12 Aug | ₹22,505 | ₹22,505 | **0** |
| 13 Aug | ₹28,905 | ₹28,905 | **0** |

**Thirteen days, thirteen exact matches.** Whoever types the daily figure reads it off Marg and gets
it right, every time. That is worth knowing before anyone goes looking for problems in the revenue
numbers — there aren't any. The ₹84,533 of historical drift is **not** a revenue-recording problem.

## 2 · The weak point is the cash/UPI split — and it has a pattern

| Date | Marg CASH | Marg UPI | Sheet UPI | |
|---|---:|---:|---:|---|
| 11 Aug | ₹20,412 | **₹0** | ₹8,728 | 25 bills, **every one marked CASH** |
| 13 Aug | ₹28,905 | **₹0** | ₹10,565 | 31 bills, **every one marked CASH** |
| 14 Aug | ₹17,943 | **₹0** | (not filed) | 23 bills, **every one marked CASH** |

Every other day runs 25–40 % UPI. Then on three days Marg records **not a single UPI bill**. Twenty-five,
thirty-one and twenty-three bills in a row, all cash, at a counter that normally takes a third of its
money digitally.

The likeliest reading is that the payment mode simply stopped being set in Marg on those days — the
sale was rung up, the mode defaulted to cash. The sheet's ₹8,728 and ₹10,565 on the 11th and 13th
came from somewhere, presumably the actual UPI figure.

**The ICICI merchant statement settles it in one look.** If ICICI shows ₹8,728 collected on 11 Aug,
Marg's mode field is wrong and the sheet is right. This is precisely what the daily UPI reconciler
(B5) would catch every single morning, unprompted.

**Do not treat this as a discrepancy to explain away.** Either the mode field or the sheet's UPI
figure is unreliable on those days, and knowing which one changes how much you trust each source.

## 3 · Marg's `CASH` column is the truth, not the mode field

12 bills marked UPI also carry a cash portion — split payments, ₹5,106 in total. So "mode = UPI"
does not mean "no cash changed hands".

The arithmetic works out exactly:

```
net total                277,083
CASH column total        193,412
difference                83,671   <- non-cash
UPI-mode bills, net       88,777
   less cash inside them   5,106
                          83,671   <- identical
```

**So the ingestion rule is: cash = the CASH column; UPI = net − CASH.** Never derive cash from the
mode field. Split payments would be silently mis-stated if we did.

## 4 · The description field carries a patient ID — and it is stable

254 of 345 bills begin with a 10-digit phone, followed by the name, followed by a 3–5 digit number:

```
<phone> RAJPAL SINGH 6790
<phone> JYOTI PANDEY 1810
```

**190 distinct phone numbers appear, and not one of them is ever paired with a different trailing
number.** That consistency is what makes it an identifier rather than a coincidence — it behaves
exactly like the clinic ID the patient spine needs.

**I need you to confirm what it is.** If it is the clinic's patient ID, the pharmacy line already
carries the join key and the whole patient-revenue spine works from this file with no extra work at
the counter. If it is something Marg generates internally, it is useless for joining to clinic
records and the counter would need to start writing the real ID.

**Three practical wrinkles:**

- **The field truncates at 33 characters.** `PRADEEP KUMAR GUPTA 77` is cut mid-ID — 6 bills sit at
  exactly 33 characters and have probably lost digits. Widening that field in Marg, if it can be
  widened, would fix it at source.
- **91 bills have no phone at all.** Some are `PROSIJER <name>` (13 bills — procedure medicines),
  some are codes like `BPJ`, `CPU`, `WR`, some are bare names, one has a 9-digit phone (a typo), and
  one runs the ID straight onto the name with no space (`ASHOK AGARWAL7657`). These land on
  `WALK-IN` rather than being guessed at.
- **18 credit notes** (`CN…`) carry negative amounts. They reduce revenue correctly and are included.

## 5 · 14 August is sitting in this file

**₹17,943 across 23 bills.** That is the day the system has been shouting about since yesterday
morning. It can be filed straight from here.

## 6 · The Marg backup is a dead end — and that is fine

The `.jmbkh` archive is a zip whose every member is **password-protected**. All 28 `.mbk` files
refuse to extract. It is Marg's own encrypted backup, not an export, and I did not attempt to work
around that.

It is also unnecessary. This `.XLS` report contains more usable structure than a raw table dump
would, already aggregated the way the business thinks. **Keep exporting this report; the backup is
for restoring Marg, not for feeding us.**

## 7 · What this changes about the build

**Marg beats Sarvam OCR decisively for the pharmacy.** Exact figures, per-bill detail, payment mode,
patient identifier, and day totals that already reconcile — against OCR's best-effort reading of a
printed page. I would make `marg_export` primary and keep `sarvam_ocr` for the manual copy and
orthotics pages, where there is no software source.

**But this file needs its own adapter, not the generic CSV one.** Two reasons:

1. **The date is not a column.** It lives in group-header rows between the bills, so the parser must
   carry the current day forward. My `csv_generic` adapter maps columns and would produce 345
   dateless rows.
2. **It is a real `.xls`** (BIFF, not CSV), and the trailer rows — `DAY TOTAL`, `GRAND TOTAL`, the
   Marg advertisement on the last line — must be recognised and skipped rather than parsed as bills.

The good news is that this shape is stable and now fully understood, and the day totals give a
built-in self-check: parse the bills, sum them, and require the sum to equal Marg's own `DAY TOTAL`
row before accepting a single line. A day that does not reconcile against the file's own total gets
rejected, not imported.

---

## What I need from you

1. **Is the trailing number the clinic's patient ID?** This decides whether the patient spine works
   from day one.
2. **Check the ICICI merchant statement for 11 and 13 August.** It tells us whether Marg's mode field
   or the sheet's UPI figure is the unreliable one — and that judgement affects every day going
   forward.
3. **`PROSIJER` bills show cash collected.** You described procedure medicines as billed in full with
   no cash across the counter. These have cash against them, so either the counter does collect for
   some, or the mode is defaulting again. Worth a look at one.

*S179 · Marg sale-report analysis. No patient identifiers reproduced.*
