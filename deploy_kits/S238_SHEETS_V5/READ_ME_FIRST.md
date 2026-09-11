# S238_SHEETS_V5 — Shivani: overtime for up to an hour's overstay, cover pay after 5 pm, OT after 9 pm

**The owner, 11-Sep-2026:**

- "The punch after 8 pm automatically should cover for this... so compulsion of marking cover duty is
  not needed; it is now verified with the out punch."
- Then, refined: "If she, on her normal duty days, overstays up to an hour, she gets OT as 2× salary rate
  as prescribed, and beyond 5 pm she gets cover duty rate payment for that day, so she will have
  incentive to spend a few minutes more and not rush back at 4."

**Now (salary_policy v1.12, staff_register v0.17):** for staff the register marks cover-eligible
(Shivani only), the out-punch decides the day:

| She leaves | Paid |
|---|---|
| before 17:00 (up to 1 hour past her 16:00 shift end) | overtime for those minutes at 2 × her rate (₹71.67/hour) |
| 17:00 or later | cover-duty payment for the day (₹200), no overtime before 21:00 |
| after 21:00 | ₹200 plus overtime for the minutes after 21:00 |

- Days marked as extra duty in the register still count as cover days. No date is counted twice.
- Both times are settings: *Cover staff: a punch-out at/after this time is a cover day* (17:00) and
  *Extra-duty (cover) ends at* (21:00).

**What moves:** only Shivani's overtime, her extra-duty credit and her net. The net moves by exactly those
two amounts, and the installer's probe checks this before anything is replaced. Nobody else changes.

**Proven:** both selftests pass. A unit test on out-punches of 16:55, 16:20, 17:30, 19:55, 20:15 and
21:30 gave 4 cover days (₹800) and 105 minutes of overtime (55 + 20 + 30 after 21:00), exactly as
specified. Other staff are untouched. The installer walk covered green, re-run, red, wrong live file, and
tampered kit.

```
bash /root/deploy/vps_deploy.sh S238_SHEETS_V5
```
