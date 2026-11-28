# S540 — Stock check page v10: your write-offs first (his "OK" 11:52 IST 28-Nov-2026 on mock-up v10)

**Mock-up (approved):** https://claude.ai/artifact/W3U9BfeW9K5QKpsgZ6YoqF, version 1795846874-dc13.
**Why (his words, 11:43 IST):** Darpan's counts show on the page "but the flow is not easy to understand". He booked losses on a few medicines, and they are with Amir for stock vouchers, but he "can't find these anywhere".
**Build:** a fresh Sanjeevni chat, by Opus. The FROM files are S971's placed bytes and S973's (F-472). No staff screen changes.

## What the page becomes (owner only, PC-first)

### 1. Top chips
- N your write-offs — with Amir, not keyed yet
- N counted today
- N other corrections on their way
- N old counts to count first

### 2. Band 1 — "Your write-offs — waiting for Amir"
- One row per `stock_desk_action` write-off that has not settled. The rows are the same as the loss register's open lines: `voucher_inquiry.losses()` lines with marg ≠ keyed, not withdrawn.
- Columns: item · written off (strips:tabs) · booked dd-mm · on Amir's card ("N days — not done", or "Kar diya dd-mm — next report decides") · a 3-step track (Booked → Amir keys → In Marg) · cost.
- Each row folds open to its path: the count, your tap, the card name with batch, the closing rule.
- Footer: the month's cost and MRP totals, and the full loss register link (`/finance/stockcheck/losses`).
- These rows leave box 2's list (no row is shown twice).

### 3. Band 2 — "Today's counts — <counter>, <day>"
- Every `stock_point` row of today, one plain verdict each.
- Within the allowance: amber, with the existing group "Write off all N" button.
- A surplus: "More than Marg — never a loss". When Marg's newest purchase report is older than the count day, add "likely a delivery not yet in Marg (Marg's purchases reach dd-mm)".
- A loss: "a loss since the last count", with its Write off / Pursue, or "written off by you — above".
- A fold underneath holds this week's earlier counts with their present state.

### 4. Band 3 — "Waiting on others"
All folded, none needing his tap today:
- other corrections on their way (box 2 minus band 1);
- old corrections re-judged (box 3);
- count first (box 6, with "All N on Darpan's next list");
- vouchers nobody asked for (box 4, with the rule-date line);
- settled (box 5);
- the rules (dkset).

## The two CCM faults (F at the close)

1. **Box 3 marks a surplus red as "today's gap — waits for your call"** (CCM, 28-11: shelf 1:0 vs Marg 0:0, verdict `fresh_gap`). Meanwhile the count list says "noted, never a loss".
   Fix: a fresh gap that is a SURPLUS is told "more than Marg — noted, never a loss". It shows no red tag and does not wait for his call.
   Where to look: `voucher_judge.whole_item` / `rejudge` and the stock_check box 3 tags.
2. **The item ledger (`/finance/sanjeevni/ledger/api/fold?k=CCM`) shows the count as "40 bottles counted, 40 bottles more"**, while the stock record reads it as 1:0 of a pack of 40.
   Fix: the ledger states counts in the record's own unit (strips:tabs, or one bottle). Read `item_ledger.py`'s count lines (S967, F-1707) against `stock_watch.qw`.

## Facts at the approval (live read 11:45 IST, counts and item names only)
- **Darpan's counts, 28-11:**
  - ONKET DT −0:4 (allowance)
  - CCM +1:0 (surplus)
  - DFO MR −1:2 (loss, written off by him the same day; Amir's card STOCK ISSUE · 28-11)
  - C2CALZ −0:2 (allowance)
  - None on 27-11.
- **The loss register, November:** 7 lines, cost ₹2,160.84, MRP ₹3,011.45. All 7 are on Amir's card and none is tapped "Kar diya":
  - NORTIMER TAB, ZUPRINOR 5, MEG QCS, CROCAL, TRAMATEE P TAB 15T and PANTAVIN 40 on the card "STOCK ISSUE · 27-11";
  - DFO MR on "STOCK ISSUE · 28-11".
- **Marg's reports:** closing stock to 27-11; purchases to 25-11.

## Proof pattern
S969 / S971's walks. The new page's bands are checked on the same made-up fixture, plus walk_s973 (the claim rows stay in band 3's "on their way" fold). The live shape is a copy of the 28-Nov database. Then the cold review, the second look and the re-look.
