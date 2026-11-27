# S531 — THE MORNING CHECK, NARROWED AND AUTOMATED — the plan for Fable's review (D1097)

*Written at the S531 close (the parent, Opus, 27-Nov-2026 13:5x IST). For the next parent session (537, **Fable**): review this plan against the live code and the newest database copy, answer the open questions in §6, and write the final build plan for Opus. **Nothing here is built.** Nothing goes to him before the review except a screen mock-up (the matched breakdown, §4.1).*

## 1 · His words (27-Nov-2026, IST)

- 13:24 — "Register holds more or less revenue than Docterz, then what's the flow, max automated and narrowed down as much as possible?"
- 13:36 — "Register has more — from Docterz — match with slips — register matches then it shows for all how it matched; if slip also doesn't settle it then raise it accordingly. Register has less than Docterz, then also include any cancellation or refunds. Sometimes a slip is accidentally made of double payment, so that also needs to be checked."
- 13:38 — "Double slips is actually procedure etc booked twice accidentally for a patient with one slip only."
- 13:44 — "Looks logical, but shouldn't be cumbersome for staff; it's to make morning check flow automated and to be settled within minimum time and maximal automated."
- 13:48 — "make the plan for review from fable in fresh session and do eos here."

Earlier the same day: 10:31 (the 26-Nov dressing: money taken, no slip, no Docterz entry, nobody told), 10:40 "PROCEED" (S968), 12:45–12:46 "only slip of this dressing also settles the match … YES" (S970).

## 2 · The chain as it stands live (27-Nov 13:10)

| step | kit | what it does |
|---|---|---|
| evening | S960 (+S961 the reception PC posts at once) | each Docterz export of today checked against the day's slips; one push to Shavez + reception: missing slips, or all good |
| morning Save | S968 | the register's Save starts `register_push.py --day D`; every 5 min 08:00–21:55 a sweep of the last 7 days; pushes "N galti — din ki jaanch" (staff lines only), "sab mile", "sab galtiyan theek" |
| the check | S962 + S968 + S970 (`day_check.check_day`) | the referee: register vs Docterz by tender and head; wanted money (slip lines Docterz lacks) placed while the register has room; refunds / radd both ways; payment-mode moves; leftovers |
| his list | S846 + S962 + S970 | a slip Docterz lacks goes to his "Slips not in Docterz" list; if the register holds its WHOLE money it is answered "Not entering in Docterz" by itself (`who='auto'`, Undo final); else Shavez can tap "Paise liye hi nahi" or remind him |

**FROM bytes for any kit (live, DECLARED-PENDING until the 28-Nov bundle where marked):** `/root/finance/day_check.py` 946f0408 (pending) · `register_push.py` 9b1fbc29 (pending) · `clinic_register.py` ba56418d (pending) · `not_in_docterz.py` 4ad98ab0 · `slip_log.py` 3395e71c · `slip_adjust.py` 7d44cf3e · `clinic_money.py` 76a05410 · `evening_check.py` b3c5bebb · `parchi_desk.py` 08680822. Read the newest bundle's bytes first (F-472).

## 3 · The gaps (read in the code, S531)

1. **Every "check by hand" line reaches nobody.** `day_check` cards of kind `hand` (keys `over:`, `swap:`, `modeany:`, `regupi:`, `bank:`, `s962ans:`, `noid:`) are never pushed (S968 pushes `who in docterz/parchi` only) and are not on his push either; they sit on the page. The commonest: `over:<tender>:<amount>` — "Docterz has ₹X more than the register — check by hand" (register LESS than Docterz, nothing explains it).
2. **Register MORE, not settled by slips** → `notfound` "patient not found — find the patient, make the parchi" — pushed to staff (S968), but with no candidates: staff must search blind.
3. **A line booked twice on ONE slip** (same procedure / X-ray, same side): caught today only when Docterz billed it once (`dup_item`, `pdup:` — a parchi card). When Docterz did not bill it at all, both lines are "wanted"; the register holds one → with S970 the back-date row is part-held (`allp` false) and stays on his list as a back-date row, not as a duplicate.
4. **No breakdown for everyone when slips settle it** — the day's one line (`top`) exists on the day check, but the staff page and the push do not say HOW it matched ("Register ₹7,700 = Docterz ₹7,600 + dressing slip ₹100, kept outside Docterz").

## 4 · The plan he approved in principle (13:44) — staff light, system first

**4.1 · Settle by itself whatever it can prove (no staff step):**
- slips that explain the register's extra (S970, live);
- refunds and cancellations (S962, live) — the slip's refund / radd tag, a Docterz bill cancelled, a refund line in the register (part 2 of D1080 if he wants the register line);
- UPI the bank proves (S653 / D788, live for Debit Card → UPI; widen to any tender pair the bank proves);
- **a line booked twice on one slip while the money is there once → the extra line marked wrong by itself** (a new mark, Undo-able, shown on his list and the staff page) — never deleting the slip line.
- **The day's breakdown shown to all** (staff page + his) when it settles: "Register = Docterz + slips outside Docterz − refunds".

**4.2 · One push, one list for staff each morning** (on the register Save; today's S968 road): only the Docterz edits the system cannot make itself (Docterz has no API) — remove a duplicate bill · change a payment mode · make a free / staff bill free — each line saying exactly what to change; one "Ho gaya" for the list; the next export confirms (the tick → re-export rule already in `day_check`).

**4.3 · A register typo = one tap:** when the gap equals exactly one Docterz bill of a head, or the bank proves the UPI figure, the staff page shows the likely right figure for that register box; "Theek karein" writes it (the register's own edit path, audited).

**4.4 · Money with no slip (register MORE, slips do not settle it) = one tap:** the service read from the amount (the rate list behind `slip_item.service_id` / the owner's service list); candidate patients seen that day with nothing billed (an X-ray photo on `xray_filing` with no bill, a slip line unbilled, a `patient_visit` / `dx_visit` row with no bill — check which of these are present by morning); reception taps the patient → the late slip is made by itself (and S970 settles it) · "register mein galat likha" → 4.3 · "pata nahi" → his push.

**4.5 · Register LESS than Docterz, in order, each step stopping when the gap is explained:** refunds and cancellations → a duplicate bill in Docterz (same ID, same item, same amount twice) → a free / staff patient billed full (the slip says free / a staff ID) → a payment-mode mix-up → the gap equals one bill (4.3) → UPI decided by the bank → still unexplained → **his one push: "26-Nov: ₹X unexplained (cash short)"**.

**4.6 · He gets one push, only for what nobody could explain;** every `hand` line goes to the person who can act on it, never only to the page.

## 5 · Proposed kit split (for the review to confirm or change)

- **K1 (server, `day_check` + `register_push`):** the `hand` lines routed (4.6); the double line on one slip (4.1, the new mark); the breakdown for all (4.1); his one push for the unexplained (4.5 end). Read-only logic + pushes; no new staff taps.
- **K2 (server, `day_check` + `clinic_register`):** the register typo one-tap (4.3) and the "Ho gaya" list (4.2) — new staff writes, audited, Undo.
- **K3 (server, `day_check` + `slip_log` + a reception screen):** money with no slip → candidates + one tap → the late slip (4.4).
- Mock-up of the staff morning screen and his push words before K2/K3 (he judges what he can see).

## 6 · Open questions for the review (answer from the code and the copy — never ask him a technical one)

1. Which candidate sources exist by the morning for 4.4 (`xray_filing` rows without a bill, `patient_visit`, `dx_visit` — its lag was ~6 days on the 27-Nov copy), and how often would each have named the right patient on the last 30 days?
2. The rate list for "service from amount": where it lives (`slip_item.service_id` →?), and how many amounts are ambiguous (two services, one price).
3. Is "a line twice on one slip" ever legitimate (two plasters, both knees with the side blank)? The side and name rule; what the last 60 days show.
4. A register edit by staff (4.3): the register's own audit and lock rules (`clinic_register.py`); must it be his tap instead?
5. Does any `hand` key need to stay with him rather than staff (`regupi:`, `bank:`)? The routing table per key.
6. How a "Ho gaya" interacts with the existing per-card ticks and the re-export rule (`day_check_tick`, `_export_at`).
7. The evening check (S960) — can some of 4.2 be caught the same evening (duplicate bill, mode) so the morning list is shorter?

## 7 · Standing rules for the build

D656 (patient data only in the device VM, counts only in chat; F-1715) · A-D149, A-D153 · staff words Hindi, his English · a push to him goes to his devices only · Undo on every automatic answer · walks with made-up data; live-shape on a copy with sums compared, never a unique-amount assumption (F-1718) · cold review + second look before placing.
