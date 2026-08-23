# S192 · THE GATED DATA CORRECTIONS — EXECUTED
### Session 192 · 19 Aug 2026 · D332 §6 items 1–4 · owner's explicit GO, after a read-only survey and a dry run

> **Live money data.** Nothing here was written until the owner had seen a read-only survey of the
> real rows AND a dry run printing every intended write. The survey is what made the correction
> safe — the S184 precedent (a survey is the only reason a ₹16 lakh double-count did not happen).

---

## 1 · What the survey established BEFORE anything was written

- All three target rows were **APPROVED, un-collected, `recovered: 0`, with NO children** — so the
  code permitted a contra (`make_contra` refuses once an advance has recovery activity).
- **`2026-08` was NOT closed** (`ledger_closed=False`), so **the ₹10,000 tripwire was live and real**:
  at the August close, `fbd756fe1473` (against 2026-07, quota lane, `instalment == amount`) would
  have recovered in full — collecting money the owner had already settled in cash in July. Caught in
  time.
- `2026-07` ledger **was** closed; July salary **not** locked.
- Darpan's ceiling was still **75% = ₹15,000**.
- The loan book confirmed as the two documented tranches: `b1eb7a8e419e` ₹1,83,000 (bal ₹1,79,000,
  interest-bearing) + `f9f60e18fd5e` ₹1,80,000 (interest-free) = the ₹3.59 lakh.

## 2 · The six writes, as committed

| # | Action | Row created |
|---|---|---|
| 1 | **CONTRA ₹10,000** `fbd756fe1473` — *"settled inside July 2026 salary (owner ruling S191)"* | `c287af8feea5` (−10,000) |
| 2 | **CONTRA ₹15,000** `540acd6b8e7c` — consolidated into the single SPECIAL | `aba609b148ee` (−15,000) |
| 3 | **CONTRA ₹5,000** `d6162b009451` — consolidated into the single SPECIAL | `9b8462f9ac2e` (−5,000) |
| 4 | **`advance_pct.json` Darpan 75 → 50** — ceiling ₹15,000 → **₹10,000**; the 75% exception ends (D332 §2.4) | file |
| 5 | **ONE ₹20,000 SPECIAL**, dated 2026-08-17, against 2026-08, **schedule 8,000 (Aug) + 4,000 × 3 (Sep/Oct/Nov)** | `0cc0b26b38c5` — **PENDING** |
| 6 | **₹0 record-only entry** dated 2026-07-31 narrating the July zero composition | `791d321b9dd4` |

**Each contra was stamped with the original's `against_month`** so the month's quota reads correctly
— see §4.

## 3 · Verified independently after the write (not asserted)

The same read-only survey was re-run:

- all three originals now carry their contra child (`−10000` · `−15000` · `−5000`), `recovered: 0`;
- **Darpan's open advances are now ONLY the two loan tranches** — the three quota rows are gone;
- `pct=50  ceiling=10000`;
- `advance_month_taken("Darpan","2026-08") = 20000` against a ₹10,000 ceiling — correctly above it,
  which is precisely why the new row is a SPECIAL;
- `0cc0b26b38c5` is absent from open advances **because it is PENDING**, which is correct: an
  unapproved advance is not an open advance.

**The July zero, now explained in the book rather than remembered** (row `791d321b9dd4`): ₹20,000
sanctioned, no attendance deduction (pre-policy, F-150); less ₹10,000 drawn 31 Jul (absorbed), less
₹5,000 loan instalment collected at the July close, less ₹5,000 offset against advances given before
31 July. **Recorded at ₹0 — it moves no money**, deliberately: July's ledger is already closed, so a
real movement would have been collected in *August's* close, which is not what the ruling intends.
Owner informed of the alternative and chose the record.

## 4 · CANDIDATE FINDING F-152 — a contra does not carry the original's attribution

`make_contra` copies category, staff, dates and the negated amount, but **not `against_month`**. A
reversed advance therefore keeps consuming its month's quota: Darpan's August quota would have read
**₹35,000 instead of ₹20,000**, and a future above-ceiling refusal could fire on money that had
already been reversed — a gate firing wrongly, the failure mode D316 warns is worse than no gate.
Worked around in the correction script by stamping `against_month` onto each contra row (visible in
the dry run before it ran). **The gap in `make_contra` itself is still open.** Fix is one line in the
contra row builder. Kin of the F-45/F-100 family; **owner's to mint — next free is F-152.**

## 5 · WHAT REMAINS ON THE OWNER

1. **Upload Darpan's signed written application** against row `0cc0b26b38c5` (`/ledger/pending` →
   open the row → attach), **then approve it**. The D331 gate has no escape hatch: it cannot be
   approved without the scan.
2. **If the ₹8,000 is to be collected in August, this must happen BEFORE the August close.** An
   unapproved advance collects nothing; the schedule's first step would simply shift.
3. **July salary close** (§6 item 5) — whenever the owner finalises the sheet with waivers and
   actual-paid. (`Salary_July_2026_for_finalisation.xlsx` stays owner-side, out of the public repo,
   F-31/D320.)

## 6 · What the August close will do, once the SPECIAL is approved

| Line | Amount |
|---|---|
| Schedule lane — step 1 of the ₹20,000 | **₹8,000** |
| Loan waterfall instalment | ₹5,000 |
| **Take-home** | **₹7,000** |

Exactly the table in the signed D332 contract (§3). The capacity rule (F-147) is not binding here:
₹13,000 of recovery against a ₹20,000 base.

Remaining schedule: ₹4,000 at each of the September, October and November closes — **cleared at the
November close**, then ₹15,000 steady from December (less the ₹5,000 loan instalment).

---
*Executed at S192 after survey → dry run → owner's explicit GO. Session 192.*
