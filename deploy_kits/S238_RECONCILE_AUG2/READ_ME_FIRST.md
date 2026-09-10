# S238_RECONCILE_AUG2 — August stated record, revision 2

**The owner, 10-Sep-2026 (night):** "Ranjeet's, Shivani's and Sukhveer's August advances — they come off
August's salary."

Revision 2 adds three lines to the August stated record, one each for Ranjeet, Shivani and Sukhveer.
Each line says that ALL of that person's short-term advances dated in August come off the August salary,
and their short-term balances at 31-Aug become ₹0. That includes the advances that were booked against
September.

**First run, 10-Sep 22:07:** it stopped RED and wrote nothing. One of Sukhveer's advances had been
reversed and entered again after the ledger copy used for testing was taken, so the reference in the
record no longer pointed at a live advance. **Reconciler v1.1** now finds the advances when it runs, so
a re-entered advance is followed. It was proven on four ledger shapes: as tested, re-entered in August,
re-entered in September, and reversed only. The selftest had 0 failures in each.

At the end, the installer also prints August as the salary page computes it now. This is read-only and
uses the live settings and hold ledger.

The reconciler itself otherwise works as before. The installer places the new record and proves the tool on a
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
