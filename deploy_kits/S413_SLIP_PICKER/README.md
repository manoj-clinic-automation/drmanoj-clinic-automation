# S413_SLIP_PICKER — the X-ray/Proc form as one search box

**The owner, 26-Sep-2026:** the drop-downs cut long names and show no price; the search must be intuitive (SBK or BK
bring the right lines) and one box must serve X-rays and procedures alike. Rates themselves he now edits on his own
tile (`/finance/clinic/sheets`); nothing here touches them.

**What changes (slip_log.py only):**
1. The two drop-down columns are replaced by **one picker**: a search box over X-rays and procedures together (a line
   is found by its name, its short form, the words in its brackets, and its kind — X-ray / plaster / cast / slab /
   injection / ILI / dressing; every typed word must match; "bk" finds B/K, SBK and HBK; "bk slab" only the slabs);
   the **most-used lines of the last 90 days** as six tappable buttons with their price; a result list while typing
   (Enter takes the first); every chosen line in **full with its price**, side (when the rate page asks), chhoot
   (procedures) and a remove cross; a **running total**. Six X-rays and three procedures per parchi, as before.
   The form posts the same fields (xray0.., proc0.., _side, _other, _disc), so saving is untouched.
2. The **X-ray room** rows: the name line runs the full width, each line whole, its own price when a parchi has more
   than one line or a chhoot; the amount and the UPI / Cash / Done buttons on their own line.
3. The old select rows and their script are removed (nothing else used them).

**Proof.** `walk_s413.py` 85/85: the rate page read, the same doors as S401, the data behind the picker complete, the
same posted fields save the same rows, the room lists each line; then, in a real 390-px Chromium page: buttons with
prices before typing, "SBK" / "BK" / "knee" / "bk slab" / "ili" / nothing-found, tap → chosen in full, side L, chhoot,
the total, the hidden fields, remove, add from a button, save from the browser (rows and chhoot in the table), an
empty parchi stopped, Other asks for a name, no script error; every screen for six logins. Negative control: the live
S401 page still has the drop-downs. On the VPS (no Playwright) the browser part reports SKIPPED, never passed; the
browser proof is this session's. `slip_log.py` 36405348 → fa2d21bf. Restarts clinic-finance only.
