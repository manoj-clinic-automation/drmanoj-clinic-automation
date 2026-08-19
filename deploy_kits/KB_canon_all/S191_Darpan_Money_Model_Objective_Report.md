# Darpan — how his salary, advances and instalments are actually managed
### An objective report, read off the live systems and the canon · Session 191 · 19 Aug 2026

**Method.** Every number below was read today from the running systems, not from the record.
`staff_ledger.py` on the box was proved by `verify_live_pins.py` to be `470bb113…`, and the
`S190_SL4` kit payload hashes to exactly that — so the code quoted here is the code that runs.
The live position came from the Staff Ledger's own statement, advances, book and salary pages.
Where the canon and the machine disagree, that disagreement is reported as a finding, not
smoothed over.

---

## 1 · What his exception actually is

Darpan is not "a staff member with a big advance". He is the only person in the practice whose
money runs on a **purpose-built instrument**, ruled in **D250** and moved wholesale into the Staff
Ledger by **D258**.

**D250 — Darpan financial systemisation.** Adopted from the paper ledger as at 31-Mar-2026,
tracking from Apr-2026:

- A **two-tranche long-term loan**: one interest-bearing at a **flat ₹1,000/month** (≈6.3% p.a. at
  adoption — the flat amount never recalculates; it stops the moment that tranche clears; an
  unpaid month capitalises the ₹1,000 onto the principal), plus an **interest-free tranche**.
- A **waterfall**: recovery pays interest first, then interest-bearing principal, then
  interest-free principal.
- **Two skips per Indian FY** (Apr–Mar). *Third onward auto-flags recovery from perks.*
- **Short-term (ST) advances**: recovered from that month's salary, rarely carrying 2–3 months.
- **A salary-day order**: *ST-recovery, then instalment, then attendance deductions — and if the
  salary cannot bear all of it, **the instalment skips** and the tracker prices it.*
- Every ad-hoc rupee classified (Perk / ST-Advance / ST-Recovery / Skip-Recovery), dated,
  narrated, kept longitudinally. Outstation allowance paid in cash at trip end.
- A printable signed schedule card as the standing answer to ad-hoc demands.

**D258 — one home per rupee.** From the verified migration of 07-08-2026, the Staff Ledger owns
all of it. The workbook's five Darpan sheets (Loan Master · Repayment Tracker · Schedule Card ·
Perks & ST-Advance Ledger · Outstation Log) are **retired — frozen history, never filled again**.
The workbook now only computes salary. Loan repayment is **never typed**: the monthly close
generates it. A skip is a button, never a ₹0 entry.

**D331 (S190)** then added the ordinary-quota layer that applies to everyone, with Darpan's
exception written into it: a derived monthly advance ceiling of **75% of base** where all other
staff get 50%. On a ₹20,000 base that is **₹15,000/month**.

---

## 2 · His live position, to the rupee, as of today

| | |
|---|---|
| Base salary | **₹20,000/month** |
| Advance ceiling (75%, D331) | **₹15,000/month** |
| Interest-bearing tranche outstanding | **₹1,79,000** |
| Interest-free tranche outstanding | **₹2,10,000** |
| **Total owed** | **₹3,89,000** |
| Perks given (outside salary, not recoverable) | ₹19,000 — two school-expense items |
| Skips used FY2026-27 | **1 of 2** (2026-04) |
| Recovered so far | ₹4,000 principal + ₹1,000 interest (the July close) |

**The five open items and what each one does at a close:**

| Item | Amount | Lane | Recovers |
|---|---|---|---|
| Loan (interest-bearing) | ₹1,79,000 left | waterfall | ₹5,000/month **inclusive** of ₹1,000 interest |
| Migrated interest-free tranche | ₹1,80,000 | waterfall | nothing until the loan clears |
| Advance, against **July** | ₹10,000 | quota lane | **in full at the August close** |
| Advance, against **August** | ₹15,000 | quota lane | **in full at the August close** |
| Advance, against **September** | ₹5,000 | quota lane | in full at the September close |

---

## 3 · The two lanes, and why there are two

Until S190 everything queued in the **D250 waterfall**, whose monthly budget is
`min(head-of-waterfall instalment, everything owed)` — ₹5,000 for Darpan. Because the loan book is
₹3.59 lakh, any new interest-free advance dropped in behind it and would not be seen again for
years. When the owner looked at the statement in S190 and saw his own ₹15,000 salary advance
reading *"waiting for the loan to clear"*, he ruled option "A", and **SL4** built the **quota
lane**: an advance that carries an explicit month, is not a loan, and is set to recover fully,
comes back **in full at the first close on or after its month**, in its own lane beside the
waterfall — never inside its queue.

That is working exactly as ruled. The statement cards now name the recovery month for each one.

**The consequence nobody has had to face yet:** the quota lane has only one speed. An advance
either returns in full at its month's close, or — if given a smaller instalment — falls back into
the waterfall behind ₹3.59 lakh. There is no middle setting.

---

## 4 · What the August close will actually do

Because the ₹10,000 was attributed to **July** but entered after July had already closed, it
collects at the first close on or after July — which is **August**. So August recovers:

| | |
|---|---|
| Quota lane | ₹10,000 + ₹15,000 = **₹25,000** |
| Waterfall | **₹5,000** (₹1,000 interest + ₹4,000 principal) |
| **Total against an ₹20,000 base** | **₹30,000** |

Using July's actual salary shape (base ₹20,000 + incentive ₹2,333.33 + OT ₹800 − ledger ₹5,000 −
attendance ₹6,266.33 = **net ₹11,867**), August lands at roughly **−₹10,000 to −₹14,000**.

**A harsh month is not, by itself, out of character here** — and it is important to say so
plainly. The S189 verification of the ₹70,000 gate established that the Apr–Jun ₹40,000 was
recovered by cutting his salary to almost nothing for about two months, confirmed by the owner
directly. Recovering fast is the established practice for this man, not an anomaly.

**The problem is not the harshness. It is what the machine records.**

In the workbook era, a salary that could not bear the deduction simply paid what it could and the
rest stayed outstanding — D250 says so in as many words. The ledger does not do this. At the close
the quota lane writes `ADVANCE_INSTALMENT` for the **entire balance**, unconditionally, with
"balance after: 0". The salary table then shows a negative net in red and **nothing carries it
anywhere**.

So if August runs as it stands and Darpan is paid nothing:

- the ledger will record **₹25,000 recovered**,
- but only about **₹16,000 of salary existed** to recover it from,
- and roughly **₹14,000 of repayment will have been recorded that no money ever paid**.

The balances would read zero while the money was never actually returned. That is a real hole in
the books, and it is the reason this report exists.

---

## 5 · The pharmacy-cash draw — the physical system, and its one missing link

Darpan is authorised to draw his salary advance directly from the Sanjeevni pharmacy cash drawer.
That physical habit is deliberately unchanged, and **nothing in this report asks you to change
it.** D330 already fitted the rule to the habit rather than the other way round: on his own entry
page the advance is capped at the derived ₹15,000, shown to him before he types, and refused
server-side past it.

**But the link from the drawer to the salary ledger is not built.** In the live finance code, at
the moment a day is approved:

> *"Approval is what posts a salary advance to the Staff Ledger. Not entry."*
> …and then it writes `ledger_posted = 0, ledger_ref = 'PENDING_LEDGER_WIRING'`, with the comment
> *"B6 wires the real Staff Ledger call. Until then this records intent explicitly rather than
> pretending the posting happened."*

The code is honest about it, which is to its credit. But B6 lived inside D329, and **D329 was
superseded whole by D330 — so the bridge was never built, and nothing replaced it.**

**In practice this means: every rupee Darpan draws from the pharmacy drawer must be typed into the
Staff Ledger by hand, by you, or his salary will never recover it.** The ₹15,000 of 17 Aug is in
the ledger only because you entered it yourself. The Apr–Jun ₹40,000 still sits in the drawer
table with `ledger_posted=0` and no staff id attached to this day.

This is the largest standing operational risk in his arrangement — not because anything is broken,
but because a step that looks automatic is manual, and it is only ever noticed when it is missed.

---

## 6 · Where the ruled policy and the running machine differ

Stated objectively, without recommendation:

| # | D250 says | The machine does | Effect |
|---|---|---|---|
| 1 | if the salary cannot bear it all, **the instalment skips** and the rest is priced | recovers everything regardless; negative net shown in red and carried nowhere | money can be recorded as repaid that was never paid |
| 2 | 3rd skip onward **auto-flags recovery from perks** | a 3rd skip is simply refused | the perks route (₹19,000 sitting there) is unreachable |
| 3 | ST advances "rarely carry 2–3 months" | quota advances recover in full, or fall behind ₹3.59 lakh | no way to spread one over two or three months |
| — | *(display)* | loan card reads "monthly deduction ₹5,000 + ₹1,000 interest" | reads as ₹6,000; the true figure is ₹5,000 **inclusive**, as July proved. The same ambiguity has propagated into Runbook v126 |

Items 1–3 are all the same shape: **D250's arithmetic was implemented faithfully and D250's
judgment was not.** The waterfall is workbook-exact to the rupee — that has been proven twice. The
clauses about what to do when the money runs short were never built, because until this month no
month ever ran short.

---

## 7 · What can be done, in plain terms

**Nothing needs deciding today.** The August close is roughly twelve days away and none of these
advances has been touched by a close yet, which is precisely why there is room to act.

**Option A — leave it, pay what the salary bears, correct nothing.** Matches how the ₹40,000 was
handled. Costs nothing to do. Accepts that the ledger will overstate what was recovered by roughly
₹14,000, which someone will have to reconcile by hand later.

**Option B — move one advance's month.** Re-attribute the ₹10,000 from July to October. August
then takes ₹15,000 + ₹5,000 = ₹20,000 (about break-even), September ₹10,000, October ₹15,000. Uses
the design exactly as intended — attribution decides which month — and needs no code. It does
consume ₹10,000 of October's ₹15,000 quota. This is two entries and can be done in minutes.

**Option C — skip the August loan instalment.** One button; you have 1 of 2 skips left this FY.
Frees ₹5,000 and capitalises ₹1,000 onto the loan. Helps, but not enough on its own.

**Option D — build D250's missing rule (a small `S191_SL5` kit).** Make the close read the month's
salary capacity and cap total recovery at it, skipping the loan instalment first exactly as D250
orders, and leave the shortfall genuinely outstanding instead of fictitiously recovered. This
fixes the hole permanently, for every member of staff, not just for Darpan — and it is the only
option that makes the books true by construction rather than by remembering.

**B and D compose well:** B makes August safe now, D makes every future August safe without anyone
having to think about it.

**Candidate findings for the register** (next free is F-147): the capacity rule never built
(**F-147**) · the unbuilt drawer→ledger bridge (**F-148**) · the unreachable perks-recovery route
(**F-149**) · the ₹5,000/₹6,000 display ambiguity.

---

*Written S191 from the live systems. No data was changed anywhere in producing it — every page
read was a GET, and no entry, migration or close was run.*
