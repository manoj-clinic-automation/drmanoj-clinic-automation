# S505_CARD_ELECTRICITY — the card's electricity bill, by its statement

Session 304 (parent), 10-Oct-2026. The owner's ruling, 10-Oct: for September's accountant pack the card's electricity bill is
**the 17-Aug payment** — the one on the ICICI Amazon Pay statement dated 12-Sep, the statement that goes with September's pack.

## What changes
- Pack item 5 (*Electricity: the auto-paid bills*): a bill a **card** paid is taken from the card statement **dated in the
  month** — the same statement the pack attaches and the card sheet uses. The bank's own auto-pay is still found by its date in
  the bank statement, as before. The running All_Transactions.xlsx is read only when no card statement of the month is read.
  On the session's copy, September goes from *1 of 2 found* to **ready**: ₹10,791 on 16-Sep from the ICICI account, and
  ₹10,821 on 17-Aug by the Amazon Pay card, on its statement dated 12-Sep.
- The Card spends summary says *spent ₹… (after refunds)* — the figure is net of the small refunds and waivers.

## Install (his one line on the VPS, after PUBLISH_ALL)
    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S505_CARD_ELECTRICITY/install_S505_CARD_ELECTRICITY.sh

## Undo
    cd /root/finance && \cp -p packs.py.bak_S505_49f2a26e packs.py && \cp -p packs.html.bak_S505_0e9378cd packs.html && systemctl restart clinic-finance
