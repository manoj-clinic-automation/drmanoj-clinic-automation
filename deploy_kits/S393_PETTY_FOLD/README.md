# S393_PETTY_FOLD — Bhati's petty book: no repeated entries, and one screen

**What happened (24-Sep).** Bhati's book in the system said ₹15,980; his paper book ₹14,420. The Shavez diary top-up
of 9,000 had been saved three times (22-Sep 21:29:26, :38, :55 — the save had no guard), and Dr Bhawna's 20,000 twice.
On the owner's word those three entries were cancelled and the opening cash of ₹440 set: the book now reads ₹14,420.

**The fix.**
1. The same entry (kind, person, name, amount) by the same person within **10 minutes** is refused with
   *"Yeh entry abhi-abhi save ho chuki hai — dobara nahi likhi"*. Another amount, another person, or after
   10 minutes is saved normally; a cancelled entry never blocks.
2. **One screen.** Both the doctors' page and Bhati's page are folds: a strip on top (today · in hand · loan · taps
   waiting), then one line per section with its figure; a tap opens it and closes the one before. No JavaScript.
   Measured at phone size (375×812): both pages fit with every section closed (before: 3,541 and 3,787 px tall).

**Proof.** `walk_s393.py` 25/25 on a scratch copy of the live database: every rupee figure of the old pages is on
the new ones; 22-Sep's three saves replayed — the 2nd and 3rd refused; the live file (S300) is the negative control
(it takes all three). Screens checked at phone size by a second reader. `petty_book.py` 88f28571 → see SUMS.md5.
Restarts clinic-finance only.
