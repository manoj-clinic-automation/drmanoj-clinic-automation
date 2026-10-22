# S629_ONE_NAME_LIST_R2 — S628 re-issued (the walk only)

**Project:** Sanjeevni (session 339, 22-Oct-2026). Built IN THE CHAT. Brief: `claude_code_briefs/S628_ONE_NAME_LIST.md` (v2) — unchanged.

**Why a new number:** S628_ONE_NAME_LIST was published (947b661, 18:50:28 IST) and its installer, on the box at 18:51:48 IST, STOPPED at [5/9]:
the walk on the NEW files was green on the live copy (69 checks, 27 controls), but the negative control had one control green on the OLD
files. The walk planted the owner's ask on B-0176 to show the scans page's sender line; the owner had since moved B-0176 to the clinic lane
(409 not_pharmacy), so the OLD page had no ask to print in Hindi. **Nothing was installed** (no file placed, no restart, no database write;
the lock released). S628 is frozen (CLAUDE.md rule 11); this kit carries the SAME five built files — the same `make_s628.py`, edit lists,
`med_names.py` and TO pins — and `walk_s629.py`, which plants the ask on the first pharmacy scan the copy accepts.

Everything else — what changes, for whom, the files and pins, how, the undo — is S628's README (`deploy_kits/S628_ONE_NAME_LIST/README.md`).
Backups here are `*.bak_S629_<from8>` and `finance.db.bak_S629_<stamp>`.

| file | FROM | TO |
|---|---|---|
| /root/finance/stock_figure.py | 8c66b6b1 | a0008c14 |
| /root/finance/porders.py | b1736494 | 3209d0a2 |
| /root/finance/order_track.py | a8c46700 | 4edfef6b |
| /root/finance/porders_s454.py | 53ef850f | 0ce83525 |
| /root/finance/med_names.py | NEW | a7439e3f |

## Install (the owner's one server line, after his publish)
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S629_ONE_NAME_LIST_R2/install_S629_ONE_NAME_LIST_R2.sh
```
