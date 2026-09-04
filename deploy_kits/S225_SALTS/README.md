# S225_SALTS — Amir's salt work list, server-side (rev 11)

**The owner (spec §6):** *"Amir's salt correction list should be available as Excel download with him and me, and A4 print also."*
**And today, on seeing the first build:** *"you had taken my responses from such excel a few days back and the list had become small…
196 is a big task for a human, specially when it becomes repetitive for no reason."* Right — the first build re-asked the 154 suspects.
This one carries **the work list his answers of 28-Aug already produced** (S207, `Sanjeevni_Salt_Fix_for_Amir.xlsx`): rename 3 salts ·
create 38 salt names · change 77 items · 7 waiting on the doctor · 1 cleanup. The 68 items he confirmed correct are not asked again.

`push_salts.py` (one line on manojz) sends that list to the server once. **`/finance/purchase/page/salts`** — Amir and the doctor — shows the
five sections in working order; Amir **ticks a row DONE** when it is done in Marg (his name and the time recorded, audited); the doctor
**answers the 7 waiting rows** from the 196-name list or by typing. A later push never un-ticks a row or overwrites an answer. **Download
Excel** (five sheets, with the DONE marks and answers) and **Print A4** come from the record at that moment. The finance front gate opens
only three doors to the manojz token, so the list rides the vendors door — `finance_app.py` is not touched.

**Proof:** `selftest_salts.py` **335/335** on the real work list — the push (126 rows, sections counted), the fail-closed page, Amir's tick,
the doctor's answer (and Amir refused it), the kept-state rule on a second push, the Excel re-read by openpyxl (5 sheets, 77-row change
sheet with the DONE mark), the A4 PDF with [x]/[ ] marks, and the refusals. Install per F-321.

**Rev 11b — the owner's fresh Marg export, evaluated before finalising.** Marg's own *SALT WISE ITEM LIST* (04-Sep, 375 items) is pushed alongside the work list and every row shows **Marg says** — done / not yet / the item's current salt — so Amir's tick and Marg's truth sit side by side (Marg confirms 3 done as at 04-Sep: 2 changes, 1 create). The router does not know this export's signature yet, so it lands in `_REFUSED`; `push_salts.py` finds it there by shape. A note line the rename sheet carried is no longer a task.
