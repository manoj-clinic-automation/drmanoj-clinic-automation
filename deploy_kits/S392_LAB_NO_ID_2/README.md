# S392_LAB_NO_ID_2 — the originals that arrive after their resends

S391 went live and cleared 8 of the 9 mailed lines at the next mailbox run. Then the **original** ID-less reports of the
21-Sep and 22-Sep evenings reached the server — after today's resends, because the mailbox reads the newest mail first.
Each found its blood test already closed by the resend, and S391's re-send rule only looked backwards in time, so they
were listed on Report baaki as *Report aayi, ID nahi likha* (9 lines + 1 genuine: a name with no test written).

**Fix:** the re-send rule looks both ways — the same exact name placed within the lab window, earlier or later, is the
same patient. The unsure rows are swept at the next look at Report baaki; the mailbox then files their PDFs.

**Proof.** `walk_s392.py` 41/41 = S391's 38 + the originals-after-resends case (all nine join, a name with no test still
waits, the line's report date becomes the original's day). The live S391 file is the negative control (it cannot place
them). `slip_log.py` 00038e76 → ffb629c1. Restarts clinic-finance only.
