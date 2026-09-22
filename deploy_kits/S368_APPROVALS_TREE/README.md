# S368_APPROVALS_TREE — kit README

**Project:** Sanjeevni (session 281, 22-Sep-2026) · **Touches a parent file:** yes, declared — `finance_ui/finance_approvals.html` (replaced; its 6c668ccc bytes kept beside it as `finance_approvals_old.html`) · restarts `clinic-finance` (declared) · `finance.db` untouched · `finance_app.py` and the crontab untouched.

## The ruling — D603 (finishes D591)
The approvals page is **one tree on one page**, in the owner's order, and the audit material is a **collapsed "Checks" section at the bottom of the same page** — his words today: *"a collapsible, expandable section … my navigation gets lesser."* Nothing is deleted; the page as it was is one link away.

```
[alerts: filing · Docterz · bank]        the parent's sentences, unchanged (the reconciler's counters now sit in Checks)
NEEDS YOU     in words, one line each, tap = jump; or "Nothing needs you."
DAYS          one line per filed day from 17-Aug, by month · sale · online · without cash · cash · status · [Approve] [Log cash]
              ▸ the S365/S367 day panel (bills ▸ medicines, how the day was filed)
CASH          one figure, split: drawer · pool · banked (the S210 card, on sanjeevni_cash since S363)
BANK          Yes Bank: statement reach, cash deposits each matched to the pool · pharmacy ICICI UPI by day
RETURNS       the month in one line ▸ each credit note ▸ its medicines · approve / reject where your OK is needed
MONTH         sale · online · cash · without cash · banked — one Marg figure, named for the days it covers
CHECKS        collapsed: Darpan's word vs the data · gaps & discounts · Marg reports (upload + pushed) · bank MPR (all units)
              · return signals & spot-count · parked rows · open differences & the walk · the old queue · the old
              without-cash card · reclassified · the old drawer ledger · the old month table · orthotics · staff cards
              · the old counters · other pages
```

## Files
- `/root/finance/sanjeevni_approvals.py` — NEW, reads only: `/finance/sanjeevni/api/needs-you` · `/api/days` · `/api/bank?month=` · `/api/months`; serves `/finance/approvals/old`. Every rupee from `sanjeevni_cash` (D600); every sentence composed here (D349).
- `/root/finance/darpan_kal.py` `19b9c0e8` → `1958ee7c` by `apply_s368.py`: `init()` also mounts the door.
- `/root/finance/finance_ui/finance_approvals.html` `6c668ccc` → `c6641ef6` by `build_page.py` **from the live bytes** (the installer proves the build reproduces the kit's page): head and stylesheet kept, every S365 renderer kept (now under Checks), the body is the tree. The login name is no longer shown as a source (F-613).
- `/root/finance/finance_ui/finance_approvals_old.html` — NEW = the 6c668ccc bytes.

## How it sits with the architecture
Money: one source, `sanjeevni_cash`. Marg: read only through the Sanjeevni doors (`sanjeevni_day`, cn-detail), so the switch to the spine after seven clean nights is server-side and the page does not change. Approve then log (D592): [Approve] → the parent's approve door; [Log cash] → `darpan_kal`'s log door, expected cash prefilled (D596); August/September are never *asked* to be logged (D598). `line_sum_vs_day_total` rows never reach Needs-you (D591) — they live under Checks ▸ Open differences.

## Proof
`walk_s368.py` on the VPS (in the installer), real app over a scratch copy: the four doors answer · 30 day lines = `sanjeevni_cash.days` (order, cash, close) · months = `month_rows` · Needs-you's returns count = the returns card's (12) · no machine word · both pool deposits confirmed · the page carries Needs you, Checks, the S365 panel and its fallback, the Marg upload · `/finance/approvals/old` byte-identical · staff refused — **14/14**.
At build, in headless Chromium (not on the box): **zero script errors**; every section filled; a day opens to its panel; Log cash box appears prefilled; Checks opens and all 16 folds load; the S217 strip renders inside Checks; phone width (390 px) with no horizontal scroll. The one 4xx seen is `/finance/api/cards` (the staff registry, 503 in the scratch environment; its card says "registry unavailable", as before).
S367's walk stays green on the built app (15/15). S365's own walk now reads its 04-Sep check as red **because 04-Sep is corrected** (D602) — the check was a snapshot of the fault, not of the kit.

## The line
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S368_APPROVALS_TREE/install_S368_APPROVALS_TREE.sh
```
