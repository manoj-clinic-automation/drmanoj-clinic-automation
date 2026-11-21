# S922_PURCHASE_FLOW_3 · Sanjeevni session 500 · 21-Nov-2026 · D1030 / D1034

The purchase-flow kit 3 from mock-up v4 FINAL (`https://claude.ai/artifact/GqBHMeFVQQmksK2fu1qmfN`, tab "Darpan"), with the owner's word of 21:00 IST ("optimise it for mobile screen also") for reception's strip.

* **`/root/finance/order_flow.py` v1.1 → v1.2** — reception's strip laid out for a phone: a small scan picture, a line's three buttons (Dobara order karo · Out of stock · Substitute aaya) on their own full-width row under the line, a fixed table that fits 375 px, the team list as short blocks. `dar_view()` — Darpan's read-only view from `groups()`: each order's medicines still to come (late · arrived short · in Marg still missing · on the way), a medicine ordered again on a later order leaving it by itself, and the team list with the doctor's word (waiting / next week).
* **`/root/finance/darpan_kal.py`** — one read door appended: `GET /finance/darpan/kal/api/order/flow` (staff or owner, as his order tab). Writes nothing.
* **`/root/finance/darpan_kal.html`** — his order tab ("आज का ऑर्डर") carries two folds under the day's list, in his script, nothing to tap: **डीलर से अभी आना बाकी** (each dealer, order day, the medicines and quantities, a status badge; "जो दवा अगली शीट में फिर से ऑर्डर होगी, वह यहाँ से अपने आप हट जाएगी।") and **Out of stock / substitute — टीम सूची** ("डॉक्टर साहब का फ़ैसला बाकी" or his word). Fetched on its own: a fault leaves the order list as it is.

Walk: `walk_s922.py` on a copy of the database (a made-up dealer; the copy removed) — 13 checks; the CONTROL (the "ordered again" rule taken out) goes red.
Install: one server line (the installer's header). Undo: `undo_s922.sh`.
Next: kit 4 the Purchase bills page (Arrived = the reader) · his Hub's line.
