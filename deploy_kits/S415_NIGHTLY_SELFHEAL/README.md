# S415_NIGHTLY_SELFHEAL — the missed nightlies (F-630)

**Measured from the reports folder on manojz:** the nightly ran 18-Sep 03:10 · 19-Sep 06:09 (catch-up) · 20-Sep 03:10 ·
21-Sep 05:13 (catch-up) · 22-Sep 06:16 (catch-up) · **23-Sep — nothing** · 24-Sep 07:30 (catch-up) · **25-Sep — nothing** ·
26-Sep 03:10. The task runs as the logged-on user (*InteractiveToken*). Windows catches up a missed start after **sleep**
(the 05–07 o'clock runs) but not reliably after a **shutdown or a sign-out** — a task that may only run when the user is
logged on has no session to catch up into, and the log-on itself is not a trigger. Nothing on the record says what the PC
was doing at 03:10 on the 23rd and 25th, because the Task Scheduler history log is usually off. Both halves are fixed here.

**What the kit does (files in `D:\Downloads\_kbtools\`):**
1. `NIGHTLY.bat` (S278 → S415): when started with the argument `morning` it asks `nightly_guard.py` whether today already
   has a run — exit 3 = yes, stop quietly (a one-line note in `reports\MORNING_*.txt`); otherwise the nightly runs as
   before. The inline PowerShell of S258 is replaced by `task_selfheal.ps1`. Nothing else in the file changes.
2. `task_selfheal.ps1`, run on every nightly: keeps the S276 catch-up flags, adds **wake-to-run** to the 03:10 task;
   creates (once) the task **"KB Manifest Rebuild - morning"** — daily 07:30 and at log-on (+3 min), running
   `NIGHTLY.bat morning`; switches the Task Scheduler history log on if it is off; writes
   `reports\TASK_HISTORY_LATEST.txt` — the two tasks' own events and the PC's sleep / wake / boot / shutdown / log-on
   events of the last 7 days, so the next missed night is read, not guessed. Every step try/catch; never fails the nightly.
3. `APPLY_S415.bat` — optional double-click: applies the same now instead of at the next 03:10, and writes the history at once.

**Proof.** `nightly_guard.py` exercised three ways (a report from another day → run; today's → exit 3; no report → run).
`NIGHTLY.bat` built from the live bytes (f0a070f2) by two anchored edits, CRLF kept. The PowerShell cannot run here; it is
written defensively and reports in words. `NIGHTLY.bat` f0a070f2 → see SUMS.md5.
