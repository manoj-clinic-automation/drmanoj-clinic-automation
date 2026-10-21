# S610_ATT_DOUBLE_PRESS — the attendance page agrees with the salary sheet (double presses, duty Sundays) (S331, 21-Oct-2026)

**The owner, 21-Oct 18:56 IST, on Surendra's October attendance:** *"few days he has punched twice and is mentioned out
there wrongly."* On 2, 3, 4, 7, 9, 14, 15, 17 and 21 Oct he pressed the machine twice within the same minute on
arrival; https://attendance.dr-manoj.in/month showed the second press as his OUT time (09:22 / 09:22) and the day
view called it "left early". The salary sheet already ignores a second press within 30 minutes
(`att_month_report.ARTEFACT_WINDOW_MIN`, "double-punch artefact": no out, no early-exit deduction) — so his money
was never affected; only the attendance page was wrong.

**The one line (VPS):**

    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S610_ATT_DOUBLE_PRESS/install_S610_ATT_DOUBLE_PRESS.sh

**What it does:** `/root/att_dashboard.py` (ebd8bd85) by 14 exact edits (`edits_s610.py`): the month grid, the phone
view and the day view use the salary sheet's own artefact window and duty days; the day view says "pressed 2 times on arrival · no out
punch". Display only. **Proven by** `walk_s610.py` (made-up person, scratch punches; the old file goes RED).
**Undo:** `--undo` (`/root/s610_backup/`).

**And the blank Sundays (19:03 IST):** *"in attendance these 2 sundays are blank, absent isn't written there, and on top
of page it's written present 14, absent 5."* The page never counted a Sunday; the salary sheet counts a Sunday-duty
person's missed Sunday — Surendra (every-Sunday duty) has 7 absences on the sheet: 1, 11, 12, 13, 18, 19, 20 Oct. The
page now asks the salary sheet's own `duty_shift()`: an absence on a duty day is written **A** in red and counted; a
day that is not a duty day reads "off"; today is never counted before it ends. His row will read A = 7, as the sheet.

Those 7 days have no punch from his finger at all (and no unknown finger appeared): if he was working, the owner's
word marks them — nothing here invents a presence.
