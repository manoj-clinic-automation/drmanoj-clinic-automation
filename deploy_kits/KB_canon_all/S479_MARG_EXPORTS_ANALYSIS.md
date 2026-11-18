# S479 — THE MARG EXPORTS, ANALYSED BEFORE THE D1000 BUILD (18-Nov-2026, the Sanjeevni chat)

**The owner's word at the open (07:49 IST):** *"deeply analyze the need for sequential exports of reports from Marg and optimize those rather than keep on adding the exports without compromising the accuracy of the data in any way."* This paper is that analysis. Read from the 18-Nov code bundle (every Sanjeevni pin matching) and the 18-Nov database copy (in the device VM, removed at the close); nothing live was touched.

## 1 · What is exported from Marg today, by whom, and what each export feeds

| export | who / when | feeds | files in the last 30 days |
|---|---|---|---|
| SALE bill-wise (Detail, last two days) | Darpan/Shavez, every morning | the day's cash check, the sale lines, the spine | 36 |
| STOCK closing (whole store) | the same morning | the expected-stock figure, the Marg watch, ordering | 42 |
| PURCHASE **bill-wise** (1st → today) | Amir, every visit (step 3) | `purchase_bill`: supplier · bill no · date · cash · credit | 12 + 1 full-month |
| PURCHASE **item-wise** (1st → today) | Amir, the same visit | `purchase_line`: the lines, with supplier and bill no (no date, no bill total) | 12 + 2 full-month |
| PURCHASE **supplier-wise** (whole month) | Amir, once after month end | `purchase_bill` again: supplier · bill no · date · cash · credit — **the same five figures per bill as the bill-wise** | 1 |
| BATCH STOCK (whole store) | Amir, **every visit** (step 4's third report, D815) | the expiry watch; the judge of his batch-fix vouchers | 7 |
| STOCK valuation · expiry · salt list · category list · item master | the 1st / every 8 or 35 days | the month's valuation row; the salt and section work | 4 · 1 · 2 · 2 · 2 |
| ORDER pending | on need | the order book | 6 |

October in full: **47 purchase export files over 13 visit days** (23 bill-wise, 22 item-wise, 1 supplier-wise, 1 bill/item-wise) and 4 Batch Stocks. November so far: 14 purchase files + 3 Batch Stocks. A month's purchase data is ~80 bills / ~190 lines; one full-month pair is 11 KB + 45 KB.

## 2 · Findings — where the sequence is longer than the data needs

**F1 · The supplier-wise statement is a second copy of the bill-wise.** The reader (`marg_purchase_rows.py`) takes exactly the same five fields from both — supplier, bill date, bill no, cash, credit; the server stores both into the same `purchase_bill` row (`bw_amount_p` / `sw_amount_p`). The only differences are the grouping on paper and the supplier's name printed without its city. They can never disagree on content; **they disagree only when Marg was edited between the two exports** — which is exactly what happened in October (three bills Amir corrected between the 06-Nov supplier-wise and the 11-Nov bill-wise, ₹549). The "disagreement" the system then flags is not a data problem; it is the older copy being older. Every rule built on that disagreement (rev-4's cross-check, S855's re-ask, D1000's "four checks") is managing a redundancy.

**F2 · The month-end is a second export of what the visit pair already exports.** After month end the month needs a bill statement and item lines covering the 1st to the last day. Today that costs three exports (supplier-wise + full-month bill-wise + full-month item-wise) on top of the visit pairs, and a fourth (the supplier-wise again) after any correction — October took 4 month-end files and still asks for a 5th. The visit pair, taken once more with FROM = the 1st and TO = the last day of the finished month, is the whole month-end.

**F3 · The Batch Stock is asked on every visit whether or not anything can be proved by it.** D815 made it step 4's third report so the system can confirm Amir's batch-fix vouchers line by line — right while vouchers are open (11 open today). On a visit with no open voucher and this month's Batch Stock already in, the export proves nothing. (Kept as it is for now: with 11 open rows it is still doing its job; a conditional ask is a later, separate kit.)

**F4 · Double exports.** Until 29-Oct nearly every visit produced two files per report a minute apart (the card showed "nahi aayi" while the 30-minute manojz pull was still due, and Amir exported again). S678 (the door's own receipt: *"server par aa gayi — dobara nahi nikaalni"*) fixed this; since then only 11-Nov shows a redo, and that one was a genuine mis-export (a 5-row item-wise). Nothing to build.

**F5 · The daily sale and stock pair is the base and is not growing.** 36 + 42 files in 30 days ≈ one pair per counter day; the Marg watch's "sale report again" ask has never fired (0 rows in `marg_watch_report`). Left alone.

## 3 · What D1000 as agreed would have done, and why it is the wrong shape

D1000 (17-Nov, 21:27–22:46): *keep* the supplier-wise as the month's figure, ask it once after month end, and when it is older than a correction let the newer bill-wise + item lines settle the month if four checks pass. That tolerates the redundancy (F1) with more rules rather than removing it; the supplier-wise is still asked every month; the "older than a correction" test still needs two copies to compare; and a Wrong mark whose paper figure the newest statement already shows (all three of October's) stays open until a human taps.

## 4 · The optimised sequence — the proposal (D1000 reshaped)

1. **One family of bill statements.** The supplier-wise and the bill-wise are the same report to the server: the NEWEST statement of either kind (by Marg's own stamp) is the month's figure; an incoming statement retires every older one of either kind whose period it contains (today's containment rule, applied across the two types). No "bill-wise vs supplier-wise" disagreement can exist. The supplier-wise is **never asked**; if someone exports it, it is accepted exactly as a bill-wise.
2. **Month-end = the visit pair once more, over the finished month.** On Amir's first visit after a month ends (and on later visits while that month is not locked and its full pair is not in), step 3 lists **four** reports: *pehle pichhle mahine ki do (01 → last day), phir is mahine ki do (01 → aaj)*. Step 4 checks both pairs. No separate month-end report, no supplier-wise.
3. **A fresh full-month pair is asked again only for a reason the system knows** — a correction to that month made after the newest full pair: Amir's *Marg sudhar* tap / "meri entry galat thi" on a bill of that month, a bill the doctor marked Wrong and Amir then corrected, a purchase return settled, a scan answered *"not in Marg — enter it"*. The ask names the reason. No known correction → nothing asked; the month settles on the newest full pair when the checks pass (lines agree with bills; every paper matches; the dealers' summaries match; the statement's own printed grand total equals the sheet).
4. **A Wrong mark resolves itself when the newest statement shows the paper's figure** ("Marg now matches the paper — export of dd-Mon"), recorded in the audit, never on a FINAL month.
5. The cross-check keeps every test it has: every bill on the sheet is carried by the statement (true by construction), and **the statement's own printed grand total vs the sheet** — the bill-wise prints a TOTAL row too, read into `grand_amount_p` today.

**Accuracy — why nothing is lost.** The five figures per bill are the same in both statements, so dropping one copy drops no information. The one thing the second copy ever detected — Marg edited between two exports — is detected better by the next export of the same kind (the containment rule retires the older). The item lines, the papers, the dealers' summaries and Marg's own printed total remain the four independent checks; none of them involved the supplier-wise.

**October, proven on the 18-Nov copy** (the family rule applied to the 06-Nov supplier-wise against the 11-Nov bill-wise, `_month_summary` re-run): the month's figure becomes **₹3,72,609** (the bill-wise — his "right" figure of 17-Nov), 82 bills, the disagreement **₹0**, the bill-wise's own printed grand total **₹3,72,609 — equal to the paise**; the three Wrong marks (Kedar A000211, Yogendra 19612, Shivaaz 3854) each carry `wrong_amount_p == bw_amount_p` — the newest statement already shows the paper's figure, so rule 4 resolves all three. What then still holds October: **1 purchase return pending (the dealer's paper) and 19 dealer summaries awaited** — real work, not exports. **Zero exports asked of Amir for October.**

**Amir's month, before and after (October's shape, 13 visits):** 47 + 4 files today; under the proposal **26 visit files + 2 month-end files + Batch Stocks only while vouchers are open**, and never a supplier-wise.

## 5 · What changes, by file (this project's only)

- `purchase_app.py` — the push's supersession across the {BILLWISE, SUPPLIERWISE} family; `_S604_REPORTS` = *bill statement (either)* + *item lines*; `_verify_statement` reads the newest statement of either kind; a one-off at install applies the family rule to non-FINAL months (August and September FINAL — untouched).
- `month_asks.py` — the export asks of §4.2–4.4 (the full pair, the known-correction trigger, the self-resolving Wrong); the "disagree" bucket retired.
- `amir_day.py` — step 3's four-report card and step 4's check of the finished month's pair; the words of §4.2.
- The Book §5.2 / §15: rev-4's "supplier-wise is FINAL" replaced by "the newest bill statement is the month's figure".
- Later, separate: the Batch Stock asked only while a voucher is open or the month's first is not in (F3).

**Undo:** one `undo_s8xx.sh` putting the three files back; the one-off's supersessions reversed from its own log.

*S479 · 18-Nov-2026 · written before any build; the owner decides §4 on what Amir will see.*

---

**Postscript (10:4x IST).** His "go" 08:21 (D1002). Built as **S864_ONE_STATEMENT**, live 09:29 IST 18-Nov — §4 as written, with the cold review's additions (the one-off carries the S795 part guard; a byte-identical re-export of a live statement is re-stamped; a whole-month statement that does not carry the sheet's bills is itself a named reason; `export_watch.py` a fourth file). The one-off's undo is the audit (`s864_superseded`, `s864_part_retired`, `verdict_resolved`), not a reversal script. October read live at 09:3x: clear and lockable, nothing asked of Amir.
