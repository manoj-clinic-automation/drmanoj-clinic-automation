# S425_FINANCE_MOUNT_GUARD — session 284 (parent), 27-Sep-2026

**What it fixes.** When `/root/finance/finance_app.py` was read whole at S284, the eleven oldest module mounts (S208_STOCK_LEDGER … S241_AMIR_DAY: stock_app, darpan_app, staff_pages + joiner_app, returns_desk, finance_clinic_day, clinic_register, purchase_app, bank_mpr_status, clinic_day_pdf, marg_door, amir_day) were bare imports. A fault in any one of them stopped the WHOLE finance app from starting — every money page, the approvals, the health page. Every mount from S243 on was already guarded (S209).

**What it changes.** One anchored patch on exact bytes: FROM `7486f3e652bdf777666af134da5b0054` (S422, live) → TO `ac24fc5e4e312b0bf3718b42380d5e64`.
1. `_MOUNT_FAILED = []` before the first mount.
2. Each of the eleven sections' code wrapped in `try/except` — the same lines, indented; a failure is printed to the journal as `<part> NOT mounted: …` and recorded.
3. One health-page row, key `mounts`, "Parts of the finance app that did not load": red naming the part(s) when any old mount failed or a guarded later module is absent from `sys.modules`; green "all 25 parts loaded" otherwise.

No behaviour change when every part loads. No other file. Restarts `clinic-finance`.

**Proof.** `walk_s425.py` (15 checks, no network): un-wrapping the patched file gives the original byte for byte; eleven guards, twelve modules in the original order; all-load → green; one import + one init broken → both recorded, the other nine still mount, row red naming both; the staff pair is one part; a missing later module turns the row red.

**Install (VPS, one line):** see the chat. The installer refuses unless the live file is exactly the S422 bytes; backs up to `finance_app.py.bak_S425_7486f3e6`; restores itself on any red after placing.

**Sanjeevni chat:** declared on the System Board at v114 before the scratch folder was named.
