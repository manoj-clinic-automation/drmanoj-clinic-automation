# S880_SHEET7_VOUCHERS — sheet 7 stops repeating the card spends · the parent · S484 · 18-Nov-2026

**His word (17:23, on the 16:5x analysis):** sheet 7 must not duplicate the card spends; it should enrich them — only the transactions that are not on the card statements, with their receipts.

**What it does** (`/root/finance/packs.py` 68c7c79d → 7f2a1172; the pack's figures elsewhere untouched):
- **A payment paper whose charge is a line of a card statement already read** (amount within Rs 1, date within 7 days, debits only) **leaves sheet 7.** It goes to the workbook's own **"Paid by card"** sheet (the trace: the card, the line's date, which month's card sheet carries it) and shows as the **Receipt** column of that line in the card sheet (4.4, *Every line* + 2 columns: the paper(s) of the charge, and whether the receipt is in Drive).
- **Sheet 7 keeps only the payments on no card**, each with **Where the debit is**: the bank statement line it matches (the account's label and the date), or — when none — *card and bank statements of this date not yet read* / *not every card's statement of this date is read yet* / *the bank statements of this date are not yet read* / *receipt only* (cash, an account not on the shelf, or a later debit). A paper that matches both a bank line and a card line of the same figure stays on sheet 7 with both named ("check which").
- Papers with no amount read stay on sheet 7 as "amount on the receipt"; NK Pathology's sheet as before; the page's row-7 label says it.

**Proof.** `walk_s880.py` 28/28 on a made-up root (made-up register, cards, statements, bank lines; the cases: a paper Rs 0.50 off its line, a card credit of a paper's figure, a bank deposit of a paper's figure, a paper matching both a bank line and a card line, a September paper on October's card sheet, every paper card-paid); the live file as the control: 8/28. S877 25/25 · S875 32/34 (its D5/D6 assert the old shape — the only reds allowed) · S866 18/18 · S873 11/11. `shape_s880.py` on the 18-Nov database copy, counts only: Sep 21 papers → 4 to the card sheet, 2 with a bank line (both also a card line: kept, named), 14 receipt-only, 1 no amount; the card sheet 40 lines, 8 with a receipt; Oct 14 papers → 0 moved (the November statements are not read yet), 10 "not every card's statement read", 4 no amount. Cold review: 2 MUST (the Rs-1 tolerance of the column; no trace of a moved paper when 4.4 is not built) and SHOULDs 3–9 built in. Rehearsed: DRY · forced red at [4/5] restores · real · already-installed · `--undo`.

**Install (the VPS, one line):**
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s880kit && cp -rp /root/deploy/repo/deploy_kits/S880_SHEET7_VOUCHERS /tmp/s880kit && bash /tmp/s880kit/install_S880_SHEET7_VOUCHERS.sh
```
`DRY=1` before `bash` proves without placing. Undo: `bash /tmp/s880kit/install_S880_SHEET7_VOUCHERS.sh --undo`.

**Known, not in this kit.** The card sheet (4.4) keeps its plain layout (no widths); sheet 7's S877 layout can be given to it later. A paper's Drive link is a yes/no flag (the register holds no link).
