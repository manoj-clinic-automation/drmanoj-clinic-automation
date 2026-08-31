# S211_PANEL — the counter's gaps and the sanctioned discounts, on the console

**ONE card added to the page you already use. No new page, no link, nothing to
navigate to.** The owner's standing rule, recorded at S210 and repeated at S211:
one page, no jumping, no duplication, all data present, collapsed and expandable
to the granular level.

## What it adds — and what it deliberately does NOT

The console already shows `Declared (Darpan)`, `Bank - ICICI UPI settled` and the
Marg day totals. **None of those are repeated.** A second copy of a number is a
second thing to reconcile, and the owner has asked twice that the panel not
duplicate.

The card carries only the two things the console has never had:

**Identity gaps** — every bill that did not resolve to a patient, collapsed to one
line each: bill, amount, mode, verdict. Click a row and it opens **in place** to
the chain of steps that produced that verdict, and the candidate patients where
the answer was ambiguous.

**Sanctioned pharmacy discounts** — sanctioned percent, gross, what was sanctioned,
what was given, the difference, and the verdict. Click to see the percentage
actually given against the percentage sanctioned. **Rounding is exempt but
recorded** — a row inside tolerance still shows its true difference, it is simply
not counted as a breach. **Over-discount is its own bucket**, because a cluster at
one percentage means a different rule is being applied, not carelessness.

One contextual line at the top: who was at the counter that day and **how that was
decided** — by rule, by the owner, or pending. A gap belongs to whoever was
standing there, and a rule must never read as an observation.

## The two pieces

| file | goes to |
|---|---|
| `patch_finance_app_panel.py` | run against `/root/finance/finance_app.py` — adds ONE read-only route, `GET /finance/api/day-gaps` |
| `finance_approvals.html` | `/root/finance/finance_ui/finance_approvals.html` |

The endpoint is read-only by construction: it opens the database, reads, returns.
No INSERT, UPDATE, DELETE or commit anywhere in it — asserted by the selftest.

## Proof

`python -B patch_finance_app_panel.py --selftest <a post-MARGTIDY finance_app.py>`
— **9/9**: patches cleanly, compiles, is idempotent, leaves the existing apply
route intact, adds the endpoint exactly once, creates no HTML page, returns none
of the duplicated figures, and contains no write statement.

The page's script block passes `node --check`, and carries no external script or
stylesheet.

Behind it, `S211_MATCH` is at **27/27** (daily report, including the discount
verdicts and the corrected declared-vs-bank check) and **14/14** (matcher,
including the regression that a JSON record can never yield a clinic-ID match
from a stray digit run).

## Install — after the publish, ONE line

    cd /root/deploy/repo && git pull && \cp deploy_kits/S211_MATCH/finance_patient_match.py deploy_kits/S211_MATCH/finance_daily_gaps.py /root/finance/ && /root/wa/venv/bin/python3 deploy_kits/S211_PANEL/patch_finance_app_panel.py /root/finance/finance_app.py && \cp /root/finance/finance_ui/finance_approvals.html /root/finance/finance_ui/finance_approvals.html.bak_S211_panel_$(date +%Y%m%d_%H%M%S) && \cp deploy_kits/S211_PANEL/finance_approvals.html /root/finance/finance_ui/finance_approvals.html && systemctl restart clinic-finance.service && sleep 3 && systemctl is-active clinic-finance.service

## Rollback

    \cp /root/finance/finance_app.py.bak_S211_daygaps_* /root/finance/finance_app.py && \cp /root/finance/finance_ui/finance_approvals.html.bak_S211_panel_* /root/finance/finance_ui/finance_approvals.html && systemctl restart clinic-finance.service
