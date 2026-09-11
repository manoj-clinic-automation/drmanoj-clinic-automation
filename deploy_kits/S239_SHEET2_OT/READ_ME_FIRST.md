# S239_SHEET2_OT — Money page: "Leave days counted" removed; Late minutes, Overtime and Cover duty shown

**The owner, 11-Sep-2026 (reading the August Money page):** in *All fines, leaves & credits*, the
"Leave days counted" column is extra — delete it; the overtime columns are missing — every staff should see
their overtime; and Shivani's cover duty. Then: "please add late minutes also".

**salary_policy v1.12 → v1.13, display only.** The table drops one column and gains five: Late minutes, Overtime
(minutes, ₹) and Cover duty (days, ₹; "-" for staff with none). No figure, no net, no rule changes — the
installer's probe computes the month with the live and the new file, refuses unless every computed number is
identical and every other cell of the table is unchanged, and prints each person's late minutes, overtime and cover.

```
bash /root/deploy/vps_deploy.sh S239_SHEET2_OT
```
