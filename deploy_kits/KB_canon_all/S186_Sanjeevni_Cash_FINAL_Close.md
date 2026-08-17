# S186 — Sanjeevni cash: the chain closed by physical count, and a phantom bank deposit removed

**Session 186 · 17 Aug 2026 · AUTHORITATIVE for the Sanjeevni cash close · APPLIED LIVE.**
Supersedes the float sections of `S183_Sanjeevni_Cash_Reconciliation_YesBank`, `S184_Float_Investigation`
and `S186_Cash_Movement_Sheet_Analysis` on every point where they differ.

> **Status corrected at the S186 close.** An earlier revision of this document ended *"no live write was
> made; the migration awaits the owner's go."* That was true when written and false two hours later.
> Filing it unchanged would have been the same fault this session raised three times over — a record
> asserting something nobody re-checked (F-109 / F-112 / F-114). **Kit `S186_C1a` was applied, verified
> 14/14, and the numbers below are the live ones.**

---

## 1. F-112 — a bank deposit that never happened, now removed

The owner supplied the Yes Bank statement for **1 Jul – 17 Aug 2026** (a/c …1923). Its **last
transaction of any kind is 30 July** — no August entries at all.

**The 13 Aug ₹75,000 cash deposit never happened**, yet `S184_C1a` booked it as one of "16 verified Yes
Bank credits (₹16,45,600)".

| | |
|---|---|
| Booked at S184 | 16 deposits · ₹16,45,600 |
| **Truth** | **15 deposits · ₹15,70,600** |
| Effect | cash in hand was understated by ₹75,000 — **corrected by `S186_C1a`** |

The five July deposits on the statement match the S183 list exactly, so the other fifteen stand.

**The record had already flagged this row and it was booked anyway.** S183 wrote, verbatim: *"13 Aug
75,000 is owner-confirmed; it falls after the statement cutoff. Possible gap … check when booking."*
No check was made. The same statement also closes that 31 Jul – 12 Aug gap: nothing happened in it.

**The structural remedy shipped the same session:** `finance_yesbank.py` (kit `S186_R1a`) matches booked
deposits against the statement in both directions and reports a deposit booked where **no loaded
statement reaches** as `deposit_unevidenced` — **never as a pass**. Given the real statement and the
*uncorrected* store it flagged exactly the 13 Aug ₹75,000 and nothing else: 5 matched, 1 caught, zero
false positives.

## 2. The custody model (established from the owner — previously unrecorded anywhere)

- **Darpan's copy resets on the 1st of every month.** The month-end balance is either taken or carried
  into the next month's copy — **and nothing recorded which.** That missing marker is how a float stays
  invisible for five months. It is now a field: `cash_custody_event.month_end_kind`.
- **Dr Bhawna never banks.** Every Sanjeevni bank deposit is made by Darpan.
- **The counter person (Vinay) hands cash direct to Dr Bhawna**, bypassing the drawer — so Darpan's copy
  and the day's collections are *not* the same quantity.
- **Darpan's April 2026 copy opened at ZERO** — owner verified the physical copy.

## 3. The ₹99,017, explained

Cash parked with Dr Bhawna 1–7 April: 24,750 + 9,668 + 13,900 + 12,715 + 23,914 + 14,070 = **₹99,017**
— the exact figure the legacy finance sheet injected on 8 April with no stated source, and the figure
S184 identified as matching the ≈₹85k shortfall. Two records produced independently, agreeing to the
rupee. It was never an accounting artefact; it was the first week's takings, in her hands.

## 4. Darpan's drawer cleared — the arithmetic proved itself

```
copy balance                                    60,198
less 15 Aug Vinay cash → Dr Bhawna              −3,926
less  6 Aug Vinay cash → Dr Bhawna              −7,309
= cash physically in the drawer                 48,963

salary advance adjusted vs July salary          10,000
advance against August salary                   20,000
handed to the owner                             18,963
                                                ──────
                                                48,963     drawer EMPTY, to the rupee
```

The payout lands exactly on ₹48,963, which **independently proves both Vinay handovers left the
drawer** — inferred earlier, unprovable until the notes were counted. **A count beats a derivation.**

## 5. The close, as applied

| Physical cash, 17 Aug | ₹ |
|---|---|
| Darpan's drawer | 0 |
| With the owner | 18,963 |
| With Dr Bhawna | 1,56,235 |
| **Total counted** | **1,75,198** |

| Books once corrected | ₹ |
|---|---|
| App cash-in-hand (confirmed on the dashboard by the owner) | 42,993 |
| plus the phantom 13 Aug deposit removed | +75,000 |
| less the 17 Aug advances to Darpan | −30,000 |
| **Books** | **87,993** |

```
PARKED  =  1,75,198 − 87,993  =  ₹87,205
```

Owner's characterisation: cash **never made to the bank and kept separate as cash-in-hand carried from
the previous financial year**. Booked **once**, narrated as exactly that (**D323**).

## 6. What `S186_C1a` did — APPLIED, verify 14/14

1. Removed the phantom 13 Aug ₹75,000 deposit (**F-112**); originals in `s186_removed_movements`
2. Parked **₹87,205** as one APPROVED, reasoned `cash_adjustment` on the earliest medical day (**D323**)
3. Recorded the 17 Aug physical count **₹1,75,198** in `cash_count` — evidence, kept out of the ledger
4. Recomputed `negative_cash` from `v_cash_ledger`

`day_line` byte-unchanged by sum and row count. Closing **₹42,993 → ₹2,05,198** (→ ₹1,75,198 once
Darpan's ₹30,000 is entered through the app). Backup `finance.db.bak_S186_C1a_20260817_164802`.

⭐ **Open `negative_cash` exceptions: 29 → 0.** S184 proved that booking them away was *mathematically
impossible at float 0* and would need roughly **₹85,000**. The float, established five sessions later
by counting the notes, is **₹87,205**. **A derivation from the books and a count of the cash agreed to
within about ₹2,200.** The exceptions resolved because the missing money was found.

## 7. Owed, and named rather than left silent

- **Darpan's ₹30,000** is not yet entered — blocked on the three scans. **The ₹10,000's category is
  undecided**: free text if it settled July salary, `salary_advance` if it is a new advance. Booking it
  wrong double-counts in his Staff Ledger.
- **Darpan's advances now total ₹70,000** (₹40,000 S184 + ₹30,000 on 17 Aug), resting on an unverified
  claim in a SQL comment — *"tracked in salary system, NOT posted to Ledger."* Nobody has looked. He is
  also skipping an August loan instalment, to be recovered in September. **Check owed.**
- **The custody block on Darpan's entry screen** awaits the Hindi labels. The schema is already built.

---
*S186 · applied live · verify 14/14 · corrected at the close so the record matches the box*
