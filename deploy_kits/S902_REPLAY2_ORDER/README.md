# S902_REPLAY2_ORDER — Replay 2 tells "the same rows in another order" from a real difference (the parent, S493, 20-Nov-2026)

S901 (18:26 IST) showed every differing Call Sheet cell sits in the sheet's LAST rows, with name-, mobile- and ID-shaped cells
swapped among themselves: the same rows, another order. A sort tie — the box's Python 3.9 allows numpy no newer than 2.0.2,
whose default sort breaks ties unlike the PC's. `replay2_s897.py` 92074846 → S897.4: a sheet whose rows are identical as a set is
ORDER (said and counted apart), not FAIL; the RESULT line reads pass / order-only / fail. The installer also lists the box's
Pythons — a 3.10+ one lets a venv carry the PC's own library versions, and then the engine's one extra line (S900) goes too.

Install (server, one line):
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s902kit && cp -rp /root/deploy/repo/deploy_kits/S902_REPLAY2_ORDER /tmp/s902kit && bash /tmp/s902kit/install_S902_REPLAY2_ORDER.sh
```
Undo: `bash /tmp/s902kit/install_S902_REPLAY2_ORDER.sh --undo`.
