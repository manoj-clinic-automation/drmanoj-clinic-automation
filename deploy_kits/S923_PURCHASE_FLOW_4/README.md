# S923_PURCHASE_FLOW_4 · Sanjeevni session 500 · 21-Nov-2026 · D1030 / D1034

The purchase-flow kit 4 from mock-up v4 FINAL (`https://claude.ai/artifact/GqBHMeFVQQmksK2fu1qmfN`, tab "Purchase bills"), and the owner's 18:33 question (why scanned bills were left out of the provisional count).

* **Why they were left out:** a scan read right only when its item lines came within ₹2 of the printed total, or below it. Tonight all eight "to check" scans had lines a few rupees ABOVE the total (₹1,881.90 against ₹1,877 — round-off, a small discount). **`/root/finance/provisional_s781.py`** now lets the lines read up to **₹10 or 0.5%** above the total (whichever is more); both numbers are his settings, on the page itself (`s781.lines_over_rs`, `s781.lines_over_pct`). A real misread (₹2,500 against ₹1,877) still asks.
* **The page's top, split:** tiles — In Marg · Arrived and scanned, not yet in Marg (counted) · the month · **Still to come** (late · on the way — a link to the orders page; never listed here). One line ties his orders page's "Arrived, not in Marg" to the scans here and names the orders that arrived with no bill scanned yet. **Needs one look** (open): each doubtful scan with its reason, its lines and his taps — *Reads right — count it* · *Ask reception to rescan*; for a likely second scan *Yes, same bill — set aside* · *No, a different bill — count it*; a counted one shows "Counted by you · Undo". **Read right, counted** (folded). Two taps, no dialog. New table `s923_scan_word`; nothing writes stock, Marg or the bills.
* **`/root/finance/order_flow.py` v1.3** — his two doors: `POST /finance/porders/api/flow/scan` and `/api/flow/scanset` (the doctor only).

Walk: `walk_s923.py` on a copy of the database — 22 checks; the CONTROL (the allowance taken out) goes red.
Install: one server line (the installer's header). Undo: `undo_s923.sh`.
Next: his Hub's Needs-you line (`sanjeevni_approvals.py`).
