# S724_FLOW_APPROVAL_TIED — the month-end flow opens on the right month; an approval holds only on the figures approved · the parent · session 390 · 06-Nov-2026

**For the owner, in one line.** The month-end flow now opens on the month just ended, and a Sheet 1 / Sheet 2 approval counts only while the figures you approved stay the same — if anything changes afterwards, the approve button comes back with the reason and the month cannot be locked on the old approval.

## Why — F-1128 (S389)
October's Sheets 1 and 2 read *approved by manoj 2026-10-05 20:49*, before October had run. Read at S390 in `/root/staff_register/staff_register.py`: the flow page opens on the **running calendar month** when no month is given (`_flow_ym` → today's month), while the lock desk opens on the month just ended. Approving on that page on 5-Oct, while September was being closed, wrote the approval against **October**. An approval was a bare row (who, when) with no tie to the figures, so on 6-Nov the lock accepted it for October's real sheets without a fresh look. (October is locked and paid; nothing here changes it.)

## What it changes — `/root/staff_register/staff_register.py` 7e92bc20 → ffbe8db2 (make_s724.py: 9 counted edits on the live bytes)
- The flow page, its approve fallback and a bad month all open on the **month just ended** (`_default_salary_ym`, the lock desk's own default).
- An approval keeps a **fingerprint** of every computed figure of the month (`pack_approval.fig_hash`, one column added on first use). The sheet pages, the flow page and the lock desk count an approval only when its fingerprint equals today's figures; otherwise the approve strip is back, saying *the approval by … on … no longer holds: the figures changed after it*. An approval from before fingerprints (any old row) does not hold.
- The **lock** recomputes and refuses an approval that is not of those figures. An approval press when the figures cannot be worked out approves nothing and says so.

## Proven
`walk_s724.py` **18 of 18** — the file's own Flask routes on a made-up database with a stand-in salary engine: the default month, the fingerprint stored and stable (key order, sets), a changed figure making both approvals stale on the sheet page, the flow page and the lock (nothing locked), approved again → holds and the lock passes the check, an old row stale, the engine missing → not approved. Control (the live file): **14 red**. The installer rebuilds the file from the box's own bytes (`make_s724.py --expect`) before placing it.

## Install (after the publish)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s724kit && cp -rp /root/deploy/repo/deploy_kits/S724_FLOW_APPROVAL_TIED /tmp/s724kit && bash /tmp/s724kit/install_S724_FLOW_APPROVAL_TIED.sh
```
## Undo
```
bash /tmp/s724kit/install_S724_FLOW_APPROVAL_TIED.sh --undo
```
