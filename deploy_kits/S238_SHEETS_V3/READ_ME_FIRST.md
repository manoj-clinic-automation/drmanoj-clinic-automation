# S238_SHEETS_V3 — last month's hold in plain sight; Sheet 1 made for the register check

**The owner, 10-Sep-2026 (late night), reading Sheet 2 of August:**

- The advances table said "from the September salary". That was the ledger as it stood before the
  correction (S238_RECONCILE_AUG2 `--apply`). Once the correction is applied, those rows read "from the
  August salary — cleared". Nothing in this kit is needed for it.
- "July holds — deduction / write-off column should be in All fines, leaves & credits too."
- Sheet 1 month summary: show the days not punched the same way Sheet 2 does, **with the dates**
  (Sundays highlighted), for cross-checking against the physical register when solving staff requests.
  Add the late fine (the total, with no hold split) and overtime with OT payable.

**Now (salary_policy v1.10, staff_register v0.15):**

- **Sheet 1, month summary** (A4 landscape): Present · Days not punched (total / sanctioned leave /
  outstation / absent without leave) · the dates themselves (Sundays in purple, L = sanctioned leave) ·
  Late marks · Late min · Late fine (total) · OT min · OT payable · a blank remark column when printed.
  A staff member's own copy never shows money.
- **Sheet 2, fines table**: two new columns under "Jul hold", "deducted now" and "written off".
- **Sheet 3 (salary sheet)**: "Prev hold deducted" and "Prev hold written off" in place of the single
  "Hold released", plus "OT paid". Sheet 3 now prints on A4 landscape with every column. Sheet 4, the
  signature sheet, stays portrait (and its "&amp;" misprint is fixed).
- **Overtime** uses the attendance report's own OT minutes: minutes beyond shift end on days with a
  real out-punch, at 2 × the person's own minute-rate (D256). It is **shown, not paid**, until the new
  setting *Overtime payable enters the net* is set to 1 on the settings page.

**Unchanged:** every net figure (the probe checks this, person by person), and every advance deduction.

**Proven:** both selftests pass. The sheets were rendered to A4 PDF, and a sub-agent's visual check was
clean after two print fixes (Sheet 3 landscape, the "&amp;" misprint). The installer walk covered green,
a re-run, red, the wrong live file, and a tampered kit. The probe was stub-tested: it passes when only
OT is added and fails when a net moves.

```
bash /root/deploy/vps_deploy.sh S238_SHEETS_V3
```
