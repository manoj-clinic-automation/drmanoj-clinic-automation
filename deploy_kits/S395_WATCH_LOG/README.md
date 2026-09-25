# S395_WATCH_LOG — the watcher says what it did, and keeps what it would not take (Sanjeevni, S281, 25-Sep-2026) · F-620

About 05:30 IST on 25-Sep the owner exported 24-Sep's bill-wise sale as text, and it was not taken: 0 captures, heartbeat 05:30:55. Nothing showed why. `medical_agent.start_watcher` starts the watcher with stdout and stderr sent to DEVNULL, and a text report `marg_txt` turns down was neither kept nor explained.

`marg_watch.py` ce41fdaa → **61414a5a**:
- Every message is also appended to `D:\SendToClinic\marg_watch.log`, dated, capped at 1 MB with the last 256 KB kept. The pull mirrors it to manojz every ten minutes. At start it says which text reader it has and whether the text route is LIVE.
- A `report*.txt` that is finished (its size holds still) but not taken is copied **once** to `_captured_txt\refused\`, with a `.why.txt` giving the reason: not a bill-wise report (with its first line), the CASH header missing, *End of Report* missing, or the reader's own refusal with the line it stopped at.
- What is taken, and how, does not change. The selftest passes, including the two new checks.

Delivered by the Drive kit channel. `marg_watch.py` is on the agent's built-in list, so the agent restarts the watcher, and the first sweep after the restart looks again at every report*.txt in its folders.
