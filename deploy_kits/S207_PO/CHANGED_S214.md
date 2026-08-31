# CHANGED AT S214 -- supersede rule adopted (⭐1.5)

`po_build.py` now routes its FLOW-report file lists (sale / purchase exports)
through `../S212_SUPERSEDE/marg_effective.py` -- the S206 rule: two
exports of one period are not two datasets; the later or wider replaces
the earlier. Snapshot reports (STOCK_CLOSING / STOCK_EXPIRY) deliberately
keep their F-235 largest-for-date pickers.

Measured on the real archive at adoption, 31-Aug-2026: sale 16 files -> 13
counted (the 3 known overlaps excluded, named on stdout at every run);
purchase clean today, so no number changed. The rule pays the day the
month-to-date export cadence begins.

SUMS.md5 row for po_build.py regenerated the same day; everything else untouched.
