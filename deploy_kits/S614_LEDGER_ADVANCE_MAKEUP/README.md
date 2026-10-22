# S614_LEDGER_ADVANCE_MAKEUP — what "advance remaining" is made of (S336, 22-Oct-2026, D753)

**The owner, 22-Oct 05:57 IST:** *"I am not seeing the 3000 advance of 21st October from November 2026 salary to be cut
in November in the top section. Another thing is, while issuing a fresh advance, I should know what are the pending
advances. Of that staff."*

**The one line (VPS):**

    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S614_LEDGER_ADVANCE_MAKEUP/install_S614_LEDGER_ADVANCE_MAKEUP.sh

**What it does** (`/root/staff_ledger.py` 92885f3b → new, by 12 exact edits in `edits_s614.py`):
1. `https://followup.dr-manoj.in/ledger/statement` — under *Advance remaining after <month>*, one line per advance
   still open after the close: Surendra today reads *Rs 2,000 — left on the advance of 17 Aug 2026 (Rs 3,000) — from the
   monthly amount of Rs 2,000, oldest first — next at the November 2026 close* and *Rs 3,000 — advance of 21 Oct 2026 — from November 2026 salary*. A loan names its
   interest apart; an agreed schedule names its next step; a part the salary cannot bear says it is held; the
   note under it now says it is about the cut above.
2. `https://followup.dr-manoj.in/ledger/` (New entry, a doctor's login) — the blue box now lists every open advance
   (date · amount · left · when cut), what the next close cuts, advances waiting for approval, what is already booked
   against the chosen *Against which month* (and how much of it still waits for approval) and the room under the
   ceiling, or by how much it is over; it follows the month chosen.
3. **F-973:** a maker's (Shavez's) New entry script died on `var P = {{}};` — the form never showed or hid its fields
   and the ceiling line never appeared. Now `var P = {};`.

Version → 4.2-S614-MAKEUP. The figures are `loans_view()`, `month_plan()`, `plan_for_staff()` and
`advance_month_taken()`'s own; no ledger or salary figure changes. F-974 (noted, not changed): `loans_view()` with a
person who has nothing to list raises; `advance_makeup()` treats that as "nothing open".

**Proven by:** the file's own selftest (342 checks); `walk_s614.py` — all of S612's walk, plus Surendra's 21-Oct shape,
a loan, a schedule, a held part, New entry's box for a doctor and a maker (page scripts parsed), and on the box the
live ledger and register on scratch copies (every person's lines add up to the top box; New entry one line per open
advance). Screen review at 375 px by a sub-agent; its five wording fixes taken in. The S612 file goes RED.

**Undo:** `--undo` puts the S612 file back (`/root/s614_backup/`).
