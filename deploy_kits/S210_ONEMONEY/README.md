# S210_ONEMONEY — one money card, one arithmetic, and the deposit-gap alarm

## Why this kit exists (30-Aug-2026, measured on the live database)

1. **The owner console carried TWO answers to "who holds what".** The Cash-position card
   (custody + hand-overs — correct) and the Cash-custody card below it (custody only)
   disagreed by **₹1,21,982** on 30-Aug. Same page, same people.
2. **₹3,20,340 sat unbanked for 31 days and nothing said so.** Last deposit 30-Jul; the
   deposit prompt watches only the drawer (₹26,182), which never crossed its threshold.
   April–July the gap never exceeded 15 days.

## What this page changes — ONE file, page-only, no server code, no restart

- The contradictory custody card is **removed**; its event trail is folded into the
  per-person detail of the one remaining money card.
- The card now leads with **"Last bank deposit — N days ago"**, red once the gap
  exceeds 15 days (the worst gap in the record before this).
- Per-person rows expand to the **full merged trail** — custody events AND day-form
  hand-overs, newest first: the collapsed→granular table the owner specified.
- Position arithmetic is untouched: `/finance/api/cash-position` (custody + movements),
  the same formula verified to the rupee against the live reads this session.

## Proof

- **js_gate (S209, verbatim): PASS** — 1 script block parsed clean.
- **Live-shape walk under node, fed the REAL 30-Aug data: 15/15** — totals to the rupee
  (3,20,340 / 26,182 / 2,23,265 / 70,893), gap badge red at 31 days, merged trails
  complete and newest-first, the wrong ₹1,98,328 total impossible, no raw −42,093 shown.
- **Failure paths:** custody API down → card still renders from cash-position alone;
  cash-position refuses → honest "could not load".

## Install — VPS, one line at a time

```
git -C /root/deploy/repo fetch --depth 1 origin main && git -C /root/deploy/repo reset --hard origin/main
```
```
\cp /root/finance/finance_ui/finance_approvals.html /root/finance/finance_ui/finance_approvals.html.bak_S210_$(date +%Y%m%d_%H%M%S)
```
```
\cp /root/deploy/repo/deploy_kits/S210_ONEMONEY/finance_approvals.html /root/finance/finance_ui/finance_approvals.html
```

No restart — pages are read from disk on every request. Then one look at
https://followup.dr-manoj.in/finance/approvals — the walk that proves it.

*S210 · 30-Aug-2026 · base: S209_JSGATE/finance_approvals.FIXED.html (da82366c…), edits anchored and refused if ambiguous.*
