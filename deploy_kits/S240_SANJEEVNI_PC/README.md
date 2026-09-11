# S240_SANJEEVNI_PC — Sanjeevni items 1 and 3, the manojz half

Run AFTER the VPS kit `S240_SANJEEVNI_123` is GREEN. One line on manojz (Command Prompt):

    powershell -NoProfile -ExecutionPolicy Bypass -File "D:\dr-manoj-git\drmanoj-clinic-automation\deploy_kits\S240_SANJEEVNI_PC\S240_PC_INSTALL.ps1"

1. `push_purchases.py` (S224 folder) gets the **F-431** fix: the 22:30 feed ran in the same minute as the pull and
   read a running pull as "asleep", so the Purchases hub showed a false red every night. 47/47 of its own selftests,
   identical before and after.
2. `push_sale_bills.py` sends every archived SALE_BILLWISE export's bill money rows (money columns only — no name,
   phone or clinic ID leaves the PC). Refuses to send a bill that does not add up.
3. Task **MargPushEvery30** (hidden, allowed on battery, :15 and :45) sends new purchase exports and new sale bills
   every 30 minutes, so the server — and the missed-export check — are never more than half an hour behind.

Report: `D:\Downloads\margsync\_analysis\S240_pc_install_report.txt`. Undo: `schtasks /Delete /TN MargPushEvery30 /F`
and restore `push_purchases.py.bak_S240_13a5cb8e`.
