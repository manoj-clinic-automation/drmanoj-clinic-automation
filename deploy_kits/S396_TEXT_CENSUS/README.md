# S396_TEXT_CENSUS — the medical PC tells Drive what text it saw, and why it did not take it (Sanjeevni, S281, 25-Sep-2026) · F-620

On 25-Sep the owner's 24-Sep bill-wise text export was not taken, and with manojz's link down nothing could show why.
Delivered through the Drive connector alone (ToMedical\_kit), each upload byte-checked before the swap.

**S396** — `marg_watch.py` 61414a5a → **6624df0b** (`marg_watch_S396.py` here), live 05:54:42 IST:
- ANY `.txt` in the watched folders is looked at; the content decides, not the name (Marg first writes `user_<id>.txt`, then `report.txt`).
- An unchanged file is not read again; only report-like text is kept in `_captured_txt\refused\`.
- Every ten minutes: `marg_text_census.txt` (every `.txt` under three days old where an export could land, with the verdict and the report's own title line — never a patient's name) and `marg_watch_log.txt` (the log's last 64 KB), written locally and into Drive `Clinic Data Archive\FromMedical`.

**S396.1** — `marg_watch.py` → **ce64bb31** (live 06:02:50 IST): every refused report text and its `.why.txt` (last three days, at most 12) is copied to `FromMedical\refused_text\`.

What it found at once: the 24-Sep export of 05:30 was the **SUMMARY** bill-wise (bills only, no item lines, no GRAND TOTAL). Re-exported with item detail from SET, it was taken 07:27:00 and the server answered SALE_BILLWISE VERIFIED 07:27:03.

`apply_s396.py` builds S396 from S395's 61414a5a; `apply_s396_1.py` builds S396.1 from S396. Selftest 28/28.
