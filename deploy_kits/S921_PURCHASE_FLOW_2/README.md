# S921_PURCHASE_FLOW_2 · Sanjeevni session 500 · 21-Nov-2026 · D1030 / D1034

The purchase-flow kit 2 from the owner's mock-up v4 FINAL (`https://claude.ai/artifact/GqBHMeFVQQmksK2fu1qmfN`, tab "Reception"): **reception's page**.

* **`/root/finance/order_flow.py` v1.0 → v1.1** — `rec_body()`: reception's strip in Roman Hindi, drawn from `groups()` alone (the same Late · Raste mein · Aaya · Purane order and team list as his page, the same counts). Her buttons, two taps, no dialog: on a late row **Call kiya — aa raha hai · Out of stock · Nahi bhejenge**; on the way **Maal aa gaya** (the S454 arrival screen); arrived without a scan **📷 Bill scan karo** (the scan app's intake); on a line that came short **Dobara order karo · Out of stock · Substitute aaya**. The team list read-only ("Doctor sahab ka faisla baaki"). His Chase shows on her late row; her word shows on his. `rec_act()` behind `POST /finance/porders/api/flow/rec` (the senders and the owner): again / out of stock through his own `act()`; Substitute aaya writes `order_flow_mark` kind 'sub'; Call kiya / Nahi bhejenge write the new table `order_flow_rec`. `/finance/porders/flow?rec=1` = his preview of her strip. F-1551: his team list in English quantities.
* **`/root/finance/porders_s454.py`** — reception's home (porders.rescan_doers: reception, alisha, shivani) carries the strip under "Naya bill scan karo" in place of its two rows (Order ka maal nahi aaya, Maal aaya?); the September link off every staff home (F-1548); no alert() on his settings and test-message cards (F-1552). Switch `order_flow.rec_on = 0` = her two old rows back (the September link stays off). Darpan's and his own homes unchanged.
* **`/root/finance/order_s778.py`** — "Ab nahi milta" / "No longer available" read **Out of stock** everywhere.
* **`/root/finance/porders.html`** — the not-yet-live engine's practice lines never on a staff screen (F-1548).
* **F-1547, once** — the 27 order messages of 12–20 Nov that the phone sent (standing 'skipped', unconfirmed) become 'sent' at their hand-out moment; the ids kept for the undo.

Walk: `walk_s921.py` on a copy of the database (a made-up late order; the copy removed) — 29 checks; the CONTROL (her word taken out of the reader) goes red.
Install: one server line (the installer's header). Undo: `undo_s921.sh`.
Next, one at a time: kit 3 Darpan's tab · kit 4 the Purchase bills page · his Hub's line.
