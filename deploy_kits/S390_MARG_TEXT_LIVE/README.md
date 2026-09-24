# S390_MARG_TEXT_LIVE — the text reader, corrected and switched on (Sanjeevni, S281, 24-Sep-2026) · F-619

S389 went in at 19:47:21 IST, and the medical PC took the owner's 22-Sep text **on hold**:

- text `abb7271f` became .XLS `9b8099f9`, **byte-identical to the build box's own conversion**;
- the parity run against **Marg's own 22-Sep Excel** (`d6ec4eb9`) found all 27 bills identical in every field and the grand total equal to the paisa;
- it went **RED on the medicine lines**: a line number of two digits (10, 11, 12) starts one column earlier in the text, and S389.1 lost its first digit.

**Fixes.**
- `marg_txt.py` S389.2 (`76b5eb5d`) reads the item line from its own first character. **PARITY GREEN 10/10** (`PARITY_22SEP_RESULT.txt`): every bill field, every parsed medicine line, the router's verdict, and the door's 133 item lines.
- `marg_watch.py` `ce41fdaa` re-reads `marg_txt.py` whenever it changes. Without this, the watcher would keep the reader it loaded at start, and an update to the reader would wait for the next restart. Proven: 25/25 selftest, plus a reload proof.

**Two steps, in order.** The live marker must never arrive before the corrected reader.
1. `marg_txt.py` and `marg_watch.py`, plus `KIT_MANIFEST_step1.txt`. The agent restarts the watcher.
2. Only after the agent's log confirms both are installed: `MARG_TXT_LIVE.txt`, via `KIT_MANIFEST_step2.txt`. From then on, a bill-wise text export is sent as the .XLS it becomes.

**The held 22-Sep is never sent.** A text held once is refused for ever, and 22-Sep is on the server already from its Excel.

To put the reader back on hold, delete `D:\SendToClinic\MARG_TXT_LIVE.txt`.
