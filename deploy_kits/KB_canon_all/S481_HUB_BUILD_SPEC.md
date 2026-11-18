# S481 — Sanjeevni Hub: Days and Cash — the build spec (for the next Sanjeevni session)

**His OK:** 11:59 IST 18-Nov-2026 — "Remaining mockup seems okay to me" on https://claude.ai/artifact/GeKbcmkCgU2KL11vecWk8R (v3, 1794983061-7fb9),
and his ruling on 9-Oct: "it was a typo of receiving the 23,421 cash being handed over. Now that the system is showing the bank settlement
amount 10,163 by UPI, make the necessary changes one time to correct the records."  His words 11:47 / 11:53 recorded below.

## What to build (one kit, or two clubbed: the screen kit and the one-time clean-up)

1. **Day panel (Hub, Days → tap a day)** — `finance_ui/finance_approvals.html` `dayDetail()` + `sanjeevni_day.py` (`/finance/sanjeevni/api/day/<d>`):
   - Without-cash bills: the name EXACTLY as Darpan typed it in Marg beside the bill number ("PROSIJER …", "HOME MEDI …"), then the bill's
     medicines (qty, rate, line value). Typed text: `sale_item_review.guess_name / raw_text.patient_name` (review-queue bills), else
     `identity_resolution.bill_name` / `identity_dispute.bill_name` (S399), else the Marg reading on the spine. Items: from `v.sale.list` by bill.
     NOTE: item `amount` in the day API is the RATE per strip; line value = qty(strips:tabs → strips) × rate (A004799: 3 × 98 = 294 ≈ 293).
   - Sale returns: patient as typed, clinic ID, mobile (his own page: full mobile allowed as on the Patients page), each line's value, and
     the Returns section's own verdict per credit note (`/finance/darpan/api/cn-hub` → `history[]`/rows: `verdict`, `word`, `tone`,
     `approval`, `bought[]`) with the SAME Approve / Reject as `rhRender` — one action, two places (his 11:53 word).
2. **Dr Bhawna's part (Days rows)** — she does not use the app; he stamps "received" for her. Per day: "Received ✓ for Dr Bhawna" beside
   "· not yet received"; a band "N handovers to Dr Bhawna (dd-Mon to dd-Mon) are not marked received · ₹… — Mark all N received".
   The API exists and allows the owner: `POST /finance/darpan/kal/api/received {date}` (darpan_kal.py 817). Live 18-Nov: 14 days 2–16 Nov,
   ₹1,46,756 (17-Nov already received). The owner console line `manoj.cash_received` lists the same rows.
3. **His day entries** (owner only; never on Darpan's/Bhati's screens): "+ Add an entry" on the day panel —
   (a) **Paid into another account** (amount, account, note) — money that never reached the drawer (14-Nov ₹1,580 NK Pathology UPI;
   4-Nov ₹954 UPI into another account); (b) **Cash taken out** (amount, for: personal / clinic expense / other, note) — leaves the drawer
   and counts WITH the doctors (14-Nov ₹4,000 given to Darpan by Dr Bhawna for personal expenses). Removable by him.
   The one calculation is `sanjeevni_cash.days()`; its handovers come from `cash_movement` (out) and `cash_custody_event`; an unknown
   party falls into `pos["bank"]` — do NOT reuse a party name blindly; decide the store so with_doctors / bank stay true.
4. **Cash card — Darpan's drawer** — "why the drawer reads ₹…": each day whose handover was less than its cash, with its cause and the
   actions (Add an entry · Accept (write off)). An ACCEPTED short (`darpan_kal_day.owner_decision='accept'`) leaves the drawer as written
   off (28-Sep ₹680 was accepted and still sits in the drawer — the rule is missing).
5. **Root fix — late bank UPI on an approved day**: `day_resync.py` PASS 1 runs only on UNAPPROVED days; 9-Oct and 14-Oct were approved
   before the bank's MPR came, so they stayed UPI ₹0 and the Hub's cash read ₹10,163 / ₹11,985 high, while Darpan's Kal ka hisaab used the
   bank (expected 13,258 / 21,063). Extend PASS 1 to approved, autofiled, never-person-corrected days (audited, as now) so the Hub and
   Darpan's page never disagree again. Checked on the 18-Nov copy: ONLY 9-Oct (10,163) and 14-Oct (11,985) differ from the bank since the
   anchor (18-Oct and 8-Nov have no statement — Sundays).

## The one-time clean-up (his rulings) — drawer ₹21,512 → ₹49 (round-offs)
| day | cause (his words) | the change | drawer |
|---|---|---|---|
| 14-Oct | bank UPI 11,985 after approval | UPI line → bank; cash 33,048 → 21,063 (handed 21,060) | −11,985 |
| 9-Oct | bank UPI 10,163 after approval; "a typo of receiving the 23,421" | UPI line → bank; cash 23,421 → 13,258; the handover (darpan_kal_day, created_by manoj 10-Oct 09:16, received_by manoj) 23,421 → 13,258, its cover/landing rows to match | ±0 |
| 14-Nov | 1,580 into NK Pathology UPI by a patient; 4,000 given to Darpan by Dr Bhawna for personal expenses | two entries (3a, 3b) | −5,580 |
| 3-Nov | "Sale bill of 1760 I had to delete because a backup person was holding the sales counter" | the day follows Marg: the removed bill leaves the day's sale. Marg watch: billwatch_seen gone A004591 (3-Nov, found 12-Nov 19:32). VERIFY its amount = 1,760 and how sale_bill/day_line still carry it (day revenue 14,936, 14 bills) | −1,760 |
| 4-Nov | "54 was also a UPI done into another account" — read as ₹954 | entry 3a | −954 |
| 28-Sep | accepted short | the accept rule (4) | −680 |
| 17-Oct | 504 short, no reason | left for HIS tap on the Cash card (Accept / entry) | (−504 when accepted) |
Round-offs ≈ ₹46 + 3 remain. Every change audited (audit_log before/after), on the live db only by the installer, after a DRY on a copy.

## Facts measured this session (18-Nov copy, read in the device VM only)
drawer per sanjeevni_cash.days(): residual days 28-Sep 680 · 14-Oct 11,988 · 17-Oct 504 · 3-Nov 1,760 · 4-Nov 954 · 14-Nov 5,580; position
drawer 21,512 · with doctors 4,57,137 · pool −7,26,095 · bank 8,00,000 (the pool figure looks wrong — read before building).
