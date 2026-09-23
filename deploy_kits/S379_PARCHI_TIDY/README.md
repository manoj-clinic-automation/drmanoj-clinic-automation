# S379_PARCHI_TIDY — the Parchi tile and the day statement, as the owner asked on 23-Sep-2026

1. **Docterz upload — removed.** X-rays now file themselves (S374), so the *Docterz upload* screen is gone from the
   Parchi menu and from the slip report. Its old address opens **Blood test**, which now also carries the
   "blood report nahi aaya" questions that used to sit on the upload screen; its menu line shows how many are open.
2. **The day statement in slip order.** On the Day Revenue page and its PDF every section runs in physical
   slip-number order, as the register does; a Docterz entry with no slip comes at the end of its section.
   A **Slip books** line names every skipped number and why: *cancelled*, *spoilt*, *no reason given yet*,
   or *not written* — counted back to the previous day's last number, so a gap between two days shows too.
3. **Naya mareez — the name.** A new patient's slip carries only the ID; once the overnight Docterz report has
   arrived, the name it gives for that ID is written onto the slip and shows in the tile's lists (`ID · name · naya`).
4. **Six X-rays added** to his rate page, on his word: Both knees AP standing ₹300 (small film) · Humerus (arm)
   AP & Lateral ₹500 · Femur (thigh) AP & Lateral ₹600 (11 × 14) · Hip AP & Lateral ₹500 · Foot AP & Oblique ₹500 ·
   Hand AP & Oblique ₹500. Right/left asked for the limbs. He edits any of them on his rate page.
5. **A discount on a procedure.** Beside each procedure on the X-ray/Proc slip, a *chhoot ₹* box (only when a
   procedure is chosen; never above its rate). The room sees the amount after it; the report's match compares the
   procedures with Docterz after the discount and names the discount when they differ.

**Proof.** `walk_s379.py` 31/31 — Part A on a synthetic day whose Docterz order is not the slip order (a cancelled
number, a number never written, a gap back to the day before), page and PDF; Part B on a scratch copy of the live
database, on its own day and IDs. The live four modules are the negative control. On the 21-Sep real data the page
reads OPD 19395–19421 (26 written, 19395 skipped) and X-ray & Proc 1150–1167 (15 written, 1150/1152/1153 skipped).
