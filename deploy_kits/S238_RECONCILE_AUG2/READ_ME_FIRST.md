# S238_RECONCILE_AUG2 — August stated record, revision 2

**The owner, 10-Sep-2026 (night):** "Ranjeet's, Shivani's and Sukhveer's August advances — they come off
August's salary."

Revision 2 adds six recovery lines to the August stated record: Ranjeet ₹5,000 + ₹1,000, Shivani
₹1,100, and Sukhveer ₹6,000 + ₹4,000 + ₹4,000. Each of their short-term balances at 31-Aug becomes ₹0.
This includes the two advances that were booked against September (Ranjeet's ₹1,000 and Sukhveer's
₹4,000), because both were given in August.

The reconciler is unchanged (v1.0). The installer places the new record and proves the tool on a
throw-away copy of the real ledger. It then prints the dry run. **It never writes.** Writing is one
separate line, `--apply`.

**Proven offline** against staff_ledger v3.7 on the walked August ledger:
- The dry run shows 6 corrections and 0 blocked.
- Apply wrote 6 rows (58 → 64), took a backup and passed its re-check.
- A second run finds 0 to do.
- Selftest: 9 checks, 0 failures.
- The salary engine then reads the August Advance deductions as Ranjeet ₹6,000, Shivani ₹1,100 and
  Sukhveer ₹14,000. Their September closes take ₹0.

```
bash /root/deploy/vps_deploy.sh S238_RECONCILE_AUG2
```
