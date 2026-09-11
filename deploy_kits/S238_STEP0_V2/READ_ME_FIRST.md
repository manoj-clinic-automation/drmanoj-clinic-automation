# S238_STEP0_V2 — Step 0 on one page

**The owner, 11-Sep-2026, on the first real print:** "Format is good, only it's a 3-page printout. Make it
condensed by using the extra space on the page." He also asked to remove the explanatory paragraph at the
top and the note about the requests queue.

**Now (staff_register v0.18):**
- **Three dates per row.** Each date has its own P / L / A tick boxes (about 4 mm) and a Fixed box.
- Rows are tighter.
- **Both paragraphs are gone.** A one-line hint stays in the header: "tick P / L / A from the register,
  then Fixed".
- Sundays are still shaded, corrected days are still greyed, and the header still repeats if a second
  page is needed.

August's real shape (11 staff, 81 dates) now fits on **1 page** instead of 3. It was rendered to A4 PDF,
and the sub-agent's visual check was clean. The staff_register selftest passes. Only the page layout
changes; no figure changes anywhere.

```
bash /root/deploy/vps_deploy.sh S238_STEP0_V2
```
