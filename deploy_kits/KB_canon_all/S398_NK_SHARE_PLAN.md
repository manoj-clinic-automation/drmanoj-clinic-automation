# S398 — The NK share of Variety's stationery into NK Pathology's accounts: the plan (D845 item 4)

*The Scan App chat, session 398, 07-Nov-2026. A plan only: nothing is built until you say so. Once the parent and the NK Pathology
chat agree their parts, each part gets a PLANNED line on the board first.*

## 1 · What stands today (read in the code, 07-Nov bundle)
- **The Stationery page** sorts every Variety challan line by line, **Clinic** or **NK**.
  - An NK line goes to the **NK ledger** on that page and never into the clinic's stock (S674, D797).
  - The NK ledger holds one line today: **B-0235, NK AYUSHMAN PAD, 2000 pieces** (challan 2727 of 26-Oct).
- **The monthly statement** lists each challan's lines as "bill to: Clinic" or "bill to: NK Pathology". It ends: *"Please bill the
  clinic and NK Pathology separately, as marked, against this statement."*
  - Their bill or estimate is then scanned, joined to the statement, the rates are typed in, and it is marked paid **once**.
  - The statement holds **one** joined bill and **one** payment. It has no way to hold a second, NK bill.
- **NK Pathology's accounts:** the accountants' pack reads NK's purchases from the scan app's **NK Pathology lane**. That is pack
  row **8.1, "Dr Bhawna's lab-purchase bills"** (`/root/finance/packs.py`, the parent's).
  - A paper on that lane goes into NK's monthly bundle by itself.
  - Nothing on the Stationery page reaches that lane today. **The NK share is therefore in no NK account.**

## 2 · The flow proposed
1. **October's statement** is made as now, and it names the NK lines.
2. **Variety bills NK on its own bill** (what the statement already asks for). Reception scans it on the NK Pathology lane, as any
   lab bill.
   - On the Stationery page it is joined to the statement **as NK's bill**, with the NK lines' rates typed on.
   - It is marked paid **by NK**.
   - Because it sits on the NK lane, it goes into pack 8.1 for its month **without any further step**.
3. **If Variety gives one bill for both**, it is joined as today. The page then works out **NK's share**: the NK lines × their rates,
   challan by challan. It makes a one-page **NK share note** (PDF): the statement month, each NK line, the total, and "paid by the
   clinic, to be repaid by NK" or "paid by NK", as you set.
   - That note is filed on the NK lane, so pack 8.1 carries it for that month.
   - The clinic's own figure for the bill is the bill **less** NK's share.
4. **A line is counted once:** every NK line sits on one statement and is paid once, by one side. The NK share is never also counted
   as clinic stationery.

## 3 · Who builds what (one estate, each its own files)
| part | project | file(s) | what |
|---|---|---|---|
| A | **the Scan App** (this chat) | `/root/assetapp/stationery.py` | the statement holds **two** joined bills (Clinic, NK), each paid on its own; the NK share worked out for a combined bill; the NK share note (PDF) filed on the NK lane; the NK ledger shows paid / unpaid |
| B | **the parent** | `/root/finance/packs.py` | pack 8.1 already takes any NK-lane paper, so probably **no change**; to confirm: an NK share note is listed as such in its index, and its amount is taken as NK's spend for the month |
| C | **NK Pathology chat** | NK's own records (`/root/labdata/`) | whether NK keeps its own consumables register or stock book for stationery; if so, it reads the NK ledger read-only (a lab stock book was ruled out of the scan app at S674) |

A goes first. B and C are checks rather than builds, unless the parent finds that the index needs a word changed.

## 4 · Your two answers — given 07:40 IST 07-Nov: **two bills, NK pays its own**
1. **Will Variety give two bills (Clinic and NK) or one combined bill?** Recommended: **two bills**. Their own statement already
   asks for it, and NK's bill then lands in NK's pack with no arithmetic.
2. **Who pays NK's share, when it comes on one bill?** NK pays Variety its part directly, or the clinic pays all and NK repays the
   clinic. Recommended: **NK pays its own bill**, which is the same answer as question 1.

**Settled (your word, 07:40 IST): two bills, NK pays its own.** Part A is the small form: the statement takes a second bill marked
NK, each bill is paid on its own, and the NK ledger shows paid / unpaid. No share note is needed. Parts B and C are checks only.

**Estimates (your word, 07:47 IST):** if Variety is paid on an estimate rather than a bill, it is joined and paid on the
Stationery page the same way, and it stays OUT of the accountants' packs. This keeps your rule that only bills go (D730 item 5).
No change to the packs.

## 5 · What is NOT in this plan
No rule for the clinic's own stationery changes. No NK stock book is added in the scan app (S674's ruling). Nothing is moved by the
system; each bill is joined by a person, as today.
