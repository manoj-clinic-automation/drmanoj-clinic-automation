# S537 — PLAN REVIEW: the morning check, narrowed and automated (D1097)

*The parent, Fable 5.1, 27-Nov-2026 14:xx IST. Reviewed: `S531_MORNING_CHECK_AUTOMATION_PLAN.md` against the live bytes (day_check 946f0408 · register_push 9b1fbc29 · clinic_register ba56418d · not_in_docterz 4ad98ab0 · slip_log 3395e71c · slip_adjust 7d44cf3e · clinic_money 76a05410 · evening_check b3c5bebb) and the 27-Nov 03:18 database copy — `check_day` run on the last 60 days (27-Sep – 26-Nov) in the device VM, counts only. The final plan for Opus is `S537_MORNING_CHECK_FINAL_BUILD_PLAN.md`. Nothing built.*

## 1 · What the 60 days say (the copy; S970's automatic answers were not yet in it)

| measure | count |
|---|---|
| days with a register and a Docterz export | 47 (12 no Docterz = closed days, 1 no register) |
| days clean | 7 · days with any card 37 |
| cards by kind | parchi 43 · **hand 20** · mode 13 · notfound 9 · missing 2 · notbilled 2 |
| hand keys | over 6 (₹5,900 on 5 days) · modeany 4 (₹4,600) · bank 4 (₹2,330) · swap 3 (₹3,000) · regupi 2 (₹1,100) · noid 1 |
| notfound (`nf:`) | 9 days, ₹4,850, ₹200–₹1,000 each — 1 a week |
| days where the one line (`top.left`) is not zero | 16 of 47 |
| back-date rows (his list) | 25 · refunds matched 1 |

So the morning's open work is **one or two lines a day, and the `hand` lines (20) reach nobody** — the plan's gap 1 is confirmed and is the largest.

## 2 · The §6 questions, answered

**Q1 — candidate sources for "money with no slip" (4.4).** On the 9 `nf` days: `xray_filing` rows with no bill — **0 on 8 days, 1 on one** (an X-ray photo with no bill is not the pattern). `patient_visit` (Docterz's clinical export) — a candidate set on every day, **2 to 9 patients**, and it equals the export's own ₹0 lines (free revisits) — the same set, two readings. `dx_visit` the same set but it lagged (20-Nov on a 27-Nov copy; `patient_visit` and `xray_filing` ran to 26-Nov). Of the 2 `nf` days the staff resolved ("found", with a pick), **the picked patient was in the `patient_visit` / ₹0-line set both times**, in the `xray_filing` set neither time. → The candidate list = **the day's Docterz patients with no paid bill** (the export's ₹0 lines ∪ `patient_visit`), 2–9 names; `xray_filing` is dropped; `dx_visit` is not needed.

**Q2 — the rate list.** `slip_item.service_id` → `owner_service` (63 active: 33 X-ray, 30 procedures; `price_p`). **Amounts are ambiguous**: 11 of 20 (kind, price) pairs name more than one service — X-ray ₹500 → 19 services, ₹300 → 5; procedures ₹500 → 4, ₹3,000 → 5; ₹500 and ₹800 exist in both kinds. The section is known from the `nf:` key, the amount is known; the service is NOT derivable. → The late slip needs the patient tap **and** a service tap from the price-filtered list of that section (a list of 1 is pre-chosen); the slip is made through `slip_log`'s own path.

**Q3 — a line twice on one slip.** 15 slips in 60 days (all the slips there are) carry a repeated line (same item words, side blank, always ×2): ILI knee 10, ankle AP/lat 4, wrist AP/lat 1. **In 13 of 15 Docterz billed one line of DOUBLE the price** (both knees, both ankles — legitimate, billed as qty 2); 1 was billed once (a true double — the existing `pdup` card); 1 unclear. On the 13 days the day's money settled without a card for that patient in 11. → **The plan's 4.1 bullet "the extra line marked wrong by itself" is withdrawn**: a repeated line is usually two sides. His 13:38 case (booked twice, one slip) is caught today by `pdup` when Docterz billed once; the uncaught shape is "Docterz billed 2×, the register holds 1×" — that goes to reception as a question, never an automatic mark. The lasting fix is on the slip: the second identical line asks for the side (a parchi-entry note, not this build).

**Q4 — a register edit by staff.** `clinic_register.py` requires `maker` / `checker` of unit clinic — the desk already writes and re-writes it; every save is audited (before/after, who); there is no lock and no owner-only window. → "Theek karein" may be a staff tap through the same save path (audited, Undo = the audited before-values). One guard from the data: when the drawer was counted (`clinic_drawer_day.counted_p`) and agrees with the register's cash, the cash figure is NOT a typo — the tap is offered for UPI/card when the bank proves the figure, for cash only when no drawer count contradicts it.

**Q5 — routing per `hand` key** (the table is in the plan §3): `noid` → Shavez (slip desk) · `over` → the ladder, then reception's one card, then him · `swap` / `modeany` → reception (pick the patient) · `regupi` → Shavez (register one-tap) · `bank` → him only (the bank feed is the suspect; MPR lateness, D-POS stand-in rules) · `s962ans` → him (his own answer).

**Q6 — "Ho gaya" and the ticks.** The per-card ticks (`day_check_tick`) carry the re-export rule: a tick older than the next export whose line still shows comes back as "Phir se". One flat "Ho gaya" would lose which line was fixed and break `not_fixed`. → **No new state**: the staff page gets a "Sab ho gaya" button that writes the existing per-card ticks (act by kind: added / changed / found) in one tap; `_norm` keys and the push logic stay as S968 left them.

**Q7 — the evening.** `evening_check` compares slips with the export only. Payment mode is checkable in the evening from the slip's tick against the Docterz mode: 7 of the 13 morning `mode` cards had a slip tick that already disagreed with Docterz; but the tick alone over-flags (21 single-tender disagreements in 60 days against 13 real cards — 35 more are split payments, not errors). → An evening **question**, not a fault: "Docterz cash, parchi UPI — kaunsa sahi?" one tap for reception, fixing either side; ~2 a week. Put last (K0), after K1/K2 prove, and only when the tick is set (the tick is blank on 953 of 1,168 slips).

## 3 · What changed from S531's plan, and why

1. **4.1 "double line marked wrong by itself" — removed** (Q3: 13 of 15 are legitimate bilateral lines).
2. **4.4 candidates narrowed** to the day's unbilled Docterz patients (Q1); `xray_filing` and `dx_visit` dropped; the service is a tap from a price-filtered list (Q2), not read from the amount.
3. **4.5 ladder re-ordered by what the data shows:** the duplicate-bill step fired 0 of 5 times (kept, it is cheap); **3 of the 5 `over` lines were exactly one consultation fee** → the common card is "one consultation: register wrong, or one patient did not pay — who?" with three answers.
4. **4.2 "Ho gaya"** becomes a one-tap writer of the existing per-card ticks (Q6).
5. **Kit split re-cut** into K1 (route + tell + candidates + breakdown + his push — no new writes) and K2 (the three staff writes), with K0 (evening mode question) last and optional. S531's K3 is folded into K1 (the list) and K2 (the tap).
6. **One check added to K1:** a parchi discount Docterz did not apply shows today as `pshort` + `over`; it is routed as ONE Docterz edit card to reception ("discount Docterz mein bhi lagayein"), not as two cards.

## 3a · His rulings of 14:31 (after the first report) — the plan's v2

1. **"Skip cash to UPI corrections, only revenue mismatch flow to be kept."** The tender split goes: no mode / modeany / swap / regupi / bank card anywhere; the match is register total vs Docterz total (net of refunds). In 60 days that removes 13 mode + 4 modeany + 3 swap + 2 regupi + 4 bank = 26 of the 93 cards and all of the "check by hand" lines but the ladder's end. The bank UPI figure stays on his page as information.
2. **"No corrections in Docterz the next morning; only same-day Docterz edits."** Every Docterz-side shape (a slip Docterz lacks, a Docterz line short of its slip, a line twice, Docterz more than the parchi) moves to the **evening** check on the export (K1 widens S960); the morning makes no `missing` / `notbilled` / parchi card and asks for no Docterz edit — a slip Docterz lacks whose money the register holds is kept outside Docterz by itself (S970, widened). The late slip from a candidate tap is also kept outside Docterz, never back-dated.
3. His word 15:09: the register stays a morning job ("more practical"); the plan is FINAL; the build in a fresh parent chat by Opus, K1 (the evening) first.

## 4 · Not done today (the 28-Nov bundle and copy)

The 27-Nov copy predates S966/S968/S970 (installed 11:25 and 13:10): `register_push` and `nid_mark` tables are not in it, and the DECLARED-PENDING pins wait for the 28-Nov bundle. Item 2 and item 3 of START_HERE_537 (pins, first-days counts) are for the next parent session's open.
