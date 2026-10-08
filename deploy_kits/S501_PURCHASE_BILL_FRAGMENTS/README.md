# S501_PURCHASE_BILL_FRAGMENTS — manojz only (Sanjeevni, session 301, 08-Oct-2026, F-800)

**What.** `push_expected.py` (our own computed stock figure, pushed to the server) refused every run from 08-Oct 09:0x IST:
*"8 purchase line(s) could not be dated"*. Marg's SUPPLIER/ITEM WISE purchase statement prints only 8 characters of a long
bill number, glued onto the item name (`06202627ANKLE BINDER BAMBOO M`, `A000207_TYRO BR`), or cut so the reader keeps a tail
(`L2678591` of `GPPL2678591`). The BILL WISE export carries the whole number. Without the computed figure Amir's orthotic
voucher proof (stage A) can never be checked, so his renames never open.

**The fix.** This folder's `push_expected.py` is S480's (`1ba529851eed04973e4bd540547c447c`) with ONE helper,
`_s501_fragment`: an undated ITEM WISE row is dated from its supplier's own BILL WISE / SUPPLIER WISE bill number when
EXACTLY ONE of that supplier's bills holds the longest piece (6 or more characters) of what Marg printed; the item name is
then the text after the piece. Anything else stays undated and the run still refuses, as before. Every row it dates is
printed (`S501 dated from the bill-wise number: …`). Its readers stay S480's (`sys.path` puts S480 next after this folder).

**Proof (dry run on the real archive, 08-Oct ~09:55 IST):** S480's file refuses with the 8 lines; this file dates all 8
(Gunina GPPL2678591 ×1, GPPPL3679039 ×2; Kedar A000207_ ×1; Yuvika YS0706202627 ×4) and computes
`EXPECTED AS ON 07-10-2026 : 384 items`, `purchases known to 08-10-2026 -- complete for this date`.

**Installed by** one line of `D:\Downloads\margsync\PUSH_STOCK_DAILY.bat`: `set KIT=` now points here (the old file is
beside it as `PUSH_STOCK_DAILY.bat.bak_S501_fe8b7f54`). PUSH_STOCK_NIGHTLY.bat and expected_on_capture.py call that file.

**Undo:** copy `PUSH_STOCK_DAILY.bat.bak_S501_fe8b7f54` back over `PUSH_STOCK_DAILY.bat`.
