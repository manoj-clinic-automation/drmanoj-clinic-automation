# S365_DAY_PANEL — kit README

**Project:** Sanjeevni (session 280, 21-Sep-2026) · **Touches a parent file:** yes, declared — `finance_ui/finance_approvals.html`; restarts `clinic-finance`.

## What it does
The approvals page's day panel, as the owner asked on 21-Sep: *simple, human readable, expandable — which sale returns were there, what were the sales*.

```
Sale (Marg)            bills ▸ each bill ▸ its medicines
 − Sale returns        credit notes ▸ their medicines
 − Paid by UPI         the bank's own payments
 − Without cash        home / procedure medicine bills
 = Cash received       (15-Sep: 11,291)
 − Paid at the clinic counter / + put back / − paid from the drawer   (only when there is one)
 = Cash for the drawer
Where the cash went · checks in words · "Nothing needs you" or what does
```
No machine words (`variance`, `line_sum_vs_day_total`, `opening → closing`) reach the owner. The old panel stays one tap away and is the automatic fallback.

## Files
- `/root/finance/sanjeevni_day.py` — NEW, reads only (`GET /finance/sanjeevni/api/day/<date>`, owner only).
- `/root/finance/darpan_kal.py` `63c70749` → by `apply_s365.py`: its `init()` also mounts the panel.
- `/root/finance/finance_ui/finance_approvals.html` `5b6ecceb` → by `apply_s365.py` (**parent's**).

## Proof
`walk_s365.py` — the real app over a scratch copy of the live database, every filed day from 17-Aug (30 days): each day's cash for the drawer equals the one calculation's, each day closes, 15-Sep = 11,291, 20-Aug's bill 2777 paid at the clinic, 11-Sep's credit note named and put back, 04-Sep's ₹200 put to the owner in words, no machine word, staff and anonymous refused, the old panel still answers. Rendered headless with two real days (names masked): no script error.

## The line
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S365_DAY_PANEL/install_S365_DAY_PANEL.sh
```
