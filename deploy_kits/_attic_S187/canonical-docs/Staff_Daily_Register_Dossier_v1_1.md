# Staff Daily Register — Consolidated Design Dossier
**v1.1 · SIGNED OFF & CANONICAL · Session 161 (was v1.0 sign-off-ready, Session 160) · supersedes v0.2**
*Canonical (Tier-1), registered in `CANONICAL_MANIFEST.md`. **§5 SUPERSEDED — see the note directly below.***
*Every decision below is owner-locked in S160. No open items. Red-line, then build.*

---

## 1. Purpose & principle

Turn month-end salary preparation from **data entry** into **confirmation**. Every exception now reconstructed at month-end (leave, uninformed lateness, dress/i-card, cover, outstation, holidays, staff changes) is **captured the same day** at the reception desk, checked, and stored. The salary engine **reads** stored decisions — it never guesses.

> **Capture daily → check → store → month-end is a sweep, not a scramble.**

---

> ### ⚠️ v1.1 SUPERSESSION NOTE (S161 — read before using §5)
> The **leave/absence salary treatment in §5 (and the monthly/FY encashment maths) is SUPERSEDED by the C-model, decisions D279 + D280 (KB Register §S161 / Archive §S161), and implemented in `salary_engine.py`.**
> Under the C-model: **C = discretionary leaves taken + genuine absences**; a **2-day/month buffer**; every day of `max(0, C−2)` **plus** over-quota festival days is deducted at **base÷30**; **encashment `((2−C)×base/30)` is paid ONLY when there are zero deductible extra days** (any extra absence forfeits it entirely). The ₹50/₹100 fines still stack; late-marks/early logic unchanged; incentive → the annual pot.
> Everything else in this dossier (roles, stores, capture screens, issuance, lifecycle, Sunday toggle, per-staff scoping) stands. Where §5's encashment wording and the C-model differ, **the C-model wins.**

This grew, by design, into a six-part subsystem: (1) daily register · (2) yearly balances · (3) history-aware staff record · (4) Sunday roster toggle · (5) uniform/i-card issuance · (6) the salary-engine changes that read all of the above.

---

## 2. Roles & authority

| Role | Who | Can do |
|---|---|---|
| **Maker** | Alisha (active); Shivani (provisioned, **inactive** until you activate) — both receptionists | Enter the day's ticks (no rupee typing). Enter ongoing uniform/i-card issuance. |
| **Checker** | Shavez | **One click** to approve a date. Never a dropdown. Never approves his own entries. |
| **Override** | Dr Manoj + Dr Bhawna (**peers** — either acts on anything) | Reverse any decision; log ad-hoc fines (flexible ₹ + note); enter staff lifecycle (join/leave/timing) + issuance backfill; flip the Sunday toggle. |

Guardrails: manager→checker separation (D265) · "informed" = the reception register digitised (D254) · one-writer-per-store (F-31).

---

## 3. Stores & the one-writer boundary

Three stores, one writer each; the salary engine only **reads**.

| Store | Writer | Holds |
|---|---|---|
| **Daily Register** (SQLite WAL, VPS) | the Register page | per (date, staff, item): leave/absent, late-informed, dress, i-card, holiday, outstation, cover, OT-permitted — with maker/checker/override + timestamps. **Also the history-aware staff record and the uniform/i-card issuance table.** |
| **Yearly Balances** (VPS) | the Register page | running per-staff, cross-month: discretionary-leave used (this month), festival-leave used (this year), **incentive pot (Apr→Mar)** |
| **Staff Ledger** (existing) | staff_ledger.py | advances, loans, perks, **and ad-hoc discretionary fines** |

**Ad-hoc fines** = a ledger debit (arbitrary ₹ + narration) → surface via the salary sheet's existing `−ledger db`. **Rule-fines** (dress/i-card/absence/late) are computed by the engine → surface via `−fines`. No reconciliation between the two.

> **Boundary note (S160 decision #4):** uniform/i-card issuance lives in the **Daily Register** store, **not** the Asset Register — keeping all staff/HR data on one screen and payroll decoupled from the equipment register.

---

## 4. Daily items → rupee mapping (authoritative)

All items apply to **every staff except Arjun** (minutes-exempt, presence-only).

| Item (maker tick) | Effect | Notes |
|---|---|---|
| **Dress improper** | **−₹20** | **hard-gated on issuance** (§8): no issued kit on record → fine impossible. Nullified on leave/absent days (§6). |
| **I-card missing** | **−₹20** | hard-gated on issuance; both can hit same day = −₹40 |
| **Absence → Sanctioned leave** | not fineable; spends a leave (§5) | greys out dress/i-card/late that day |
| **Absence → Absent (genuine)** | feeds ₹50/₹100 fine lines; **no base-pay deduction** | plain absent unchanged from today |
| **≥60-min late → Informed** | +2 marks | informed-by recorded (Bhawna / Manoj) |
| **≥60-min late → Not informed** | **+3 marks** | register-checked |
| **Clinic holiday** (date-level) | all staff: no duty, no fine | **Holi = closed**; date-wide tick |
| **Outstation** (Darpan) | **+₹250 / night** | food & bed paid outside this system |
| **OT-permitted** (optional) | that day's OT **pre-accepted** | unused tick → OT stays a month-end candidate |
| **Cover-duty** | **+₹200 / duty — SHIVANI ONLY** | config exception on her user-id; not general |
| **Ad-hoc fine** (override only) | **−₹ (flexible)** + optional note | written to Staff Ledger, not here |

---

## 5. Leave model

Four credits, resolved in order:

1. **Sunday roster (Reading 1).** `sunday_group` rosters ~2 OFF Sundays/month → **OFF = ignored** (not present, not absent, never fined). *These ARE the "2 Sundays off."* Governed by the **toggle** in §7.
2. **Discretionary leave: 2 / month, reset monthly.**
   - Within quota → paid, not fineable.
   - **Unused → encashed monthly at 1 day's salary each** (0 taken → +2 days; 1 → +1; 2 → +0).
3. **Festival leave: 2 / year**, spent on the staffer's own festival (no religion encoded → parity). Holi is a *clinic closure*, separate, and does **not** consume a festival leave. **Unused festival leave → encashed at FY close** (1 day's salary each), paid with the Diwali disbursement (§9).
4. **Over-quota leave** (beyond 2 discretionary + 2 festival): **−1 day's salary**, and the **fine is additional and conditional per the already-decided rules** (₹100/day beyond 3 total absents; ₹50 if uninformed). Stacks.

**Plain genuine absent:** existing behaviour only — ₹50 uninformed / ₹100 beyond 3 genuine absents; **no base-pay deduction** (leave days no longer count toward the 3).

---

## 6. Nullification rule

A **leave or absent** day auto-suppresses that date's **dress, i-card, and late** items — you can't fine presence-behaviour on a non-present day. UI greys them; the engine enforces it independently.

---

## 7. Sunday roster — toggle (fresh-month)

- A single **clinic-wide toggle**, **override-controlled** (you / Dr Bhawna), on the Register page.
- **Fresh-month rule:** the roster applies to a month **only if the toggle was ON before that month began.** Flip ON mid-August → August stays roster-free (every day duty); OFF-Sundays start **1 September**. No mid-month math, no already-passed-Sunday retro. Flip OFF → stops from the next fresh month.
- **Pre-condition:** `staff_master.sunday_group` populated for all (July's no-offs gap = groups likely unset). Until populated, the toggle has nothing to apply.

---

## 8. Uniform & i-card issuance

- Tracked in the **Daily Register** store (§3), seasonal: **summer = T-shirt · winter = shirt + blazer/hoodie**.
- **Seeded manually at rollout** from Shavez's existing sheet; **new joiners begin blank**.
- **Ongoing entries: maker (Alisha) → checker (Shavez)** — Shavez does not enter *and* check his own; the one-time backfill may be entered/approved by override.
- **Fine hard-gate:** dress/i-card fine (§4) is only eligible once the matching item is on the issuance record. No record → tick disabled → fine impossible. *This is the fairness lock — you can't fine for an item never issued.*

---

## 9. Incentive → annual pot

- Monthly earned incentive (FULL = 1 day's salary, HALF = ½ day, else ₹0) **no longer hits monthly net**.
- **Accrues into a per-staff pot** over the financial year **Apr 1 → Mar 31**. A bad month contributes **₹0** — floors at zero, **never subtracts**.
- **Disbursed as a lump on the Diwali *following* FY close.** Unused festival-leave encashment (§5) is paid in the same disbursement.
- **Leaver:** the pot is **paid on exit, pro-rated** for the partial financial year (§10).

---

## 10. Staff lifecycle — history-aware record

The staff record gains **dated validity**; for any given day the engine uses the values in force **on that day** (never recompute the past).

- **New joining — join date.** Presence/absence/fines counted **only from the join date**; earlier days are neither present nor absent. First-month base **pro-rated**.
- **Leaving — last-working date.** After it: inactive, no accrual, no fines, off the roster. Final-month base **pro-rated to the last day**; final payout = final salary + leave encashment + **incentive pot (pro-rated, paid on exit)**.
- **Timing / shift change — effective-from date.** **Date-ranged shifts:** only days **from the effective date forward** use the new timing; past days keep the shift they were judged under. No retroactive recompute.
- **Entered on the Register page, override-only** (you / Dr Bhawna), logged with dates + audit trail.

---

## 11. Month-end flow

1. The month's daily rows are already captured + checked.
2. Engine processes them into a **staff-wise summary table** (present/leave/absent, marks, fines, dress/i-card, cover, outstation, encashment, pot accrual, pro-rating).
3. **You do the final sweep** (confirm / override).
4. Confirmed summary feeds the existing **FINAL SALARY** assembly — now on clean data. APPROVE & LOCK unchanged.

No month-end data entry.

---

## 12. Register page (screen)

- **Date selector** — defaults to **today**, steppable to earlier dates.
- **Maker grid** — rows = all staff except Arjun; columns = §4 items as **checkboxes / dropdowns only, zero typing**.
- **Checker view** — the date's entries read-only + a single **Approve** button.
- **Override view** — reverse any cell · ad-hoc fine (₹ + note → ledger) · staff lifecycle (join/leave/timing) · issuance backfill · Sunday toggle.
- Behind portal SSO; roles from `clinic_sso` (add Dr Bhawna override; Alisha maker live; Shivani maker inactive).

---

## 13. Month-summary header renames (plain language)

`>=60min days`→**60+ min late (days)** · `Early-dep minutes`→**Early-out mins** · `Early-big days`→**Big early-exit (days)** · `No-out-punch days`→**No punch-out (days)** · `Ded: marks Rs`→**Late-mark deduction ₹** · `Ded: early-dep Rs`→**Early-out deduction ₹** · `OT cand. minutes/Rs`→**OT unapproved (mins/₹)** · `Months over cap (yr)`→**Penalty months (yr)** · `Net Rs`→**Net adjustment ₹** (single net; unapproved OT excluded).

---

## 14. Build sequence (page-first, per your choice)

1. **Sign off this dossier.**
2. **Data model + Register page** — SQLite store + maker/checker/override screen; test on dummy dates.
3. **Yearly Balances store** — leave counters + incentive pot.
4. **Uniform/i-card issuance table** — seeded from Shavez's sheet.
5. **History-aware staff record** — join/leave/timing, date-ranged shifts.
6. **Engine reads the store** — dress/i-card/leave/cover/outstation/encashment; incentive→pot; single net; header renames; Sunday toggle; lifecycle pro-rating; Shivani ₹200.
7. **Dry-run July + partial August** — verify Shivani cover = ₹800, leave lifts fines, nets reconcile — **before** the first real APPROVE.

Each step: offline build → `py_compile` on `/root/wa/venv/bin/python3` → selftest → install with backup + md5 → confirm live. Same discipline as the portal. **A live Flask change also gets a test-client route hit (200 + expected content)** before delivery (S160 lesson).

---

## 15. Boundaries preserved

F-31 (no salary data in repos/chat) · one-writer-per-store · D254 (register = "informed") · D265 (manager→checker) · Staff Ledger stays the home for advances/loans/perks/ad-hoc fines · uniform/i-card in the Register store, not the Asset Register · frozen products untouched.

---

## Appendix — decision log (all S160)

- Cover-duty ₹200 = **Shivani only** (config exception).
- Absence split: **sanctioned leave vs genuine absent**; leave not fineable.
- Anomalies (EARLY_BIG / brief-presence) → maker-checker, never auto-deducted.
- **Single net**; unapproved OT excluded.
- ₹20 dress + ₹20 i-card; **hard-gated on issuance**; nullified on leave/absent.
- Leave: 2 Sundays (roster) + **2 discretionary/month (reset, unused→encashed monthly)** + **2 festival/year (own festival, unused→encashed at FY close)**; **Holi = clinic closed**.
- Over-quota leave = **−1 day pay + additional conditional fine**; plain absent = fines-only unchanged.
- Incentive → **annual pot, Apr→Mar, paid the following Diwali**; bad month **₹0**, never negative; **leaver paid pro-rated on exit**.
- Outstation **₹250/night** in-system (food/bed out).
- Sunday roster = **override toggle, fresh-month rule**.
- Staff lifecycle = **history-aware, date-ranged shifts, override-only entry**.
- Uniform/i-card **in the Register store** (not Asset Register); **seeded manually** from Shavez's sheet; ongoing maker→checker.
- OT-with-permission = optional, **default-accepted** when ticked.
- Ad-hoc fine = **override-only, flexible ₹ + note → Staff Ledger**.
- New SSO: **Dr Bhawna override**; Shivani maker (inactive).

*— end v1.1 (S161; §5 superseded by the C-model, D279/D280) —*
