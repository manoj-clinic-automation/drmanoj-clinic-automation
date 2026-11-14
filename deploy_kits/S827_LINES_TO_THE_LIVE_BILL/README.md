# S827_LINES_TO_THE_LIVE_BILL — a bill moved between dealers in Marg keeps its item lines (14-Nov-2026, Sanjeevni session 455) · F-1243

**The fault.** Deepam Pharma's bill 502 of 18-Aug-2026 (₹10,641): Marg's bill list of 02-Sep had it under MANNAT PHARMA; Amir moved it to Deepam, and the list of 17-Sep (the live one) has it under DEEPAM PHARMA. Marg's bill/item list prints no dealer, so the system gives each line the dealer of its bill — but it still counted the replaced Mannat copy as a candidate and, with August's item list (27-Aug, Mannat), filed the line under MANNAT. Deepam's live bill showed no lines.

**The kit.**
- `/root/finance/purchase_app.py` (98ae8f76 → the TO pin; rebuilt on the box from the live bytes by `make_s827.py`): an item line is given its dealer only from the bills of the **live** bill-wise exports — two queries (`_store_lines`' one-bill test, `_redate_lines`' bill list, which `_line_owner_s282` also reads).
- `repair_s827.py`: moves the two live lines of 502 (ROSIKA FORTE 50 — the bill/item list's and the item list's) to DEEPAM PHARMA, only when Deepam's 502 is the one live bill and Mannat's is not; one transaction; the lines' state before written beside the database; one audit row. August is FINAL — the owner's word 08:24 IST 14-Nov; **no total changes** (only the dealer of two lines).

**Proof (on the box, before placing):** every purchase line re-filed on a copy of finance.db with the old and the new file — on the 14-Nov copy: 5,215 lines, **0 differ** (the rule changes no line already filed; the repair moves the two). The repair's dry run must name exactly those lines.

**Bench.** `walk_s827.py` (made-up root): 5 green on the new file; the control on the live file 2 red (the fault reproduced). S740's own walk reads the same on both files. Cold review: SAFE AFTER FIXES -- its three must-verify points checked in the code (an older bill list is superseded in the same push BEFORE the lines are filed; every bill row carries its export's md5; the audit columns exist); the proof's allow-rule now names bill 502; a red after the repair says where the lines' former dealer is kept. The repair also moves the item list's own line (858) on purpose: Marg's bill is Deepam's now; the 27-Aug item list is never filed again (its md5 is known).

**Install (the VPS, one line):**

    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s827kit && cp -rp /root/deploy/repo/deploy_kits/S827_LINES_TO_THE_LIVE_BILL /tmp/s827kit && bash /tmp/s827kit/install_S827_LINES_TO_THE_LIVE_BILL.sh

**Undo:** the installer prints the one line.
