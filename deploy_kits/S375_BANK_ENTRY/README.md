# S375_BANK_ENTRY — kit README

**Project:** Sanjeevni (session 281, 22-Sep-2026) · **Touches a parent file:** yes, declared — `finance_ui/finance_approvals.html` · restarts `clinic-finance` · `finance.db`: **one new empty table** (`bank_transfer`); no existing table is altered.

## The ruling — D604
Sanjeevni has **two accounts**: **ICICI** collects the POS; **Yes Bank** takes the cash deposits, pays the suppliers by one bulk NEFT, and carries the POS rental and its GST. Either account may transfer to **its own HUF savings account**. The bulk NEFT pays a month's purchases **in the next month, latest by its third week** (September is late only because of the migration).

Three rules the build holds to:
1. **A transfer is never income.** The POS money is income on the day it is collected; every later move changes the place, not the total. The walk proves no month's sale, online or cash figure moves by a rupee.
2. **Money to an HUF savings account leaves the pharmacy's picture** — a withdrawal, not an expense. The row says so on the page.
3. **Nothing is believed because it was typed.** Every entry reads *waiting for the statement* until the bank's own statement covers its date, then *confirmed* — or, if the bank never shows it, it is named.

## What it does
- **Bank now carries both accounts.** *ICICI Sanjeevni — holds about ₹X (₹Y collected since 17-Aug, ₹Z moved out)*, worked out from ICICI's own daily settlement files less the transfers recorded, and saying plainly that it is our count until the ICICI statement is read. *Yes Bank* as before, with the deposits and now the transfers.
- **Two buttons, his:** *Record a cash deposit* (pool → Yes Bank; leaves the pool at once, the one calculation reads it) and *Record a transfer* (ICICI → Yes Bank · ICICI → ICICI HUF · Yes Bank → Yes Bank HUF).
- **Remove** — an entry the statement has not yet confirmed can be taken back; one it has confirmed cannot.
- Refused, in words: a future date, a date before the 17-Aug anchor, zero, the same entry twice, a route that is not his, and a transfer larger than ICICI holds.
- `/root/finance/sanjeevni_approvals.py` `e601d398` → `4f98cb37` (v1.1) · `finance_ui/finance_approvals.html` `c6641ef6` → `19c877e5` (both by `apply_s375.py`, anchored on the live bytes).

## Proof
`walk_s375.py` on a scratch copy of the live database — **17/17**: the deposit and all three routes are taken · the bad route, the repeat, the future date, the zero and the over-balance are refused with a sentence · the deposit leaves the doctors' pool at once and the removal puts it back · **no month's sale, online or cash changes at all** · the drawer is untouched · ICICI's position drops by what was moved out · new entries read *waiting*, the two September deposits still read *confirmed* · a confirmed deposit cannot be removed · staff are refused at all three doors · the page carries both buttons and the three routes.
At build, in headless Chromium against the real app: both boxes open, a transfer and a deposit recorded from the screen, the rows and ICICI's line update, **zero script errors**.

## The line
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S375_BANK_ENTRY/install_S375_BANK_ENTRY.sh
```
