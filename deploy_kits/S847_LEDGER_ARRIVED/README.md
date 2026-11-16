# S847_LEDGER_ARRIVED — the Item ledger's "Arrived — not yet in Marg", made safe (16-Nov-2026, Sanjeevni session 470)

**Why.** Read live after S845 went in (11:18 IST): ROSIKA FORTE's **expected stock 5071:0** — a pharmacy scan of 12-Oct (B-0150, Deepam
Pharma) still on the Purchase bills page's waiting list, its quantity read as **5010**. A month-old scan and a misread number were added.

**Now** (item_ledger.py only; read only, as S845):
- a waiting scan more than the arrivals' grace (`arrival.bill_grace_days`, 3) older than **Marg's newest purchase bill** is shown with
  "scanned dd-mm, and Marg's purchases already run to dd-mm — not added: it is in Marg under another number or was never entered (the Purchase
  bills page settles it)" — never added;
- a line whose units exceed **five times the item's largest purchase line or highest Marg closing** is shown with "looks misread … the paper
  decides" — never added;
- the expected-stock box says "a waiting scan carries it but adds nothing — see below" when that is so.
The list itself stays the Purchase bills page's own (`provisional_s781.provisional`).

**File:** `/root/finance/item_ledger.py` 22c24bd9 (S845) → TO — the whole file (this project's own; its live bytes checked against S845's pin first).
**Proof:** `synth_s847.py` 5/5 (fresh scan added; stale and misread shown, not added; the page's figure and wording) — the control on S845's
page red 4; `synth_s845.py` 19/19 and `walk_s845.py --box` 45/45 on the new page (no regression); on the box the installer runs S845's walk
on copies of the live databases, both synths, and the control. `rehearse_s847.sh` 12/12 on a stand (S845 installed; made-up databases).
**Install:** publish, then the one server line in the installer's head. **Undo:** `bash /root/deploy/repo/deploy_kits/S847_LEDGER_ARRIVED/undo_s847.sh`.
