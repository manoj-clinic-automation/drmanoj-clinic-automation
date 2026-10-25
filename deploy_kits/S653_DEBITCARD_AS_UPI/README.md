# S653_DEBITCARD_AS_UPI — a Docterz "Debit Card" the bank shows as UPI is UPI (kit S653, session S354, 25-Oct-2026)

**Why.** F-1022, answered by the owner at 12:24 IST 25-Oct-2026 (D788): *"Reception staff wrongly chooses the debit card option most of
the times when the payment is through UPI. The debit card option is very, very rare. And if at all there is a debit card used, then it
will reflect in the next day's bank MDR report, because all cards do not give full payment. Some deductions are always there."*
The day check (D776) was turning each of those into a *Payment mode wrong* line for reception — 5 on 23-Oct alone.

**What changes.** `/root/finance/day_check.py` `da63a580` → `c23e3f2f`, 3 counted edits in the payment-mode step: when that step moves a
Docterz *Debit Card* payment to UPI (the register — the referee — does not hold it as card) and the bank shows its exact amount as UPI,
no correction line is written; one note on the page says *counted as UPI, nothing to change* and reminds that *Online Payment* is the
right choice for UPI. Docterz's own totals are shown as recorded (13-Oct ruling). A Debit Card the register holds as card, or one the
bank does not show (statement not in yet), is exactly as before. No data step; restarts clinic-finance.

**Proven.** `walk_s653.py` runs the check for every day from 1-Oct to yesterday with the new and the live file on a throw-away copy of the
25-Oct database: **4 of 4** — 7 Debit Card → UPI lines dropped, every other line of every day unchanged, the note on each such day, the
totals unchanged. `--old`: 2 S653 red · 0 older red.

## Install (on the server)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s653kit && cp -rp /root/deploy/repo/deploy_kits/S653_DEBITCARD_AS_UPI /tmp/s653kit && bash /tmp/s653kit/install_S653_DEBITCARD_AS_UPI.sh
```
## Undo
```
\cp -p /root/finance/day_check.py.bak_S653 /root/finance/day_check.py; systemctl restart clinic-finance
```
