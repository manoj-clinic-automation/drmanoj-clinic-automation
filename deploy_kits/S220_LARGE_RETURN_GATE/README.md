# S220_LARGE_RETURN_GATE — the ₹1,000 line, enforced · the spot-count list

**Why (measured, S220):** the May→Aug near-doubling of returns is not more returns (43 · 31 · 39 · 43)
but **bigger** ones — average ₹232 → ₹433; returns of **₹1,000+ went 0 → 6 in August, ₹8,330, 45% of the
month.** `returns.large_p` (₹1,000) has existed since S208; nothing enforced it.

**The owner's rulings (02-Sep):** a return ≥ ₹1,000 is not settled until he taps OK on the returns card
the same day; and *"random stock checks of the items which we flag could be a deterrent"* while routine
stock checking is suspended. All English; inside the card that exists; no new tile.

**What it does.**
- `darpan_app.py` — a large return **needs the owner's decision even when its verdict is ok**: it joins
  `needs` (PENDING → the NEED YOU badge) until approved/rejected through the existing cn-approve flow. It
  is never `flagged` — size is not a money finding. New: `/finance/darpan/api/spot-check` (POST, owner
  only) records what was counted, by name and time, in `audit_log` too.
- `finance_returns_escalate.py` — after every Apply and hourly (never on a page load), the items of every
  **large** or **money-flagged** return of the day go on `stock_spot_check`, once (UNIQUE per bill + item),
  status *due*. D361 holds: nothing before `returns.act_from` is listed.
- `finance_approvals.html` — under the returns header: *"₹1000+ returns this month: N · ₹ · N need your
  OK"*; the row badge *"₹1000+ — your OK"*; at the foot, the **Spot-count list** (item · batch · why ·
  credit note · date · counted / skip). Count the shelf, type what is there; the difference against Marg
  is read later.

**Proven:** selftest **19/19** on a copy of the live db — the real `escalate_day`, the real blueprint on a
bare Flask app (the selftest_darpan pattern), a synthetic ₹1,500 return on a walk day when the box has no
large return since the cutover yet; **browser render test 7/7** in a real Chromium with the patched page
(the gate line, the badge, the list, the buttons, no JS errors). Three pins predicted offline.

| file | what |
|---|---|
| `patch_darpan_largegate_s220.py` | darpan_app.py — 5 anchors |
| `patch_escalate_spotlist_s220.py` | finance_returns_escalate.py — 2 anchors |
| `patch_hub_largegate_s220.py` | finance_approvals.html — 4 anchors |
| `selftest_largegate_s220.py` | 19 checks on a copy of the db |
| `PREDICTED_PINS.txt` | the three pins the owner's md5sum must read |
