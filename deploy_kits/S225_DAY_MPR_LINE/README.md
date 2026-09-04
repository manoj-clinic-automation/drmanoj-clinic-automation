# S225_DAY_MPR_LINE — the bank's word on the Day Revenue page

**The owner, 04-Sep-2026 15:35:** *"the bank MPR isn't showing in the day sheet; on the day page the report should be
stated as applied or pending from bank or whatever, and a direct link of the day's MPR to match then and there."*

**What it adds** (an anchor patch on `finance_clinic_day.py`, live pin `dceb79a0…`, which the repository holds byte for byte):

- **On every day page** — a *Bank MPR* card under the header: the bank-status module's own sentence (APPLIED at HH:MM · LATE ·
  REFUSED · NO UPI · WAITING · NOT RECEIVED), then, when the bank has applied, **the match**: our online (UPI) total for
  the day beside the bank's applied total — *Matches*, or *Does not match: bank is higher/lower by ₹ N* — and the button
  **Open the day's bank MPR ›** to `/finance/clinic/bank/mpr/<date>`.
- **On the month table** — a **Bank** column: one word per day, in the module's own colour, each a link to that day's MPR.

Nothing here decides what the bank's state is; it asks `mpr_state()` in `bank_mpr_status.py` (S224) — one rule, one place
(D349). If that module were ever missing, the page says so and still renders.

**Proof:** `selftest_day_mpr_s225.py` **17/17** — patches the exact live bytes (refuses a wrong pin; idempotent), mounts the
result with the real `bank_mpr_status.py` on a temp database, and reads: an applied-and-matching day, an applied-late day that
differs by ₹2,000, a day the bank has not yet sent, the month column, the MPR page itself, the signed-out answer, and the
module-absent case. Predicted new pin `713bdf3a…`.
