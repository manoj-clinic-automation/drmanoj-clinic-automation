# S238_SHEET2_REVIEW — step 0 for attendance, and Sheet 2 made plain

**The owner, 10-Sep-2026 (night), after reading the new money sheet:**

1. Staff forget punches. Before the final salary, list each staff member's machine-absent days
   so they can be checked against the physical attendance register and corrected. What is left
   is the final attendance.
2. Advances are almost always against the running month. Flag any that was booked against a
   later month, so a slip can be corrected.
3. The second table is the advances and loans still open. For each one, show whether it is
   recovered in one go or on instalments, and for instalments, how much a month and until when.
   Its headings were misleading.
4. In the fines table, "Leaves 7 / Absent 4" read like 11 days not punched. Remove that ambiguity.
5. Print on A4, with the fines table in landscape.
6. The ENFORCED line is for the owner only. It must not print.
7. A hold is only marked. It is paid, not withheld. A 20% improvement cancels it (30% was too
   high); otherwise it is deducted the next month.

**Now:**

- **Step 0 on the month-end flow.** A printable A4 list shows, for each staff member, every
  rostered day with no punch, with a box for P / L / A as the physical register shows it. Days
  already corrected are shown as done. The Fix-absents desk is one click away. The flow page
  shows how many days are still absent.
- **Sheet 2, advances taken.** Each advance says how it is actually recovered. Anything booked
  against a later month than the month it was given is shaded and flagged "later month — check".
- **Sheet 2, still being recovered.** For each advance there are two columns, "Recovered in one
  go" and "On instalments". The instalment column gives the amount a month, the first and last
  months, and any smaller first or last amount. These months are worked out with the ledger
  close's own rules. Checked against the real close engine run for September to January on the
  August ledger: 19 of 19 advance-months agree. The one other row in the comparison is an advance
  given in September, which the August sheet rightly does not list.
- **Sheet 2, fines.** "Days not punched" is split into sanctioned leave, outstation and absent
  without leave, so it is one set of days and nothing is added twice. It is followed by "Leave
  days counted" and "Days off allowed".
- **Print.** Sheet 2 prints on A4 landscape, and each section stays whole. The ENFORCED/PREVIEW
  line shows on screen only.
- **Holds.** The wording says the hold is marked and paid, not deducted. improve_pct is set to
  20 through the same audited door the settings page uses.

**Unchanged:** every rupee of the Advance line. The installer proves this before it replaces
anything, running the live engine and the new one in separate processes (F-414).

## Install — after the publish, one line on the VPS
```
bash /root/deploy/vps_deploy.sh S238_SHEET2_REVIEW
```
