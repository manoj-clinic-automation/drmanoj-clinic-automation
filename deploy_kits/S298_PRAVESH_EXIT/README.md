# S298_PRAVESH_EXIT

**One line on the VPS:**

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S298_PRAVESH_EXIT/install_S298_PRAVESH_EXIT.sh
```

The owner ticked steps 1–6 of Pravesh's exit (EXIT-2026-0001) on 16-Sep and stopped at step 7, whose wording was borrowed from the joining flow ("the person appears"). Step 7 is not a tick: read on 17-Sep, the staff master still had Pravesh (code 17) active, the attendance register still had him active, and code 17 had never been retired.

**A — the words.** `joiner_app.py`: on an exit, step 7 reads *"staff master and attendance register updated — the person no longer appears"* with *"Claude does this step … Tell Claude who left and the last working day."* Joining is unchanged.

**B — the step itself, for Pravesh.** `exit_s298.py`: staff_master.csv active Y→N on his one row (every other byte untouched); register last working day 31-Aug-2026 and inactive (the register's own resignation rule, so August days keep him); code 17 retired, never reissued; step 7 ticked by "Claude (kit S298)"; record COMPLETE. **Refuses unless August 2026 is locked** — the month report drops an inactive person from every month it runs, so his August pay must already be frozen. Prints how many punches the device has taken under code 17 since 31-Aug.

**Proof:** exit selftest 12 checks (negative controls red at 1, 3, 5, 11) · walk 6 checks through the real joiner_app over a copy of finance.db, the old file red at 2 · the tool run on a copy of the real finance.db, then undone to identical tables · a BOM-headed staff master changed by exactly one byte · installer rehearsed on a fake root.
