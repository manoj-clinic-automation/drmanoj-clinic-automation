# S382_REPORT_BAAKI — blood reports and X-ray photos pending, one tap

**The owner, 24-Sep-2026 (GO on the plan):** a list of the pathology reports not mailed — date, clinic ID, patient
name, all three compulsory — for Sukhveer at the pathology desk (with his attendance), both receptionists and Shavez;
the same flow for the X-ray photos (Shavez does Awdhesh's part); a tap when mailed; any discrepancy flagged.

**The tile "Report baaki" 🧪** (portal, Clinic section) → `https://followup.dr-manoj.in/finance/slips/pending`

| who | sees | taps |
|---|---|---|
| Sukhveer | Blood tab | Mail kar diya · Test nahi hua · Baad mein · a missing name |
| Alisha, Shivani | Blood + X-ray | the same, **+ Naya** (walk-in, reception's), the report-without-order lines |
| Shavez | Blood + X-ray | the same; the X-ray tab's Photo daal di · X-ray nahi hua |
| the doctors | both, read-only | — (a counts door for the Gist line comes next) |

**Blood line states:** *baaki* → *der ho gayi* (after the same day ends; next day 11 am for a test logged after 5 pm) ·
*mail bheja — aane ka intezaar* → *mail nahi aaya — dobara bhejein* (3 hours, or next day 11 am after a 6 pm tap) ·
*baad mein* (quiet 3 days). A report the mailbox catches clears its own line. A report for an ID nobody wrote a test
for is listed for reception: **Test hua tha** (walk-in, the test is written) or **ID galat** (fix it in Check karein).
**X-ray:** a slip with an X-ray and no photo filed → *photo baaki* → *der* next day noon; *Photo daal di* waits an hour
for the mailbox to file it, then flags. Every tap also answers the same item in **Check karein**, so nobody is asked twice.

**Proof.** `walk_s382.py` 32/32 on a scratch copy of the live database, its own days and IDs, the clock moved through
the day; the live `slip_log.py` is the negative control. `check_portal_s382.py` on a scratch copy of the portal: the
tile for sukhveer, alisha, shivani, shavez and the doctor, not for bhati or darpan; Sukhveer's attendance tile present.
