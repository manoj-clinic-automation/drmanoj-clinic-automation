# S240_EXPECTED_LATEBILLS

**What it fixes.** The computed stock ("ours") starts from a pinned Marg stock export and adds purchases by *bill date*. A Marg stock export is always the stock *as keyed at the moment it is taken*. So a bill dated on/before the baseline but keyed later was in neither figure: ours read low for its items (and the physical count then looked like excess).

**How keying time is found.** No export carries it, so it is bounded by capture stamps:

- **hi** — the first export (item-wise, bill-item-wise, bill-wise or supplier-wise) that contains the bill.
- **lo** — the last export covering its date that does not contain it (never earlier than the bill date).
- If hi ≤ baseline capture → the bill is inside the baseline (unchanged).
- If lo ≥ baseline capture → **late**. It is added.
- If the window straddles the capture, the whole-shop closing exports inside the window decide it. The bill's items must step up in one gap between two closings, and that gap lies on one side of the baseline.
- Otherwise the bill is **named as "keying time unknown"** and is **not added**. That is the same as the old behaviour, but now it is visible.

The mirror case is also handled: a bill dated after the baseline but already inside it (keyed before the export) is not counted twice.

**Extras.**

- ITEM WISE cuts long names ("…LF L ELA"). A late row is completed to the one baseline name it starts; it is never completed where there are two candidates or the name is short.
- `--upto` (a cross-check only) now also drops purchases dated after it. The daily run passes no `--upto`, so it is unchanged.
- A note is printed when the baseline was exported during shop hours on its own day.

**Install (manojz):** `powershell -ExecutionPolicy Bypass -File D:\dr-manoj-git\drmanoj-clinic-automation\deploy_kits\S240_EXPECTED_LATEBILLS\S240_LATEBILLS_INSTALL.ps1`

**Rollback:** copy `push_expected.py.bak_S240_a0e47a98` back over `push_expected.py` in S208_STOCK_LEDGER, or set `LATE_KEYED=off`.
