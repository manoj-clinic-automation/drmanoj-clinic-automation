# S925_OWNER_TILE_TO_FLOW · Sanjeevni session 501 · 22-Nov-2026

The owner (08:59 IST): his portal must reach the purchase flow page; (09:15) retire the old Orders and Order medicines pages.

* **`/root/finance/porders.py`** — his plain `/finance/porders` (the Purchase orders tile on his home) opens `/finance/porders/flow`. `?home=1` is still his one-task screen, `?old=1` the old page. Only the owner's login (the porders checker) is moved: reception, Darpan and Shavez see what they saw.
* **`/root/finance/order_flow.py` v1.4 → v1.5** — "Reception's screen →" beside BACK on the flow page (to `/finance/porders?home=1`).

* **`/root/finance/purchase_app.py`** — the old **Orders** (`/finance/purchase/page/orders`) and **Order medicines** (`/finance/purchase/page/staff`) pages RETIRED (the owner 09:15): their addresses open `/finance/porders` (a login with no purchase-orders role — Amir — the purchase hub); the purchase top bar carries one "Purchase orders" link in their place; the hub's Orders card opens the purchase orders page. The old bodies are kept unreachable for one release.

Walk: `walk_s925.py` through the real blueprints (porders, order_flow, purchase_app) in a Flask test app on a copy of the database — 12 checks; the CONTROL (the live files) goes red on the 7 that change.
Install: one server line (the installer's header). Undo: `undo_s925.sh`.
