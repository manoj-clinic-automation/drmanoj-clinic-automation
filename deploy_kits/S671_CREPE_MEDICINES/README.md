# S671_CREPE_MEDICINES — crepe bandages, every size, are Medicines · project Sanjeevni · session 359 · 28-Oct-2026

**For the owner.** Crepe bandages are pharmacy stock sold to patients, not consumables. The nine crepe rows now say *Medicines* by your word, as Leukoband has since your ruling of 18-Sep.

The owner, 28-Oct-2026 05:31 IST: *"crepe bandages, all sizes, and leukoband are stocked in pharmacy for selling to patients, and they shdnt be consumables."*
**Rows (finance.db `stock_item_section`), Consumables (the S268 seed, the word CREPE) → Medicines (source owner):** CREPE 8CM 3IN SUNLINE · CREPE BANDAGE 6CM 2IN · GLOCREPE · LEUKOCREPE 6 CM · LEUKOCREPE 8 CM · LEUKOCREPE 10CM 4IN · LEUKOCREPE 15CM 6INC · TOPCREPE 10 CM · TOPCREPE 15 CM. LEUKOBAND 4 INCH is already Medicines (owner, 18-Sep) and is not touched.
No code, no restart, no crontab. The count rounds, the stock statement's section totals, the piles and the expiry watch read the table at each use.
**Proven on the 28-Oct database copy:** check = 9 seed Consumables. Apply moved 9 of 9, and every other row of the 397-row table was byte-for-byte unchanged. A second apply was refused. Undo put back a table identical to the original.
**A crepe size Marg adds later** gets no row until the table is seeded again. Until then, screens that fall back on the word list class it Consumables. Named for the next section kit (the word lists in `section_map.py` / `stock_app.py` are a record, S268).

## Install
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s671kit && cp -rp /root/deploy/repo/deploy_kits/S671_CREPE_MEDICINES /tmp/s671kit && bash /tmp/s671kit/install_S671_CREPE_MEDICINES.sh
```
## Undo (the installer prints it with the backup's name)
```
cd /tmp/s671kit && /usr/bin/python3 -B s671_rows.py undo /root/finance/finance.db /root/deploy/s671_rows_before_<stamp>.json
```
