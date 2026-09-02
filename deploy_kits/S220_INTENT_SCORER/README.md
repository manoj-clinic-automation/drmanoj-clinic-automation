# S220_INTENT_SCORER — the deep analytics: patterns against their own baselines

**The owner's brief (02-Sep):** *"deep analytics to catch the intent from historic data and from constant
monitoring, because this is a sum which anyone can exploit."* Governing rule, his (S211): *the detector
proposes; a person disposes.* A signal is a row to look at — never a finding, never red, never a verdict.

**`finance_intent.py`** (NEW · read-only on the books · writes only `intent_signal` · nightly at 01:30):

| signal | what it measures | against |
|---|---|---|
| void shape | same-day, same-patient return for a bill's exact rupees (a correction — or a vanished cash sale) | 12-week weekly median |
| cash out, bank in | a return whose earlier sale of that item, same patient, was paid by **UPI** — refunds are cash (owner's rule), so cash leaves the drawer for money that came by bank | count in 4 weeks |
| repeat returner · shared mobile | 3+ returns in 90 days; returns on a mobile shared by several records | — |
| rate drift | trailing 4-week returns ÷ sales | prior 12-week median (≥ 1.5× = LOOK) |
| item outlier | an item's 90-day return rate vs the counter's | ≥ 3× with 3+ returns |
| large share | ₹1,000+ returns' share of the month | prior 3-month median |
| bill continuity | router-flagged numbering gaps (M1), tracked from 02-Sep | 0 |

**Deliberately not built, measured:** return-then-resale (171 of 204 returned lines resell within 30 days —
no discriminating power), owner-absent-day concentration (no attendance on `day_entry` yet), per-person
(no Marg user register on the router yet — Darpan on >90% of days).

**What the past says, as of 01-Sep (the baseline run):** 7 returns in 4 weeks whose sale was UPI-paid
(₹3,887) · rate 3.0% vs 2.0% median (1.5×) · six items returning at 3–7× the counter's rate (DISPERZYME CD
15%, NURVION LC 14%, RUNVACE TP 10%, DFO MR, ONKET DT, TAPAL ER) · two repeat returners · seven shared mobiles.
All marked *past* — they raise nothing (D361); they are the baseline.

**Owner-only until proven** (his rule): `/finance/darpan/api/intent` answers only the owner; the card shows a
collapsed **Intent signals** block under the returns list, LOOK rows first, past rows greyed, English only.

**Proven:** selftest 13/13 on a copy of the live db (engine, writer, CLI, endpoint, owner gate); browser
render 9/9 in a real Chromium. Three pins predicted (two moved, one new).

| file | what |
|---|---|
| `finance_intent.py` | the scorer (NEW) |
| `patch_darpan_intent_s220.py` | darpan_app.py — the endpoint (1 anchor) |
| `patch_hub_intent_s220.py` | finance_approvals.html — the block + loader (3 anchors) |
| `selftest_intent_s220.py` | 13 checks |
