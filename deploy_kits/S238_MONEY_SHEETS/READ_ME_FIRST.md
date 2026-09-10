# S238_MONEY_SHEETS — the money sheets say what the ledger says, and print cleanly

**Built 10-Sep-2026 (S238) from the owner's review of August's Sheet 1 and Sheet 2.** It replaces the
unpublished `S238_SHEET1_PRINT`, whose Sheet 1 change is carried in here unchanged.

## WHAT CHANGES

**1 · The Advance column is the ledger's own.** The register used to work out advance deductions itself,
from each advance's balance *today*. For August that would have taken Darpan ₹29,000 (your record:
₹20,000), Surendra ₹0 (₹7,000), and Ranjeet, Shivani and Sukhveer's advances a month early. Now it deducts
exactly what the staff ledger recorded for the month. **The Lock refuses until the ledger has closed that
month.**

**2 · Sheet 1** prints as two A4 pages: the attendance grid with every day on the first, and the month
summary on the second.

**3 · Sheet 2**
- *Advances taken this month* — reversed (mistaken) entries are left out, and the old "Instalment"
  column is now **"How it is recovered"**: *in full from the August salary*, *Aug 8,000 · Sep 4,000 …*,
  or *loan · 5,000 a month*.
- *Open advances & loans* — **the position at the end of the month**, not "as of today": open at the
  start · taken · recovered · interest · open at the end, one line per person. Darpan's page shows each of
  his advances and a total. A locked month reads the same on any later day.
- *Improvement holds* — the last month's hold and **what happened to it, in words** (cancelled,
  collected, still held). If the last month was never locked, it says that plainly.
- *Printing* — every section stays whole on one A4 sheet, and several share a sheet when they fit.

## INSTALL — after the publish, one line on the VPS
```
bash /root/deploy/vps_deploy.sh S238_MONEY_SHEETS
```
**Before it replaces anything**, it works out August with the current engine and the new one side by
side and prints both, person by person, next to what the ledger recorded. It refuses if the new figure
differs from the ledger for anyone. Both files go in together, or neither does.
