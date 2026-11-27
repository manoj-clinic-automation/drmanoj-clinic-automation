# S537 — THE MORNING CHECK — FINAL BUILD PLAN FOR OPUS (D1097; his rulings of 14:31 and 15:09 27-Nov) — FINAL

*The parent, Fable 5.1, 27-Nov-2026, FINAL at his word 15:09 ("finalise now and build in fresh chat"). Review: `S537_PLAN_REVIEW.md` (v1 of this plan is superseded; its §2 routing of payment-mode lines is withdrawn). The build: a fresh parent chat, Opus, K1 first. Owner's words that govern: **14:31 — "skip cash to UPI corrections, only revenue mismatch flow to be kept; I don't want any corrections in Docterz the next morning etc, only same-day Docterz edits should be there"**; 13:36 (register more → slips → show how it matched; register less → refunds and cancellations); 13:44 (not cumbersome for staff; settled in minimum time, maximally automated); 03-Sep (no technical questions to him). Nothing built; his look at the staff screen mock-up v2 before K2.*

## 1 · The shape — two moments, nothing in between

**Evening (same day, on the export — the S960 road, widened):** everything that is a *Docterz* matter is found and fixed the same evening by reception, while the patients are still fresh: a slip Docterz does not carry (live), a Docterz line short of its slip (parchi discount not applied), a slip line Docterz lacks, a line billed twice against a single slip line. A corrected export clears the list (live). **After this evening, Docterz is closed for the day: the morning never asks for a Docterz edit.**

**Morning (on the register Save — the S968 road): money against money only.** Register total (net of refunds, as written) vs Docterz total (net of radd, S962). No tender split; no payment-mode card of any kind.
- **equal** → "✓ sab mile" with the breakdown, for everyone;
- **register MORE** → the slips kept outside Docterz explain it (S970, live, by itself) → else a late slip is made from a candidate tap and kept outside Docterz (never a back-date, never a Docterz edit) → else "register galat" (one tap) → else his push;
- **register LESS** → refunds / radd (live) → the ladder (§3) → his push "₹X unexplained (cash short)".

**He gets one push, only for what nobody could explain.** The bank's UPI figure and the per-tender view stay on his own page as information, never as a card or a push.

## 2 · K1 — THE EVENING WIDENED (server; `evening_check.py` b3c5bebb + `parchi_desk.py` 08680822; reads `day_check`'s parchi rules)

Today the evening names only the slips the export does not carry. K1 adds, from the same export and the same slips (no register needed), as lines on the same evening push and the desk panel, each with its one tap:
1. **Docterz line short of the slip** (`pshort` shape; the parchi discount not applied): "<patient>: parchi ₹400, Docterz ₹500 — Docterz mein chhoot lagaiye";
2. **a slip line Docterz lacks** (`part` / `add` shape, the patient IS in the export): "<patient>: X-ray ₹500 parchi par, Docterz mein nahi — bill mein jodiye";
3. **a line billed twice against one slip line** (`pdup` shape, Docterz 2× vs slip 1×): "<patient>: Docterz mein do baar, parchi par ek — dono taraf hua tha? [Haan, parchi theek karo] [Nahi, Docterz se ek hataiye]" — the only two-way question; its answer writes either the slip's second line or a Docterz to-do; never automatic (13 of 15 repeated slip lines were bilateral — review Q3);
4. **Docterz has more than the parchi** on a patient who has a slip (`pover` shape): "<patient>: Docterz ₹1,000, parchi ₹500 — kaunsa sahi?" [parchi mein jodiye] [Docterz theek karein].
Each line is cleared by the next export (the rule that already clears missing slips) or by the slip-side tap. The evening push stays ONE push per export; the "sab theek" push when a corrected export clears all. Payment mode is NOT compared (14:31).

**Walks:** fixtures for each of the four shapes + a clean export; a corrected export clears each; a mixed export; control red. **Live shape (copy, counts):** the last 30 evening exports replayed — how many lines each shape would have raised, 0 errors; the four shapes together ≤ the morning's parchi cards of those days (43 in 60 days).

## 3 · K2 — THE MORNING AS A REVENUE MATCH (server; `day_check.py` 946f0408 + `register_push.py` 9b1fbc29 + the staff page)

- **K2.1 One figure.** `check_day` compares `sum(register)` with `sum(Docterz net of radd)`; the tender loop, the mode move, `swap:`, `modeany:`, `regupi:`, `bank:` cards are **removed from the cards** (kept as figures in `totals` for his page). `missing` / `notbilled` cards (Docterz edits) are **no longer made in the morning**: a slip Docterz lacks whose money the register holds is answered "kept outside Docterz" by itself (S970, live) — K2 widens S970 to the rows it still leaves (the part-held row, the row not on his list) with the same Undo rule.
- **K2.2 Register MORE, unexplained** (`nf:` today): the card lists the day's Docterz patients with no paid bill (2–9; the export's ₹0 lines ∪ `patient_visit`; review Q1) → tap → the service from the price-filtered list of that section (1 = pre-chosen; review Q2) → the late slip is made by `slip_log`'s own path, dated that day, **marked "kept outside Docterz"** at once (nid 'outside', Undo final) → the match settles. Second tap: "Register galat likha" → K2.3. Third: "Pata nahi" → his push.
- **K2.3 Register LESS — the ladder, stopping when explained:** refunds / radd (live) → **the gap equals exactly one bill of one head** (3 of 5 in 60 days = one consultation fee): reception's card "15 bill × ₹600, register ₹8,400 — [Register galat tha → ₹9,000] [Ek mareez ne paise nahi diye — kaun?] [Pata nahi]"; "kaun" lists the head's patients; the pick marks that bill **money never taken** on the slip side (the existing radd 'money never taken' record — a slip-side mark, not a Docterz edit) → still unexplained → his push.
- **K2.4 "Theek karein" (the register):** through `clinic_register`'s own save, audited, Undo = the audited before-values; guard: not offered for cash when `clinic_drawer_day.counted_p` exists and equals the register's cash. The Save re-runs the push (S968), which then clears itself.
- **K2.5 The breakdown for all** (`top`, exists): staff page + clean push: "Register ₹7,700 = Docterz ₹7,600 + parchi bahar ₹100 − wapas ₹0 · 22 mareez mile"; English on his page.
- **K2.6 His push** (the S962 road, login manoj, his devices only, once per day per key; `register_push.owner_sent`, one additive column): "26-Nov: ₹600 unexplained (cash short) — staff: don't know" · "26-Nov: your answer on slip 123 (kept outside) — the register does not hold it" · "26-Nov: ₹500 slip made for <ID>, kept outside Docterz" (information, so his list stays his).
- **"Sab ho gaya"** on the staff page writes the existing per-card ticks (no new state; the re-export rule untouched).

**Walks:** equal / more / less fixtures; S970 widened rows (part-held, not-on-list) answered with Undo final; candidates = ₹0 lines ∪ patient_visit − paid; the late slip refused for a patient already billed, a service not at that price, a day older than STAFF_DAYS (7); the ladder stops at each rung; drawer guard (3 fixtures); his push once per key; no card of kind mode anywhere (a mutant that re-adds one goes red); S968/S970 walks regression. **Live shape (copy, counts):** 60 days re-run — cards fall from 93 to ≤ 25 (the 9 `nf`, the 5 `over`, the back-date rows that still need him), 0 errors; the 2 resolved `nf` days reach the picked patient; the 2 `regupi` days suggest the Docterz figure. **Rehearsal** as S968/S970 (dry · red · install · again · undo · wrong FROM).

## 4 · The words (staff Hindi · his English)

- evening push (reception), one per export: "26-Nov shaam: 3 kaam Docterz mein — <patient>: ₹500 X-ray parchi par, bill mein jodiye ; <patient>: chhoot ₹100 lagaiye ; <patient>: do baar bill — dono taraf hua tha?" · clear: "✓ 26-Nov: Docterz aur parchi sab mile".
- morning push, clean: "✓ 26-Nov: sab mile — Register ₹7,700 = Docterz ₹7,600 + parchi bahar ₹100".
- morning push, open: "26-Nov: 1 kaam — ₹500 X-ray cash register mein hai, Docterz mein nahi — kiska tha?".
- `nf` card: "₹500 X-ray cash — register mein hai, Docterz mein nahi. Kal ke bina-bill mareez: [A (1234)] [B (2345)] [C (3456)] — jiska hai use chhuein (parchi ban jaayegi, Docterz mein nahi likhni) · [Register galat] · [Pata nahi]".
- register-less card: "Docterz mein consultation ₹600 zyada (15 × ₹600 = ₹9,000; register ₹8,400). [Register galat tha → ₹9,000] [Ek mareez ne paise nahi diye — kaun?] [Pata nahi]".
- his push: "26-Nov: ₹600 unexplained (cash short) — staff: don't know" · "26-Nov: ₹500 slip made for 4471, kept outside Docterz".

## 5 · Order, model, gates

K1 the evening (Opus) → his look at the staff-screen mock-up v2 → K2 the morning (Opus). Each kit: board PLANNED line · built on the newest bundle's bytes · walks + control red · live shape on a copy (counts, sums compared, never a unique-amount assumption — F-1718) · cold review + second look by sub-agents · placed · his publish + one server line · DECLARED-PENDING until the next bundle. D656 throughout. A-D149, A-D153 stand. **K2 lands only after K1 has run live for at least 3 evenings with exports** (the morning stops asking for Docterz edits only once the evening is proven to catch them).

## 6 · The register stays a morning job (his word 15:09: "morning for register work is more practical")

The Save stays the next morning; the revenue match runs on it (K2). The evening (K1) does every Docterz matter on the export; nothing of the register is asked in the evening. Settled; not to be raised again.

## 7 · Not in this build (noted)

The slip entry asks for a side when a second identical line is written (parchi-entry, Shavez's screen) · the Morning Match part 2 (the register's own refund line — his look first) · the new-number screen · F-1720 (BSUID-only STOP in `wa_ladder` m10) · the per-tender and bank views on his page (unchanged, information only).
