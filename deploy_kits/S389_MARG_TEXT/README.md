# S389_MARG_TEXT — Marg's one-click text export, read into the same .XLS (Sanjeevni, S281, 24-Sep-2026) · F-619

**The owner, 24-Sep:** *"There is some issue with Microsoft Office in the medical PC. So Excel is not being exported. So either I export a text file or a PDF file as you deem to be okay."* Text was chosen. A PDF is archived, but no figure can be read from it.

**The gap.** Nothing in the estate read Marg's text export: `C:\Users\Public\MARG\<id>\report.txt`.
- The watcher took only `.xls`, `.xlsx` and `.pdf`.
- The door refused by magic bytes.
- Every reader wants the 9-column sheet: the finance `marg_report`, the router with its signatures, `marg_ingest.sale_lines`, route B `marg-push`, and route C `sale_bill`.

23-Sep's bill-wise sale was missing for that reason.

**The change: medical PC only.** No change on the VPS, on manojz, or in any parent file.
- `marg_txt.py` (NEW) reads the bill-wise sales text export (item detail, CASH column, *End of Report*). It uses fixed columns measured from the report's own header line, and a bill row off those columns is refused. It drops the page furniture and carries the day and grand totals as printed. It writes **the same nine-column .XLS Marg's Excel export is**: BIFF8 in OLE2, standard library only, deterministic.
- `marg_watch.py` (f39ce036 → 491aded8) looks at every `report*.txt` in its folders; the content decides. A recognised report is converted and the .XLS captured, and the text is kept in `_captured_txt\`. Excel, PDF and the stick rule are unchanged.
- **HOLD BY DEFAULT.** Until `D:\SendToClinic\MARG_TXT_LIVE.txt` exists and begins with `LIVE`, a converted report goes to `_captured_txt\held\` and **nothing is sent**. A text held once is never sent later. So files arriving in any order cannot send anything early, and 22-Sep (already on the server from its Excel) is used only for the proof.

**Proof at build time.**
- `marg_txt.py --selftest` passes.
- `marg_watch.py --selftest` passes 25/25: 12 old checks and 13 new, covering hold, held-never-sent, `report*.txt` only, the cut-off file, the restart, and exactly marg_txt's bytes.
- The owner's 23-Sep text, through the **server's own readers** from the nightly bundle of 24-Sep:
  - finance `marg_report` reads it clean: 25 bills and 115 lines; gross 23,026.11, net 22,672.00 and cash 19,963.00, each equal to the printed DAY TOTAL;
  - the router says **VERIFIED SALE_BILLWISE/DETAIL 2026-09-23**;
  - `marg_ingest.sale_lines` gives 115 lines.

**Parity (`parity_s389.py`).** The owner's 22-Sep text, taken on hold, is compared with Marg's own 22-Sep .XLS (`d6ec4eb9`, in MargArchive): every bill field, every parsed medicine line, the router's verdict and the door's item lines. Only when that is GREEN is `MARG_TXT_LIVE.txt` delivered, by the same channel.

**Delivery.** Drive `ToMedical\_kit`: `marg_watch.py` from the built-in list (the agent restarts the watcher), plus one `KIT_MANIFEST.txt` line for `marg_txt.py`, md5-gated.
