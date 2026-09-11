# S240_SANJEEVNI_123 — Sanjeevni plan items 1, 2, 3 (VPS half)

**Built 11-Sep-2026, Session 240. Approved at S239 (D462): "if it is a sound and safe tech call, then I give my go ahead".**

| item | what it does | where you see it |
|---|---|---|
| 1 · missed-export check | On a day Amir punches in: PURCHASE BILL WISE and the item-wise report (1st → date) that day, and the stock closing that night or before 10:30 next morning. **Supplier-wise only at month-end** (1st–5th, for the whole last month) — the owner's ruling of 11-Sep. Missing = a red line. | Marg Purchases hub (English) · Amir's salt page (Hinglish) · one phone push next morning |
| 2 · spine cadence | The item spine re-runs every 30 min when its sources move, and every night, and writes what changed (new names, unresolved, new tasks). | `/root/finance/spine_drift_latest.txt` · table `marg_spine_drift` |
| 3 · sale bills | Every sale bill's own money row (gross, discount, tax, net, cash) arrives from manojz — money columns only — and is kept in `sale_bill`. | nothing visible yet (Rung 3 is the side-by-side, on your word) |

**The door (the assistant's call, changed from S239 after reading the code):** the sale bills come through the
purchase door that already exists (`/finance/purchase/api/push`, type `SALE_BILL`). No export file travels, no name
or phone travels, `finance_app.py` and the gate are not touched. `/finance/api/marg-push` was not used because it
re-stages item lines for the books and refuses a file it has already seen.

**Install — one line on the VPS, after the publish:**

    bash /root/deploy/vps_deploy.sh S240_SANJEEVNI_123

Gates: SUMS + KIT_ID → live `purchase_app.py` must be rev 12 `3adad7f9` and `sale_bill.py` the S237 copy, else it
refuses and changes nothing → selftests on the box → a dated copy of `finance.db` → place → restart → healthz +
gate probe. If the app does not answer, rev 12 is restored and the service restarted by itself.

**Undo:** `\cp /root/finance/purchase_app.py.bak_S240_3adad7f9 /root/finance/purchase_app.py` then
`systemctl restart clinic-finance.service`, and remove the four `# S240_SANJEEVNI` cron lines.

Then the manojz half: `deploy_kits\S240_SANJEEVNI_PC\S240_PC_INSTALL.ps1`.
