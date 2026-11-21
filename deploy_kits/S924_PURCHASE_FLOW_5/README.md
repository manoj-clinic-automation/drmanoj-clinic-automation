# S924_PURCHASE_FLOW_5 · Sanjeevni session 500 · 21-Nov-2026 · D1030 / D1034

The last of the purchase-flow kits from mock-up v4 FINAL: **his Hub's Needs-you line.**

* **`/root/finance/order_flow.py` v1.3 → v1.4** — the Hub's Needs-you speaks of the purchase flow in ONE line, the counts of his grouped page (`groups()`): "Purchase orders: N late · M medicines still missing · K out of stock / substitute for your word — your grouped page" (opens `/finance/porders/flow`). It takes the place of order_track's own "Orders: N late …" line (its older late rule said 2 late where the orders page said 0) and of order_s778's line per out-of-stock tap (eleven lines on 21-Nov). The wrong-dealer note stays; every other line is unchanged. Installed once per process when the module mounts; any fault gives the old lines back.

Walk: `walk_s924.py` on a copy of the database — Needs-you before and after (49 lines → 38: twelve replaced by one); the CONTROL (the hook not installed) goes red.
Install: one server line (the installer's header). Undo: `undo_s924.sh`.
