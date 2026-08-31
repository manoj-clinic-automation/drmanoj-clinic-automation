# S211_MATCH — H2 · the matcher and the daily gap report

**The engine, not yet the screen.** Two modules, both read-only, both proven. The page
and route that show this to you and to Darpan are the next step. **Nothing here is
installed on its own** — installing an engine nobody can see delivers nothing and only
adds risk.

| file | what it is |
|---|---|
| `finance_patient_match.py` | identity by LOOKUP (D355): given the text the counter typed, a NAMED VERDICT and the chain of steps that produced it |
| `finance_daily_gaps.py` | one day's report — identity gaps, payment gaps, and who was at the counter |

Neither module writes to any table, ever.

---

## The rule that holds the matcher together

Every rung returns the **set** of patients it resolves to. **One is a match; more than
one is AMBIGUOUS** — shown with its candidates, never picked. That is precisely what a
confidence score destroyed: `0.6` could not tell *one weak match* from *three equally
good ones*, and those are entirely different situations.

Clinic ID and mobile carry the weight. **The name only corroborates** — a near name
with an exact ID is a match; a near name alone never is.

No full mobile is stored: the bill's number is fingerprinted with the same salted
one-way function the clinic PC used, and the fingerprint is what is looked up.
**Without the salt the mobile rung refuses**, rather than silently skipping — a rung
that quietly stops working is worse than one that stops loudly.

### Proven against the real master — 10/10

`python REHEARSAL_match.py --tracker <the followup_tracker folder>` builds a throwaway
database from the **real 7,813 patients** and asks what the counter actually creates:

- a complete bill matches on the clinic ID — **400/400**
- mobile + name, no clinic ID -> partial match — **400/400**
- **a clinic ID alone is a clean match, never parked** — 400/400. The old 0.6 tier had
  this backwards: it parked the strongest identifier there is
- a family mobile with no name -> **ambiguous, 200/200, never a pick**
- a misspelled name still matches when the ID is right — 263/264
- a wrong name against a right ID -> **ambiguous, 295/295** — never a silent match
- all **17 colliding clinic IDs** -> ambiguous, not clean
- six shapes of junk (PROSIJER, WR, BPJ, blank...) -> the counter gap

**The number that matters: a family mobile never resolved to the wrong relative —
0 of 200.** That is F-34, and it cannot happen now.

**A measurement, not a gate:** with a name present, the given-name rule separates
**143 of 200** family mobiles. The other 57 stay ambiguous because relatives genuinely
share a surname and nothing on the bill can tell them apart; those go to a human with
the candidates shown.

> An earlier version of this rehearsal asserted a 90% separation rate — fitting the
> gate to the result. It now asserts the SAFETY property (never the wrong relative) and
> reports the rate as information. That is fault **i** from this same session, nearly
> repeated an hour after we numbered it.

## The daily report

**One day, never a backlog.** A cumulative total can never reach zero, and a number
that can never reach zero is one everybody stops reading.

**Identity gaps** — only bills that did not match are listed. Each carries its working
step by step; an ambiguous row shows its candidates instead of choosing.

**Payment gaps** — the day's declared modes against what the bank actually settled
(bank is the arbiter, S208). Where the bank settled more than the bills declare, it
lists the cash-marked bills that **could** account for it. It proposes; a person
disposes. Nothing is changed.

**Who was at the counter** — Darpan's punch means Darpan; no punch means Vinay; the
owner's selector overrides both and is recorded as his. If the punches cannot be read,
attribution is **pending, never guessed**. Every answer carries *how* it was decided,
so a rule never reads as an observation.

**The backfill boundary is honoured**: before 18-Jun-2026 the three identifiers were
not being captured, so an unmatched bill there is not counted as a gap — and the report
says why rather than staying silent.

`python REHEARSAL_dailygaps.py` — **14/14**, including that the whole report is
read-only.

## What it is not

No enforcement, no blocking, no approval queue, no escalation. The owner's scope
ruling: it shows the gap and offers a match where one is possible.
