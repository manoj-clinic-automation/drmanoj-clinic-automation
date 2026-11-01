# S696_MONTH_CONSOLE — The month, on the command console

*The parent, session 376 · 01-Nov-2026 · the owner's "Build now" (18:01 IST) on the mock-up "The month" (https://claude.ai/artifact/B4u8r6vLHwjywWr9NQjhaW); his rulings 13:41–17:59 IST.*

## For the owner
Your command console gains a section **The month**, and its own page:

```
https://followup.dr-manoj.in/finance/console/month
```

Two tabs: the month just ended (kept first until its pack is sent) and the running month, live. On each: **where the month stands** — seven groups in calendar order (attendance → salary · Sanjeevni · Darpan's month jobs · rooms · petty book and renewals · the accountants' pack · IPD statement), green done / amber your hand / grey waiting on someone else, your own actions on the closed bars (Approve & save · Lock · Finalise · Check it · Send · Settings) — then **revenue by head** (clinic by Docterz head, Sanjeevni counter with its deductions and returns, physiotherapy in-clinic; Bhati's home visits shown but kept apart, as you ruled) with a subtotal under each head and the grand total, cash / UPI / card / "Paid (two ways)"; **X-ray expenses against revenue** inside the rooms group (films used per size × the last box's price ÷ 150, the X-ray's AMC, service and battery costs spread by the month as the X-ray costs page spreads them); **bought for the rooms** (the film bills, the Scan App's lanes of the month, the bills not yet laned); **supplies and replacements** (the stationery challans clinic vs NK, the statement made or not, batteries fitted, machines serviced or added). Every line opens the page it came from. Sections are collapsed; an open one wears the green bar; each remembers whether you left it open.

**Nothing is typed here, nothing is written anywhere.** The reading is made the way the console already makes its own (on a copy of the database, inside the console's builder); the staff register's and the Scan App's databases are opened read-only. No patient appears in it: counts, codes and amounts only.

## The rulings, as built
- One page, two months (D-number at the close). The ended month first until its pack is sent.
- Subtotals per head, then the grand total; "Paid (two ways)", never "split" (his 13-Oct ruling); Wallet counts as UPI (Razorpay to the bank).
- X-ray expenses: bills of the month are not the cost of the month's work; only films have a true per-use figure; the machine's own cost and electricity are not in it. The slips' X-ray total and Docterz's X-ray head are both shown when they differ.
- Procedure consumables: a bill with no lane is shown as "lane not settled" (Y51), never guessed.
- Fail-soft: a piece that cannot be read is said on the page ("not read: …"), never silently missing.

## Files
| file | FROM → TO | what |
|---|---|---|
| `/root/finance/owner_console.py` | e414e7ad → 7eade6df | 6 counted edits (`make_s696.py`): VERSION S696 1.4 · MONTH_PAGE · two routes `/finance/console/month`, `/finance/console/api/month` · `sec_month` second in ORDER · the name map · `month` in the snapshot |
| `/root/finance/month_read.py` | NEW → see TO_PINS.md5 | the reading |
| `/root/finance/month_page.html` | NEW → see TO_PINS.md5 | the page |

No data step, no new table, no portal change. Restarts clinic-finance. The reading file `console_reading.dat` is rebuilt once after the restart so the page has the month at once.

## Proof
- `walk_s696.py` on made-up databases (never a patient): 53 of 53 green, 8 mutants caught; the control on the live console: 8 red.
- The reading on the 31-Oct nightly copy (in the device VM): October 46 procedures · 215 X-rays · 35 lines not matching Docterz · films 188 / 33 · 28 Sanjeevni days approved · the pack's shelf 3 of 15 — the same figures the live pages showed on 01-Nov.
- The console's own builder with the new section on that copy: 0.92 s, no section failed.
- The page rendered at 1366×768 (a 14-inch laptop): everything in one screen, no vertical scroll; 390 px: no sideways scroll; 102 site-relative links, none malformed; every subtotal and the grand total add up.
- The installer rehearsed on a made-up root: DRY · install · ALREADY INSTALLED · HALF PLACED refused · corrupt kit refused · someone else's switch kept · a forced red at [7/8] and a journal red restore all three · a changed live file refused at [2/8] · a stale lock and switch taken over.

## Install
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s696kit && cp -rp /root/deploy/repo/deploy_kits/S696_MONTH_CONSOLE /tmp/s696kit && bash /tmp/s696kit/install_S696_MONTH_CONSOLE.sh
```
`DRY=1 bash …` runs every gate, the rebuild, the walk, the control and the builder with nothing written.

## Undo (one line)
```
\cp -p /root/finance/owner_console.py.bak_S696_e414e7ad /root/finance/owner_console.py && rm -f /root/finance/month_read.py /root/finance/month_page.html && systemctl restart clinic-finance
```
