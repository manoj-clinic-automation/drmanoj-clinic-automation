# S397_STOCK_TEXT -- Sanjeevni project, S281, 25-Sep-2026

Marg's text export of the WHOLE STORES CLOSING STOCK, read into the same four-column sheet Marg's Excel
export of it is, so nothing downstream changes (the Office on the medical PC is broken; Excel exports stopped).

Files, all for D:\SendToClinic on the medical PC, delivered through Drive ToMedical\_kit:
* marg_txt.py   38d85298 -- S397: kind() SALE | STOCK; stock_rows(); the sale path is byte-identical to S389.2.
* marg_watch.py 81145aa7 -- S397: at every start offers every text refused in the last three days to the
  reader again (the 24-Sep stock, kept at 07:36:58 on 25-Sep, is taken this way); clearer stock reasons.
* KIT_MANIFEST.txt 8230562e -- the marg_txt line moves 76b5eb5d -> 38d85298.

Order: marg_txt.py + KIT_MANIFEST.txt first; marg_watch.py only after the heartbeat shows marg_txt 38d85298
(a watcher restarted before the reader arrives would re-refuse, and not retry until its next start).

Proof (PROVE_S397_RESULT.txt, GREEN 14/14): the spine reader S331.1 reads Marg's 23-Sep Excel and the
converted 24-Sep text with every check passing; the router identifies both as STOCK_CLOSING/TOTALS; every
letterhead, title, heading and page-furniture row is identical cell for cell; the same 378 items fall on
the same rows; and 23-Sep closing - 24-Sep sales = 24-Sep closing on every item (the four KNEE SUPPORT
HINGED sizes as one family, as the sale report cuts names at 20 letters), 26431 - 1085 = 25346.
The only row Marg's Excel has that this does not: Marg's own advert line under TOTAL, which every reader
already sets aside as furniture.
