# Drawer investigation — root causes, gaps found, and the checks to close them
**S195 · 21 Aug 2026 · read-only investigation, no data changed**

Triggered by: Darpan's drawer opening not matching the nil-reset. What began as one
number turned into six findings, four of which are systemic.

---

## 1. What actually happened

**The drawer reconciles to ₹3 once two faults are corrected.**

| Date | Cash in | Out | Note |
|---|---|---|---|
| 17 Aug | 13,401 | 0 | hand-over NOT recorded |
| 18 Aug | 18,469 | 0 | entered as 17,172 — short ₹1,297 |
| 19 Aug | 15,124 | 0 | |
| 20 Aug | 7,939 | 51,930 → Dr Manoj | less ₹3,000 no-payment bills |
| | **54,933 − 3,000 − 51,930 = ₹3** | | rounding |

**Darpan is cleared.** His handwritten copy says total 25,176 / UPI 6,707 — matching
the Marg export to the rupee. He counted correctly and handed over correctly; the
*books* were wrong.

### Fault A — the 17 Aug hand-over was never recorded as a transfer out
Custody records ₹163,963 leaving on 17 Aug (18,963 → Dr Manoj, 145,000 → Dr Bhawna),
but the day's filing shows `out = 0.00`. The books therefore still count that money in
the drawer, which is why it reads ₹193,904.

### Fault B — 18 Aug was entered ₹1,297 short
Entered total 23,879 vs the true 25,176. Investigated exhaustively:
- **Not a missing bill** — no single bill equals 1,297.
- **Not a truncated report** — no prefix of the day's bills totals 23,879
  (closest prefix is 23,956, off by 77).
- **Not credit-note or discount mishandling** — none of those compositions
  (net−CN = 26,816; net+CN = 23,536; net−discount = 24,410) equals 23,879.
- So **23,879 is not derivable from the Marg data by any mechanism** — it came from
  the entry itself.

Revision history adds the process picture: day 124 (18 Aug) was created **empty** on
19 Aug 06:54, then actually filled on **20 Aug between 11:47 and 12:09 — two days
late, in five saves inside 22 minutes.**

---

## 2. Gaps found (the systemic part)

**G1 · Nothing compares the entered total against Marg.** The Marg data for 18 Aug was
already in the system and said 25,176. The page accepted 23,879 and no check ever
compared them. A ₹1,297 error sat undetected for three days and was only found because
the drawer failed to balance. **This is the highest-value gap.**

**G2 · UPI is not captured at billing — it is hand-derived.** Marg's exports for 17
and 18 Aug label every bill `.CASH`; the D.R. column was already measured unreliable
(23 of 23 bills marked cash on a fortnight that was 36.9% non-cash). So UPI is read off
the machine afterwards and typed in, and because the page computes **cash = total −
UPI**, any UPI error moves the drawer one-for-one. The only independent check is the
UPI statement reconciliation.

**G3 · Custody events and cash movements are not linked.** A hand-over recorded in one
subsystem does not move the drawer, which is computed from the other. Money can read as
"Dr Manoj has it" and "still in the drawer" simultaneously — Fault A exactly.

**G4 · Marg's later corrections never flow back.** 19 Aug: totals agree (44,120) but the
split does not — Marg's corrected export says cash 18,790 / non-cash 25,330 while the
books hold cash 15,124 / UPI 28,996, a ₹3,666 divergence. Corrections made in Marg days
later are invisible to the books.

**G5 · Late filing is not surfaced.** 18 Aug sat empty for two days.

**G6 · The email query agent silently drops long commands.** Any `Q:` subject beyond
~75 characters is never seen — no reply, no error. Confirmed: a 40-character SQL
command answers in two minutes; identical queries at 84–113 characters vanish. This
silently disabled the whole `sql` command class during this investigation.

---

## 3. Suggested actions, in priority order

**A1 · Cross-check the entered total against Marg at save time.** *(closes G1)*
When a day is saved and Marg data exists for that date, compare the totals. Mismatch →
show it on the page and flag it for the checker. Cheap to build — the data is already
there — and it would have caught this instantly. **Do this first.**

**A2 · Reconcile custody against cash movements.** *(closes G3)*
A standing check that flags any custody event with no matching cash movement (and vice
versa). Decide the design point: either a hand-over writes both, or one view derives
from the other. Until then the drawer can silently drift.

**A3 · Require UPI to be evidenced.** *(closes G2)*
Flag any day whose UPI figure has not been matched against the UPI statement. Given
cash is derived from UPI, an unverified UPI is an unverified drawer.

**A4 · Monthly Marg-vs-books comparison.** *(closes G4, and is the Amir quality check)*
Compare the latest Marg export of each day against what the books hold; report
differences in total and in split. The report router's archive keeps every version of a
day, so this becomes straightforward once it is running.

**A5 · Late-filing alert.** *(closes G5)* Flag a day not filed by a set hour.

**A6 · Fix the email agent's long-subject bug.** *(closes G6)* Either match on the
decoded subject or search unlabelled mail and filter in code. Until fixed, keep `Q:`
subjects short.

---

## 4. Corrections pending owner approval (nothing done yet)
1. **18 Aug**: total 23,879 → 25,176 (UPI unchanged at 6,707; cash becomes 18,469).
   An approved day — the change is recorded as a revision, earlier version retained.
2. **17 Aug**: record the hand-over that zeroed the drawer. **Open question:** the books
   say the drawer stood at ₹195,198 that morning while custody records only ₹163,963
   moving — a ₹31,235 difference that cannot be resolved from data alone and needs
   Dr Manoj's recollection of the actual amount taken.
