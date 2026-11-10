# S421 — Why fewer patients come back (10-Nov-2026, the parent) — counts only, no patient data

Sources (read on manojz, aggregates only): follow-up tracker data folder (visit_ledger to 09-Nov, followup_ledger due dates Jun-Oct with status, patient_diagnosis 7,618 patients with the taxonomy category, last ingested 24-Oct, outbound_log calls to 07-Nov); finance_nightly 10-Nov (visits, day sheet).

## 1. Returns by gap (visits whose 30 days are over)
| month | back <=7 d | back 8-30 d | total |
|---|---|---|---|
| Jun | 35% | 26% | 61% |
| Jul | 32% | 23% | 55% |
| Aug | 32% | 19% | 52% |
| Sep | 33% | 15% | 48% |
| Oct 1-10 | 29% | 17% | 46% |
Not an identity artifact: keyed by mobile instead of patient ID gives the same figures. 60-day returns fall too (65, 60, 57%).

## 2. Follow-up dates given in Docterz (followup_ledger, by due month)
| due | n | on time | late | never | called (outgoing, due-2..due+21) | came if called | came if not called |
|---|---|---|---|---|---|---|---|
| Jun | 373 | 43% | 22% | 35% | 92% | 65% | 65% |
| Jul | 494 | 32% | 26% | 41% | 67% | 64% | 48% |
| Aug | 436 | 28% | 25% | 46% | 72% | 61% | 35% |
| Sep | 426 | 25% | 21% | 54% | 60% | 53% | 35% |
| Oct | 392 | 26% | 12% | 61% | 64% | 45% | 27% |
Connected calls to those patients: 277, 238, 196, 166, 166. Outgoing+incoming call log by month: 884, 874, 715, 626, 525. (Oct "never" still open for late returners.) Called-vs-came is an association, not proof.

## 3. By diagnosis group (follow-ups due Jun-Oct)
| group | due | on time | late | never | called |
|---|---|---|---|---|---|
| New patients since July — no diagnosis on file | 905 | 31% | 14% | 55% | 63% |
| Rheumatology | 269 | 28% | 37% | 35% | 71% |
| Degenerative joint (OA) | 202 | 23% | 28% | 49% | 72% |
| Trauma | 169 | 45% | 24% | 31% | 80% |
| Radicular spine | 156 | 30% | 24% | 46% | 81% |
| No diagnosis recorded | 104 | 31% | 13% | 56% | 76% |
| Degenerative spine | 69 | 32% | 25% | 43% | 78% |
| Mechanical spine | 60 | 27% | 20% | 53% | 82% |
8-30 day review by visit month (established patients): OA 37 -> 31 -> 22 -> 12%; Rheumatology 32 -> 29 -> 30 -> 24%; Trauma 30 -> 27 -> 38 -> 11% (Sep n=19).

## 4. Mix
Patients first registered after June (not in the diagnosis file; their mobile also unknown to it): Jul 113, Aug 194, Sep 189, Oct 169. Their 8-30 day return 13-16% against 26-30% for established patients (Jul-Aug).

## 5. Gap found
The diagnosis file has no patient registered after June: 735 of the 1,305 patients seen Jun-Oct (and 905 of 2,121 follow-ups) carry no diagnosis. Docterz CLINICAL exports (the only ones with a Diagnosis column) were taken 3 times (Sep, Oct). The console's diagnosis view needs a daily diagnosis feed.

## 6. Owner's ruling 08:08 IST: June unreliable; use Aug-Oct only, allow for festivals
Per open day (Mon-Sat): visits Aug 23.7 · Sep 22.1 · Oct 19.0 · 1-9 Nov 13.7. First-ever patients/day 7.5 · 7.3 · 6.3. Reviews (prior visit within 60 d)/day 13.8 · 12.0 · 10.7. Old patients back after >60 d: 63 · 73 · 56. Paid consultations 431 · 393 · 370.
Weekly visits/day: Aug 20-25; Sep 21-24 (the Pitru Paksha week from 28-Sep still 24.0); from 5-Oct 17-20 (Navratri 11-20 Oct, Dussehra 20-Oct, Karwa Chauth 29-Oct); 2-Nov week 14.0 (Dhanteras 6-Nov, Diwali 8-Nov). Festival dates: hindupad.com 2026 list.
Reading: Aug->Sep reviews fell 13% while new patients held and the weekly rate held -> not festival. Oct fell across new and reviews alike -> festival season likely. Follow-ups due Aug/Sep/Oct: on time 28/25/26%, never 46/54/61% (Oct still open), called 72/60/64%, came if called 61/53/45% vs not called 35/35/27%. No earlier year to compare a festival October against.

## 7. CORRECTION + the calling list is partly stale (09:5x IST, owner's ask 09:44)
The tracker's own statuses undercount returns. Two rules in followup_ledger: (a) a visit 1-3 days BEFORE the due date is not counted as a return; (b) one visit closes only one follow-up row - when a patient has two rows (an older overdue one and the new one), the visit closes the older row ("Returned Late") and the new row stays "Actionable Missed".
Aug-Oct "never came" rows (665) with a visit by the SAME patient ID anyway: 130 (96 came 1-3 days early, 22 within a week of due, 9 later).
Recounted by patient ID (on time = due-3 .. due+7; late = +8..+30): Aug n425 on time 53% late 9% never 38% | Sep n421 48% 8% 44% | Oct n392 46% 4% 14% (143 still open). Called 73/61/64%; came back if called 68/62/56% vs not called 46/47/39%. (Section 2's 28/25/26% on time is the tracker's strict status - superseded by this.)
OPEN calling list 10-Nov (ledger 20:30 IST 09-Nov): Due Today 6, Grace Period 8, Actionable Missed 49, Identity Unresolved 8, Invalid mobile 3. Same patient ID already visited: 16 (12 came 1-3 days early; 4 visited on/after due but the visit closed an older row of theirs). A further 9 match a visit by name or mobile only (possible re-registration).
