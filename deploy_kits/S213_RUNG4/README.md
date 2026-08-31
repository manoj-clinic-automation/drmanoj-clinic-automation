# S213_RUNG4 — ladder rung 4 valued through finance_money (⭐1.3)

**Built and walk-proven offline at Session 213, 31-Aug-2026. NOT INSTALLED —
and deliberately not installable until the measurement below is read.**

## The defect, and why it could not just be deleted

`find_return_lines` rung 4 (S212 `finance_returns_audit.py:108-111`) identifies
a return's item lines, when every stronger rung fails, by "same day and the
amounts agree" — but it compared `SUM(amount_p)` over the lines, **a sum of
RATES PER PACK**, against the bill's **MONEY**. That is the exact confusion
`finance_money.py` exists to end, and the same arithmetic that produced the
withdrawn ₹38,157. It still **recovered 18 bills** at S211's measurement, so it
is load-bearing: deleted, 18 real returns fall back to NOT FOUND. The owner's
order: rework it through `finance_money` and re-measure — never simply delete.

## v2, the rework (`finance_returns_audit.py` — full file)

Each same-day candidate's lines are VALUED through `bill_gross_p`; a candidate
with ANY unreadable line is skipped (a partial total must never identify a
bill); acceptance is unchanged — exactly ONE fit within ₹1. The walk proves the
diff touches ONLY the module docstring and this block; every other byte equals
the installed S212 version (`a8c4d6f5…`).

## The measurement gate — the install waits on it

`MEASURE_rung4.py` (READ-ONLY, prints no patient data) runs BOTH rules over
every return bill on the live database that reaches rung 4, and prints:
identical recoveries · **suspect matches only the old rule made** (rate
coincidences) · new recoveries only the money rule makes · bills matched to
DIFFERENT bills by each rule (the dangerous class). The owner reads that table;
only then does the one-line install go ahead. A rung-4 line source is labelled
on the card ("same day and the money agrees"), so downstream nothing else
changes.

## The walk (9 checks)

The defect reproduced on a real database (old matches a rate coincidence, v2
refuses) · v2 recovers what old missed · ambiguity refused · unreadable line
disqualifies · byte-diff confined to the two declared regions · regression:
`returns_for_day` still reconciles to the paisa. Relative paths only.

## Gate
From INSIDE this folder: `md5sum -c SUMS.md5` · `python -B WALK_rung4.py`.
