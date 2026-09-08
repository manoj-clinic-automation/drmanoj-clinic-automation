# THE STAFF ADVANCE POLICY — AS BUILT · v1 · S232 · 08-Sep-2026

**This document describes what the code actually does.** It was rebuilt from
`staff_ledger.py` **v3.6-S225-LOANS-D374** — the bytes that run, verified byte-identical to
the live VPS pin `80257711…` (kit `S225_LOANS_VIEW`) — and from the D331 → D332 → D349 →
D352 → D374 ruling trail.

**It SUPERSEDES `S190_Staff_Advance_Policy_D331.md`**, which is a *design* paper from S190
and was never corrected as the design was built and then amended five times. That paper is
retired in place, not deleted (F-23), with a banner pointing here. **§9 lists every
statement in it that is now false**, because a reader who has quoted it needs to know
exactly what to unlearn.

> **Why this rebuild happened.** The owner said both stored copies were wrong. They were —
> and they were *identical* to each other, in git and in project knowledge, byte for byte.
> **Two stores agreeing is not correctness** (the S231 rule). A byte sweep is blind to a
> document that agrees with itself everywhere and has been overtaken by reality.

---

## 1 · THE CEILING — one rule, derived, never typed

```
ceiling(staff) = floor( base_salary × pct(staff) / 100 / 100 ) × 100
```

- **`pct` defaults to 50** for everybody. Per-staff overrides live in `advance_pct.json`
  beside `users.json`.
- **`base_salary`** comes from `staff_master.csv` — the file the salary side already
  owns. The ledger reads it and never writes it (F-136: derived, never a second copy).
- **Floored to the last ₹100.**

**There is no 75% exception any more.** **D352 (S204) retired Darpan's** — *"darpan was
finally in same 50% rule"*. On a ₹20,000 base his ceiling is **₹10,000**, not ₹15,000.
**And there is no grandfathering: D425 (S232, the owner — *"darpan live at 50% thru august"*) —
₹10,000 bit at once, August included.**
D352 also carries the rule that outlived it: **an exception belongs in a settings row,
never in a code fallback** — a fallback silently re-creates a retired rule on any rebuilt
or restored store, which is precisely how the Sanjeevni side went on allowing ₹15,000
after the ledger had already moved to ₹10,000.

**The gate fails OPEN, deliberately and visibly.** No base salary on file → ceiling 0 →
**the gate is disabled**, shown inline as unenforced. A missing `staff_master` row is a
data gap to fix, not a reason the clinic stops paying advances.

## 2 · WHAT EATS THE MONTH'S QUOTA

An advance counts against the month named by **`against_month`** — the explicit
attribution when present, otherwise the entry's own calendar month. An advance may be
attributed to a **future** month (the owner's 17-Aug device); it then counts against
*that* month's ceiling and does not recover until that month's close. It may **never** be
attributed to a past month — that would re-open a quota already spent.

Counted against a month's quota:

| | counts? |
|---|---|
| APPROVED advances attributed to that month | **yes** |
| **PENDING** advances attributed to that month | **yes** — money asked for is quota spoken for |
| REJECTED | no |
| **interest-bearing loans** | **no** — see §5; they bypass the quota gate entirely |
| rows with **no explicit `against_month`** (pre-D331, incl. the S155 migration entries) | **no — grandfathered** |

**The grandfathering matters and is easy to forget.** The S155 migration rows are dated
August 2026 but represent years of history. Before this rule, Darpan's card read
*"₹3,63,000 of ₹15,000"*. Those rows are visible in the position card and the statement and
they recover normally — **they simply do not eat a current month's quota.**

## 3 · ABOVE THE CEILING — a SPECIAL advance

Entry refuses unless the row is marked `special`, and the refusal states both figures:

> *advance for 2026-09 would be Rs 12,000 against the Rs 10,000 ceiling (50% of base, D331)
> — already taken Rs 0. Above the ceiling it must be entered as a SPECIAL advance, with the
> signed written application uploaded before approval.*

Three properties of a SPECIAL advance, as built:

1. **It is never direct.** A checker entering his own row still lands in **PENDING**. The
   checker's normal direct-entry shortcut is switched off for specials, structurally, so
   the application gate at `decide()` can never be bypassed.
2. **A flag inside the ceiling is discarded.** Mark a row special when it is under the
   ceiling and the flag is dropped — "special" means *above the ceiling*, nothing else.
3. **The signed written application** (Dr Manoj or Dr Bhawna) is stored against the row,
   its **sha256 written into the row itself**, mode 600, under `LEDGER_DIR/applications/`.

### 3.1 · THE PART BOTH OLD COPIES GET WRONG — D374

The S190 paper says, twice and emphatically: *approval refuses without the application on
file. **No escape hatch.*** **That has not been true since 04-Sep-2026.**

**D374 (S225), the owner in his own words — *"make it optional for me, I can add it
later"*** — amends D331:

- The checker **may approve first and attach the paper later.**
- The row then carries **`application_owed = true`**.
- **Every screen showing that advance says "application owed"** until it is cleared.
- Uploading the application clears the flag and records who attached it and when.

**The evidence is still required. Only its timing moved.** The difference between D331 and
D374 is not whether the paper is needed — it is whether the money waits for the paper.
It does not.

## 4 · RECOVERY — four lanes, in this order, under one budget

At each monthly close, advances attributed to that month or earlier are partitioned by
**one function** (`advance_lane`, D349) and collected in this order:

| # | lane | what it is |
|---|---|---|
| 0 | **DEFERRED** | removed first — a deferred advance collects **nothing** this month (§6) |
| 1 | **SCHEDULE** | an advance carrying an explicit repayment schedule collects this month's scheduled amount, in its own lane |
| 2 | **QUOTA** | a D331-era, non-loan advance taken with the default *recover-fully* instalment recovers **in full** at its month's close, in its own lane |
| 3 | **LOAN / WATERFALL** | everything else: the D250 queue — interest first, then interest-bearing principal, then interest-free, overflowing across tranches within the month |

**Precedence is deliberate: schedule BEFORE quota BEFORE waterfall.**

> **D349 exists because this test was written twice.** Once in the close and once in the
> statement page — and the two drifted. The copy that drifted was **the one a human
> reads**: it told the owner that Darpan's ₹20,000 *"recovers in full at the 2026-08
> close"*. It does not; the close takes ₹8,000. Now one function decides what a lane means
> and every surface reads it. **A second copy of a rule is how two screens disagree.**

**The quota lane exists so that a month's own salary money is not queued behind the loan
book.** Without it the owner's ₹15,000 August advance would have waited behind ₹3.59 lakh
of loans — *"waiting for the loan to clear"*, in the statement's own words. A deliberately
**partial** instalment opts the advance back into the waterfall; the entry form's *"blank =
recover fully this month"* is that promise.

### 4.1 · THE CAPACITY RULE — nothing recovers that the salary cannot bear (F-147 / D333)

```
capacity(staff, month) = base − other debits already booked into the month − min_takehome
```

**One budget per staff, spent by every lane in order.** What a lane cannot take is not
lost and not silently dropped: a **`CAPACITY_HOLD`** row is written naming the exact
rupees held, and the money **stays owed and collects later**.

Like the ceiling, this gate **fails open**: no base salary on file → capacity is unknown →
recovery proceeds rather than freezing. `min_takehome` is a setting, not code.

## 5 · INTEREST-BEARING LOANS — the parallel instrument

- **Checker-only to issue.** A maker cannot create one.
- **Flat ₹1,000 per month** while an interest-bearing balance is open. The instalment
  **is** the whole deduction and the interest comes **out** of it — interest first, then
  interest-bearing principal, then interest-free.
- **Instalment minimum ₹1,000** on an interest-bearing loan.
- **Interest stops the moment the interest-bearing tranche clears.**
- **They bypass the ceiling gate and the quota count, both.** A loan is the
  instalment-repayable instrument with its own recovery machinery; it is not a monthly
  quota draw. *(The application requirement for new loans is procedural on the checker
  side, not enforced in code.)*

## 6 · DEFER — the owner-facing verb since D332

**SKIP was replaced by DEFER** (D332 §2.1) as the verb the owner uses:

- The **whole instalment shifts one month**; the schedule extends by one.
- **No automatic capitalisation** — interest rides inside each collected instalment, so
  deferring does not change the loan's total interest.
- **Two free defers per Indian financial year (Apr–Mar).** The 3rd and later carry a
  **₹1,000 penalty on interest-bearing loans only** — and the owner **may waive it at the
  tap**, with a reason, recorded in the row.
- Interest-free advances defer penalty-free, always.

The older **SKIP** survives in the engine for interest-bearing loans (a skip month recovers
nothing and ₹1,000 capitalises; **max 2 per FY**, the 3rd refused) and is also how
historical workbook skips were recorded at migration. **A skip pauses only the waterfall —
the quota lane always collects, because that is the month's own salary money.**

## 7 · WHO MAY DO WHAT

| role | may enter |
|---|---|
| **maker_full** (Shavez / manager) | Night duty · Cover duty · I-card replacement · **Advance issued** |
| **maker_limited** (Alisha / Shivani / reception) | **nothing here** — their work moved to the Staff Register at S162/D286 |
| **checker** (the doctors) | the full list, plus ad-hoc fines, perks and Other |

Interest-bearing loans: **checker only.** System rows — instalment, interest, capitalise,
skip, defer, capacity hold, salary paid — are **machine-made at close and can never be
entered by hand**; they are absent from every role's list, so the entry path cannot create
one. Approved rows are **append-only**; corrections are made by **contra**, and an advance
that already has activity against it cannot be contra'd at all — its instalments are
adjusted instead.

Portal SSO proves only **who** you are; the ledger's own `users.json` still decides **what**
you may do. A manager can never gain checker powers through SSO.

## 8 · THE OTHER BOOK — the Sanjeevni drawer

One man, one ceiling, two systems. The finance side's month-to-date reads the ledger's
JSONL read-only and fail-soft, and counts **only FORWARD-attributed ledger rows**, so the
same rupee can never sit in both counts. If the ledger file cannot be read, the finance
gate degrades to its own rows and **says so on the screen** — *"(Sanjeevni book only —
salary ledger unreachable)"*. It never crashes and never goes quietly.

**Known, documented blind spot:** a same-month direct-pipeline advance is not netted from
the drawer limit. Rare by flow, and the checker sees both books.

---

## 9 · WHAT THE OLD DOCUMENT SAYS THAT IS NO LONGER TRUE

| the S190 paper says | as built |
|---|---|
| *"Darpan's exception: 75%"* · *"₹15,000"* (stated four times, incl. the status banner) | **Retired by D352 (S204). 50% for everyone; ₹10,000 on a ₹20,000 base.** |
| *"`decide(approve=True)` … refuses without the application on file. **No escape hatch**"* (stated twice) | **Amended by D374 (S225). Approve now, attach later; the row carries `application_owed` and every screen says so.** |
| *"a MAKER may draft a special advance … the maker–checker chain"* | True, and incomplete: **a special advance is never direct for anyone** — a checker's own entry also goes PENDING. |
| *"§5.3 STILL OPEN — Darpan's base in `staff_master.csv`"* | **Answered.** ₹20,000, measured on the box at D352. |
| *"Build plan (after the owner's OK — **nothing is built yet**)"* | Built at S190 and rebuilt five times since: SL3 · SL4 · SL6/D332 · D349 · D374. |
| — *(absent entirely)* | **The schedule instrument** (D332 §4): an advance is an amount **plus a repayment schedule**; uneven distributions (8,000 then 4,000 × 3) are the point. |
| — *(absent entirely)* | **The lane rule** (D349) and the deliberate precedence schedule → quota → waterfall. |
| — *(absent entirely)* | **The capacity rule** (F-147/D333) and `CAPACITY_HOLD`. |
| — *(absent entirely)* | **DEFER** replacing SKIP, the 2-free-per-FY discipline and the **waivable** penalty. |
| — *(absent entirely)* | **Grandfathering** of pre-D331 rows — the reason a card no longer reads "₹3,63,000 of ₹15,000". |
| — *(absent entirely)* | **Interest-bearing loans bypass the ceiling gate and the quota count.** |
| — *(absent entirely)* | **Both gates fail OPEN, visibly**, when no base salary is on file. |

## 10 · OPEN — needing the owner's word

1. ~~**D352's own leftover, open since S204**: was August grandfathered at ₹15,000?~~
   **ANSWERED 08-Sep-2026 — D425. No grandfathering: 50% through August, ₹10,000.**
   Nothing recomputes and no row changes — the ceiling gates entry and approval, never
   recovery, so an already-approved August row stays as it is and recovers as it would
   have. **One consequence is worth naming:** D352 measured Darpan's August draw at
   **₹15,000**, so under this ruling it stood **₹5,000 over its ceiling** and would have
   been a SPECIAL advance carrying a signed written application. **D374 is exactly the
   instrument for that** — the application may be attached after the fact, against the
   row, and the row reads *application owed* until it is. Whether to attach one now is
   the owner's call; nothing waits on it.
2. **A stale comment in live code (F-370).** `staff_ledger.py` still carries
   *"pct from advance_pct.json … default 50; **Darpan 75, the owner's ruling**"*. The
   **data** is correct — the box already holds `{"Darpan": 50}` — so **no behaviour is
   wrong**; but the comment contradicts a ruling and will mislead the next person to read
   it. A one-line fix, to ride with the next `staff_ledger.py` kit rather than a trip to
   the box on its own.

---

*Staff Advance Policy — AS BUILT v1 · S232 · 08-Sep-2026. Rebuilt from
`staff_ledger.py` v3.6-S225-LOANS-D374 (`80257711…`) and the D331 · D332 · D333 · D349 ·
D352 · D374 · D425 trail. Supersedes `S190_Staff_Advance_Policy_D331.md`. Trusts neither stored
copy of it — §9 is the list of what they got wrong.*
