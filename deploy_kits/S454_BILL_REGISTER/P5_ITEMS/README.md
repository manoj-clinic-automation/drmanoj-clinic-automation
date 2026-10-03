# S454_BILL_REGISTER · part 5 — P5_ITEMS

Session 283 (Sanjeevni), 03-Oct-2026 · the brief's section 11. These pages read the bills; they change no stock, no order and no bill.

## What and why

- **§11.1 The items check** (`/finance/purchase/page/items?month=YYYY-MM`, the owner only, English, phone width). For each Marg purchase bill of
  the month it works out the lines' own value: quantity × rate, less the discount, plus the tax, as `purchase_line` holds them. A bill whose
  value does not come to its amount within `purchase.total_noise_rs` (Rs 10) is listed with the difference and its lines.
  - Marg prints each line twice (item-wise and bill-item-wise). One copy is read: the bill-item-wise one when it is there, from the newest
    export in force.
  - Marg's own net figure for each line is shown beside the value. Where they differ, something reached the bill that the line's columns do
    not show (most often a discount that is not in the discount column).
  - The head line gives how many bills add up and how many do not. The Sarvam page links to it.
  - Measured before it was drawn: August 57 of 83 bills with lines add up (one bill has no lines); September 57 of 81.
- **§11.2 Learning the suppliers' item names** (`item_check.learn`, table `s454_item_name`). It learns only from a **verified** pair (S454 §5's
  rule) whose scan has as many item lines as Marg's entry. A scan line is paired with the Marg line whose quantity and rate agree, when no other
  line of that bill does. The name that supplier printed is learnt against Marg's item, once.
  - **A guard, found on 03-Oct's data:** two names that share nothing are never learnt as one, because quantity and rate can agree by chance.
    On the first run "BARBELLY Junction only," (read off an address line) was paired with CHYMORAL AP, and "CCM TAB" with DFO 4X GEL. Names
    count as akin when they are at least 0.4 alike as strings, or both carry a word with the same first three letters. Form words such as TAB
    and CAP do not count.
  - The Sarvam check (`purchase_app._s446_compare_one`) judges a scan's item name by the learnt names first.
  - After each compare, the learner runs (`sarvam_compare`). When it learns a name, that supplier's rows are compared again, so the Sarvam page's
    item figure counts by the learnt names.

## Pins (FROM → TO), `/root/finance/`

`purchase_app.py` FROM 61e6d26a (part 3's) → TO in `PINS.sh`. New: `item_check.py`.

## Files

- `make_s454p5.py`: the patcher. It makes two anchored edits, and its one block goes above the `__main__` guard.
- `item_check.py`
- `walk_s454p5.py`: R (today's figures), I (the items page), L (the learning), S (the staff-eye walk). NEW is the box plus part 5; OLD is the box
  as it is.
- `plan_old_s454p5.py` + `walks_old_s454p5.py`: the earlier walks.
- `data_s454p5.py`: the table, the learner once, and September's item figure before and after.
- `install_S454_P5.sh`
- `PINS.sh`

The duty map does not change. The items check is a page the owner opens; it raises no line and no duty.
