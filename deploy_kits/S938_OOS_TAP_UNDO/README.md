# S938_OOS_TAP_UNDO · Sanjeevni session 508 · 23-Nov-2026

The owner (18:01 IST): "She did it by mistake, as most are orders under process from 20th nov sheet ... Only lanzol junior is old order, and that too needs to be put back for now, and a way back for such accidental taps needed."

At 17:22–17:24 Alisha (on reception's order screen, while phoning the dealers) tapped **Out of stock** on ten lines of the red box. Each tap sent the medicine to his page for a word and took it off reception's lists.

* **`/root/finance/order_s778.py`** — `na_undo()`: an Out of stock tap the doctor has not answered taken back — exactly what the tap did, reversed (the Marg sheet line's hold removed, a carry it dropped opened again, a Dobara row it cleared given back); the tap row removed and kept whole in `purchase_audit` (`s778_na_undo`). Reception: a tap of today only; the doctor (and Shavez on his page): any tap still waiting. A tap he has answered or put a word on is refused. Reception's red box now lists **today's Out of stock taps with Undo** (two taps, no dialog).
* **`/root/finance/order_flow.py` v2.1 → v2.2** — on his Purchase orders page, a row of a staff tap still waiting carries **"Tapped by mistake — put back on the order list"**.
* **`/root/finance/porders_s454.py`** — the door `POST /finance/porders/api/s778/na_undo`.
* **One-off** `s938_fix.py` (run by the installer after the files are live): Alisha's 23-Nov 17:20–17:30 taps on the ten medicines he named, put back — only those still waiting for him; anything else untouched.

Walk: `walk_s938.py` through the real blueprints on a copy of the database — a real red-box line tapped and taken back by reception (or, when the live box is empty, one of today's real taps), back in the box, kept in the audit; made-up taps on a carry and a sheet line given back; yesterday's tap refused to reception, allowed to him; an answered tap and one with his word refused; his row's button and `do=undo_tap`. CONTROL (the live files) red on 14.
Install: one server line (the installer's header). Undo: `undo_s938.sh` (the files back; the one-off's data stays — the ten are simply back on the list).
