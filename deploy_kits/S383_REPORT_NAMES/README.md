# S383_REPORT_NAMES — step 3 of the Report baaki plan

1. **The name on the report.** The lab's e-mail subject carries the patient's name (it is in the filed report's name).
   When it is nothing like the name the clinic has for that ID — spelling, titles (Smt, Mr…) and short forms forgiven —
   reception gets a line on **Report baaki**: *Report par naam alag* → **Wahi mareez** or **ID galat**.
   On the week's real reports: 1 of 25 would have been raised.
2. **Your line.** The **Clinic Gist** tile now reads `📞 calls │ 🧪 N blood (late) · N X-ray · N mismatch`, and the Gist
   page opens with a **Reports pending** card that taps through to the list. Read in your browser; hidden when it
   cannot be read — never shown as zero.

**Proof.** `walk_s383.py` 37/37 (S382's walk + the name check + the counts) on a scratch copy of the live database;
`check_portal_s383.py` renders the Gist page and reads the tile script from a scratch copy of the portal; the S382
files are the negative control. `slip_log.py` 3e6cb9b0 → 30d799e1 · `portal.py` f9c7e306 → 80d6dc44. Restarts
clinic-finance and clinic-portal.
