# D332 — The Waiver, Defer & Repayment-Defined Advance layer · FINAL FOR SIGNATURE
### Session 191 · 19 Aug 2026 · v2, superseding this morning's draft · every ruling below is the owner's, minuted from today's session

**Nothing here is built or entered. Signature makes it D332; the data corrections in §6 run only
after a separate explicit GO.**

---

## 1 · The one-sentence system

**An advance is an amount plus a repayment schedule, defined at approval; the monthly close
collects the schedule automatically; the owner can DEFER any single collection by one tap with a
reason; nothing recovers that the salary cannot bear; and everything owed is always visible with
its months remaining.**

Everything below is that sentence applied.

## 2 · Rulings minuted today (owner, S191)

1. **DEFER replaces SKIP — one verb.** The entire instalment shifts whole; the schedule extends
   one month; no automatic ₹1,000 capitalisation (interest rides inside each collected
   instalment, so total loan interest is unchanged by deferral). **The 2/FY discipline survives
   as a WAIVABLE PENALTY on interest-bearing loans only:** the first 2 defers per FY are free;
   from the 3rd, the defer dialog states "₹1,000 penalty will capitalise unless waived" — one
   checkbox + reason to forgive. The rule attaches to the INSTRUMENT, never the person — today
   only Darpan holds a loan, so it is contextual to him by construction, with nothing named.
   Interest-free advances defer penalty-free always. Deferred months stay loud: red band on the
   Advances card, own statement line, own column on the salary sheet.
2. **July 2026 closes at ₹0 payable for Darpan.** Full ₹20,000 sanctioned, no attendance
   deduction (pre-policy, F-150). The zero is fully composed: − ₹10,000 drawn 31 Jul (absorbed)
   − ₹5,000 loan instalment (already collected at the July close) − ₹5,000 **offset against
   advances given to him before 31 July** (owner ruling: the offset and the instalment together
   complete the netting). Recorded as one adjustment entry narrating the composition, so the
   zero is explained in the book, not remembered. All other staff per the July sheet (per-rules column), pending the owner's waiver
   pass and actual-paid close.
3. **17 Aug consolidates to ONE advance of ₹20,000** (₹15,000 drawer + ₹5,000 given from the
   salary side via Dr Manoj — an adjustment entry at the time; the "against September" booking
   dissolves into it). Booked interest-free with an **owner-set uneven SCHEDULE: ₹8,000 against
   August · ₹4,000 each against September, October, November** — cleared at the November close.
   August retains headroom for the ₹5,000 loan instalment and ₹7,000 drawable. It is above the
   new ₹10,000 cap, so it is booked as **the first SPECIAL under the new rule** — written
   approval scanned against the row (the D331 upload), schedule defined at approval. The
   regularisation is the policy's own worked example, not an exception to it.
4. **Darpan's ceiling: 50% from August** — ₹10,000/month, same as all staff. The 75% exception
   ends. No protected-floor special case (operational friction with old staff); the 50% cap and
   the schedule do the work.
5. **Future Sanjeevni salary-advance flow — request, never draw:** he enters the request on his
   own page (capped inline at ₹10,000, refused past it with both figures); **the drawer is not
   touched**; the owner's single approval tap **releases the cash AND writes the Staff Ledger
   row** — one act, two books, F-148 dissolved structurally. Above the cap = SPECIAL: scanned
   signed application + repayment schedule defined before approval unlocks. **No advance can
   enter the book without its repayment defined** (default: recover in full at this month's
   close).
6. **Mid-month advances close within their month; any excess rolls to the next month's quota**
   (owner ruling, earlier today).
7. **Enforcement is policy, shiftable without touching code (F-150 built as settings):**
   attendance enforcement unlocked by the **notice-served date** (notice not yet shared — no
   promise outstanding); incentive-ladder rungs as dated settings; Sunday policy the same — off
   until switched. July AND August are preview-only months.
8. **Waiver instrument as drafted this morning (4a–4g approved):** WAIVE forgives / DEFER
   postpones, never one button; scopes LINE / STAFF_MONTH / ALL_MONTH; `waiver_authority` seeded
   to Dr Manoj, **Dr Bhawna scoped in but INACTIVE** (owner activates); compulsory written
   reason, no escape hatch; amounts derived, never frozen; own visible column; token-protected;
   append-only, contra-reversed. **Workflow:** salary detail generated → staff corrections and
   requests → owner's final waivers → owner closes with **actual amounts paid**.
9. **Perks:** entry stays one line (a perk is a record, not money owed — no approval chain);
   NEW per-staff **Perks view** with lifetime total and year filter, one click.
10. **Wording (F-151):** "attendance deduction", never "fine", everywhere it renders — D250's own
    statutory caution, currently violated by the live column header and the salary-page help text.

## 3 · Darpan's schedule, resulting (owner's distribution)

| Month | Loan | Advance (₹20,000, scheduled) | Take-home |
|---|---|---|---|
| Aug | ₹5,000 | **₹8,000** (against Aug) | **₹7,000** |
| Sep | ₹5,000 | ₹4,000 | ₹11,000 |
| Oct | ₹5,000 | ₹4,000 | ₹11,000 |
| Nov | ₹5,000 | ₹4,000 — **cleared** | ₹11,000 |
| Dec → | ₹5,000 | — | **₹15,000 steady** |

**8,000 + 4,000×3 = 20,000 · August: 8,000 + 5,000 + 7,000 = the full 20,000 accounted.**

Any single month: one DEFER tap shifts that collection whole. New requests while this runs:
within the ₹10,000 cap and subject to approval as always — the checker sees the open schedule
inline when deciding.

## 4 · What already exists vs the one recovery gap

Named-instalment advances, maker–checker, the application upload, `against_month`, the approvals
console, the close — **all standing (D258/D331)**. For eleven of twelve staff the waterfall
already recovers a named instalment correctly, because with one open item the budget IS its
instalment. **The single gap:** when a loan and an advance coexist, the budget is set by the
loan's instalment and the advance collects nothing behind ₹3.59 lakh. **Fix (the only
recovery-side code in this design):** every interest-free advance carries a **repayment
SCHEDULE** — by default uniform (the named instalment), optionally an owner-set uneven
distribution ("₹8,000 → ₹4,000 → ₹4,000 → ₹4,000") — and the close collects the current month's
scheduled amount **in its own lane**, beside the waterfall; the waterfall keeps the loan book.
A uniform instalment and SL4's recover-in-full are both special cases of the schedule — one
generalisation subsumes everything. **Sequencing note:** the ₹8,000 August collection needs only
SL4's existing lane; the schedule's first ₹4,000 collects at the SEPTEMBER close — so this build
does not block the August close.

## 5 · Build plan

| Kit | Contents |
|---|---|
| `S191_SL5` (ledger) | the waiver instrument (§2.8) · policy-date settings incl. notice-served unlock (§2.7) · wording fix F-151 |
| `S191_SL6` (ledger) | DEFER replaces SKIP + the waivable 3rd-defer penalty on loans (§2.1) · the schedule lane incl. uneven distributions (§4) · capacity rule — never recover more than the salary bears (F-147) · loud-defer surfaces · schedule display: every open item shows amount · schedule · recovered · months left · next collection |
| `S191_SL7` (ledger) | per-staff Perks view (§2.9) |
| `S191_F6` (finance) | the request-not-draw flow (§2.5): request row, inline cap, approval writes both books in one act (F-148) |

Each: offline rehearsal on a store carrying the live SHAPE (F-140), projection written before
measuring, D317 kit chain, PUBLISH_ALL.

## 6 · Data corrections — GATED, run only on explicit GO, before the August close

1. **₹10,000 `fbd756fe1473`** — contra, narration "settled inside July 2026 salary (owner ruling
   S191)". *Without this the August close collects it a second time.*
2. **₹15,000 `540acd6b8e7c` + ₹5,000 `d6162b009451`** — contra both; enter ONE ₹20,000 SPECIAL
   advance dated 17 Aug, schedule ₹8,000 (Aug) + ₹4,000 × 3 (Sept–Nov), owner's signed approval
   scanned against the row. Until SL6 lands, the same distribution is achievable as two rows
   (₹8,000 against-August recover-in-full + ₹12,000 @ ₹4,000 from Sept) — owner's pick at GO.
3. **July adjustment entry** — one entry narrating the full zero composition: ₹10,000 drawer
   draw absorbed · ₹5,000 loan instalment collected · ₹5,000 offset against pre-31-July advances.
4. **`advance_pct.json`: Darpan 75 → 50** (on-box, one line).
5. **July salary close** — per the sheet, owner fills waivers + actual-paid, then closes.

Order matters: 1–4 before the August close; 5 whenever the owner finalises the sheet.

## 7 · Findings riding with this design

**F-147** capacity rule (build) · **F-148** drawer→ledger bridge (build the request flow + test)
· **F-149** perks route unreachable (corrected by defer-not-skip + perks view) · **F-150**
policy dates as settings (build) · **F-151** "fine" wording (correct). Numbers subject to the
owner's F-141 ruling still pending from S190.

---

*v3 FINAL — AGREED BY THE OWNER (S191) with the three §2.1/§2.3/§4 refinements minuted at agreement. · Session 191 · becomes D332 on the owner's OK. Supersedes v2 in place.
Companions: `S191_Darpan_Money_Model_Objective_Report.md` · `Salary_July_2026_for_finalisation.xlsx`
(kept out of the public repo, F-31/D320).*
