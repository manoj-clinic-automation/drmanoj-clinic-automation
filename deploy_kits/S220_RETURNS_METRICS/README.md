# S220_RETURNS_METRICS — the gist line and the two metrics, on the card that exists

**The owner's question (02-Sep):** *"total returns — out of it what amount surfaces in analytics with intent
flags, so we have a metric to track?"* and *"I get a gist, expandable down to the last detail, in the same
place."*

**What it adds — one English line under the returns header:**

> **Aug 2026:** ₹20,348 returned · **2.9% of sales ↑** (Jul 2026 2.3%) · examinable **75.3%** · flagged **28.7%** (₹5,834) · 0 to look at

- **rate** = returns ÷ sales on the bill spine, this month and last — one source, one rule (D349); amber
  above 2.0% or when it rose on the previous month.
- **examinable %** = share of the month's return rupees the audit could judge (target ≥ 98 → green).
- **flagged %** = share carrying a money verdict — watched, not coloured; the first F-277 morning should
  make it fall, and that fall is the measurement.
- **to look at** = the returns that need the owner (NEED YOU). Every number expands into the rows below.

**Proven:** selftest 11/11 on a copy of the live db through the real blueprint — the rupees recomputed
independently from the audit's own rows, the rate checked against the spine, fail-soft on an empty month;
browser render 8/8 in a real Chromium. Two pins predicted. No new table, no write, English only.

| file | what |
|---|---|
| `patch_darpan_metrics_s220.py` | darpan_app.py — 3 anchors |
| `patch_hub_metrics_s220.py` | finance_approvals.html — 1 anchor |
| `selftest_metrics_s220.py` | 11 checks |
