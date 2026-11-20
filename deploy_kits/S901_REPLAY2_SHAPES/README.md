# S901_REPLAY2_SHAPES — Replay 2 names the Call Sheet columns that differ (the parent, S493, 20-Nov-2026)

S900 put the engine on its feet on the box (Python 3.9): Replay 2 then ran every evening, every data file agreed with the PC's
next snapshot (only the random Revenue_ID, as Replay 1), and the workbooks agreed on every tab but one — **the Call Sheet**,
15–46 cells a run, against the PC's own uploads in the receiver's inbox. A count cannot be read. `replay2_s897.py` 2a79ea7a → S897.3:
each differing cell is described by its column header (row 1), row number and the two cells' types and lengths — never a value.
The installer shows one run in full (#7) and then the whole month's counts.

Install (server, one line):
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s901kit && cp -rp /root/deploy/repo/deploy_kits/S901_REPLAY2_SHAPES /tmp/s901kit && bash /tmp/s901kit/install_S901_REPLAY2_SHAPES.sh
```
Undo: `bash /tmp/s901kit/install_S901_REPLAY2_SHAPES.sh --undo`.
