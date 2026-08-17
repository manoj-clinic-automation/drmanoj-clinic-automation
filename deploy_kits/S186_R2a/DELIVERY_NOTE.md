# Kit S186_R2a — the three surfaces

**Session 186 · replaces the live app · gated · backed up · self-restoring**
**Prerequisite: S186_R1a must be installed** (the installer refuses otherwise).

## What arrives

| Surface | What it does |
|---|---|
| `/finance/workbench` | **Entered · Marg · Bank** on one screen, by month |
| `/finance/api/yesbank-statement` | load a Yes Bank CSV — it reconciles immediately |
| `/finance/api/yesbank/reconcile` | re-check any window without loading anything |
| `/finance/api/custody` | who handed what to whom, with the **month-end marker** |
| `/finance/api/cash-count` | the drawer count — **blank is UNKNOWN and flagged**, never zero |

## The diff is purely additive

```
0 lines removed        239 lines added        4,355 -> 4,594
```

Built on the **live bytes** (`c66bec2b9e…`), hash-verified from your box this morning — not on the
repo copy, which is two builds stale and would have deleted the clinic module. That is F-97 avoided
by the pin work, and this is the second kit to use it.

`finance_yesbank` is imported **fail-soft**: if the module ever goes missing the three new routes
return 503 and every existing screen behaves exactly as before. A finance screen must never go dark
because an optional module moved (D264 / D322(a)).

## Proven before shipping — the F-87 differential

Run on a seeded store, unmodified live bytes versus this build:

| | passed | failures |
|---|---|---|
| unmodified live `finance_app.py` | 303 / 314 | 11 |
| **this build** | **330 / 341** | **11** |

**27 checks added, ZERO failures added.** The 11 are pre-existing and identical in both.

Two of my own new checks failed at first — they asserted the harness's role state rather than the
guard. I proved the routes themselves were right (a maker gets **403** from the new routes and from
the existing checker-only routes alike) and then fixed my tests to use an identity holding no seat.
**That is F-106: a test must assert behaviour, never a state.** Catching it in my own tests rather
than shipping it is the point of running the differential at all.

## What is deliberately NOT in this kit

**Darpan's daily entry screen is untouched.** Its Hindi labels are not approved yet, and the maker
screen is the highest-traffic surface in the system. Custody capture therefore lives on the doctor's
workbench for now. When you approve the labels, a small follow-up kit adds the "cash handed to" block
to his screen — a UI-only change with no schema behind it, because R1a already built that.

## Three details worth knowing

- **The workbench suggests; it never applies.** A gap between Marg and what was entered is shown and
  **graded** — exact / likely / weak, following D315 — and a human decides. There is no auto-apply
  path in the code or the page.
- **A blank drawer count is recorded as UNKNOWN and flagged**, not as zero. An uncounted drawer and
  an empty drawer are different facts, and conflating them is how a float stays hidden for five
  months.
- **Account numbers are stored last-4 only.** The full number never enters the database or a log.

## Install

```
bash /root/deploy/vps_deploy.sh S186_R2a
```

Then open **https://followup.dr-manoj.in/finance/workbench** and load today's Yes Bank CSV. It will
tell you in one line what the books claim that the bank did not.
