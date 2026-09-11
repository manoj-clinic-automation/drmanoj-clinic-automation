# S238_SHEETS_V4 — Step 0 as a proper A4 sheet; Amir by punch dates; Shivani's cover-duty OT

**The owner, 11-Sep-2026:**

- "Step 0 sheet is very crude, needs to be A4 print friendly."
- "Amir not needed in attendance full grid, I only need to know his punch dates of the month."
- "Shivani overtime misses her cover duty logic. Overtime should be for time beyond the normal cover
  time she overstayed. Her cover duty is from 4–9 pm."

**Now (salary_policy v1.11, staff_register v0.16):**

- **Step 0** is one clean A4 portrait table:
  - The staff name spans that person's rows.
  - Each row has the date and day, "Physical register says" with P / L / A tick boxes, and a "Fixed in
    system" tick box.
  - Sundays are shaded, with a dark bar that survives black-and-white printing.
  - Days already corrected are greyed.
  - The header repeats on every page, and no person's rows split across pages.
  - At the end: a "Punch dates only" box and Checked by / Signature / Date lines.
- **Amir Sohail** (new setting *Staff shown by punch dates only*) is out of the Sheet 1 grid and out of
  Step 0. Sheet 1 shows "Amir Sohail — punched on N day(s): …", and Step 0 lists his punch dates at the
  end.
- **Overtime on an extra-duty (cover) day** counts only the minutes after the cover ends (new setting
  *Extra-duty (cover) ends at*, 21:00). The cover hours are already paid as extra duty. On other days,
  OT is unchanged.
- The key under the printed grid no longer says "hover".

- **Overtime is paid** (the owner, 11-Sep-2026: overtime is the incentive for staff not to rush home when
  the clinic runs late). The installer sets *Overtime payable enters the net* to 1 through the audited
  settings door. An optional **daily threshold**, which ignores a day with less than 15 minutes of
  overtime (punch-out drift), is on the settings page. It is **OFF** by default.

**What moves:** each net rises by exactly that person's overtime paid, and by nothing else. The
installer's probe checks this person by person before anything is replaced.

**Proven:**
- Both selftests pass.
- The OT rules were unit-tested: on a cover day, out at 21:20 → 20 min and out at 20:50 → 0; with the
  threshold on, a 10-minute day drops out; with the threshold off and no cover days, nothing changes.
- The new settings save and validate (a bad time is refused).
- Sheets rendered to A4 PDF. The sub-agent's visual check was clean after polish.
- Installer walk: green, re-run, red, wrong live file, and tampered kit.

```
bash /root/deploy/vps_deploy.sh S238_SHEETS_V4
```
