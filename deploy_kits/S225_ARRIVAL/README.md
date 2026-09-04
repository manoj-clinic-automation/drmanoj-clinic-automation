# S225_ARRIVAL — when the goods arrive (rev 8)

**Spec §4, the owner's words:** *"on arrival they simply tap to acknowledge" · "if qty is different, they enter the supplied
one" · "option to mark if stockist is short of a medicine" · "bill scan button should be at contextual place(s)".*

On the staff page, every **sent** order now carries **Arrived** (one tap — every line supplied as ordered) and **Different**
(a small table: supplied quantity per line, and a *short* tick where the stockist could not supply). Either way the order
becomes **received**, by that person, at that minute, audited. Less-than-asked is recorded as a short even without the tick.
A short-supplied line **rides into the next reorder plan by itself** — added to that stockist's line (still rounded to tens)
with *"short-supplied on order #N — carried"* in the reasons — until it is re-ordered from that stockist, or 45 days pass.
A **received** order shows **Scan the bill** (the in-app scan intake) with the note to type — stockist and amount — so the
scan pairs with the bill on the scan-links page. Pre-filling the scan form itself needs a change in the asset app; owed.

**Proof:** `selftest_arrival.py` **305/305** — everything before as regression, then: one-tap receipt, receipt by line with a
short, a partial supply recorded short without the tick, the carry into the plan (rounded, worded), the carry consumed by a
re-order, the scan button, refusals (twice-received 409, signed-out 401). The install walks a **probe copy** (F-321).
