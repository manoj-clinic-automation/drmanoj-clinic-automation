# S239_SHEET2_PARTTIME — part-time staff shown by the days they punched

**The owner, 11-Sep-2026:** "Amir Sohail is a part-time worker whose days are Sunday and Thursday, and
sometimes he changes them. In the leave, fine and credit table he does not find a column. I want his report
so that I can see when he has punched in the month. He does not fit here at all."

salary_policy v1.14 → v1.15, display only. Part-time staff (setting *dates_only_staff*, today Amir Sohail):
- leave the Sheet 2 *All fines, leaves & credits* table and the Sheet 1 days-not-punched table;
- appear on Sheet 2 under **Part-time staff — days punched**: date, day, in, out, and the count.

The probe refuses unless every computed figure is identical and the fines table is exactly the old one
without him; it prints how his pay is worked today, for the owner.

```
bash /root/deploy/vps_deploy.sh S239_SHEET2_PARTTIME
```
