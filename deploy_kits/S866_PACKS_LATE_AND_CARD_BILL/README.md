# S866_PACKS_LATE_AND_CARD_BILL — the parent, S480, 18-Nov-2026

**His word (09:05 IST 18-Nov, on /finance/packs):** the 1050 statement was in the mail yet shows missing; the card statements show "not decrypted"; only one electricity bill shows (the other is paid by the card) — "rectify these, and they must not recur".

**Causes read (S480):**
- **1050** (Dr Manoj Agarwal, Yes Bank savings): the statement reached Drive at 07:53 IST 18-Nov, after the shelf's last daily read (07:30). Nothing was wrong with it; it simply waited for 05:40 tomorrow.
- **Cards:** every card statement since October arrived but is locked — no card password was ever stored on the page (F-835's open item, his hand). The page called this "decrypted copy not yet made / no decrypted twin", words from the retired PC-script days.
- **Electricity:** the second bill is paid by the ICICI Amazon Pay card and is read from that card's statement dated in the month (S505). ICICI never mailed the Amazon Pay statement for 13-Sep to 12-Oct (his mailbox read: Aug, Sep and Nov came; October did not), and the November one is locked.

**What changes:**
1. cron `15 9,13,19 * * * … stmt_shelf.py run  # S866_SHELF_LATER` — the shelf also reads Drive at 09:15, 13:15 and 19:15 IST; one read at the end of the install.
2. `/root/finance/packs.py` 7dc8c39a → TO_PINS — each card row and cell says the true reason: *here but locked — type the card's password once under Statement passwords*; *no statement dated <month> came from the bank — the next one did; download it from the bank's site into Drive > Credit Card Statements > <card>*; or *not come yet*. A newer locked statement never makes the month 'late'. The electricity row names the card statement its missing bill waits on (setting `packs.electricity_cards`, default the Amazon Pay card).
3. `/root/finance/packs.html` f5991911 → TO_PINS — the cell shows that reason.

**Proof:** `walk_s866.py` 18/18 on a made-up shelf (control on the live files red); the installer's shape check: last month's pack on a copy of the live database, old against new — only the card rows and the electricity row may differ. Rehearsal: dry, install, again, undo, undo again, red rollback, tamper, live moved, cron line present, lock held, no shelf line.

**Install:** his publish, then one server line (the installer's head). **Undo:** `bash /tmp/s866kit/install_S866_PACKS_LATE_AND_CARD_BILL.sh --undo`.

**His one step (no kit can do it):** the card passwords, typed once under *Statement passwords* on the page.

**Cold review (S480):** SAFE TO INSTALL. Its SHOULD built in (a card file of the month the shelf has not marked says *on the shelf but not opened yet*, never *not come*) and LOW 1 (a stored password that did not open it is named as such). LOW 2-4 left: the final read could overlap a cron read at :15 (harmless: one row per Drive file); the identify child has its own 600 s limit; the electricity line can be long.
