# S956_SAME_DAY_DELIVERY · Sanjeevni session 519 · 25-Nov-2026 — after S952 + S954

**Why.** His word 18:08: *"meg qcs and jakmac differ a lot still on stk chk and item pages."* JAKMAC 5: Darpan counted 28:4 at 10:27 on 23-11 — exactly Marg's figure at the start of that day. Gunina's bill 100075 (20:0), dated 23-11, came in after him. The shelf figure (S928) took every purchase dated the count's own day as already inside the count, so those 20 strips never reached it: −20:0 on the Stock check page and the item page, false.

**The rule now (`stock_figure.shelf`, v1.7).** For a spot / Darpan count (a Count now too), the purchases dated its own day that reached the shelf AFTER it are added: a bill whose delivery line (a tap or its order's scan; the bill from the line's answer or the one arrivals rule) arrived after the count — added; at or before — never; no arrival time known — added only for a count saved before `count.same_day_until` (12:00 to start; deliveries come in the afternoon). An evening count (the day's end) and the full count are unchanged. Cold review: 2 MUST (a Count now in the evening; a delivery whose bill came by the arrivals rule read as unknown) + 1 SHOULD (an afternoon count) built in; noted for later: `_s936_match`'s base-day rule (stock_watch), split sizes. On 25-Nov's data only JAKMAC 5 moves (−20:0 → 0).

**MEG QCS** is not this: its last count is 14-10, 42 days and 344 strips ago — its −19:1 is the page's own "estimate; count again". It needs a fresh count.

**Files.** `/root/finance/stock_figure.py` S952's 500a7d46 → v1.7 (made by `make_s956.py`, each anchor once). The install rebuilds the stock of record at once. Walk `walk_s956.py` on a copy (twice); CONTROL (S952's file) red. Undo `undo_s956.sh` (file back, record rebuilt by the old code).
