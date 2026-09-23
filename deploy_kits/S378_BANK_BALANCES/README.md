# S378_BANK_BALANCES — kit README

**Project:** Sanjeevni (session 281, 23-Sep-2026) · **Touches a parent file:** yes, declared — `finance_ui/finance_approvals.html` · restarts `clinic-finance` · **`finance.db` is not touched** — both figures are read, nothing is stored.

## The ask
His words after S377 went live: *"better if it could also show the updated balances of both the accounts boldly and clearly in the banks section."*

## What it does
Bank opens with **two bold figures**, one per account, each with one grey line saying how it was made:

- **ICICI Sanjeevni** — S377's count: the balance the bank printed on its own statement, plus every settlement credited since, less every transfer recorded out. (If the count is ever short of what he has moved, the tile says so.)
- **Yes Bank Sanjeevni** — the balance **its own statement closes on**, plus every movement we have recorded that the statement does not show: a cash deposit, a transfer in, a transfer out. A movement the statement **does** show is already inside the bank's figure and is never added twice. No seeding is needed and none is possible to get wrong: the figure moves forward by itself each time he loads a newer statement.

Under both, one sentence in grey: *a payment or a charge the bank has taken since its statement — a supplier NEFT, the POS rental, its GST — is not in these figures; the next statement settles them.* The ICICI fold below no longer repeats the figure; it explains it.

`sanjeevni_approvals.py` `f52ff847` → `7ab5fec6` (v1.3) · `finance_ui/finance_approvals.html` `87157a85` → `750f89e0` (both by `apply_s378.py`, anchored on the live bytes).

## Proof
`walk_s378.py` on a scratch copy of the live database — **11/11**: Yes Bank is anchored on its own statement and equals closing + unshown movements · **a deposit the statement already shows is not added twice** · ICICI still reads S377's count · a new deposit raises Yes Bank by exactly its amount, a transfer out lowers it by exactly its amount, and ICICI is untouched by both · removing them puts both figures back exactly · no month's sale, online or cash moves at any point · the view serves both balances with how each was made · the page carries both tiles and the rest of the tree.
In headless Chromium: the tiles read **ICICI ₹6,337** and **Yes Bank ₹3,29,352** on the test copy, each with its one-line explanation; the figures stack cleanly at phone width (390 px, no horizontal scroll); **zero script errors**.

## The line
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S378_BANK_BALANCES/install_S378_BANK_BALANCES.sh
```
