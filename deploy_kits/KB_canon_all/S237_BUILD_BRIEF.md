# S237 BUILD BRIEF — the staff-ledger chapter, and how to close it
**Session 237 · 09–10 Sep 2026 · the one document the next session reads instead of the papers**

> **Next session opens here.** §2 is the worklist. Everything above it is the context that makes the
> worklist make sense; everything below it is the rest of the session's state.

---

## 0 · What S237 was

Three quarters of it was the **staff ledger** — August's salary could not be finalised because the
advances could not be read. It ended with August settled to the rupee, a per-staff statement in
Excel and PDF, an account structure the owner ruled, and **twenty-five faults**, most of them in
machinery that was built correctly and then never told anyone when it did nothing.

The rest: a certificate watcher built and installed, the renewal chain traced and repaired, Rung 1
of the Sanjeevni plan (`sale_bill`) built and installed, and the Marg vendor request drafted.

**Governing ruling of the session, and it outranks everything else here:**

> *"Whatever transactions I submitted to you are the only thing which we can understand out here, and
> I want those to be replicated exactly in our system so that in future there is no confusion whether
> we have to go inside the code also."*

**His record is the authority. Where the ledger disagrees, the ledger is wrong and is corrected to
match — including where that means changing code.**

---

## 1 · Where August stands

| Staff | A · loan | B · interest-free | C · short-term | Total 31-Aug |
|---|---:|---:|---:|---:|
| Darpan | 174,000 | 180,000 | 20,000 | **374,000** |
| Surendra | — | — | 6,000 | **6,000** |
| Shivani | — | — | 1,100 | **1,100** |
| Ranjeet | — | — | 6,000 | **6,000** |
| Sukhveer | — | — | 14,000 | **14,000** |
| Shavez | — | — | — | **—** |
| **Total** | **174,000** | **180,000** | **47,100** | **401,100** |

**Owner's account ruling (10-Sep):** three accounts per staff member, **never pooled** — A the
interest-bearing loan, B the interest-free tranche, C the short-term outstanding — and the
short-term **schedule** shown separately again. Every statement is now built this way.

**Darpan's loan, on his own arithmetic:** original ₹225,000 · 12 instalments to the July salary =
₹59,000 gross = ₹47,000 principal + ₹12,000 interest · so **₹178,000 at 31-Jul**, ₹174,000 after
August's ₹4,000. **The ledger says ₹175,000 — ₹1,000 more.**

**Darpan's forward position:**

| Month | A · loan | C · short-term | Off salary | Take-home on ₹20,000 |
|---|---:|---:|---:|---:|
| September | 5,000 | 12,000 | 17,000 | 3,000 |
| October | 5,000 | 4,000 | 9,000 | 11,000 |
| November | 5,000 | 4,000 | 9,000 | 11,000 |
| December on | 5,000 | — | 5,000 | 15,000 |

**B has no schedule at all**, and nothing collects against it while A runs. A alone is about
forty-four months. On today's terms B does not begin to move until roughly mid-2030. **That is a
terms question for the owner, not a bookkeeping one**, and it is the largest single open item in the
staff-money system.

---

## 2 · ⭐ THE WORKLIST — this is what the next session does, in this order

### 2A · The reconciler (the instrument, built once, run every month)

**What it is.** A read-then-write tool that takes the owner's stated record as its input, reads the
live ledger, prints every difference, and — on a second explicit run — corrects them.

**Why it is first.** Six of the corrections below have **no route through the application at all**
(§2B). Every one of them is a one-off hand-edit if this does not exist, and there will be more
every month.

**Shape, non-negotiable:**

1. **Dry run is the default.** It reads, compares, prints the gap list, writes nothing. No flag,
   no environment variable, no way to write by accident.
2. **`--apply` is a separate deliberate run**, which first takes a dated backup of `ledger.jsonl`,
   writes every row through the module's own `append_ledger()` so the shape cannot drift, and prints
   a before-and-after for the file.
3. **A correction note is written beside the ledger** every time it applies: what was written, on
   whose authority, against which stated list, on what date.
4. **The stated record lives in the tool as data**, not as code — a table it reads, so next month's
   list replaces this month's without touching logic.
5. **Read-only by construction elsewhere:** it never calls `close_month`, never touches
   `salary_final`, never deletes.

**Build it offline against a fixture that carries the LIVE SHAPE** (F-140), py_compile, selftests,
then a live-shape walk on a copy of the real file before it ever runs on the real one.

### 2B · What the reconciler must correct — the exact list

| # | What | Route today |
|---|---|---|
| 1 | **Darpan's loan is ₹1,000 overstated** — ledger ₹175,000, owner's record ₹174,000. One month where interest and principal were split the wrong way. | **no UI route** |
| 2 | **April 2026 is recorded as a formal SKIP** for a month the owner says was paid — and it spent one of the two skips allowed in the financial year. | **no UI route** |
| 3 | **Darpan's ₹8,000 August recovery** (first tranche of the 17-Aug ₹20,000) was never collected — the close took only the loan's ₹5,000. | **no UI route** — August closed 20-Aug |
| 4 | **Darpan's ₹7,000 August recovery** against the 31-Aug ₹15,000. | **no UI route** — same |
| 5 | **Surendra's ₹7,000 August recovery** (₹2,000 + ₹3,000 cleared, ₹2,000 first instalment of the ₹8,000). | **no UI route** — same |
| 6 | **Three rows dated 18/19 August for money given on 17 August**, their narrations contradicting their own dates. | contra + re-enter, or reconciler |

**Item 3 and 4 are time-critical.** `schedule_due_cum()` counts months elapsed since a schedule's
first step and takes that many steps **cumulatively, less what has been recovered**. Darpan's
₹15,000 carries `2026-08:7000, 2026-09:8000`. If August's ₹7,000 is not in the book before the
September close, **September will reach for the whole ₹15,000**, not ₹8,000. The same applies to the
₹20,000 if its schedule is attached: September would reach for ₹12,000 instead of ₹4,000.

### 2C · Two functions to read before anything is built

Both were named but never read this session. Each decides a design question, and guessing either is
how this session lost three hours.

1. **`create_app()`'s advance routes** — can a schedule be attached to an advance **after** it is
   issued? The 17-Aug ₹20,000 has no schedule and cannot be contra'd once it has children. Read the
   routes; if there is no path, the reconciler owns it.
2. **`approve_salary()` (line ~1862)** — does the salary lock accept an **actual-paid** figure that
   differs from the computed one? D332 §2.8 described closing "with actual amounts paid". If it is
   built, a closed month is correctable in cash and half of §2B becomes optional. If it is not, that
   is the single highest-value thing to add.

### 2D · The five system changes, in build order

| # | Change | Why it is where it is |
|---|---|---|
| 1 | **Duplicate warning at entry** — same staff, same amount, same day. | Smallest change on the list. Three duplicate rows went in during August and the owner found them a fortnight later by reading a statement. Removes a whole class of his reading work. |
| 2 | **The close reports what it could not collect**, by name, on the sheet. | August was meant to take ₹13,000 from Darpan and took ₹5,000. Nothing said so. That silence is the root of the entire chapter. |
| 3 | **Narration compulsory on a SPECIAL advance.** | `narr_req` is false for `ADVANCE_ISSUE`, so the one row that most needs a reason is the one row that does not ask for one. The ₹14,000 went in with an empty narration. |
| 4 | **The statement page rewritten** — see §2E. | It is the page the owner and the staff both read, and it is currently unreadable to its own subject. |
| 5 | **A loan-restatement row.** | Checker-only; sets a balance to a stated figure; compulsory written reason; document attached through the D331 upload machinery that already exists; shows permanently on the statement with its date and authority. Over a seven-year contract this recurs, and the choice should never again be between a wrong balance and a hand-edited file. |

**Not in this list, deliberately:** the ceiling percentage (a settings change, not a build — see
§2F), and the `contra_of` overload (F-401, largest, and the ledger is readable through the statement
rewrite meanwhile).

### 2E · The statement page — what is wrong and what it should do

Measured on Darpan's twenty-one rows, 10-Sep.

| # | Defect | Fix |
|---|---|---|
| 1 | **Six rows that cancel each other are shown in full** — three reversed pairs. Nothing is owed on any of them. | Collapse to one greyed line, or behind "show reversed entries". |
| 2 | **Both migrated tranches are dated 7 August**, so ₹183,000 and ₹180,000 read as advances taken in August. | Render under **Brought forward**, above the months. |
| 3 | **Machine-written rows carry row ids and decision numbers** — *"auto instalment for loan b1eb7a8e… (balance after: 175000)"*, *"CONTRA of 540acd6b… (D332 S2.3)"*. | The page knows the category and the parent. Render *"Instalment — interest-bearing loan · balance after ₹175,000"*; keep the id underneath for the trail. **Stored narrations are the audit trail and are never rewritten.** |
| 4 | **Two school-expense perks** (₹13,000 Adarsh, ₹6,000 Angel) sit in the same column as advances and read as ₹19,000 of debt. | Their own section. A perk is a record, not money owed. |
| 5 | **All months show at once**, with mixed date shapes (`2026-04` beside `2026-08-07`) sorting oddly. | Group under the owner's three accounts; month filter default to the current month. |

### 2F · Owner decisions still open

1. **Tranche B's terms.** ₹180,000 with no schedule, untouched until ~2030. The structure will hold
   whatever he decides; right now it holds nothing.
2. **The ceiling percentage.** Darpan's is ₹10,000 and August held ₹35,000, so SPECIAL is the normal
   path rather than the exception — two steps and an "application owed" flag on nearly every entry
   he makes. The gate is working; the number is wrong for the traffic.
3. **The loan workbook** — the evidence for items 1 and 2 of §2B. A restated opening balance on a
   seven-year contract must rest on the document, not on a chat.

### 2G · Three ledger entries the owner may still owe

Confirm at the top of the session before anything else — two were done during S237, the third may
not have been:

- Darpan's ₹15,000 of 31-08-2026 with schedule `2026-08:7000, 2026-09:8000` — **DONE, and the system
  posted ₹7,000 to August and ₹8,000 to September by itself.** First thing all session that behaved
  exactly as designed.
- Shivani's two duplicate ₹1,100 and Surendra's duplicate ₹3,000 — **DONE.**
- **Sukhveer's ₹4,000 of 23-08-2026 — a third advance, not yet entered.** ₹6,000 (10-Aug) + ₹4,000
  (13-Aug) + ₹4,000 (23-Aug) = ₹14,000 in August.

---

## 3 · The rest of S237's state

**Built and installed this session:** `S237_CERT_WATCH` (two-pass TLS check, 10/4-day thresholds
tuned to CyberPanel's measured 15-day renewal window, timer at 06:40 IST) · `S237_SALE_BILL`
(Rung 1 of the Sanjeevni plan — the bill header table; ₹27,375.33 of discount across 524 bills)
· `S237_LEDGER_STATEMENT` (read-only; no `--write`, no `--fix`).

**The renewal chain**, traced end to end and repaired: CyberPanel drives acme.sh and renews at 15
days; its `renew.py` ran **weekly with output discarded**; now daily. Nothing in `/root/.acme.sh/`
is to be removed — it is not dead weight, CyberPanel drives it.

**Still open from before the detour:** Rung 2 (attribute the bill discount to lines — needs T1,
`deploy_kits\S236_DISCOUNT\` published but not installed) · where sale exports live on the VPS
(`sale_bill.py --locate` found none under four candidate roots) · Amir's 12 orthotic rows parked
pending Ram Singh · the Marg vendor request drafted, not sent.

---

## 4 · The four things this session proves about the whole system

1. **A job that reports success is not evidence** (F-386). The August close reported success and
   collected ₹5,000 of an intended ₹13,000.
2. **A gate says nothing about a row that is missing** (F-369). April's paid instalment is absent,
   and nothing anywhere notices an absence.
3. **The obvious folder holds the fossil.** `/root/deploy/repo/staff_ledger/` — and the owner's PC
   clone — hold v3.0 of an app running at v3.6. Hash against the manifest before reasoning from any
   file. **This cost S237 three wrong answers in a row.**
4. **A design signed off is not a design built, and a design built is not a design used.** The
   schedule lane was built at S191 and the box added at S225; the schedule was never attached to the
   one advance it was designed for, and August collected nothing.

---

*S237_BUILD_BRIEF · written at the S237 close · lives in project knowledge, `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S237\`, and loose on the SSD.*
